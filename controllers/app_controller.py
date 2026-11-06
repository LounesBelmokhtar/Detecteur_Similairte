"""
Contrôleur principal de l'application graphique (C du modèle MVC).

Il orchestre le chargement des fichiers, la sélection du niveau de comparaison,
l'exécution dans un thread séparé, l'agrégation des résultats et les exports.
Toute mise à jour de l'interface passe par les méthodes publiques de la vue.
"""

from __future__ import annotations

import os
import threading
from typing import Dict, List, Optional, TYPE_CHECKING

from models.config import THRESHOLD_LOW
from models.loader import SourceFile, load_source_file
from models.methods.base import SimilarityResult
from models.methods.level1_text import Level1TextMethod
from models.methods.level2_tokens import Level2TokensMethod
from models.methods.level3_structure import Level3StructureMethod
from models.ranking import CandidateRank, classify_alert, rank_candidates

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les annotations
    from views.main_window import MainWindow


class AppController:
    """Contrôleur reliant la fenêtre principale au modèle métier."""

    def __init__(self, view: "MainWindow") -> None:
        self.view = view
        self.results: List[CandidateRank] = []
        self.reference_source: Optional[SourceFile] = None
        self.candidate_sources: Dict[str, SourceFile] = {}
        self._comparing = False
        view.attach(self)

    # =========================================================================
    # Lancement de la comparaison
    # =========================================================================
    def start_comparison(self) -> None:
        """Valide la configuration puis lance la comparaison dans un thread."""
        if self._comparing:
            self.view.show_info("En cours", "Une comparaison est déjà en cours.")
            return

        cfg = self.view.get_config()
        ref_path = cfg["reference_path"]
        cand_paths: List[str] = cfg["candidate_paths"]

        if not ref_path:
            self.view.show_warning("Référence manquante",
                                   "Veuillez sélectionner un fichier de référence.")
            return
        if not cand_paths:
            self.view.show_warning("Candidats manquants",
                                   "Veuillez ajouter au moins un fichier candidat.")
            return

        self.reference_source = load_source_file(str(ref_path))
        if not self.reference_source.is_valid:
            self.view.show_error(
                "Erreur de lecture",
                f"Impossible de lire la référence : {self.reference_source.error_message}")
            return

        self.candidate_sources = {}
        for path in cand_paths:
            src = load_source_file(path)
            self.candidate_sources[path] = src

        self._comparing = True
        self.view.set_progress(0, "Comparaison en cours…")

        thread = threading.Thread(target=self._run_comparison, args=(cfg,), daemon=True)
        thread.start()

    def _run_comparison(self, cfg: Dict[str, object]) -> None:
        """Exécute la comparaison (appelé dans un thread séparé)."""
        level = str(cfg["level"])
        high_threshold = float(cfg["threshold_high"])
        low_threshold = THRESHOLD_LOW
        auto_mode = level == "auto"

        def build_method(level_key: str):
            """Instancie la méthode correspondant au niveau demandé."""
            if level_key == "1":
                return Level1TextMethod(
                    min_fragment_lines=int(cfg["min_fragment_lines"]),
                    strip_comments=bool(cfg["strip_comments"]),
                )
            if level_key == "3":
                return Level3StructureMethod(
                    min_fragment_lines=int(cfg["min_fragment_lines"]),
                )
            return Level2TokensMethod(
                kgram_size=int(cfg["kgram_size"]),
                gst_min_tile=int(cfg["gst_min_tile"]),
                min_fragment_lines=int(cfg["min_fragment_lines"]),
            )

        methods = {k: build_method(k) for k in ("1", "2", "3")}
        levels_used: set = set()

        results: List[CandidateRank] = []
        total = max(1, len(self.candidate_sources))

        for idx, (path, cand_src) in enumerate(self.candidate_sources.items()):
            pct = (idx / total) * 100
            self.view.after(0, lambda p=pct, n=os.path.basename(path):
                            self.view.set_progress(p, f"Comparaison de {n}…"))

            if auto_mode:
                cand_level = "3" if (
                    self.reference_source.language != cand_src.language
                ) else "2"
            else:
                cand_level = level
            levels_used.add(cand_level)
            method = methods[cand_level]

            sim: SimilarityResult = method.compare(self.reference_source, cand_src)
            rank = CandidateRank(
                rank=0,
                path=sim.candidate_path,
                filename=os.path.basename(sim.candidate_path),
                language=sim.language,
                score=sim.score,
                alert=classify_alert(sim.score, low_threshold, high_threshold),
                sub_scores=sim.sub_scores,
                fragments=sim.fragments,
                time_ms=sim.time_ms,
                notes=sim.notes,
            )
            results.append(rank)

        ranked = rank_candidates(results)

        if auto_mode:
            levels_desc = "niveau auto (" + ", ".join(sorted(levels_used)) + ")"
        else:
            levels_desc = methods[level].name

        self.view.after(0, lambda: self._on_comparison_done(ranked, levels_desc))

    def _on_comparison_done(self, results: List[CandidateRank], method_name: str) -> None:
        """Callback exécuté dans le thread principal après la comparaison."""
        self._comparing = False
        self.results = results
        self.view.display_results(results, method_name)

    # =========================================================================
    # Vue côte à côte
    # =========================================================================
    def open_diff(self, result: CandidateRank) -> None:
        """Ouvre la fenêtre de comparaison côte à côte pour un résultat."""
        if self.reference_source is None:
            return
        cand_src = self.candidate_sources.get(result.path)
        if cand_src is None:
            return

        self.view.show_diff(
            reference_lines=self.reference_source.lines,
            reference_filename=self.reference_source.filename,
            reference_language=self.reference_source.language,
            candidate_lines=cand_src.lines,
            result=result,
        )

    # =========================================================================
    # Exports
    # =========================================================================
    def export_csv(self) -> None:
        if not self.results:
            self.view.show_info("Aucun résultat", "Lancez d'abord une comparaison.")
            return
        path = self.view.ask_save_path(
            "Exporter en CSV", ".csv",
            [("CSV", "*.csv"), ("Tous", "*.*")],
        )
        if not path:
            return
        try:
            from models.report.export_csv import export_csv
            out = export_csv(
                self.results, path,
                reference_path=self.reference_source.path if self.reference_source else "")
            self.view.show_info("Export CSV", f"Rapport CSV écrit :\n{out}")
        except Exception as exc:  # pragma: no cover - dépend du système de fichiers
            self.view.show_error("Erreur d'export", str(exc))

    def export_html(self) -> None:
        if not self.results:
            self.view.show_info("Aucun résultat", "Lancez d'abord une comparaison.")
            return
        path = self.view.ask_save_path(
            "Rapport HTML", ".html",
            [("HTML", "*.html"), ("Tous", "*.*")],
        )
        if not path:
            return
        try:
            from models.report.export_html import export_html
            cand_sources = {p: src.lines for p, src in self.candidate_sources.items()}
            cand_langs = {p: src.language for p, src in self.candidate_sources.items()}
            out = export_html(
                self.results, path,
                reference_path=self.reference_source.path,
                reference_lines=self.reference_source.lines,
                reference_filename=self.reference_source.filename,
                reference_language=self.reference_source.language,
                candidate_sources=cand_sources,
                candidate_languages=cand_langs,
            )
            self.view.show_info("Rapport HTML", f"Rapport HTML écrit :\n{out}")
        except Exception as exc:  # pragma: no cover - dépend du système de fichiers
            self.view.show_error("Erreur d'export", str(exc))

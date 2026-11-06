"""
Contrôleur de l'interface en ligne de commande (C du modèle MVC).

Il exécute le parcours complet (chargement, comparaison, classement, exports)
et délègue tout affichage à :class:`views.console.ConsoleView`.
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Dict, List

from models.config import THRESHOLD_HIGH, THRESHOLD_LOW
from models.loader import SourceFile, detect_language, load_directory, load_source_file
from models.methods.level1_text import Level1TextMethod
from models.methods.level2_tokens import Level2TokensMethod
from models.methods.level3_structure import Level3StructureMethod
from models.ranking import CandidateRank, classify_alert, rank_candidates
from views.console import ConsoleView


class CLIController:
    """Orchestre une exécution de la CLI à partir des arguments analysés."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.view = ConsoleView(quiet=args.quiet)

    # =========================================================================
    # Fabriques
    # =========================================================================
    def _build_method(self, level: str):
        args = self.args
        if level == "1":
            return Level1TextMethod(
                strip_comments=not args.keep_comments,
                min_fragment_lines=args.min_frag,
            )
        if level == "3":
            return Level3StructureMethod(min_fragment_lines=args.min_frag)
        return Level2TokensMethod(
            kgram_size=args.kgram,
            gst_min_tile=args.gst_min,
            min_fragment_lines=args.min_frag,
        )

    @staticmethod
    def _choose_level_auto(ref_path: str, cand_path: str) -> str:
        """Niveau « Auto » par couple : 3 si les langages diffèrent, sinon 2."""
        return "3" if detect_language(ref_path) != detect_language(cand_path) else "2"

    # =========================================================================
    # Exécution
    # =========================================================================
    def run(self) -> int:
        args = self.args

        ref_source = load_source_file(args.ref)
        if not ref_source.is_valid:
            self.view.error(ref_source.error_message)
            return 1

        cand_paths: List[str] = list(args.cands)
        if args.cands_dir:
            for src in load_directory(args.cands_dir):
                cand_paths.append(src.path)

        if not cand_paths:
            self.view.error("aucun candidat fourni (--cands ou --cands-dir).")
            return 1

        auto_mode = args.level == "auto"
        level_label = "auto" if auto_mode else args.level
        self.view.header(ref_source.filename, ref_source.language,
                         level_label, len(cand_paths))

        results: List[CandidateRank] = []
        candidate_sources: Dict[str, SourceFile] = {}
        t_start = time.perf_counter()

        for path in cand_paths:
            cand = load_source_file(path)
            candidate_sources[path] = cand
            level = self._choose_level_auto(args.ref, path) if auto_mode else args.level
            method = self._build_method(level)
            sim = method.compare(ref_source, cand)
            rank = CandidateRank(
                path=sim.candidate_path,
                filename=os.path.basename(sim.candidate_path),
                language=sim.language,
                score=sim.score,
                sub_scores=sim.sub_scores,
                fragments=sim.fragments,
                time_ms=sim.time_ms,
                notes=sim.notes,
            )
            rank.alert = classify_alert(rank.score, THRESHOLD_LOW, THRESHOLD_HIGH)
            results.append(rank)

        ranked = rank_candidates(results)
        elapsed = (time.perf_counter() - t_start) * 1000.0

        self.view.results_table(ranked)
        self.view.footer(elapsed)

        if args.csv:
            from models.report.export_csv import export_csv
            out = export_csv(ranked, args.csv, reference_path=args.ref)
            self.view.export_done("CSV ", out)

        if args.html:
            from models.report.export_html import export_html
            cand_sources = {p: src.lines for p, src in candidate_sources.items()}
            cand_langs = {p: src.language for p, src in candidate_sources.items()}
            out = export_html(
                ranked, args.html,
                reference_path=args.ref,
                reference_lines=ref_source.lines,
                reference_filename=ref_source.filename,
                reference_language=ref_source.language,
                candidate_sources=cand_sources,
                candidate_languages=cand_langs,
            )
            self.view.export_done("HTML", out)

        return 0

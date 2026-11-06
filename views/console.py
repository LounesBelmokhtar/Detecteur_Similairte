"""
Vue console (V du modèle MVC pour la CLI).

Regroupe l'analyse des arguments et le rendu texte : la logique de comparaison
est entièrement déléguée au contrôleur CLI.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from models.config import ETHICAL_WARNING
from models.ranking import CandidateRank


def configure_utf8() -> None:
    """Force UTF-8 sur les sorties standard (Windows / cp1252)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def build_parser() -> argparse.ArgumentParser:
    """Construit le parseur d'arguments de l'interface en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Détecteur de similarité entre codes sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=ETHICAL_WARNING,
    )
    parser.add_argument("--ref", required=True,
                        help="Chemin du fichier de référence.")
    parser.add_argument("--cands", nargs="*", default=[],
                        help="Liste de fichiers candidats.")
    parser.add_argument("--cands-dir", default=None,
                        help="Dossier de candidats (parcours récursif).")
    parser.add_argument("--level", default="2", choices=["1", "2", "3", "auto"],
                        help="Niveau de comparaison (défaut : 2).")
    parser.add_argument("--kgram", type=int, default=5,
                        help="Taille des k-grammes (niveau 2, défaut : 5).")
    parser.add_argument("--gst-min", type=int, default=4,
                        help="Longueur minimale d'une tuile GST (niveau 2, défaut : 4).")
    parser.add_argument("--min-frag", type=int, default=3,
                        help="Nombre minimal de lignes pour un fragment (défaut : 3).")
    parser.add_argument("--keep-comments", action="store_true",
                        help="Conserver les commentaires (niveau 1, défaut : supprimés).")
    parser.add_argument("--csv", default=None,
                        help="Chemin de sortie pour l'export CSV.")
    parser.add_argument("--html", default=None,
                        help="Chemin de sortie pour le rapport HTML.")
    parser.add_argument("--quiet", action="store_true",
                        help="Affichage minimal (scores uniquement).")
    return parser


class ConsoleView:
    """Rendu texte des résultats dans le terminal."""

    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet

    def error(self, message: str) -> None:
        print(f"ERREUR : {message}", file=sys.stderr)

    def header(self, reference_name: str, reference_language: str,
               level_label: str, candidate_count: int) -> None:
        if self.quiet:
            return
        print(f"Référence : {reference_name} ({reference_language})")
        print(f"Niveau    : {level_label}")
        print(f"Candidats : {candidate_count}")
        print("-" * 72)

    def results_table(self, ranked: Sequence[CandidateRank]) -> None:
        if not self.quiet:
            print(f"{'#':>3}  {'Fichier':<32} {'Lang':<11} {'Score':>7}  "
                  f"{'Alerte':<10} {'Frags':>5} {'ms':>7}")
            print("-" * 72)
        for r in ranked:
            if self.quiet:
                print(f"{r.score:.1f}\t{r.filename}")
            else:
                print(f"{r.rank:>3}  {r.filename:<32} {r.language:<11} {r.score:>6.1f}%  "
                      f"{r.alert_emoji}{r.alert_label:<9} {len(r.fragments):>5} "
                      f"{r.time_ms:>7.1f}")

    def footer(self, elapsed_ms: float) -> None:
        if self.quiet:
            return
        print("-" * 72)
        print(f"Temps total : {elapsed_ms:.1f} ms")
        print(f"⚠  {ETHICAL_WARNING}")

    def export_done(self, kind: str, path: str) -> None:
        if not self.quiet:
            print(f"{kind} → {path}")

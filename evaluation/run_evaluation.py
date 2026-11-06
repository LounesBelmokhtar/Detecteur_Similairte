"""
Script d'évaluation du détecteur de similarité.

Exécute les trois niveaux de comparaison sur le jeu d'évaluation
(`evaluation/scenarios.py`), puis produit :
  - un tableau récapitulatif par scénario ;
  - les métriques de classification (précision, rappel, F1, accuracy)
    par niveau, en prenant `models.config.THRESHOLD_LOW` comme seuil d'alerte ;
  - les scores moyens par catégorie et par niveau.

Usage :
    python -m evaluation.run_evaluation
    python -m evaluation.run_evaluation --csv evaluation/resultats.csv --plots
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Dict, List

sys.stdout.reconfigure(encoding="utf-8")

from models.config import THRESHOLD_LOW
from models.loader import load_source_file
from evaluation.scenarios import CATEGORIES, SCENARIOS
from models.methods.level1_text import Level1TextMethod
from models.methods.level2_tokens import Level2TokensMethod
from models.methods.level3_structure import Level3StructureMethod

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_ROOT = os.path.join(PROJECT_ROOT, "samples")


def run_all_scenarios() -> List[Dict[str, object]]:
    """
    Exécute les trois niveaux sur chaque scénario.
    Retourne une ligne par (scénario, niveau) sous forme de dictionnaire.
    """
    methods = {
        1: Level1TextMethod(),
        2: Level2TokensMethod(),
        3: Level3StructureMethod(),
    }

    rows: List[Dict[str, object]] = []
    for sc in SCENARIOS:
        ref = load_source_file(os.path.join(SAMPLES_ROOT, sc.reference.replace("/", os.sep)))
        cand = load_source_file(os.path.join(SAMPLES_ROOT, sc.candidate.replace("/", os.sep)))
        for level, method in methods.items():
            result = method.compare(ref, cand)
            rows.append({
                "scenario": sc.ident,
                "category": sc.category,
                "level": level,
                "score": round(result.score, 2),
                "expected_alert": sc.expected_alert,
                "detected_alert": result.score > THRESHOLD_LOW,
                "time_ms": round(result.time_ms, 2),
            })
    return rows


def classification_metrics(rows: List[Dict[str, object]], level: int) -> Dict[str, float]:
    """Calcule accuracy / precision / recall / F1 pour un niveau donné."""
    tp = fp = tn = fn = 0
    for r in rows:
        if r["level"] != level:
            continue
        expected = bool(r["expected_alert"])
        detected = bool(r["detected_alert"])
        if expected and detected:
            tp += 1
        elif not expected and detected:
            fp += 1
        elif not expected and not detected:
            tn += 1
        else:
            fn += 1

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "accuracy": round(accuracy * 100, 1),
        "precision": round(precision * 100, 1),
        "recall": round(recall * 100, 1),
        "f1": round(f1 * 100, 1),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
    }


def mean_scores_by_category(rows: List[Dict[str, object]]) -> Dict[int, Dict[str, float]]:
    """Score moyen par catégorie et par niveau."""
    result: Dict[int, Dict[str, float]] = {1: {}, 2: {}, 3: {}}
    for level in (1, 2, 3):
        for cat in CATEGORIES:
            scores = [float(r["score"]) for r in rows
                      if r["level"] == level and r["category"] == cat]
            result[level][cat] = round(sum(scores) / len(scores), 1) if scores else 0.0
    return result


def print_report(rows: List[Dict[str, object]]) -> None:
    """Affiche le rapport complet sur la sortie standard."""
    print("=" * 100)
    print("ÉVALUATION DU DÉTECTEUR DE SIMILARITÉ")
    print(f"Seuil d'alerte : score > {THRESHOLD_LOW}")
    print("=" * 100)

    # --- Détail par scénario --------------------------------------------------
    print(f"\n{'Scénario':<28} {'Catégorie':<14} {'N1':>7} {'N2':>7} {'N3':>7}  Attendu")
    print("-" * 100)
    by_sc: Dict[str, Dict[str, object]] = {}
    for r in rows:
        by_sc.setdefault(str(r["scenario"]), {"category": r["category"],
                                              "expected": r["expected_alert"]})
        by_sc[str(r["scenario"])][f"l{r['level']}"] = r["score"]
    for sc in SCENARIOS:
        d = by_sc.get(sc.ident, {})
        expected = "ALERTE" if sc.expected_alert else "aucune"
        print(f"{sc.ident:<28} {sc.category:<14} "
              f"{d.get('l1', 0):>7} {d.get('l2', 0):>7} {d.get('l3', 0):>7}  {expected}")

    # --- Métriques de classification -----------------------------------------
    print("\n" + "=" * 100)
    print("MÉTRIQUES DE CLASSIFICATION (seuil d'alerte)")
    print("-" * 100)
    print(f"{'Niveau':<10} {'Accuracy':>9} {'Precision':>10} {'Rappel':>8} {'F1':>7}   TP/FP/TN/FN")
    for level in (1, 2, 3):
        m = classification_metrics(rows, level)
        print(f"{level:<10} {m['accuracy']:>8}% {m['precision']:>9}% "
              f"{m['recall']:>7}% {m['f1']:>6}%   "
              f"{m['tp']}/{m['fp']}/{m['tn']}/{m['fn']}")

    # --- Scores moyens par catégorie ------------------------------------------
    print("\n" + "=" * 100)
    print("SCORES MOYENS PAR CATÉGORIE (%)")
    print("-" * 100)
    means = mean_scores_by_category(rows)
    print(f"{'Catégorie':<16} {'Niveau 1':>9} {'Niveau 2':>9} {'Niveau 3':>9}")
    for cat in CATEGORIES:
        print(f"{cat:<16} {means[1][cat]:>8} {means[2][cat]:>8} {means[3][cat]:>8}")


def export_csv(rows: List[Dict[str, object]], path: str) -> None:
    """Exporte les résultats détaillés en CSV."""
    fieldnames = ["scenario", "category", "level", "score",
                  "expected_alert", "detected_alert", "time_ms"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nRésultats CSV exportés : {path}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Évaluation du détecteur de similarité.")
    parser.add_argument("--csv", default=None,
                        help="Chemin de sortie du fichier CSV des résultats.")
    parser.add_argument("--plots", action="store_true",
                        help="Générer les graphiques matplotlib.")
    args = parser.parse_args(argv)

    rows = run_all_scenarios()
    print_report(rows)

    if args.csv:
        export_csv(rows, args.csv)

    if args.plots:
        try:
            from evaluation.plots import generate_all
            out_dir = os.path.join(PROJECT_ROOT, "evaluation", "figures")
            os.makedirs(out_dir, exist_ok=True)
            generate_all(rows, out_dir)
            print(f"Graphiques générés dans : {out_dir}")
        except ImportError:
            print("matplotlib non disponible : graphiques ignorés.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

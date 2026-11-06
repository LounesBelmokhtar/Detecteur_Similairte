"""
Graphiques d'évaluation (matplotlib).

Génère à partir des résultats produits par `evaluation.run_evaluation` :
  1. barres groupées : scores moyens par catégorie et par niveau ;
  2. nuage de points : score niveau 1 vs niveau 2, coloré par catégorie ;
  3. matrice de confusion par niveau (heatmap).

Usage :
    from evaluation.plots import generate_all
    generate_all(rows, "evaluation/figures")
"""

from __future__ import annotations

import os
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")  # backend non interactif (compatibilité sans affichage)
import matplotlib.pyplot as plt
import numpy as np

from evaluation.scenarios import CATEGORIES

CATEGORY_COLORS = {
    "identique": "#2e7d32",
    "modifie": "#ef6c00",
    "sans_relation": "#c62828",
    "cross_langue": "#1565c0",
}


def _mean_by_category_and_level(rows: List[Dict[str, object]]) -> Dict[str, Dict[int, float]]:
    out: Dict[str, Dict[int, float]] = {}
    for cat in CATEGORIES:
        out[cat] = {}
        for level in (1, 2, 3):
            scores = [float(r["score"]) for r in rows
                      if r["category"] == cat and r["level"] == level]
            out[cat][level] = sum(scores) / len(scores) if scores else 0.0
    return out


def plot_mean_scores(rows: List[Dict[str, object]], out_path: str) -> None:
    """Barres groupées : score moyen par catégorie pour chaque niveau."""
    data = _mean_by_category_and_level(rows)
    levels = [1, 2, 3]
    x = np.arange(len(CATEGORIES))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, level in enumerate(levels):
        values = [data[cat][level] for cat in CATEGORIES]
        bars = ax.bar(x + (i - 1) * width, values, width,
                      label=f"Niveau {level}", edgecolor="white")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{val:.0f}", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Score moyen (%)")
    ax.set_title("Scores moyens par catégorie et par niveau de comparaison")
    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORIES)
    ax.set_ylim(0, 110)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_level1_vs_level2(rows: List[Dict[str, object]], out_path: str) -> None:
    """Nuage de points : score niveau 1 (axe X) vs niveau 2 (axe Y)."""
    fig, ax = plt.subplots(figsize=(7, 7))

    for cat in CATEGORIES:
        by_sc: Dict[str, Dict[int, float]] = {}
        for r in rows:
            if r["category"] != cat:
                continue
            by_sc.setdefault(str(r["scenario"]), {})[int(r["level"])] = float(r["score"])
        xs = [by_sc[s][1] for s in by_sc if 1 in by_sc[s] and 2 in by_sc[s]]
        ys = [by_sc[s][2] for s in by_sc if 1 in by_sc[s] and 2 in by_sc[s]]
        ax.scatter(xs, ys, label=cat, color=CATEGORY_COLORS.get(cat, "gray"),
                   s=60, alpha=0.8, edgecolors="white")

    ax.plot([0, 100], [0, 100], "--", color="gray", alpha=0.4, label="y = x")
    ax.set_xlabel("Score niveau 1 (%)")
    ax.set_ylabel("Score niveau 2 (%)")
    ax.set_title("Gain du niveau 2 sur le niveau 1")
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_confusion_matrices(rows: List[Dict[str, object]], out_path: str,
                            threshold: float) -> None:
    """Trois heatmaps (une par niveau) de la matrice de confusion."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    for ax, level in zip(axes, (1, 2, 3)):
        tp = fp = tn = fn = 0
        for r in rows:
            if r["level"] != level:
                continue
            exp, det = bool(r["expected_alert"]), bool(r["detected_alert"])
            if exp and det:
                tp += 1
            elif not exp and det:
                fp += 1
            elif not exp and not det:
                tn += 1
            else:
                fn += 1
        matrix = np.array([[tp, fn], [fp, tn]])
        ax.imshow(matrix, cmap="Blues", vmin=0)
        for (i, j), val in np.ndenumerate(matrix):
            ax.text(j, i, str(val), ha="center", va="center",
                    color="black" if val < matrix.max() * 0.6 else "white",
                    fontsize=14)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Prédit\nsimilaire", "Prédit\ndifférent"])
        ax.set_yticklabels(["Réel\nsimilaire", "Réel\ndifférent"])
        ax.set_title(f"Niveau {level} (seuil {threshold:.0f})")

    fig.suptitle("Matrices de confusion par niveau")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def generate_all(rows: List[Dict[str, object]], out_dir: str) -> None:
    """Génère les trois graphiques dans `out_dir`."""
    from models.config import THRESHOLD_LOW

    os.makedirs(out_dir, exist_ok=True)
    plot_mean_scores(rows, os.path.join(out_dir, "scores_moyens.png"))
    plot_level1_vs_level2(rows, os.path.join(out_dir, "niveau1_vs_niveau2.png"))
    plot_confusion_matrices(rows, os.path.join(out_dir, "matrices_confusion.png"),
                            THRESHOLD_LOW)

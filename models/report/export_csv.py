"""
Export des résultats de comparaison au format CSV.
Compatible avec l'ouverture directe dans Excel, LibreOffice, etc.
"""

from __future__ import annotations

import csv
import os
from typing import List

from models.config import ETHICAL_WARNING
from models.ranking import CandidateRank


def export_csv(results: List[CandidateRank], output_path: str,
               reference_path: str = "") -> str:
    """
    Écrit les résultats classés dans un fichier CSV.

    Colonnes : Rang, Fichier, Langage, Score (%), Alerte, sous-scores…,
               Temps (ms), Notes.
    """
    abs_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)

    # Collecter toutes les clés de sous-scores présentes
    sub_keys: List[str] = []
    for r in results:
        for key in r.sub_scores:
            if key not in sub_keys:
                sub_keys.append(key)

    header = ["Rang", "Fichier", "Langage", "Score (%)", "Niveau alerte"]
    header += [f"Sous-score : {k}" for k in sub_keys]
    header += ["Temps (ms)", "Nb fragments", "Notes", "Avertissement"]

    with open(abs_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(header)

        for r in results:
            row = [
                r.rank,
                r.filename,
                r.language,
                f"{r.score:.2f}",
                r.alert_label,
            ]
            for k in sub_keys:
                val = r.sub_scores.get(k)
                row.append(f"{val:.2f}" if val is not None else "")
            row.append(f"{r.time_ms:.2f}")
            row.append(len(r.fragments))
            row.append(" | ".join(n for n in r.notes if n))
            row.append(ETHICAL_WARNING)
            writer.writerow(row)

    return abs_path

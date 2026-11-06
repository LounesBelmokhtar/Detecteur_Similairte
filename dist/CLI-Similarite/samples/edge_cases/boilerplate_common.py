"""Exemple de code avec beaucoup de boilerplate commun (imports, main, structure).

Ce fichier illustre les faux positifs : deux programmes très différents
peuvent obtenir un score élevé s'ils partagent la même structure de fichier
(import, définition de main, impressions…).
"""

import sys
import os
import math
import json
import csv


def load_config(path):
    """Charge une configuration JSON."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_input(value, min_val=0, max_val=100):
    """Valide qu'une valeur est dans les bornes."""
    if value < min_val:
        raise ValueError("Valeur trop faible")
    if value > max_val:
        raise ValueError("Valeur trop élevée")
    return True


def compute_average(values):
    """Calcule la moyenne d'une liste."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def write_report(rows, out_path):
    """Écrit un rapport CSV."""
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["clé", "valeur"])
        writer.writerows(rows)


def main():
    """Point d'entrée principal."""
    print("Démarrage du programme…")
    try:
        data = [10, 20, 30, 40, 50]
        avg = compute_average(data)
        print("Moyenne :", avg)
        validate_input(avg)
        write_report([("moyenne", avg)], "report.csv")
        print("Terminé.")
    except Exception as exc:
        print("Erreur :", exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

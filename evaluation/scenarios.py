"""
Définition du jeu d'évaluation : paires (référence, candidat) avec vérité terrain.

Chaque scénario porte :
  - un identifiant et une catégorie (identique / modifie / sans_relation / cross_langue) ;
  - un chemin de référence et de candidat relatifs à `samples/` ;
  - `expected_alert` : True si un outil doit signaler une similarité forte
    (score > seuil d'alerte), False pour des codes sans relation.

La vérité terrain est utilisée pour construire la matrice de confusion,
la précision, le rappel et le F1 de chaque niveau.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Scenario:
    """Un cas d'évaluation (paire de fichiers + vérité terrain)."""
    ident: str
    category: str          # "identique" | "modifie" | "sans_relation" | "cross_langue"
    reference: str         # chemin relatif à samples/
    candidate: str         # chemin relatif à samples/
    expected_alert: bool   # True = doit être détecté comme similaire
    description: str = ""


# ==============================================================================
# JEU D'ÉVALUATION
# ==============================================================================

SCENARIOS: List[Scenario] = [
    # --- Identiques (copie exacte ou reformatage seul) -----------------------
    Scenario(
        "copy_exact", "identique",
        "identical/bubble_sort_ref.py", "identical/bubble_sort_copy.py",
        True, "Copie byte-à-byte du fichier de référence.",
    ),
    Scenario(
        "reformat", "identique",
        "identical/bubble_sort_ref.py", "identical/bubble_sort_reformat.py",
        True, "Copie avec commentaires supprimés et espacement modifié.",
    ),
    # --- Modifiés (renommage, réordonnancement, while, code mort) ------------
    Scenario(
        "renamed", "modifie",
        "identical/bubble_sort_ref.py", "modified/bubble_sort_renamed.py",
        True, "Renommage systématique de variables et de fonctions.",
    ),
    Scenario(
        "reordered", "modifie",
        "identical/bubble_sort_ref.py", "modified/bubble_sort_reordered.py",
        True, "Fonctions et blocs réordonnés, même algorithme.",
    ),
    Scenario(
        "while_rewrite", "modifie",
        "identical/bubble_sort_ref.py", "modified/bubble_sort_while.py",
        True, "for convertis en while (réécriture partielle).",
    ),
    Scenario(
        "dead_code", "modifie",
        "identical/bubble_sort_ref.py", "modified/bubble_sort_dead_code.py",
        True, "Code mort et commentaires ajoutés autour de l'algorithme.",
    ),
    Scenario(
        "combo", "modifie",
        "identical/bubble_sort_ref.py", "modified/bubble_sort_combo.py",
        False, "Renommage + while + code mort combinés (cas difficile).",
    ),
    # --- Sans relation (mêmes langages) ---------------------------------------
    Scenario(
        "vs_binary_search", "sans_relation",
        "identical/bubble_sort_ref.py", "unrelated/binary_search.py",
        False, "Tri à bulles vs recherche binaire (même langage).",
    ),
    Scenario(
        "vs_factorial", "sans_relation",
        "identical/bubble_sort_ref.py", "unrelated/factorial.py",
        False, "Tri à bulles vs factorielle (même langage).",
    ),
    Scenario(
        "vs_gcd", "sans_relation",
        "identical/bubble_sort_ref.py", "unrelated/gcd.py",
        False, "Tri à bulles vs PGCD (même langage).",
    ),
    Scenario(
        "neg_bubble_binary", "sans_relation",
        "cross_language/negative_bubble_vs_binary_py.py",
        "unrelated/binary_search.py",
        False, "Paire négative explicite fournie avec le jeu d'essai.",
    ),
    # --- Cross-langages : même algorithme (doivent être détectés) -------------
    Scenario(
        "py_java_bubble", "cross_langue",
        "identical/bubble_sort_ref.py", "cross_language/BubbleSort.java",
        True, "Tri à bulles Python vs Java (même algorithme).",
    ),
    Scenario(
        "py_c_bubble", "cross_langue",
        "identical/bubble_sort_ref.py", "cross_language/bubble_sort.c",
        True, "Tri à bulles Python vs C (même algorithme).",
    ),
    Scenario(
        "py_java_fib", "cross_langue",
        "cross_language/fibonacci.py", "cross_language/Fibonacci.java",
        True, "Fibonacci récursif Python vs Java.",
    ),
    Scenario(
        "py_c_fib", "cross_langue",
        "cross_language/fibonacci.py", "cross_language/fibonacci.c",
        True, "Fibonacci récursif Python vs C.",
    ),
    Scenario(
        "py_js_fib", "cross_langue",
        "cross_language/fibonacci.py", "cross_language/fibonacci.js",
        True, "Fibonacci récursif Python vs JavaScript.",
    ),
    Scenario(
        "py_java_gcd", "cross_langue",
        "unrelated/gcd.py", "cross_language/Gcd.java",
        True, "PGCD Python vs Java.",
    ),
    Scenario(
        "py_c_binary", "cross_langue",
        "unrelated/binary_search.py", "cross_language/binary_search.c",
        True, "Recherche binaire Python vs C.",
    ),
    Scenario(
        "py_java_primality", "cross_langue",
        "cross_language/primality_test.py", "cross_language/PrimalityTest.java",
        True, "Test de primalité Python vs Java.",
    ),
    # --- Cross-langages : algorithmes différents (ne PAS détecter) ------------
    Scenario(
        "x_py_fib_vs_c_bubble", "cross_langue",
        "cross_language/fibonacci.py", "cross_language/bubble_sort.c",
        False, "Fibonacci Python vs tri à bulles C.",
    ),
    Scenario(
        "x_py_fib_vs_c_gcd", "cross_langue",
        "cross_language/fibonacci.py", "cross_language/gcd.c",
        False, "Fibonacci Python vs PGCD C.",
    ),
    Scenario(
        "x_py_bin_vs_c_bubble", "cross_langue",
        "unrelated/binary_search.py", "cross_language/bubble_sort.c",
        False, "Recherche binaire Python vs tri à bulles C.",
    ),
    Scenario(
        "x_py_prim_vs_c_bubble", "cross_langue",
        "cross_language/primality_test.py", "cross_language/bubble_sort.c",
        False, "Primalité Python vs tri à bulles C.",
    ),
    Scenario(
        "x_py_fact_vs_c_gcd", "cross_langue",
        "unrelated/factorial.py", "cross_language/gcd.c",
        False, "Factorielle Python vs PGCD C.",
    ),
]

CATEGORIES: List[str] = ["identique", "modifie", "sans_relation", "cross_langue"]

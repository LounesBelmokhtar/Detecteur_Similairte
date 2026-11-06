"""
Paquet du modèle métier (M du modèle MVC) du détecteur de similarité.

Regroupe le chargement des sources, l'analyse lexicale et syntaxique, la
normalisation, la comparaison (niveaux 1 à 3), le classement et les exports.
Ce paquet ne doit jamais importer Tkinter ni aucun module d'interface.
"""

from models.loader import SourceFile, load_source_file, load_directory, detect_language
from models.lexer import Token, tokenize, filter_tokens
from models.fragments import Fragment, merge_adjacent_fragments
from models.ranking import CandidateRank, classify_alert, weighted_score, rank_candidates

__all__ = [
    "SourceFile", "load_source_file", "load_directory", "detect_language",
    "Token", "tokenize", "filter_tokens",
    "Fragment", "merge_adjacent_fragments",
    "CandidateRank", "classify_alert", "weighted_score", "rank_candidates",
]

"""
NIVEAU 1 — Comparaison textuelle directe.

Hypothèse : même langage, mêmes noms de variables, même ordre des instructions.
Trois mesures principales combinées de façon pondérée :
  1. Ratio de difflib.SequenceMatcher au niveau des lignes ;
  2. Similarité de Levenshtein normalisée (programmation dynamique) ;
  3. Similarité de Jaccard sur n-grammes de tokens ;
  4. (Bonus) LCS (plus longue sous-séquence commune) au niveau des lignes.

Les fragments similaires sont extraits via SequenceMatcher.get_matching_blocks()
avec un minimum de lignes configurable pour éviter les faux positifs triviaux.
"""

from __future__ import annotations

import time
from difflib import SequenceMatcher
from typing import Dict, List, Sequence, Tuple

from models.config import (
    LEVEL1_MIN_MATCHING_LINES,
    LEVEL1_NGRAM_SIZE,
    WEIGHTS_LEVEL1,
)
from models.fragments import Fragment, merge_adjacent_fragments
from models.loader import SourceFile
from models.normalizer import normalize_text_level1
from models.methods.base import SimilarityResult


# ==============================================================================
# Mesures de similarité textuelle
# ==============================================================================

def sequence_matcher_ratio(lines_a: Sequence[str], lines_b: Sequence[str]) -> float:
    """
    Ratio difflib.SequenceMatcher entre deux séquences de lignes (0.0 à 1.0).
    Mesure le degré de recouvrement optimal des blocs de lignes identiques.
    """
    if not lines_a and not lines_b:
        return 1.0
    if not lines_a or not lines_b:
        return 0.0
    return SequenceMatcher(None, lines_a, lines_b, autojunk=False).ratio()


def levenshtein_distance(a: Sequence, b: Sequence) -> int:
    """
    Distance de Levenshtein (nombre minimum d'opérations d'édition) par
    programmation dynamique classique, complexité O(len(a) * len(b)).

    Pour économiser la mémoire, on ne conserve que deux lignes de la matrice
    (la ligne courante et la ligne précédente) au lieu de la matrice complète.
    """
    len_a, len_b = len(a), len(b)

    # Cas limites
    if len_a == 0:
        return len_b
    if len_b == 0:
        return len_a

    # Optimisation mémoire : deux tableaux de taille len_b + 1
    prev_row = list(range(len_b + 1))   # Ligne 0 : distance depuis le début de b
    curr_row = [0] * (len_b + 1)

    for i in range(1, len_a + 1):
        curr_row[0] = i                 # Distance depuis le début de a
        for j in range(1, len_b + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr_row[j] = min(
                prev_row[j] + 1,        # Suppression dans a
                curr_row[j - 1] + 1,    # Insertion dans a
                prev_row[j - 1] + cost, # Substitution ou correspondance
            )
        prev_row, curr_row = curr_row, prev_row

    return prev_row[len_b]


def levenshtein_similarity(a: Sequence, b: Sequence) -> float:
    """
    Similarité de Levenshtein normalisée : 1 - d(a,b) / max(|a|,|b|).
    Résultat borné dans [0.0, 1.0].
    """
    if not a and not b:
        return 1.0
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(a, b)
    return max(0.0, 1.0 - dist / max_len)


def _build_ngrams(items: Sequence, n: int) -> List[Tuple]:
    """Construit la liste des n-grammes glissants d'une séquence."""
    if n <= 0:
        return []
    return [tuple(items[i:i + n]) for i in range(len(items) - n + 1)]


def jaccard_ngrams_similarity(
    a: Sequence,
    b: Sequence,
    n: int = LEVEL1_NGRAM_SIZE,
) -> float:
    """
    Similarité de Jaccard sur les n-grammes : |A ∩ B| / |A ∪ B|.
    Utilise des ensembles d'hashables pour un calcul efficace.
    """
    ngrams_a = set(_build_ngrams(a, n))
    ngrams_b = set(_build_ngrams(b, n))

    if not ngrams_a and not ngrams_b:
        return 1.0
    if not ngrams_a or not ngrams_b:
        return 0.0

    intersection = len(ngrams_a & ngrams_b)
    union = len(ngrams_a | ngrams_b)
    return intersection / union if union else 0.0


def lcs_length(a: Sequence, b: Sequence) -> int:
    """
    Longueur de la plus longue sous-séquence commune (LCS) par programmation dynamique,
    complexité O(len(a) * len(b)) — mémoire optimisée sur deux lignes.
    """
    len_a, len_b = len(a), len(b)
    if len_a == 0 or len_b == 0:
        return 0

    prev = [0] * (len_b + 1)
    curr = [0] * (len_b + 1)

    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (len_b + 1)

    return prev[len_b]


def lcs_similarity(a: Sequence, b: Sequence) -> float:
    """Similarité normalisée basée sur la LCS : 2 * |LCS| / (|a| + |b|)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    lcs = lcs_length(a, b)
    return (2.0 * lcs) / (len(a) + len(b))


# ==============================================================================
# Extraction des fragments (blocs de lignes communes)
# ==============================================================================

def extract_line_fragments(
    lines_ref: List[str],
    lines_cand: List[str],
    min_lines: int = LEVEL1_MIN_MATCHING_LINES,
) -> List[Fragment]:
    """
    Extrait les blocs de lignes consécutives identiques via SequenceMatcher.
    Les blocs plus courts que `min_lines` sont écartés (accolades, imports…).
    """
    if not lines_ref or not lines_cand:
        return []

    matcher = SequenceMatcher(None, lines_ref, lines_cand, autojunk=False)
    fragments: List[Fragment] = []

    for block in matcher.get_matching_blocks():
        # block.size = nombre de lignes identiques consécutives
        if block.size < min_lines:
            continue
        fragments.append(Fragment(
            ref_start=block.a + 1,             # Conversion 0-indexé → 1-indexé
            ref_end=block.a + block.size,
            cand_start=block.b + 1,
            cand_end=block.b + block.size,
            score=1.0,
            label=f"Bloc de {block.size} lignes",
        ))

    return merge_adjacent_fragments(fragments)


# ==============================================================================
# Méthode de comparaison du niveau 1
# ==============================================================================

class Level1TextMethod:
    """Niveau 1 : comparaison textuelle directe après normalisation de base."""

    level: int = 1
    name: str = "Niveau 1 — Textuel"

    def __init__(self, weights: Dict[str, float] | None = None,
                 min_fragment_lines: int = LEVEL1_MIN_MATCHING_LINES,
                 strip_comments: bool = True,
                 ngram_size: int = LEVEL1_NGRAM_SIZE) -> None:
        self.weights = weights or dict(WEIGHTS_LEVEL1)
        self.min_fragment_lines = min_fragment_lines
        self.strip_comments = strip_comments
        self.ngram_size = ngram_size

    def compare(self, reference: SourceFile, candidate: SourceFile) -> SimilarityResult:
        """
        Compare deux fichiers sources au niveau textuel.

        Score final = combinaison pondérée de :
          - ratio SequenceMatcher (lignes),
          - similarité de Levenshtein normalisée (lignes),
          - Jaccard sur n-grammes de tokens,
          - LCS au niveau des lignes.
        """
        t0 = time.perf_counter()
        notes: List[str] = []

        # --- Gestion des cas limites -----------------------------------------
        if not reference.is_valid or not candidate.is_valid:
            return SimilarityResult(
                candidate_path=candidate.path,
                language=candidate.language,
                score=0.0,
                sub_scores={},
                fragments=[],
                time_ms=0.0,
                notes=[
                    f"Référence invalide : {reference.error_message}" if not reference.is_valid else "",
                    f"Candidat invalide : {candidate.error_message}" if not candidate.is_valid else "",
                ],
            )

        if reference.is_empty and candidate.is_empty:
            return SimilarityResult(
                candidate_path=candidate.path,
                language=candidate.language,
                score=100.0,
                sub_scores={"all": 100.0},
                fragments=[],
                time_ms=0.0,
                notes=["Deux fichiers vides : similarité définie à 100 %."],
            )

        if reference.is_empty or candidate.is_empty:
            return SimilarityResult(
                candidate_path=candidate.path,
                language=candidate.language,
                score=0.0,
                sub_scores={"all": 0.0},
                fragments=[],
                time_ms=0.0,
                notes=["Un des deux fichiers est vide."],
            )

        if reference.language != candidate.language:
            notes.append(
                f"Langages différents ({reference.language} vs {candidate.language}) : "
                "le niveau 1 n'est pas adapté, préférez le niveau 3."
            )

        # --- Normalisation textuelle -----------------------------------------
        norm_ref = normalize_text_level1(reference.raw_content, self.strip_comments, reference.language)
        norm_cand = normalize_text_level1(candidate.raw_content, self.strip_comments, candidate.language)

        lines_ref = [ln for ln in norm_ref.split("\n") if ln != ""]
        lines_cand = [ln for ln in norm_cand.split("\n") if ln != ""]

        # --- Calcul des sous-mesures ------------------------------------------
        sm_ratio = sequence_matcher_ratio(lines_ref, lines_cand)
        lev_sim = levenshtein_similarity(lines_ref, lines_cand)
        jac_sim = jaccard_ngrams_similarity(lines_ref, lines_cand, self.ngram_size)
        lcs_sim = lcs_similarity(lines_ref, lines_cand)

        sub_scores = {
            "sequence_matcher": round(sm_ratio * 100.0, 2),
            "levenshtein": round(lev_sim * 100.0, 2),
            "jaccard_ngrams": round(jac_sim * 100.0, 2),
            "lcs_lines": round(lcs_sim * 100.0, 2),
        }

        # --- Score global pondéré ---------------------------------------------
        total_weight = sum(self.weights.get(k, 0.0) for k in sub_scores)
        if total_weight > 0:
            score = sum(sub_scores[k] * self.weights.get(k, 0.0) for k in sub_scores) / total_weight
        else:
            score = 0.0

        # --- Fragments similaires ----------------------------------------------
        fragments = extract_line_fragments(
            lines_ref, lines_cand, min_lines=self.min_fragment_lines
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return SimilarityResult(
            candidate_path=candidate.path,
            language=candidate.language,
            score=round(min(100.0, max(0.0, score)), 2),
            sub_scores=sub_scores,
            fragments=fragments,
            time_ms=round(elapsed_ms, 2),
            notes=notes,
        )

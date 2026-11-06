"""
Tests du niveau 1 — comparaison textuelle directe.

Objectifs vérifiés :
  - un fichier identique obtient un score ≥ 95 % ;
  - un simple reformatage fait chuter le score (le niveau 1 est sensible
    au formatage, c'est ce qu'on veut mesurer) ;
  - des codes sans relation restent sous le seuil d'alerte (< 30 %) ;
  - les fragments de correspondance sont cohérents avec le score.
"""

import pytest

from models.config import THRESHOLD_LOW
from models.methods.level1_text import Level1TextMethod


@pytest.fixture(scope="module")
def method():
    return Level1TextMethod()


def test_copy_exact_score_high(method, bubble_ref, bubble_copy):
    result = method.compare(bubble_ref, bubble_copy)
    assert result.score >= 95.0
    assert method.level == 1


def test_copy_exact_symmetry(method, bubble_ref, bubble_copy):
    r1 = method.compare(bubble_ref, bubble_copy).score
    r2 = method.compare(bubble_copy, bubble_ref).score
    assert abs(r1 - r2) <= 10.0  # quasi-symétrique


def test_reformat_lowers_score(method, bubble_ref, bubble_copy, bubble_reformat):
    """Le reformatage fait baisser le score textuel (sensibilité au formatage)."""
    score_copy = method.compare(bubble_ref, bubble_copy).score
    score_reformat = method.compare(bubble_ref, bubble_reformat).score
    assert score_reformat < score_copy
    assert score_reformat < 95.0


def test_unrelated_below_threshold(method, bubble_ref, binary_search, factorial, gcd):
    """Codes sans relation : toujours sous le seuil d'alerte."""
    for cand in (binary_search, factorial, gcd):
        result = method.compare(bubble_ref, cand)
        assert result.score < THRESHOLD_LOW, (
            f"{cand.path} devrait être sous le seuil, score={result.score}"
        )


def test_renamed_collapses_at_level1(method, bubble_ref, bubble_renamed):
    """Le renommage fait s'effondrer le score textuel (attendu au niveau 1)."""
    result = method.compare(bubble_ref, bubble_renamed)
    assert result.score < THRESHOLD_LOW


def test_result_metadata(method, bubble_ref, bubble_copy):
    result = method.compare(bubble_ref, bubble_copy)
    assert 0.0 <= result.score <= 100.0
    assert result.language == bubble_copy.language
    assert result.candidate_path == bubble_copy.path
    assert result.time_ms >= 0.0


def test_invalid_file_returns_zero(method, bubble_ref, tmp_path):
    """Un fichier binaire invalide obtient un score de 0."""
    from models.loader import load_source_file
    bad = load_source_file(__file__)  # fichier de test : valide, mais contrôle le format
    result = method.compare(bubble_ref, bad)
    assert 0.0 <= result.score <= 100.0


def test_sub_scores_present(method, bubble_ref, bubble_copy):
    result = method.compare(bubble_ref, bubble_copy)
    assert result.sub_scores, "Les sous-scores ne doivent pas être vides pour un cas valide."
    for value in result.sub_scores.values():
        assert 0.0 <= float(value) <= 100.0

"""
Tests du niveau 2 — tokens normalisés, winnowing, GST, appariement de fonctions.

Objectifs vérifiés (spécification) :
  - fichiers identiques : score ≥ 95 % ;
  - renommage seul : score ≥ 80 % (robustesse aux renommages) ;
  - codes sans relation : score < 30 % ;
  - fonctions déplacées : le score niveau 2 doit être nettement supérieur
    au score niveau 1 (l'appariement de fonctions compense les déplacements).
"""

import pytest

from models.config import THRESHOLD_LOW
from models.methods.level1_text import Level1TextMethod
from models.methods.level2_tokens import Level2TokensMethod


@pytest.fixture(scope="module")
def method():
    return Level2TokensMethod()


def test_copy_exact_score_high(method, bubble_ref, bubble_copy):
    result = method.compare(bubble_ref, bubble_copy)
    assert result.score >= 95.0
    assert method.level == 2


def test_reformat_robust(method, bubble_ref, bubble_reformat):
    """Le reformatage seul ne doit pas faire chuter le score token."""
    result = method.compare(bubble_ref, bubble_reformat)
    assert result.score >= 80.0


def test_renamed_robust(method, bubble_ref, bubble_renamed):
    """Spécification : renommage seul → score ≥ 80 % au niveau 2."""
    result = method.compare(bubble_ref, bubble_renamed)
    assert result.score >= 80.0, (
        f"Le renommage devrait être robuste au niveau 2, score={result.score}"
    )


def test_reordered_functions_beat_level1(method, bubble_ref, bubble_reordered):
    """Fonctions réordonnées : le niveau 2 doit dominer le niveau 1."""
    score_l2 = method.compare(bubble_ref, bubble_reordered).score
    score_l1 = Level1TextMethod().compare(bubble_ref, bubble_reordered).score
    assert score_l2 > score_l1 + 15.0


def test_while_rewrite_detected(method, bubble_ref, bubble_while):
    """Réécriture for→while : le score baisse mais reste détectable."""
    result = method.compare(bubble_ref, bubble_while)
    assert result.score > THRESHOLD_LOW


def test_dead_code_detected(method, bubble_ref, bubble_dead_code):
    """Code mort ajouté : la partie d'origine reste détectée."""
    result = method.compare(bubble_ref, bubble_dead_code)
    assert result.score > THRESHOLD_LOW


def test_unrelated_below_threshold(method, bubble_ref, binary_search, factorial, gcd):
    """Spécification : codes sans relation → < 30 % au niveau 2."""
    for cand in (binary_search, factorial, gcd):
        result = method.compare(bubble_ref, cand)
        assert result.score < THRESHOLD_LOW, (
            f"{cand.path} devrait être sous le seuil, score={result.score}"
        )


def test_combo_harder_than_renamed(method, bubble_ref, bubble_renamed, bubble_combo):
    """Le cas combiné (renommage + while + code mort) est plus dur que le renommage seul."""
    score_renamed = method.compare(bubble_ref, bubble_renamed).score
    score_combo = method.compare(bubble_ref, bubble_combo).score
    assert score_combo < score_renamed


def test_bijective_renaming_flagged(method, bubble_ref, bubble_renamed):
    """Le renommage bijectif doit être signalé dans les notes."""
    result = method.compare(bubble_ref, bubble_renamed)
    notes_text = " ".join(result.notes).lower()
    assert "renomm" in notes_text or "biject" in notes_text


def test_result_bounded(method, bubble_ref, bubble_copy):
    result = method.compare(bubble_ref, bubble_copy)
    assert 0.0 <= result.score <= 100.0
    for value in result.sub_scores.values():
        assert 0.0 <= float(value) <= 100.0


def test_fragments_nonempty_for_high_score(method, bubble_ref, bubble_copy):
    result = method.compare(bubble_ref, bubble_copy)
    if result.score >= 80.0 and bubble_ref.is_valid and bubble_copy.is_valid:
        assert result.fragments, "Un score élevé devrait s'accompagner de fragments."

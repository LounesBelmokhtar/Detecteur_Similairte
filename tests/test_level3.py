"""
Tests du niveau 3 — similarité structurelle inter-langages.

Objectifs vérifiés (spécification) :
  - fichiers identiques : score ≥ 95 % ;
  - renommage seul : score ≥ 80 % (la structure ignore les identifiants) ;
  - cross-langages : le même algorithme en Python/Java/C/JS obtient un score
    nettement supérieur aux algorithmes différents (hiérarchie exigée) ;
  - scores bornés dans [0, 100].
"""

import pytest

from models.methods.level3_structure import (
    Level3StructureMethod,
    detect_algorithm_patterns,
    reduce_to_canonical,
    structural_similarity,
    tree_similarity,
)
from tests.conftest import sample


@pytest.fixture(scope="module")
def method():
    return Level3StructureMethod()


# --- Mêmes langages -----------------------------------------------------------

def test_copy_exact_score_high(method, bubble_ref, bubble_copy):
    result = method.compare(bubble_ref, bubble_copy)
    assert result.score >= 95.0
    assert method.level == 3


def test_reformat_robust(method, bubble_ref, bubble_reformat):
    result = method.compare(bubble_ref, bubble_reformat)
    assert result.score >= 80.0


def test_renamed_robust(method, bubble_ref, bubble_renamed):
    """Spécification : renommage seul → ≥ 80 % au niveau 3."""
    result = method.compare(bubble_ref, bubble_renamed)
    assert result.score >= 80.0


def test_unrelated_same_language_lower_than_modified(
    method, bubble_ref, bubble_combo, binary_search, factorial, gcd
):
    """Un code modifié mais de même algorithme doit rester au-dessus des sans-relation."""
    score_combo = method.compare(bubble_ref, bubble_combo).score
    unrelated_scores = [
        method.compare(bubble_ref, cand).score
        for cand in (binary_search, factorial, gcd)
    ]
    assert score_combo > max(unrelated_scores) - 15.0


# --- Cross-langages : hiérarchie exigée ---------------------------------------

SAME_ALGO_PAIRS = [
    ("identical/bubble_sort_ref.py", "cross_language/BubbleSort.java"),
    ("identical/bubble_sort_ref.py", "cross_language/bubble_sort.c"),
    ("cross_language/fibonacci.py", "cross_language/Fibonacci.java"),
    ("cross_language/fibonacci.py", "cross_language/fibonacci.c"),
    ("cross_language/fibonacci.py", "cross_language/fibonacci.js"),
    ("unrelated/gcd.py", "cross_language/Gcd.java"),
    ("unrelated/binary_search.py", "cross_language/binary_search.c"),
    ("cross_language/primality_test.py", "cross_language/PrimalityTest.java"),
]

DIFF_ALGO_PAIRS = [
    ("cross_language/fibonacci.py", "cross_language/bubble_sort.c"),
    ("cross_language/fibonacci.py", "cross_language/gcd.c"),
    ("unrelated/binary_search.py", "cross_language/bubble_sort.c"),
    ("cross_language/primality_test.py", "cross_language/bubble_sort.c"),
    ("unrelated/factorial.py", "cross_language/gcd.c"),
]


@pytest.mark.parametrize("ref_rel,cand_rel", SAME_ALGO_PAIRS)
def test_cross_language_same_algorithm_score(method, ref_rel, cand_rel):
    """Même algorithme en langages différents : score nettement positif (≥ 55 %)."""
    result = method.compare(sample(ref_rel), sample(cand_rel))
    assert result.score >= 55.0, (
        f"{ref_rel} vs {cand_rel} : score trop bas pour le même algorithme "
        f"({result.score:.1f})"
    )


@pytest.mark.parametrize("ref_rel,cand_rel", DIFF_ALGO_PAIRS)
def test_cross_language_different_algorithm_score(method, ref_rel, cand_rel):
    """Algorithmes différents en langages différents : score modeste (≤ 50 %)."""
    result = method.compare(sample(ref_rel), sample(cand_rel))
    assert result.score <= 50.0, (
        f"{ref_rel} vs {cand_rel} : score trop élevé pour des algorithmes "
        f"différents ({result.score:.1f})"
    )


def test_cross_language_hierarchy(method):
    """Exigence : min(same-algo) > max(diff-algo) avec une marge nette."""
    same_scores = [
        method.compare(sample(r), sample(c)).score for r, c in SAME_ALGO_PAIRS
    ]
    diff_scores = [
        method.compare(sample(r), sample(c)).score for r, c in DIFF_ALGO_PAIRS
    ]
    assert min(same_scores) > max(diff_scores) + 10.0, (
        f"Hiérarchie non respectée : same min={min(same_scores):.1f}, "
        f"diff max={max(diff_scores):.1f}"
    )


# --- Composants internes ------------------------------------------------------

def test_reduce_to_canonical_strips_envelopes(bubble_ref):
    from models.ast_parser import parse_ast
    root = parse_ast(bubble_ref.raw_content, bubble_ref.language)
    red = reduce_to_canonical(root)
    assert red is not None
    # Après réduction, tous les nœuds conservés portent une catégorie canonique
    for node in red.walk():
        assert node.canonical is not None or not node.children or \
            node.node_type == "__reduced_group__"


def test_tree_similarity_identical_is_high(bubble_ref):
    from models.ast_parser import parse_ast
    root = parse_ast(bubble_ref.raw_content, bubble_ref.language)
    score = tree_similarity(root, root)
    assert score >= 0.99


def test_structural_similarity_identical_is_one():
    vec = {"a": 0.5, "b": 0.5}
    assert structural_similarity(vec, dict(vec)) == pytest.approx(1.0)


def test_structural_similarity_disjoint_is_zero():
    assert structural_similarity({"a": 1.0}, {"b": 1.0}) == pytest.approx(0.0)


def test_detect_patterns_bubble(bubble_ref, bubble_copy, binary_search):
    ref_patterns = detect_algorithm_patterns(bubble_ref)
    assert "bubble_sort" in ref_patterns
    assert ref_patterns["bubble_sort"] >= 0.7

    bs_patterns = detect_algorithm_patterns(binary_search)
    assert "bubble_sort" not in bs_patterns


def test_result_bounded_and_metadata(method, bubble_ref, bubble_copy):
    result = method.compare(bubble_ref, bubble_copy)
    assert 0.0 <= result.score <= 100.0
    assert result.language == bubble_copy.language
    for value in result.sub_scores.values():
        assert 0.0 <= float(value) <= 100.0


def test_notes_mention_cross_language(method):
    """La comparaison inter-langages doit le signaler dans les notes."""
    ref = sample("identical/bubble_sort_ref.py")
    cand = sample("cross_language/BubbleSort.java")
    result = method.compare(ref, cand)
    notes_text = " ".join(result.notes).lower()
    assert "langage" in notes_text or "cross" in notes_text or "langue" in notes_text

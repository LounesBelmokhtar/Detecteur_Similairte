"""
Tests des composants du cœur : chargement, lexage, normalisation,
catégorisation canonique, extraction AST, fragments et classement.
"""

import pytest

from models.config import THRESHOLD_HIGH, THRESHOLD_LOW
from models.ast_parser import compute_max_nesting, extract_functions, parse_ast
from models.canonical import CanonicalCategory, get_canonical_category
from models.fragments import Fragment, merge_adjacent_fragments
from models.lexer import filter_tokens, tokenize
from models.loader import detect_language, load_source_file
from models.normalizer import (
    detect_bijective_renaming,
    normalize_text_level1,
    normalize_tokens_level2,
    strip_comments,
)
from models.ranking import classify_alert, rank_candidates, weighted_score
from tests.conftest import sample


# --- Loader --------------------------------------------------------------------

def test_detect_language_by_extension():
    assert detect_language("a.py") == "python"
    assert detect_language("a.java") == "java"
    assert detect_language("a.c") == "c"
    assert detect_language("a.js") == "javascript"
    assert detect_language("a.cpp") == "cpp"


def test_load_source_file_ok(bubble_ref):
    assert bubble_ref.is_valid
    assert bubble_ref.language == "python"
    assert bubble_ref.line_count > 0
    assert not bubble_ref.is_empty


def test_load_binary_file_invalid():
    bad = load_source_file("samples/edge_cases/binary_dummy.bin")
    assert bad.is_valid is False
    assert bad.error_message


def test_load_empty_file():
    empty = load_source_file("samples/edge_cases/empty.py")
    assert empty.is_valid
    assert empty.is_empty


def test_load_directory_returns_list():
    from models.loader import load_directory
    files = load_directory("samples/unrelated", recursive=False)
    assert len(files) >= 3


# --- Lexer ---------------------------------------------------------------------

def test_tokenize_python_returns_tokens():
    tokens = tokenize("def f(x):\n    return x + 1\n", "python")
    assert tokens
    types = {t.type for t in tokens}
    assert "identifier" in types


def test_filter_tokens_ignores_comments():
    tokens = tokenize("# commentaire\nx = 1\n", "python")
    filtered = filter_tokens(tokens, ignore_comments=True)
    assert all(not t.type == "comment" for t in filtered)
    assert filtered  # il reste x = 1


def test_tokenize_unknown_language_fallback():
    tokens = tokenize("x = 1; y = 2;", "unknown")
    assert tokens  # le lexeur regex de secours fonctionne


# --- Normaliseur ---------------------------------------------------------------

def test_normalize_text_strips_comments():
    out = normalize_text_level1("# c\nx = 1\n", strip_comments=True, language="python")
    assert "# c" not in out
    assert "x = 1" in out


def test_normalize_text_keeps_strings():
    out = normalize_text_level1('x = "# pas un commentaire"\n',
                                strip_comments=True, language="python")
    assert "# pas un commentaire" in out


def test_strip_comments_preserves_indentation():
    code = "if True:\n    # commentaire\n    x = 1\n"
    out = strip_comments(code, "python")
    assert "    x = 1" in out
    assert "# commentaire" not in out


def test_normalize_tokens_level2():
    tokens = normalize_tokens_level2('name = "secret"\ncount = 42\n', "python")
    values = [t.value for t in tokens]
    assert "ID" in values      # les identifiants deviennent ID
    assert "NUM" in values     # les nombres deviennent NUM
    assert "STR" in values     # les chaînes deviennent STR
    assert "secret" not in values


def test_detect_bijective_renaming():
    a = "def foo(x):\n    return x + 1\n"
    b = "def bar(y):\n    return y + 1\n"
    mapping = detect_bijective_renaming(a, b, "python")
    assert mapping, "Un renommage bijectif devrait produire une table de correspondance."
    # Chaque identifiant de la référence doit être mappé de façon cohérente
    for old, new in mapping.items():
        assert old != new


def test_detect_bijective_renaming_absent_on_identical():
    a = "def foo(x):\n    return x + 1\n"
    mapping = detect_bijective_renaming(a, a, "python")
    # Sur un code identique, la « correspondance » est l'identité (x → x)
    for old, new in mapping.items():
        assert old == new


def test_renaming_consistency_ratio():
    from models.normalizer import renaming_consistency_ratio
    a = "def foo(x):\n    return x + 1\n"
    b = "def bar(y):\n    return y + 1\n"
    c = "def foo(x):\n    return x * 2\n"
    assert renaming_consistency_ratio(a, b, "python") >= 0.8
    assert renaming_consistency_ratio(a, c, "python") >= 0.8  # même noms, usage diffère peu


# --- Catégorisation canonique ---------------------------------------------------

@pytest.mark.parametrize("node_type,language,expected", [
    ("for_statement", "python", CanonicalCategory.LOOP),
    ("while_statement", "python", CanonicalCategory.LOOP),
    ("if_statement", "python", CanonicalCategory.IF),
    ("for_statement", "c", CanonicalCategory.LOOP),
    ("while_statement", "java", CanonicalCategory.LOOP),
    ("if_statement", "java", CanonicalCategory.IF),
    ("call", "python", CanonicalCategory.CALL),
    ("call_expression", "c", CanonicalCategory.CALL),
    ("identifier", "python", None),          # jamais IF (bug historique)
    ("identifier", "java", None),
    ("if", "python", CanonicalCategory.IF),  # mot-clé exact = IF (safe-words)
])
def test_get_canonical_category(node_type, language, expected):
    assert get_canonical_category(node_type, language) == expected


# --- AST ------------------------------------------------------------------------

def test_parse_ast_python(bubble_ref):
    root = parse_ast(bubble_ref.raw_content, "python")
    assert root is not None
    funcs = extract_functions(root)
    names = [u.name for u in funcs]
    assert "bubble_sort" in names


def test_parse_ast_java():
    src = "class A { int f(int x) { return x; } }"
    root = parse_ast(src, "java")
    assert root is not None
    funcs = extract_functions(root)
    assert any(u.name == "f" for u in funcs)


def test_complexity_and_nesting(bubble_ref):
    root = parse_ast(bubble_ref.raw_content, "python")
    assert compute_max_nesting(root) >= 2  # boucles imbriquées + if


def test_no_anonymous_node_pollution(bubble_ref):
    """Les nœuds sans type nommé ne doivent pas apparaître comme nœuds canoniques."""
    root = parse_ast(bubble_ref.raw_content, "python")
    for node in root.walk():
        if node.canonical == CanonicalCategory.IF:
            assert node.node_type != "identifier"


# --- Fragments ------------------------------------------------------------------

def test_merge_adjacent_fragments():
    frags = [
        Fragment(ref_start=1, ref_end=3, cand_start=1, cand_end=3, score=0.9),
        Fragment(ref_start=4, ref_end=6, cand_start=4, cand_end=6, score=0.8),
        Fragment(ref_start=20, ref_end=22, cand_start=20, cand_end=22, score=0.7),
    ]
    merged = merge_adjacent_fragments(frags, max_gap=1)
    assert len(merged) == 2  # les deux premiers se fusionnent


def test_merge_adjacent_requires_same_direction():
    frags = [
        Fragment(ref_start=1, ref_end=3, cand_start=10, cand_end=12, score=0.9),
        Fragment(ref_start=4, ref_end=6, cand_start=2, cand_end=4, score=0.8),
    ]
    merged = merge_adjacent_fragments(frags, max_gap=1)
    assert len(merged) == 2  # directions différentes : pas de fusion


# --- Ranking ---------------------------------------------------------------------

def test_classify_alert_levels():
    assert classify_alert(10.0, THRESHOLD_LOW, THRESHOLD_HIGH) == "low"
    assert classify_alert(50.0, THRESHOLD_LOW, THRESHOLD_HIGH) == "medium"
    assert classify_alert(90.0, THRESHOLD_LOW, THRESHOLD_HIGH) == "high"


def test_weighted_score():
    score = weighted_score({"a": 100.0, "b": 0.0}, {"a": 0.5, "b": 0.5})
    assert score == pytest.approx(50.0)


def test_weighted_score_normalizes_weights():
    score = weighted_score({"a": 100.0, "b": 0.0}, {"a": 2.0, "b": 2.0})
    assert score == pytest.approx(50.0)


def test_rank_candidates_sorted_descending():
    from models.ranking import CandidateRank
    results = [
        CandidateRank(path="low.py", filename="low.py", language="python", score=10.0),
        CandidateRank(path="high.py", filename="high.py", language="python", score=90.0),
        CandidateRank(path="mid.py", filename="mid.py", language="python", score=50.0),
    ]
    ranked = rank_candidates(results)
    assert [r.path for r in ranked] == ["high.py", "mid.py", "low.py"]
    assert ranked[0].rank == 1
    assert ranked[0].alert == "high"

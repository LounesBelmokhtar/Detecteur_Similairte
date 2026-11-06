"""
NIVEAU 3 — Comparaison structurelle inter-langages.

Reprend le niveau 2 et ajoute une représentation indépendante du langage :
  - Séquence canonique linéarisée (nœuds AST projetés en catégories universelles) ;
  - Descripteurs structurels invariants (histogramme, imbrication, complexité) ;
  - Distance / similarité d'édition d'arbres sur les arbres réduits ;
  - Détection heuristique de motifs algorithmiques classiques.

Les scores inter-langages sont naturellement plus bas : un facteur d'échelle
configurable (LEVEL3_SCALE_FACTOR) compense partiellement cet écart mécanique.
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

from models.config import WEIGHTS_LEVEL3, LEVEL3_SCALE_FACTOR
from models.ast_parser import (
    UniformASTNode,
    compute_file_complexity,
    compute_max_nesting,
    extract_functions,
    parse_ast,
)
from models.canonical import CanonicalCategory
from models.fragments import Fragment, merge_adjacent_fragments
from models.loader import SourceFile
from models.methods.base import SimilarityResult
from models.methods.level1_text import jaccard_ngrams_similarity, lcs_similarity


# ==============================================================================
# 1. SÉQUENCE CANONIQUE — comparable avec les méthodes du niveau 2
# ==============================================================================

def canonical_sequence(root: Optional[UniformASTNode]) -> List[str]:
    """Séquence linéarisée des catégories canoniques (parcours pré-ordre de l'AST réduit)."""
    if root is None:
        return []
    return [node.canonical.value for node in root.walk_canonical() if node.canonical]


def canonical_tokens_as_pseudo(sequences: List[str]):
    """
    Convertit une séquence de catégories en « pseudo-tokens » compatibles
    avec le tokenizer de niveau 2 (chaque catégorie = 1 token).
    """
    from models.lexer import Token
    tokens: List[Token] = []
    for idx, cat in enumerate(sequences):
        tokens.append(Token(
            type="CANON",
            value=cat,
            line=idx + 1,
            column=0,
            end_line=idx + 1,
            end_column=0,
        ))
    return tokens


def canonical_sequence_similarity(
    seq_ref: List[str],
    seq_cand: List[str],
) -> Tuple[float, List[Fragment]]:
    """
    Similarité sur séquences canoniques :
      - Jaccard n-grammes (n=3) comme mesure principale ;
      - LCS comme complément ;
      - Fragments via appariement de sous-séquences consécutives.
    """
    if not seq_ref and not seq_cand:
        return 1.0, []
    if not seq_ref or not seq_cand:
        return 0.0, []

    jac = jaccard_ngrams_similarity(seq_ref, seq_cand, n=3)
    lcs = lcs_similarity(seq_ref, seq_cand)

    combined = 0.6 * jac + 0.4 * lcs

    # Fragments : blocs identiques de catégories consécutives (≥ 3 éléments)
    fragments: List[Fragment] = []
    from difflib import SequenceMatcher
    matcher = SequenceMatcher(None, seq_ref, seq_cand, autojunk=False)
    for block in matcher.get_matching_blocks():
        if block.size >= 3:
            fragments.append(Fragment(
                ref_start=block.a + 1,
                ref_end=block.a + block.size,
                cand_start=block.b + 1,
                cand_end=block.b + block.size,
                score=1.0,
                label=f"Séquence canonique de {block.size} nœuds",
            ))

    return min(1.0, combined), merge_adjacent_fragments(fragments)


# ==============================================================================
# 2. DESCRIPTEURS STRUCTURELS INVARIANTS AU LANGAGE
# ==============================================================================

def structural_descriptor(root: Optional[UniformASTNode]) -> Dict[str, float]:
    """
    Construit un vecteur de descripteurs structurels indépendant du langage :
      - Histogramme normalisé des catégories canoniques ;
      - Profondeur d'imbrication maximale ;
      - Nombre de fonctions, de paramètres moyens ;
      - Complexité cyclomatique (totale et moyenne) ;
      - Ratio de boucles / conditions / appels.
    """
    descriptor: Dict[str, float] = {}

    if root is None:
        return descriptor

    canon_nodes = root.walk_canonical()
    counts = Counter(n.canonical for n in canon_nodes if n.canonical)
    total = sum(counts.values()) or 1

    # Histogramme normalisé (fréquence relative de chaque catégorie)
    for cat in CanonicalCategory:
        descriptor[f"hist_{cat.value}"] = counts.get(cat, 0) / total

    # Imbrication et complexité : mise à l'échelle [0, 1] pour que la
    # similarité cosinus ne soit pas dominée par la seule magnitude brute.
    descriptor["max_nesting"] = min(compute_max_nesting(root) / 8.0, 1.0)
    descriptor["complexity"] = min(compute_file_complexity(root) / 40.0, 1.0)

    # Unités fonctionnelles
    units = extract_functions(root)
    descriptor["n_functions"] = min(len(units) / 10.0, 1.0)
    avg_p = (sum(u.param_count for u in units) / len(units)) if units else 0.0
    descriptor["avg_params"] = min(avg_p / 8.0, 1.0)

    # Ratios de structures de contrôle
    descriptor["ratio_loop"] = counts.get(CanonicalCategory.LOOP, 0) / total
    descriptor["ratio_if"] = counts.get(CanonicalCategory.IF, 0) / total
    descriptor["ratio_call"] = counts.get(CanonicalCategory.CALL, 0) / total
    descriptor["ratio_assign"] = counts.get(CanonicalCategory.ASSIGN, 0) / total
    descriptor["ratio_binop"] = counts.get(CanonicalCategory.BINARY_OP, 0) / total
    descriptor["ratio_return"] = counts.get(CanonicalCategory.RETURN, 0) / total
    descriptor["ratio_declare"] = counts.get(CanonicalCategory.DECLARE, 0) / total

    # Taille : échelle logarithmique pour rester comparable aux ratios
    import math as _math
    descriptor["log_size"] = _math.log1p(total) / _math.log1p(400.0)

    # Profil d'imbrication : répartition des niveaux de profondeur des boucles
    loop_depth_hist: Counter = Counter()

    def _profile(node: UniformASTNode, depth: int) -> None:
        if node.canonical in (CanonicalCategory.LOOP, CanonicalCategory.IF):
            loop_depth_hist[min(depth, 5)] += 1
        for child in node.children:
            _profile(child, depth + (1 if node.canonical in (CanonicalCategory.LOOP, CanonicalCategory.IF) else 0))

    _profile(root, 0)
    prof_total = sum(loop_depth_hist.values()) or 1
    for d in range(6):
        descriptor[f"depth_{d}"] = loop_depth_hist.get(d, 0) / prof_total

    # Transitions (bigrammes) entre catégories de contrôle de flux, dans
    # l'ordre du parcours : capturent la séquence LOOP→LOOP→IF (tri imbriqué)
    # vs LOOP→IF (recherche), que l'histogramme seul ne distingue pas.
    control_cats = {
        CanonicalCategory.LOOP, CanonicalCategory.IF,
        CanonicalCategory.RETURN, CanonicalCategory.FUNCTION_DEF,
    }
    control_seq: List[str] = []
    for n in root.walk_canonical():
        if n.canonical in control_cats:
            control_seq.append(n.canonical.value)
    trans_total = max(len(control_seq) - 1, 1)
    for i in range(len(control_seq) - 1):
        descriptor[f"trans_{control_seq[i]}>{control_seq[i + 1]}"] = (
            descriptor.get(f"trans_{control_seq[i]}>{control_seq[i + 1]}", 0.0)
            + 1.0 / trans_total
        )

    return descriptor


def cosine_similarity_vec(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """
    Similarité cosinus entre deux vecteurs creux (dictionnaires).
    Les clés absentes sont considérées comme 0.
    """
    keys = set(vec_a) | set(vec_b)
    if not keys:
        return 1.0

    dot = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in keys)
    norm_a = math.sqrt(sum(vec_a.get(k, 0.0) ** 2 for k in keys))
    norm_b = math.sqrt(sum(vec_b.get(k, 0.0) ** 2 for k in keys))

    if norm_a == 0 and norm_b == 0:
        return 1.0
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return max(0.0, dot / (norm_a * norm_b))


def structural_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """
    Similarité structurelle par distance de variation totale (Total Variation).

    Les vecteurs sont d'abord normalisés en L1 (somme = 1) puis on calcule :
        sim = 1 - 0.5 * Σ |a_i - b_i|

    Contrairement au cosinus, cette mesure est sensible aux écarts absolus de
    proportion : deux petits programmes dont l'histogramme de catégories est
    dominé par les mêmes dimensions courantes obtiennent un cosinus très élevé
    alors que la variation totale révèle leurs vrais écarts de répartition.
    Résultat borné [0, 1].
    """
    keys = set(vec_a) | set(vec_b)
    if not keys:
        return 1.0

    norm_a = sum(abs(vec_a.get(k, 0.0)) for k in keys)
    norm_b = sum(abs(vec_b.get(k, 0.0)) for k in keys)

    if norm_a == 0 and norm_b == 0:
        return 1.0
    if norm_a == 0 or norm_b == 0:
        return 0.0

    l1_diff = sum(
        abs(vec_a.get(k, 0.0) / norm_a - vec_b.get(k, 0.0) / norm_b)
        for k in keys
    )
    return max(0.0, 1.0 - 0.5 * l1_diff)


# ==============================================================================
# 3. DISTANCE D'ÉDITION D'ARBRES (version simplifiée)
# ==============================================================================

def _subtree_size(node: Optional[UniformASTNode]) -> int:
    """Nombre de nœuds d'un sous-arbre (pour pondération par la taille)."""
    if node is None:
        return 0
    return 1 + sum(_subtree_size(c) for c in node.children)


def tree_edit_distance_simple(
    node_a: Optional[UniformASTNode],
    node_b: Optional[UniformASTNode],
    max_depth: int = 12,
) -> float:
    """
    Distance d'édit d'arbres simplifiée inspirée de Zhang-Shasha,
    reformulée en similarité récursive pondérée par la taille des sous-arbres.

    Principe :
      - Chaque nœud contribute un « point » de similarité locale base ∈ {0, 0.5, 1}
        selon la concordance de sa catégorie canonique ;
      - Les enfants sont appariés séquentiellement (simplification de
        l'appariement d'édition d'arbre optimal) ; les enfants sans correspondance
        apportent 0 ;
      - La similarité du nœud est la moyenne pondérée par la taille :
            sim = (base * 1 + Σ taille_enfant_i * sim_enfant_i)
                  / (1 + Σ taille_enfant_i)

    Cette pondération fait que les divergences profondes dans les grands
    sous-arbres pèsent proportionnellement à leur importance, au lieu d'être
    diluées par les niveaux supérieurs qui correspondent toujours.
    Retourne une similarité bornée [0, 1].
    """
    if node_a is None and node_b is None:
        return 1.0
    if node_a is None or node_b is None:
        return 0.0
    if max_depth <= 0:
        return 1.0 if node_a.node_type == node_b.node_type else 0.0

    # Catégorie de comparaison : canonique si définie, sinon type brut
    cat_a = node_a.canonical.value if node_a.canonical else node_a.node_type
    cat_b = node_b.canonical.value if node_b.canonical else node_b.node_type

    if cat_a == cat_b:
        base = 1.0
    elif node_a.canonical is not None and node_b.canonical is not None:
        base = 0.0   # Deux catégories canoniques différentes = vrai conflit
    elif node_a.node_type == node_b.node_type:
        base = 0.7   # Même type brut mais canonique non défini des deux côtés
    else:
        base = 0.0

    children_a = node_a.children
    children_b = node_b.children

    if not children_a and not children_b:
        return base

    # Appariement séquentiel des enfants pondéré par taille
    weighted_sum = base * 1.0
    total_weight = 1.0

    n_max = max(len(children_a), len(children_b))
    for i in range(n_max):
        ca = children_a[i] if i < len(children_a) else None
        cb = children_b[i] if i < len(children_b) else None
        child_sim = tree_edit_distance_simple(ca, cb, max_depth - 1)
        child_weight = max(_subtree_size(ca), _subtree_size(cb), 1)
        weighted_sum += child_sim * child_weight
        total_weight += child_weight

    return max(0.0, min(1.0, weighted_sum / total_weight))


def reduce_to_canonical(node: Optional[UniformASTNode]) -> Optional[UniformASTNode]:
    """
    Construit l'arbre réduit : seuls les nœuds portant une catégorie canonique
    sont conservés ; les enveloppes non canoniques sont supprimées en reliant
    directement les descendants canoniques les plus proches au parent conservé.

    Cet arbre réduit est le format de comparaison inter-langages : il aligne
    naturellement `method_declaration` (Java) sur `function_definition` (C)
    puisque les deux deviennent FUNCTION_DEF, quelles que soient les enveloppes.
    """
    if node is None:
        return None

    if node.canonical is None:
        # Enveloppe non canonique : propager les descendants canoniques proches
        reduced_children: List[UniformASTNode] = []
        for child in node.children:
            child_reduced = reduce_to_canonical(child)
            if child_reduced is not None:
                if child_reduced.node_type == "__reduced_group__":
                    reduced_children.extend(child_reduced.children)
                else:
                    reduced_children.append(child_reduced)
        if not reduced_children:
            return None
        if len(reduced_children) == 1:
            return reduced_children[0]
        group = UniformASTNode(
            node_type="__reduced_group__",
            language=node.language,
            start_line=node.start_line,
            end_line=node.end_line,
            text="",
            canonical=None,
        )
        group.children = reduced_children
        return group

    # Nœud canonique conservé
    kept = UniformASTNode(
        node_type=node.node_type,
        language=node.language,
        start_line=node.start_line,
        end_line=node.end_line,
        text=node.text,
        canonical=node.canonical,
    )
    for child in node.children:
        child_reduced = reduce_to_canonical(child)
        if child_reduced is not None:
            if child_reduced.node_type == "__reduced_group__":
                kept.children.extend(child_reduced.children)
            else:
                kept.children.append(child_reduced)
    return kept


def _reduced_tree_similarity(
    node_a: Optional[UniformASTNode],
    node_b: Optional[UniformASTNode],
) -> float:
    """
    Similarité sur arbres réduits avec appariement glouton des enfants par
    catégorie canonique (et non par position pure), pondérée par la taille.

    Pour chaque enfant de A, on cherche le premier enfant non apparié de B
    portant la même catégorie ; s'il n'existe pas, l'enfant de A apporte 0.
    Cette souplesse absorbe les décalages d'ordre et les différences de
    granularité entre langages (params déclarés avant/après, blocs intercalés).
    """
    if node_a is None and node_b is None:
        return 1.0
    if node_a is None or node_b is None:
        return 0.0

    # Similarité locale du nœud
    if node_a.canonical is not None and node_b.canonical is not None:
        base = 1.0 if node_a.canonical == node_b.canonical else 0.0
    elif node_a.node_type == node_b.node_type:
        base = 0.7
    else:
        base = 0.0

    children_a = node_a.children
    children_b = node_b.children

    if not children_a and not children_b:
        return base

    # Appariement glouton des enfants par catégorie
    used_b: set = set()
    weighted_sum = base * 1.0
    total_weight = 1.0

    for ca in children_a:
        matched_idx = -1
        if ca.canonical is not None:
            for j, cb in enumerate(children_b):
                if j in used_b:
                    continue
                if cb.canonical == ca.canonical:
                    matched_idx = j
                    break
        else:
            # Enfant non canonique (groupe réduit) : appariement positionnel
            for j, cb in enumerate(children_b):
                if j not in used_b:
                    matched_idx = j
                    break

        if matched_idx >= 0:
            used_b.add(matched_idx)
            cb = children_b[matched_idx]
            child_sim = _reduced_tree_similarity(ca, cb)
        else:
            child_sim = 0.0

        child_weight = max(_subtree_size(ca), 1)
        weighted_sum += child_sim * child_weight
        total_weight += child_weight

    # Enfants de B sans correspondance pénalisent aussi
    for j, cb in enumerate(children_b):
        if j not in used_b:
            w = max(_subtree_size(cb), 1)
            total_weight += w

    return max(0.0, min(1.0, weighted_sum / total_weight))


def tree_similarity(root_a: Optional[UniformASTNode], root_b: Optional[UniformASTNode]) -> float:
    """
    Similarité d'arbre globale : réduction aux nœuds canoniques puis comparaison
    pondérée par taille avec appariement glouton par catégorie.
    """
    if root_a is None and root_b is None:
        return 1.0
    if root_a is None or root_b is None:
        return 0.0

    red_a = reduce_to_canonical(root_a)
    red_b = reduce_to_canonical(root_b)

    if red_a is None and red_b is None:
        return 1.0
    if red_a is None or red_b is None:
        return 0.0

    return _reduced_tree_similarity(red_a, red_b)


# ==============================================================================
# 4. DÉTECTION DE MOTIFS ALGORITHMIQUES (bonus recommandé)
# ==============================================================================

def detect_algorithm_patterns(source: SourceFile) -> Dict[str, float]:
    """
    Heuristiques reconnaissant des motifs algorithmiques classiques.
    Retourne un dictionnaire {nom_du_motif: score_de_confiance [0..1]}.

    L'analyse porte sur le texte source et la séquence canonique :
    les motifs sont volontairement pragmatiques (recherche de combinaisons
    caractéristiques) plutôt que formels, conformément à l'esprit de heuristique.
    Les commentaires sont d'abord supprimés (via le lexer) pour que les motifs
    ne soient pas perturbés par de la documentation placée entre les instructions,
    tout en conservant l'indentation d'origine.
    """
    from models.normalizer import strip_comments

    code = strip_comments(source.raw_content, source.language)
    patterns: Dict[str, float] = {}

    # --- Tri à bulles : double boucle imbriquée + comparaison + échange ------
    has_nested_loop = bool(re.search(
        r"(for|while)[^\n]*\{[^}]*(for|while)",
        code, re.DOTALL
    )) or bool(re.search(
        r"for[^\n]*:\s*\n\s+(for|while)",
        code
    ))
    has_comparison = bool(re.search(r"(>|<)\s*(\w+\[|arr|a\[)", code)) or \
        bool(re.search(r"\w+\s*>\s*\w+", code))
    has_swap = bool(re.search(r"(\w+)\s*(=|,)\s*(\w+).*(=|,)\s*\1\b", code, re.DOTALL)) or \
        "swap" in code.lower()
    if has_nested_loop and has_comparison:
        patterns["bubble_sort"] = 0.7 + (0.2 if has_swap else 0.0)

    # --- PGCD : modulo sur variables dans une boucle (hors chaînes format) ----
    has_modulo = bool(re.search(r"\w+\s*%\s*\w+", code))
    has_loop = bool(re.search(r"(for|while)", code))
    if has_modulo and has_loop:
        patterns["gcd"] = 0.65

    # --- Fibonacci : récursion ou deux variables mises à jour ----------------
    has_recursive_two = bool(re.search(
        r"return\s+\w+\s*\(\s*\w+\s*-\s*1\s*\)\s*[+]\s*\w+\s*\(\s*\w+\s*-\s*2",
        code
    )) or bool(re.search(
        r"\w+\s*\(\s*\w+\s*-\s*1\s*\)[^;\n]*\w+\s*\(\s*\w+\s*-\s*2",
        code
    ))
    if has_recursive_two or ("fibonacci" in code.lower() or "fib" in code.lower()):
        patterns["fibonacci"] = 0.85 if has_recursive_two else 0.5

    # --- Test de primalité : racine carrée dans une boucle --------------------
    has_sqrt = bool(re.search(r"(sqrt|Math\.sqrt|math\.sqrt|\*\*\s*0\.5)", code))
    has_modulo_i = bool(re.search(r"\w+\s*%\s*\w+", code))
    if (has_sqrt and has_modulo_i) or ("is_prime" in code or "isPrime" in code or "prime" in code.lower()):
        patterns["primality_test"] = 0.7 if has_sqrt else 0.4

    # --- Recherche dichotomique : milieu + comparaison + borne gauche/droite --
    has_mid = bool(re.search(r"(mid|middle|mi)\s*=", code))
    has_bounds = bool(re.search(r"(low|left|start)\s*=", code)) and \
        bool(re.search(r"(high|right|end)\s*=", code))
    if has_mid and has_bounds:
        patterns["binary_search"] = 0.75

    # --- Recherche linéaire : boucle avec return/compare sur élément ----------
    has_index_loop = bool(re.search(r"(for|while)[^\n]*\bi\b", code))
    has_element_access = bool(re.search(r"\w+\[\s*\w+\s*\]", code))
    if has_index_loop and has_element_access and not has_nested_loop:
        patterns["linear_search"] = 0.5

    # --- Tri par insertion : boucle + décalage --------------------------------
    if has_nested_loop and not has_swap and has_comparison:
        patterns["insertion_sort"] = 0.55

    # --- Inversion de chaîne ---------------------------------------------------
    if ("reverse" in code.lower() or "[::-1]" in code or
            bool(re.search(r"length\s*-\s*1", code))):
        patterns["string_reverse"] = 0.5

    return patterns


def pattern_similarity(
    patterns_ref: Dict[str, float],
    patterns_cand: Dict[str, float],
) -> Tuple[float, List[str]]:
    """
    Compare deux ensembles de motifs détectés.
    Retourne (score [0..1], liste des motifs partagés).
    """
    if not patterns_ref and not patterns_cand:
        return 0.5, []   # Aucun motif : indécis, valeur neutre

    all_names = set(patterns_ref) | set(patterns_cand)
    if not all_names:
        return 0.5, []

    shared: List[str] = []
    acc = 0.0
    for name in all_names:
        ref_val = patterns_ref.get(name, 0.0)
        cand_val = patterns_cand.get(name, 0.0)
        pair_sim = min(ref_val, cand_val) / max(ref_val, cand_val, 1e-9)
        acc += pair_sim
        if ref_val > 0.3 and cand_val > 0.3:
            shared.append(name)

    score = acc / len(all_names)
    return score, shared


# ==============================================================================
# Méthode de comparaison du niveau 3
# ==============================================================================

class Level3StructureMethod:
    """Niveau 3 : similarité structurelle inter-langages."""

    level: int = 3
    name: str = "Niveau 3 — Structure inter-langages"

    def __init__(self, weights: Dict[str, float] | None = None,
                 min_fragment_lines: int = 3,
                 scale_factor: float = LEVEL3_SCALE_FACTOR) -> None:
        self.weights = weights or dict(WEIGHTS_LEVEL3)
        self.min_fragment_lines = min_fragment_lines
        self.scale_factor = scale_factor

    def compare(self, reference: SourceFile, candidate: SourceFile) -> SimilarityResult:
        """
        Compare deux fichiers sources par leur représentation structurelle.
        Fonctionne même lorsque les langages diffèrent.
        """
        t0 = time.perf_counter()
        notes: List[str] = []

        # --- Cas limites --------------------------------------------------------
        if not reference.is_valid or not candidate.is_valid:
            return SimilarityResult(
                candidate_path=candidate.path, language=candidate.language,
                score=0.0, time_ms=0.0,
                notes=[reference.error_message or "", candidate.error_message or ""],
            )
        if reference.is_empty and candidate.is_empty:
            return SimilarityResult(
                candidate_path=candidate.path, language=candidate.language,
                score=100.0, sub_scores={"all": 100.0}, time_ms=0.0,
                notes=["Deux fichiers vides : similarité définie à 100 %."],
            )
        if reference.is_empty or candidate.is_empty:
            return SimilarityResult(
                candidate_path=candidate.path, language=candidate.language,
                score=0.0, sub_scores={"all": 0.0}, time_ms=0.0,
                notes=["Un des deux fichiers est vide."],
            )

        same_lang = reference.language == candidate.language
        if not same_lang:
            notes.append(
                f"Comparaison inter-langages ({reference.language} ↔ {candidate.language}). "
                "Les scores structurels sont naturellement plus bas que les scores intra-langages."
            )

        # --- Parsing AST --------------------------------------------------------
        ast_ref = parse_ast(reference.raw_content, reference.language)
        ast_cand = parse_ast(candidate.raw_content, candidate.language)

        if ast_ref is None and ast_cand is None:
            notes.append(
                "AST indisponible pour les deux fichiers (tree-sitter non chargé "
                "ou langage non supporté) : repli sur la séquence textuelle."
            )
        elif ast_ref is None or ast_cand is None:
            notes.append(
                "AST indisponible pour un des fichiers : les sous-scores structurels "
                "seront partiels."
            )

        # --- 1. Séquence canonique -------------------------------------------
        seq_ref = canonical_sequence(ast_ref)
        seq_cand = canonical_sequence(ast_cand)
        canon_score, canon_fragments = canonical_sequence_similarity(seq_ref, seq_cand)

        # --- 2. Descripteurs structurels ----------------------------------------
        desc_ref = structural_descriptor(ast_ref)
        desc_cand = structural_descriptor(ast_cand)
        struct_score = structural_similarity(desc_ref, desc_cand)

        # --- 3. Similarité d'arbre -----------------------------------------------
        tree_score = tree_similarity(ast_ref, ast_cand)

        # --- 4. Motifs algorithmiques ---------------------------------------------
        patterns_ref = detect_algorithm_patterns(reference)
        patterns_cand = detect_algorithm_patterns(candidate)
        motif_score, shared_patterns = pattern_similarity(patterns_ref, patterns_cand)
        if shared_patterns:
            notes.append(
                f"Motifs algorithmiques reconnus : {', '.join(shared_patterns)}."
            )

        # --- Sous-scores ----------------------------------------------------------
        sub_scores = {
            "canonical_sequence": round(canon_score * 100.0, 2),
            "structural_vector": round(struct_score * 100.0, 2),
            "tree_similarity": round(tree_score * 100.0, 2),
            "pattern_heuristics": round(motif_score * 100.0, 2),
        }

        # --- Score global pondéré ---------------------------------------------------
        total_weight = sum(self.weights.get(k, 0.0) for k in sub_scores)
        if total_weight > 0:
            raw_score = sum(sub_scores[k] * self.weights.get(k, 0.0)
                            for k in sub_scores) / total_weight
        else:
            raw_score = 0.0

        # Calibrage : léger facteur d'échelle pour compenser la baisse inter-langages
        # uniquement lorsque les langages diffèrent (les scores intra-langages
        # sont déjà bien calibrés).
        if not same_lang:
            calibrated = raw_score * self.scale_factor
            calibrated = min(100.0, calibrated)
        else:
            calibrated = raw_score

        # --- Fragments inter-langages : appariement d'unités structurelles ------------
        fragments = self._match_structural_units(
            reference, candidate, ast_ref, ast_cand, canon_fragments
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return SimilarityResult(
            candidate_path=candidate.path,
            language=candidate.language,
            score=round(min(100.0, max(0.0, calibrated)), 2),
            sub_scores=sub_scores,
            fragments=fragments,
            time_ms=round(elapsed_ms, 2),
            notes=notes,
        )

    def _match_structural_units(
        self,
        ref_file: SourceFile,
        cand_file: SourceFile,
        ast_ref: Optional[UniformASTNode],
        ast_cand: Optional[UniformASTNode],
        fallback_fragments: List[Fragment],
    ) -> List[Fragment]:
        """
        Met en correspondance les fonctions / boucles / blocs de haut niveau
        entre les deux fichiers (potentiellement de langages différents).
        Projette ensuite les plages de tokens canoniques sur les lignes réelles.
        """
        if ast_ref is None or ast_cand is None:
            return fallback_fragments

        units_ref = extract_functions(ast_ref)
        units_cand = extract_functions(ast_cand)

        fragments: List[Fragment] = []

        if units_ref and units_cand:
            # Appariement glouton par similarité de séquence canonique
            pairs: List[Tuple[float, int, int]] = []
            for i, uref in enumerate(units_ref):
                for j, ucand in enumerate(units_cand):
                    seq_a = uref.node.canonical_sequence()
                    seq_b = ucand.node.canonical_sequence()
                    if not seq_a or not seq_b:
                        continue
                    sim = jaccard_ngrams_similarity(seq_a, seq_b, n=3)
                    pairs.append((sim, i, j))

            pairs.sort(reverse=True, key=lambda p: p[0])
            used_ref: set = set()
            used_cand: set = set()

            for sim, i, j in pairs:
                if i in used_ref or j in used_cand:
                    continue
                if sim < 0.3:
                    continue
                used_ref.add(i)
                used_cand.add(j)

                uref = units_ref[i]
                ucand = units_cand[j]
                ref_len = uref.end_line - uref.start_line + 1
                cand_len = ucand.end_line - ucand.start_line + 1

                if ref_len >= self.min_fragment_lines and cand_len >= self.min_fragment_lines:
                    fragments.append(Fragment(
                        ref_start=uref.start_line,
                        ref_end=uref.end_line,
                        cand_start=ucand.start_line,
                        cand_end=ucand.end_line,
                        score=round(sim, 2),
                        label=f"« {uref.name} » ↔ « {ucand.name} »",
                    ))

        if not fragments:
            fragments = fallback_fragments

        return merge_adjacent_fragments(fragments)

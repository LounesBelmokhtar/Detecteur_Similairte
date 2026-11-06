"""
NIVEAU 2 — Comparaison par tokens normalisés et transformations.

Reprend le niveau 1 et ajoute l'insensibilité aux transformations :
  - Renommage de variables / fonctions (normalisation → ID, NUM, STR) ;
  - Déplacement de fonctions et de blocs (winnowing, GST, appariement d'unités) ;
  - Mise en forme et commentaires modifiés (supprimés en amont).

Algorithmes implémentés explicitement :
  - Winnowing (empreintes de k-grammes, fenêtre glissante) — inspiré de MOSS ;
  - Greedy String Tiling — inspiré de JPlag ;
  - Appariement glouton des unités fonctionnelles ;
  - Hachage des sous-arbres AST normalisés (même langage).
"""

from __future__ import annotations

import hashlib
import time
from typing import Dict, List, Optional, Sequence, Tuple

from models.config import (
    LEVEL2_GST_MIN_TILE_LENGTH,
    LEVEL2_KGRAM_SIZE,
    LEVEL2_WINNOWING_WINDOW,
    WEIGHTS_LEVEL2,
)
from models.ast_parser import CodeUnit, extract_functions, parse_ast
from models.fragments import Fragment, merge_adjacent_fragments
from models.loader import SourceFile
from models.normalizer import (
    detect_bijective_renaming,
    normalize_tokens_level2,
    renaming_consistency_ratio,
)
from models.lexer import Token
from models.methods.base import SimilarityResult


# ==============================================================================
# 1. WINNOWING — Empreintes de k-grammes (algorithme MOSS)
# ==============================================================================

def _hash_kgram(kgram: Tuple[Token, ...]) -> int:
    """
    Hachage stable d'un k-gramme de tokens.
    On concatène (type, valeur) de chaque token puis on applique SHA-1.
    Un hash déterministe garantit que des k-grammes identiques entre deux fichiers
    produisent exactement la même empreinte.
    """
    payload = "|".join(f"{t.type}:{t.value}" for t in kgram)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    return int(digest, 16)


def extract_kgram_hashes(tokens: Sequence[Token], k: int = LEVEL2_KGRAM_SIZE) -> List[int]:
    """Liste des hachages des k-grammes glissants de la séquence de tokens."""
    if len(tokens) < k:
        if tokens:
            return [_hash_kgram(tuple(tokens))]
        return []
    return [_hash_kgram(tuple(tokens[i:i + k])) for i in range(len(tokens) - k + 1)]


def winnow(hashes: List[int], window: int = LEVEL2_WINNOWING_WINDOW) -> set:
    """
    Winnowing : sélection d'empreintes par fenêtre glissante de taille `w`.
    Dans chaque fenêtre, on retient le hash minimal ; en cas d'égalité,
    on retient le plus à droite (règle de droite de Schleimer et al., 2003).

    Cette sélection garantit que tout k-gramme apparaissant dans les deux
    documents est détecté avec une probabilité déterministe élevée, tout en
    réduisant massivement le nombre d'empreintes à comparer.
    """
    if not hashes:
        return set()
    if window <= 1 or len(hashes) <= window:
        return {min(hashes)}

    selected: set = set()
    min_val: Optional[int] = None
    min_idx: int = -1

    for i, h in enumerate(hashes):
        # Glisser la fenêtre : on réinitialise le min à chaque entrée
        if i == 0 or h < min_val:
            min_val = h
            min_idx = i
        elif h == min_val:
            min_idx = i   # En cas d'égalité, préférer la position la plus à droite

        # Sortie de fenêtre : min_val sorti, il faut recalculer
        if i >= window - 1:
            # L'empreinte sélectionnée est celle du min dans la fenêtre [i-w+1, i]
            selected.add(min_val)

            # Recalculer le min sur la prochaine fenêtre si le min courant sort
            next_start = i - window + 2
            if min_idx < next_start:
                # Le minimum est sorti de la fenêtre : recalcul
                window_vals = hashes[next_start:i + 1]
                if window_vals:
                    # Préférer la position la plus à droite en cas d'égalité
                    min_val = min(window_vals)
                    min_idx = next_start + len(window_vals) - 1 - window_vals[::-1].index(min_val)
                    min_idx = len(hashes) - 1
                    for j in range(len(window_vals) - 1, -1, -1):
                        if window_vals[j] == min_val:
                            min_idx = next_start + j
                            break
    # Si aucun n'a été sélectionné (documents très courts)
    if not selected and hashes:
        selected.add(min(hashes))
    return selected


def winnowing_similarity(
    tokens_ref: Sequence[Token],
    tokens_cand: Sequence[Token],
    k: int = LEVEL2_KGRAM_SIZE,
    window: int = LEVEL2_WINNOWING_WINDOW,
) -> float:
    """
    Similarité par empreintes Winnowing.

    On utilise la moyenne des deux containments (couverture directionnelle) :
        score = 0.5 * (|F_ref ∩ F_cand| / |F_ref| + |F_ref ∩ F_cand| / |F_cand|)

    Cette mesure symétrique est moins pénalisante que Jaccard lorsque l'un
    des fichiers contient du contenu additionnel (code mort, réordonnancement),
    tout en restant sensible aux vraies dissimilarités. Borné [0, 1].
    """
    fp_ref = winnow(extract_kgram_hashes(tokens_ref, k), window)
    fp_cand = winnow(extract_kgram_hashes(tokens_cand, k), window)

    if not fp_ref and not fp_cand:
        return 1.0
    if not fp_ref or not fp_cand:
        return 0.0

    intersection = len(fp_ref & fp_cand)
    containment_ref = intersection / len(fp_ref)
    containment_cand = intersection / len(fp_cand)
    return 0.5 * (containment_ref + containment_cand)


# ==============================================================================
# 2. GREEDY STRING TILING (GST) — algorithme JPlag
# ==============================================================================

def greedy_string_tiling(
    tokens_a: Sequence[Token],
    tokens_b: Sequence[Token],
    min_tile_length: int = LEVEL2_GST_MIN_TILE_LENGTH,
) -> List[Tuple[int, int, int]]:
    """
    Greedy String Tiling (GST) : identification récursive des plus longues
    sous-séquences communes non chevauchantes entre deux séquences de tokens.

    Principe (simplifié de JPlag) :
      1. On construit un index hashé des positions de tous les k-grammes de B
         (k = min_tile_length) ;
      2. On parcourt A et, pour chaque position, on cherche la tuile la plus longue
         en étendant progressivement ;
      3. On marque les positions utilisées dans A et B (plus de recouvrement) ;
      4. On répète jusqu'à ce qu'aucune tuile d'au moins min_tile_length ne soit trouvée.

    Retourne une liste de tuples (pos_a, pos_b, length) indexés à 0.
    """
    if len(tokens_a) < min_tile_length or len(tokens_b) < min_tile_length:
        return []

    hash_a = [hash(tuple(t.value + ":" + t.type for t in tokens_a[i:i + min_tile_length]))
              for i in range(len(tokens_a) - min_tile_length + 1)]
    hash_b = [hash(tuple(t.value + ":" + t.type for t in tokens_b[i:i + min_tile_length]))
              for i in range(len(tokens_b) - min_tile_length + 1)]

    # Index : hash de k-gramme → positions dans B
    index_b: Dict[int, List[int]] = {}
    for pos, h in enumerate(hash_b):
        index_b.setdefault(h, []).append(pos)

    # Marqueurs de recouvrement
    marked_a = [False] * len(tokens_a)
    marked_b = [False] * len(tokens_b)
    tiles: List[Tuple[int, int, int]] = []

    # On trie les positions de A par hash pour regrouper les recherches
    order_a = sorted(range(len(hash_a)), key=lambda i: hash_a[i])

    found_any = True
    while found_any:
        found_any = False
        best_tile: Optional[Tuple[int, int, int]] = None
        best_length = 0

        for pos_a in order_a:
            if marked_a[pos_a]:
                continue
            h = hash_a[pos_a]
            candidates = index_b.get(h, [])
            for pos_b in candidates:
                if marked_b[pos_b]:
                    continue
                # Étendre la tuile tant que les tokens correspondent
                length = 0
                while (pos_a + length < len(tokens_a)
                       and pos_b + length < len(tokens_b)
                       and not marked_a[pos_a + length]
                       and not marked_b[pos_b + length]
                       and tokens_a[pos_a + length].value == tokens_b[pos_b + length].value
                       and tokens_a[pos_a + length].type == tokens_b[pos_b + length].type):
                    length += 1

                if length >= min_tile_length and length > best_length:
                    best_length = length
                    best_tile = (pos_a, pos_b, length)

        if best_tile is not None:
            pa, pb, ln = best_tile
            # Marquer les positions couvertes
            for i in range(pa, pa + ln):
                marked_a[i] = True
            for i in range(pb, pb + ln):
                marked_b[i] = True
            tiles.append(best_tile)
            found_any = True

    return tiles


def gst_similarity(
    tokens_ref: Sequence[Token],
    tokens_cand: Sequence[Token],
    min_tile_length: int = LEVEL2_GST_MIN_TILE_LENGTH,
) -> Tuple[float, List[Tuple[int, int, int]]]:
    """
    Score GST : somme des longueurs de tuiles couvrant la référence
    divisée par le nombre total de tokens de la référence.
    Mesure directionnelle (couverture de la référence) bornée [0, 1].
    """
    if not tokens_ref:
        return 1.0 if not tokens_cand else 0.0
    if not tokens_cand:
        return 0.0, []

    tiles = greedy_string_tiling(tokens_ref, tokens_cand, min_tile_length)
    covered = sum(t[2] for t in tiles)
    score = covered / len(tokens_ref) if tokens_ref else 0.0
    return min(1.0, score), tiles


def gst_to_fragments(
    tiles: List[Tuple[int, int, int]],
    tokens_ref: List[Token],
    tokens_cand: List[Token],
) -> List[Fragment]:
    """
    Convertit les tuiles GST (positions de tokens) en fragments (plages de lignes).
    Chaque tuile est projetée sur les lignes des tokens qu'elle couvre.
    """
    fragments: List[Fragment] = []
    for pos_a, pos_b, length in tiles:
        if length <= 0:
            continue
        ref_start = tokens_ref[pos_a].line
        ref_end = tokens_ref[pos_a + length - 1].end_line
        cand_start = tokens_cand[pos_b].line
        cand_end = tokens_cand[pos_b + length - 1].end_line

        fragments.append(Fragment(
            ref_start=ref_start,
            ref_end=ref_end,
            cand_start=cand_start,
            cand_end=cand_end,
            score=1.0,
            label=f"Tuile de {length} tokens",
        ))

    return merge_adjacent_fragments(fragments)


# ==============================================================================
# 3. APPARIEMENT DES UNITÉS FONCTIONNELLES (fonctions déplacées)
# ==============================================================================

def match_functions(
    units_ref: List[CodeUnit],
    units_cand: List[CodeUnit],
    min_fragment_lines: int = 3,
) -> Tuple[float, List[Fragment]]:
    """
    Appariement glouton des fonctions entre référence et candidat.

    Principe :
      1. Pour chaque paire possible (ref, cand), calculer la similarité GST de tokens ;
      2. Trier les paires par similarité décroissante ;
      3. Associer gloutonement tant que les deux unités ne sont pas déjà appariées.

    Le score global pondère chaque paire par la taille (nb de lignes) de l'unité
    de référence, mesurant ainsi la part de la référence couverte.
    """
    if not units_ref:
        return 1.0 if not units_cand else 0.0
    if not units_cand:
        return 0.0, []

    # Construire les séquences de tokens normalisés par unité
    def _unit_tokens(unit: CodeUnit, language: str) -> List[Token]:
        # Récupérer les lignes de l'unité
        src = "\n".join(unit.node.text.split("\n")) if unit.node.text else ""
        # Re-tokeniser le texte du nœud si disponible
        from models.loader import SourceFile
        return normalize_tokens_level2(unit.node.text, language)

    # On construit une matrice de similarité par paires
    pairs: List[Tuple[float, int, int]] = []
    for i, uref in enumerate(units_ref):
        for j, ucand in enumerate(units_cand):
            # Comparaison des séquences canoniques de sous-arbres
            seq_ref = uref.node.canonical_sequence()
            seq_cand = ucand.node.canonical_sequence()
            if not seq_ref or not seq_cand:
                sim = 0.0
            else:
                # Jaccard sur n-grammes de catégories
                from models.methods.level1_text import jaccard_ngrams_similarity
                sim = jaccard_ngrams_similarity(seq_ref, seq_cand, n=3)

            # Bonus : si les noms de fonctions correspondent exactement
            if uref.name == ucand.name and uref.name.startswith("_") is False:
                sim = min(1.0, sim + 0.15)

            pairs.append((sim, i, j))

    # Tri par similarité décroissante, puis appariement glouton
    pairs.sort(reverse=True, key=lambda p: p[0])
    matched_ref: set = set()
    matched_cand: set = set()
    matched_pairs: List[Tuple[float, int, int]] = []

    for sim, i, j in pairs:
        if i in matched_ref or j in matched_cand:
            continue
        matched_ref.add(i)
        matched_cand.add(j)
        matched_pairs.append((sim, i, j))

    # Score pondéré par la taille des unités de référence
    total_weight = 0.0
    acc = 0.0
    fragments: List[Fragment] = []

    for sim, i, j in matched_pairs:
        weight = max(1, units_ref[i].end_line - units_ref[i].start_line + 1)
        acc += sim * weight
        total_weight += weight

        if sim > 0.3:
            ref_start = units_ref[i].start_line
            ref_end = units_ref[i].end_line
            cand_start = units_cand[j].start_line
            cand_end = units_cand[j].end_line
            if (ref_end - ref_start + 1) >= min_fragment_lines:
                fragments.append(Fragment(
                    ref_start=ref_start,
                    ref_end=ref_end,
                    cand_start=cand_start,
                    cand_end=cand_end,
                    score=round(sim, 2),
                    label=f"Fonction « {units_ref[i].name} » → « {units_cand[j].name} »",
                ))

    # Les unités non appariées contribuent à la pénalité (non couvertes)
    for i, u in enumerate(units_ref):
        if i not in matched_ref:
            weight = max(1, u.end_line - u.start_line + 1)
            total_weight += weight  # acc reste inchangé → score diminue

    score = acc / total_weight if total_weight > 0 else 0.0
    return min(1.0, score), fragments


# ==============================================================================
# 4. HACHAGE DES SOUS-ARBRES AST (même langage)
# ==============================================================================

def ast_subtree_similarity(
    root_ref,
    root_cand,
) -> float:
    """
    Similarité basée sur l'ensemble des hachages de sous-arbres.
    Jaccard sur les hash SHA-1 des sous-arbres normalisés.
    """
    if root_ref is None or root_cand is None:
        return 0.0

    hashes_ref = {n.subtree_hash() for n in root_ref.walk()}
    hashes_cand = {n.subtree_hash() for n in root_cand.walk()}

    if not hashes_ref or not hashes_cand:
        return 0.0

    intersection = len(hashes_ref & hashes_cand)
    union = len(hashes_ref | hashes_cand)
    return intersection / union if union else 0.0


# ==============================================================================
# Méthode de comparaison du niveau 2
# ==============================================================================

class Level2TokensMethod:
    """Niveau 2 : tokens normalisés, winnowing, GST, appariement de fonctions."""

    level: int = 2
    name: str = "Niveau 2 — Tokens & transformations"

    def __init__(self, weights: Dict[str, float] | None = None,
                 kgram_size: int = LEVEL2_KGRAM_SIZE,
                 winnowing_window: int = LEVEL2_WINNOWING_WINDOW,
                 gst_min_tile: int = LEVEL2_GST_MIN_TILE_LENGTH,
                 min_fragment_lines: int = 3) -> None:
        self.weights = weights or dict(WEIGHTS_LEVEL2)
        self.kgram_size = kgram_size
        self.winnowing_window = winnowing_window
        self.gst_min_tile = gst_min_tile
        self.min_fragment_lines = min_fragment_lines

    def compare(self, reference: SourceFile, candidate: SourceFile) -> SimilarityResult:
        """
        Compare deux fichiers sources au niveau des tokens normalisés.
        Robuste au renommage, au déplacement de fonctions et à la mise en forme.
        """
        t0 = time.perf_counter()
        notes: List[str] = []

        # --- Cas limites -------------------------------------------------------
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

        if reference.language != candidate.language:
            notes.append(
                f"Langages différents ({reference.language} vs {candidate.language}) : "
                "le niveau 2 n'est pas adapté, préférez le niveau 3."
            )

        # --- Tokenisation normalisée -------------------------------------------
        tokens_ref = normalize_tokens_level2(reference.raw_content, reference.language)
        tokens_cand = normalize_tokens_level2(candidate.raw_content, candidate.language)

        # --- 1. Winnowing --------------------------------------------------------
        win_score = winnowing_similarity(tokens_ref, tokens_cand,
                                         k=self.kgram_size,
                                         window=self.winnowing_window)

        # --- 2. Greedy String Tiling --------------------------------------------
        gst_score, tiles = gst_similarity(tokens_ref, tokens_cand,
                                          min_tile_length=self.gst_min_tile)
        gst_fragments = gst_to_fragments(tiles, tokens_ref, tokens_cand)

        # --- 3. Appariement des fonctions ----------------------------------------
        ast_ref = parse_ast(reference.raw_content, reference.language)
        ast_cand = parse_ast(candidate.raw_content, candidate.language)
        units_ref = extract_functions(ast_ref)
        units_cand = extract_functions(ast_cand)

        if units_ref and units_cand:
            func_score, func_fragments = match_functions(
                units_ref, units_cand, self.min_fragment_lines
            )
        else:
            # Pas de fonctions détectées : utiliser le score GST
            func_score = gst_score
            func_fragments = []

        # --- 4. Sous-arbres AST ----------------------------------------------------
        ast_score = ast_subtree_similarity(ast_ref, ast_cand)

        # --- Indicateur de renommage cohérent (diagnostic) --------------------------
        rename_ratio = renaming_consistency_ratio(
            reference.raw_content, candidate.raw_content, reference.language
        )
        rename_map = detect_bijective_renaming(
            reference.raw_content, candidate.raw_content, reference.language
        )
        actual_renames = {old: new for old, new in rename_map.items() if old != new}
        if rename_ratio > 0.7 and actual_renames:
            sample_renames = ", ".join(
                f"{old}→{new}" for old, new in list(actual_renames.items())[:3]
            )
            notes.append(
                f"Renommage détecté (cohérence {rename_ratio:.0%}) : "
                f"identifiants renommés de façon bijective (ex. {sample_renames})."
            )

        # --- Sous-scores ----------------------------------------------------------
        sub_scores = {
            "winnowing": round(win_score * 100.0, 2),
            "gst": round(gst_score * 100.0, 2),
            "function_matching": round(func_score * 100.0, 2),
            "ast_subtrees": round(ast_score * 100.0, 2),
        }

        # --- Score global pondéré --------------------------------------------------
        total_weight = sum(self.weights.get(k, 0.0) for k in sub_scores)
        if total_weight > 0:
            score = sum(sub_scores[k] * self.weights.get(k, 0.0) for k in sub_scores) / total_weight
        else:
            score = 0.0

        # --- Fragments -------------------------------------------------------------
        fragments = gst_fragments + func_fragments
        fragments = merge_adjacent_fragments(fragments)

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

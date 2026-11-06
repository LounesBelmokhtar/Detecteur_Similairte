"""
Normalisation de code source selon les trois niveaux du détecteur.

Niveau 1 : normalisation textuelle (espaces, fins de ligne, commentaires).
Niveau 2 : normalisation par tokens (identifiants → ID, littéraux → NUM/STR).
Niveau 3 : projection sur séquence de catégories canoniques (géré par canonical.py).
"""

from __future__ import annotations

import re
from typing import Dict, List

from models.config import STDLIB_IDENTIFIERS
from models.lexer import Token, filter_tokens, tokenize


# ==============================================================================
# NIVEAU 1 — Normalisation textuelle
# ==============================================================================

def normalize_text_level1(
    content: str,
    strip_comments: bool = True,
    language: str = "unknown",
) -> str:
    """
    Normalisation textuelle de base pour le niveau 1 :
    - Conversion des fins de ligne en \\n ;
    - Suppression des commentaires (via le lexer, pour ne pas casser les chaînes) ;
    - Suppression des espaces superflus (début/fin de ligne) ;
    - Suppression des lignes vides successives.
    """
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    if strip_comments:
        content = _remove_comments(content, language)

    lines = content.split("\n")
    cleaned: List[str] = []
    prev_empty = False

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            if not prev_empty:
                cleaned.append("")
                prev_empty = True
        else:
            # Réduire les espaces internes multiples à une seule occurrence
            stripped = re.sub(r"[ \t]{2,}", " ", stripped)
            cleaned.append(stripped)
            prev_empty = False

    # Supprimer la ligne vide éventuelle en tête et en queue
    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return "\n".join(cleaned)


def _remove_comments(code: str, language: str) -> str:
    """
    Supprime les commentaires du code en utilisant le lexer
    pour distinguer correctement les commentaires des chaînes de caractères.
    """
    tokens = tokenize(code, language)
    if not tokens:
        return code

    # Reconstruction ligne par ligne en ignorant les tokens commentaires
    # On travaille sur les offsets pour préserver le reste du code
    result = list(code)
    # Marquer les positions des commentaires (parcouleur du bas vers le haut)
    for tok in tokens:
        if not tok.is_comment:
            continue
        # Calculer les offsets bytes dans la chaîne originale
        # On reconstruit via les lignes
        pass

    # Méthode alternative plus simple : filtrer ligne par ligne
    # en évitant de supprimer du contenu dans les chaînes multi-lignes.
    return _strip_comments_by_line(code, language)


def _strip_comments_by_line(code: str, language: str) -> str:
    """Supprime les commentaires en préservant les chaînes de caractères."""
    tokens = tokenize(code, language)
    if not tokens:
        return code

    # Construire un masque caractère par caractère
    chars = list(code)

    # Calculer les offsets absolus depuis les positions ligne/colonne
    lines = code.split("\n")
    line_offsets: List[int] = []
    offset = 0
    for ln in lines:
        line_offsets.append(offset)
        offset += len(ln) + 1  # +1 pour le \n

    for tok in tokens:
        if not tok.is_comment:
            continue
        # Début
        start_idx = line_offsets[tok.line - 1] + tok.column if tok.line - 1 < len(line_offsets) else 0
        if tok.end_line - 1 < len(line_offsets):
            end_idx = line_offsets[tok.end_line - 1] + tok.end_column
        else:
            end_idx = len(chars)

        # Remplacer par des espaces pour préserver la numérotation des lignes
        for i in range(start_idx, min(end_idx, len(chars))):
            if chars[i] != "\n":
                chars[i] = " "

    return "".join(chars)


def strip_comments(code: str, language: str) -> str:
    """
    Supprime uniquement les commentaires du code source en conservant
    l'indentation et la mise en page d'origine (utile pour les heuristiques
    basées sur des expressions régulières qui dépendent du formatage).
    """
    return _strip_comments_by_line(code, language)


# ==============================================================================
# NIVEAU 2 — Normalisation par tokens
# ==============================================================================

def normalize_tokens_level2(
    code: str,
    language: str = "unknown",
    ignore_comments: bool = True,
    keep_stdlib: bool = True,
) -> List[Token]:
    """
    Normalise les tokens pour le niveau 2 :
    - Identifiants non-standard → « ID » ;
    - Nombres → « NUM » ;
    - Chaînes → « STR » ;
    - Mots-clés, opérateurs et identifiants de la bibliothèque standard conservés.
    """
    raw_tokens = tokenize(code, language)
    tokens = filter_tokens(raw_tokens, ignore_comments=ignore_comments)
    stdlib = STDLIB_IDENTIFIERS.get(language, set())

    normalized: List[Token] = []
    for tok in tokens:
        new_type = tok.type
        new_value = tok.value

        if tok.type == "number":
            new_type = "NUM"
            new_value = "NUM"
        elif tok.type == "string":
            new_type = "STR"
            new_value = "STR"
        elif tok.type == "boolean":
            new_type = "BOOL"
            new_value = "BOOL"
        elif tok.type == "identifier":
            if keep_stdlib and tok.value in stdlib:
                # Conserver l'identifiant de la bibliothèque standard
                new_type = "identifier"
                new_value = tok.value
            else:
                new_type = "ID"
                new_value = "ID"

        normalized.append(Token(
            type=new_type,
            value=new_value,
            line=tok.line,
            column=tok.column,
            end_line=tok.end_line,
            end_column=tok.end_column,
        ))

    return normalized


def _raw_identifiers(code: str, language: str) -> List[str]:
    """Séquence brute des valeurs d'identifiants (hors commentaires/ponctuation)."""
    tokens = filter_tokens(tokenize(code, language), ignore_comments=True)
    return [t.value for t in tokens if t.type == "identifier"]


def detect_bijective_renaming(
    ref_code: str,
    cand_code: str,
    language: str = "unknown",
) -> Dict[str, str]:
    """
    Détecte un renommage cohérent (alpha-renaming) entre référence et candidat.
    Retourne une table de correspondance {ancien_nom → nouveau_nom}
    si chaque identifiant de la référence est systématiquement remplacé
    par le même identifiant dans le candidat (bijectivité).

    Important : on travaille sur les identifiants BRUTS (avant normalisation
    en « ID »), car la normalisation efface justement les noms à comparer.
    """
    ref_ids = _raw_identifiers(ref_code, language)
    cand_ids = _raw_identifiers(cand_code, language)

    if not ref_ids or not cand_ids:
        return {}

    # On aligne les séquences brute d'identifiants (positions 1:1 si longueurs égales)
    if len(ref_ids) != len(cand_ids):
        # Essayer par fréquence d'apparition
        ref_freq: Dict[str, int] = {}
        cand_freq: Dict[str, int] = {}
        for x in ref_ids:
            ref_freq[x] = ref_freq.get(x, 0) + 1
        for x in cand_ids:
            cand_freq[x] = cand_freq.get(x, 0) + 1

        if len(ref_freq) != len(cand_freq):
            return {}

        # Associer par ordre de fréquence décroissante
        ref_sorted = sorted(ref_freq, key=lambda k: (-ref_freq[k], k))
        cand_sorted = sorted(cand_freq, key=lambda k: (-cand_freq[k], k))
        mapping = dict(zip(ref_sorted, cand_sorted))
    else:
        mapping: Dict[str, str] = {}
        bijective = True
        reverse: Dict[str, str] = {}
        for old, new in zip(ref_ids, cand_ids):
            if old in mapping and mapping[old] != new:
                bijective = False
                break
            if new in reverse and reverse[new] != old:
                bijective = False
                break
            mapping[old] = new
            reverse[new] = old

        if not bijective:
            # Repli sur le tri par fréquence
            ref_freq = {}
            cand_freq = {}
            for x in ref_ids:
                ref_freq[x] = ref_freq.get(x, 0) + 1
            for x in cand_ids:
                cand_freq[x] = cand_freq.get(x, 0) + 1
            ref_sorted = sorted(ref_freq, key=lambda k: (-ref_freq[k], k))
            cand_sorted = sorted(cand_freq, key=lambda k: (-cand_freq[k], k))
            mapping = dict(zip(ref_sorted, cand_sorted))

    return mapping


def renaming_consistency_ratio(
    ref_code: str,
    cand_code: str,
    language: str = "unknown",
) -> float:
    """
    Mesure la cohérence du renommage : proportion d'identifiants de la référence
    qui sont remplacés de façon constante dans le candidat.
    1.0 = renommage parfaitement bijectif ; 0.0 = aucun renommage cohérent.
    Travaille sur les identifiants bruts (avant normalisation en « ID »).
    """
    ref_ids = _raw_identifiers(ref_code, language)
    if not ref_ids:
        return 1.0

    mapping = detect_bijective_renaming(ref_code, cand_code, language)
    if not mapping:
        return 0.0

    # Vérifier la cohérence positionnelle si les longueurs coïncident
    cand_ids = _raw_identifiers(cand_code, language)
    if len(ref_ids) == len(cand_ids) and len(ref_ids) > 0:
        hits = sum(1 for old, new in zip(ref_ids, cand_ids)
                   if mapping.get(old) == new)
        return hits / len(ref_ids)

    # Sinon, estimer via la couverture des identifiants uniques de la référence
    unique_ref = set(ref_ids)
    covered = sum(1 for u in unique_ref if u in mapping)
    return covered / len(unique_ref) if unique_ref else 0.0

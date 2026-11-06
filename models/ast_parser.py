"""
Parsing AST uniforme multi-langages.

Convertit l'AST tree-sitter en une structure récursive indépendante de la bibliothèque,
puis expose des utilitaires d'extraction d'unités (fonctions, boucles) et de hachage
de sous-arbres pour les niveaux 2 et 3.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional

from models.canonical import CanonicalCategory, get_canonical_category
from models.lexer import _get_tree_sitter_parser


@dataclass
class UniformASTNode:
    """Nœud d'arbre syntaxique unifié, compatible tree-sitter ou repli regex."""
    node_type: str
    language: str
    start_line: int          # Ligne de début (1-indexé)
    end_line: int            # Ligne de fin (1-indexé)
    text: str = ""           # Texte du nœud (tronqué si trop long)
    canonical: Optional[CanonicalCategory] = None
    children: List["UniformASTNode"] = field(default_factory=list)

    # ---------------------------------------------------------------
    # Parcours utilitaires
    # ---------------------------------------------------------------
    def walk(self) -> List["UniformASTNode"]:
        """Parcours pré-ordre de l'arbre complet."""
        result: List[UniformASTNode] = [self]
        for child in self.children:
            result.extend(child.walk())
        return result

    def walk_canonical(self) -> List["UniformASTNode"]:
        """Parcours pré-ordre des seuls nœuds ayant une catégorie canonique."""
        result: List[UniformASTNode] = []
        for node in self.walk():
            if node.canonical is not None:
                result.append(node)
        return result

    def find_all(self, category: CanonicalCategory) -> List["UniformASTNode"]:
        """Retourne tous les nœuds possédant la catégorie canonique donnée."""
        return [n for n in self.walk() if n.canonical == category]

    def subtree_hash(self) -> str:
        """
        Hachage SHA-1 du sous-arbre normalisé : type + catégorie canonique des descendants.
        Deux sous-arbres structuralement identiques produisent le même hash,
        indépendamment des identifiants et littéraux exacts.
        """
        parts: List[str] = []
        for node in self.walk():
            cat = node.canonical.value if node.canonical else "_"
            parts.append(f"{node.node_type}:{cat}")
        joined = "|".join(parts)
        return hashlib.sha1(joined.encode("utf-8")).hexdigest()

    def canonical_sequence(self) -> List[CanonicalCategory]:
        """Séquence linéarisée des catégories canoniques (parcours pré-ordre)."""
        return [n.canonical for n in self.walk_canonical() if n.canonical is not None]


# ==============================================================================
# Construction de l'arbre uniforme via tree-sitter
# ==============================================================================

def _build_uniform_nodes(ts_node, language: str) -> List[UniformASTNode]:
    """
    Récursion : convertit un nœud tree-sitter en liste de nœuds uniformes.

    Les nœuds anonymes (jetons bruts : ponctuation, mots-clés comme `for`,
    `if`…) sont « transparents » : ils ne sont pas conservés comme nœuds
    (ce serait un double comptage LOOP/IF déjà portés par le nœud
    structurant parent tel que `for_statement`), mais leurs éventuels
    descendants nommés sont aplatis dans le parent pour ne perdre aucune
    structure. Les commentaires sont supprimés.
    """
    # Ignorer les commentaires
    if ts_node.type in ("comment", "line_comment", "block_comment"):
        return []

    # Nœud anonyme (jeton brut) : on descend en aplatisant
    if not ts_node.is_named:
        flattened: List[UniformASTNode] = []
        for child in ts_node.children:
            flattened.extend(_build_uniform_nodes(child, language))
        return flattened

    canon = get_canonical_category(ts_node.type, language)

    text = ""
    try:
        raw = ts_node.text or b""
        text = raw.decode("utf-8", errors="replace")
        if len(text) > 200:
            text = text[:200] + "..."
    except Exception:
        text = ""

    node = UniformASTNode(
        node_type=ts_node.type,
        language=language,
        start_line=ts_node.start_point[0] + 1,
        end_line=ts_node.end_point[0] + 1,
        text=text,
        canonical=canon,
    )

    for child in ts_node.children:
        node.children.extend(_build_uniform_nodes(child, language))

    return [node]


def parse_ast(code: str, language: str) -> Optional[UniformASTNode]:
    """
    Analyse le code source et retourne l'arbre syntaxique uniforme.
    Retourne None si tree-sitter n'est pas disponible pour ce langage.
    """
    parser = _get_tree_sitter_parser(language)
    if parser is None:
        return None

    try:
        source_bytes = code.encode("utf-8", errors="replace")
        tree = parser.parse(source_bytes)
        roots = _build_uniform_nodes(tree.root_node, language)
        if not roots:
            return None
        # S'il y a plusieurs racines (aplatissement), on crée une racine synthétique
        if len(roots) == 1:
            return roots[0]
        synthetic = UniformASTNode(
            node_type="synthetic_root",
            language=language,
            start_line=roots[0].start_line,
            end_line=roots[-1].end_line,
            text="",
            canonical=None,
        )
        synthetic.children = roots
        return synthetic
    except Exception:
        return None


# ==============================================================================
# Extraction d'unités (fonctions / méthodes / procédures)
# ==============================================================================

@dataclass
class CodeUnit:
    """Unité de code extraite (fonction, méthode, boucle de haut niveau)."""
    name: str               # Nom de l'unité (ou "__main__" pour le code global)
    start_line: int
    end_line: int
    node: UniformASTNode
    param_count: int = 0
    complexity: int = 1      # Complexité cyclomatique approximée


def extract_functions(root: Optional[UniformASTNode]) -> List[CodeUnit]:
    """
    Extrait toutes les unités fonctionnelles (fonctions, méthodes) de l'arbre.
    Si aucune fonction n'est détectée, retourne le fichier entier comme unité unique.
    """
    if root is None:
        return []

    func_nodes = root.find_all(CanonicalCategory.FUNCTION_DEF)
    units: List[CodeUnit] = []

    for idx, fn in enumerate(func_nodes):
        # Nom de la fonction : recherché par type de nœud (identifier / name),
        # en descendant dans les enveloppes (function_declarator…) si nécessaire.
        name = f"_func_{idx}"
        for node in fn.walk():
            if node is fn:
                continue
            if node.node_type in ("identifier", "field_identifier", "name"):
                if node.text and node.text.isidentifier():
                    name = node.text
                    break
        if name.startswith("_func_"):
            # Repli : premier enfant dont le texte est un identifiant
            for child in fn.children:
                if child.canonical is None and child.text and child.text.isidentifier():
                    name = child.text
                    break

        # Comptage des paramètres
        param_count = len(fn.find_all(CanonicalCategory.PARAM))

        # Complexité cyclomatique approximée : 1 + nb de branchements
        complexity = 1
        for n in fn.walk():
            if n.canonical in (CanonicalCategory.IF, CanonicalCategory.LOOP, CanonicalCategory.SWITCH):
                complexity += 1

        units.append(CodeUnit(
            name=name,
            start_line=fn.start_line,
            end_line=fn.end_line,
            node=fn,
            param_count=param_count,
            complexity=complexity,
        ))

    return units


def compute_file_complexity(root: Optional[UniformASTNode]) -> int:
    """Complexité cyclomatique globale approximative du fichier."""
    if root is None:
        return 1
    complexity = 1
    for n in root.walk():
        if n.canonical in (CanonicalCategory.IF, CanonicalCategory.LOOP, CanonicalCategory.SWITCH):
            complexity += 1
    return complexity


def compute_max_nesting(root: Optional[UniformASTNode]) -> int:
    """Profondeur maximale d'imbrication de structures de contrôle (boucles/conditions)."""
    if root is None:
        return 0
    control_cats = {CanonicalCategory.LOOP, CanonicalCategory.IF, CanonicalCategory.SWITCH}
    max_depth = 0

    def _recurse(node: UniformASTNode, depth: int) -> None:
        nonlocal max_depth
        new_depth = depth + 1 if node.canonical in control_cats else depth
        max_depth = max(max_depth, new_depth)
        for child in node.children:
            _recurse(child, new_depth)

    _recurse(root, 0)
    return max_depth

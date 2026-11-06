"""
Table de correspondance et catégories canoniques pour l'analyse syntaxique multi-langages.

Le niveau 3 utilise cette abstraction unifiée pour s'abstraire des particularités syntaxiques
de Python, Java, C, C++ et JavaScript. Chaque nœud pertinent de l'AST est projeté dans une
catégorie canonique sémantiquement universelle.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, Set


class CanonicalCategory(str, Enum):
    """Catégories canoniques indépendantes du langage de programmation."""
    FUNCTION_DEF = "FUNCTION_DEF"    # Définition de fonction ou méthode
    PARAM = "PARAM"                  # Paramètre formel de fonction
    LOOP = "LOOP"                    # Boucle (for, while, do-while)
    IF = "IF"                        # Branchement conditionnel if / elif
    ELSE = "ELSE"                    # Branche alternative else
    SWITCH = "SWITCH"                # Aiguillage switch / match
    RETURN = "RETURN"                # Instruction de retour
    ASSIGN = "ASSIGN"                # Affectation de variable
    DECLARE = "DECLARE"              # Déclaration explicite de variable / type
    CALL = "CALL"                    # Appel de fonction / méthode
    BINARY_OP = "BINARY_OP"          # Opération binaire (arithmétique, logique, comparaison)
    UNARY_OP = "UNARY_OP"            # Opération unaire (+, -, !, ~)
    INDEX = "INDEX"                  # Indexation / accès tableau ou dictionnaire
    BREAK = "BREAK"                  # Interruption de boucle
    CONTINUE = "CONTINUE"            # Poursuite de boucle
    LITERAL = "LITERAL"              # Littéral constant (nombre, chaîne, booléen)
    IDENTIFIER = "IDENTIFIER"        # Identifiant de variable ou fonction
    BLOCK = "BLOCK"                  # Bloc d'instructions / corps d'exécution
    UNKNOWN = "UNKNOWN"              # Nœud non classifié


# Nœuds purement syntaxiques ou spécifiques à ignorer (bruit)
IGNORED_NODE_TYPES: Set[str] = {
    ";", "{", "}", "(", ")", "[", "]", ",", ":", ".", "->", "::",
    "comment", "line_comment", "block_comment",
    "import_statement", "import_from_statement", "preproc_include",
    "package_declaration", "type_annotation", "type_identifier",
    "primitive_type", "type_qualifier", "visibility_modifier",
    "public", "private", "protected", "static", "final", "const",
    "void", "self", "this", "cls", "export_statement",
    # Enveloppes déclaratives redondantes avec leur parent (C/C++/Java) :
    # les paramètres et le nom de fonction restent accessibles via les enfants.
    "function_declarator", "pointer_declarator", "array_declarator",
    "abstract_function_declarator", "abstract_pointer_declarator",
}


# Mappage des types de nœuds tree-sitter par langage vers les catégories canoniques
PYTHON_CANONICAL_MAP: Dict[str, CanonicalCategory] = {
    "function_definition": CanonicalCategory.FUNCTION_DEF,
    "parameters": CanonicalCategory.PARAM,
    "for_statement": CanonicalCategory.LOOP,
    "while_statement": CanonicalCategory.LOOP,
    "if_statement": CanonicalCategory.IF,
    "elif_clause": CanonicalCategory.IF,
    "else_clause": CanonicalCategory.ELSE,
    "match_statement": CanonicalCategory.SWITCH,
    "return_statement": CanonicalCategory.RETURN,
    "assignment": CanonicalCategory.ASSIGN,
    "augmented_assignment": CanonicalCategory.ASSIGN,
    "call": CanonicalCategory.CALL,
    "binary_operator": CanonicalCategory.BINARY_OP,
    "boolean_operator": CanonicalCategory.BINARY_OP,
    "comparison_operator": CanonicalCategory.BINARY_OP,
    "not_operator": CanonicalCategory.UNARY_OP,
    "unary_operator": CanonicalCategory.UNARY_OP,
    "subscript": CanonicalCategory.INDEX,
    "break_statement": CanonicalCategory.BREAK,
    "continue_statement": CanonicalCategory.CONTINUE,
    "integer": CanonicalCategory.LITERAL,
    "float": CanonicalCategory.LITERAL,
    "string": CanonicalCategory.LITERAL,
    "true": CanonicalCategory.LITERAL,
    "false": CanonicalCategory.LITERAL,
    "none": CanonicalCategory.LITERAL,
    "block": CanonicalCategory.BLOCK,
}

JAVA_CANONICAL_MAP: Dict[str, CanonicalCategory] = {
    "method_declaration": CanonicalCategory.FUNCTION_DEF,
    "constructor_declaration": CanonicalCategory.FUNCTION_DEF,
    "formal_parameter": CanonicalCategory.PARAM,
    "for_statement": CanonicalCategory.LOOP,
    "enhanced_for_statement": CanonicalCategory.LOOP,
    "while_statement": CanonicalCategory.LOOP,
    "do_statement": CanonicalCategory.LOOP,
    "if_statement": CanonicalCategory.IF,
    "switch_expression": CanonicalCategory.SWITCH,
    "switch_statement": CanonicalCategory.SWITCH,
    "return_statement": CanonicalCategory.RETURN,
    "assignment_expression": CanonicalCategory.ASSIGN,
    "local_variable_declaration": CanonicalCategory.DECLARE,
    "field_declaration": CanonicalCategory.DECLARE,
    "method_invocation": CanonicalCategory.CALL,
    "binary_expression": CanonicalCategory.BINARY_OP,
    "unary_expression": CanonicalCategory.UNARY_OP,
    "array_access": CanonicalCategory.INDEX,
    "break_statement": CanonicalCategory.BREAK,
    "continue_statement": CanonicalCategory.CONTINUE,
    "decimal_integer_literal": CanonicalCategory.LITERAL,
    "decimal_floating_point_literal": CanonicalCategory.LITERAL,
    "string_literal": CanonicalCategory.LITERAL,
    "character_literal": CanonicalCategory.LITERAL,
    "true": CanonicalCategory.LITERAL,
    "false": CanonicalCategory.LITERAL,
    "null_literal": CanonicalCategory.LITERAL,
    "block": CanonicalCategory.BLOCK,
}

C_CANONICAL_MAP: Dict[str, CanonicalCategory] = {
    "function_definition": CanonicalCategory.FUNCTION_DEF,
    "parameter_declaration": CanonicalCategory.PARAM,
    "for_statement": CanonicalCategory.LOOP,
    "while_statement": CanonicalCategory.LOOP,
    "do_statement": CanonicalCategory.LOOP,
    "if_statement": CanonicalCategory.IF,
    "switch_statement": CanonicalCategory.SWITCH,
    "return_statement": CanonicalCategory.RETURN,
    "assignment_expression": CanonicalCategory.ASSIGN,
    "declaration": CanonicalCategory.DECLARE,
    "call_expression": CanonicalCategory.CALL,
    "binary_expression": CanonicalCategory.BINARY_OP,
    "unary_expression": CanonicalCategory.UNARY_OP,
    "pointer_expression": CanonicalCategory.UNARY_OP,
    "subscript_expression": CanonicalCategory.INDEX,
    "break_statement": CanonicalCategory.BREAK,
    "continue_statement": CanonicalCategory.CONTINUE,
    "number_literal": CanonicalCategory.LITERAL,
    "string_literal": CanonicalCategory.LITERAL,
    "char_literal": CanonicalCategory.LITERAL,
    "compound_statement": CanonicalCategory.BLOCK,
}

JS_CANONICAL_MAP: Dict[str, CanonicalCategory] = {
    "function_declaration": CanonicalCategory.FUNCTION_DEF,
    "method_definition": CanonicalCategory.FUNCTION_DEF,
    "arrow_function": CanonicalCategory.FUNCTION_DEF,
    "function": CanonicalCategory.FUNCTION_DEF,
    "formal_parameters": CanonicalCategory.PARAM,
    "for_statement": CanonicalCategory.LOOP,
    "for_in_statement": CanonicalCategory.LOOP,
    "for_of_statement": CanonicalCategory.LOOP,
    "while_statement": CanonicalCategory.LOOP,
    "do_statement": CanonicalCategory.LOOP,
    "if_statement": CanonicalCategory.IF,
    "switch_statement": CanonicalCategory.SWITCH,
    "return_statement": CanonicalCategory.RETURN,
    "assignment_expression": CanonicalCategory.ASSIGN,
    "variable_declaration": CanonicalCategory.DECLARE,
    "lexical_declaration": CanonicalCategory.DECLARE,
    "call_expression": CanonicalCategory.CALL,
    "binary_expression": CanonicalCategory.BINARY_OP,
    "unary_expression": CanonicalCategory.UNARY_OP,
    "update_expression": CanonicalCategory.UNARY_OP,
    "subscript_expression": CanonicalCategory.INDEX,
    "member_expression": CanonicalCategory.INDEX,
    "break_statement": CanonicalCategory.BREAK,
    "continue_statement": CanonicalCategory.CONTINUE,
    "number": CanonicalCategory.LITERAL,
    "string": CanonicalCategory.LITERAL,
    "true": CanonicalCategory.LITERAL,
    "false": CanonicalCategory.LITERAL,
    "null": CanonicalCategory.LITERAL,
    "statement_block": CanonicalCategory.BLOCK,
}


def get_canonical_category(node_type: str, language: str) -> Optional[CanonicalCategory]:
    """
    Associe un type de nœud AST spécifique au langage à sa catégorie canonique universelle.
    Retourne None si le nœud doit être ignoré.
    """
    if node_type in IGNORED_NODE_TYPES:
        return None

    mapping: Dict[str, CanonicalCategory]
    if language == "python":
        mapping = PYTHON_CANONICAL_MAP
    elif language == "java":
        mapping = JAVA_CANONICAL_MAP
    elif language in ("c", "cpp"):
        mapping = C_CANONICAL_MAP
    elif language == "javascript":
        mapping = JS_CANONICAL_MAP
    else:
        # Recherche par correspondance heuristique de nom
        for m in (PYTHON_CANONICAL_MAP, JAVA_CANONICAL_MAP, C_CANONICAL_MAP, JS_CANONICAL_MAP):
            if node_type in m:
                return m[node_type]
        return None

    if node_type in mapping:
        return mapping[node_type]

    # Heuristiques génériques sur le nom du nœud.
    # Attention : les tests doivent être « sûr-mots » pour éviter des faux
    # positifs comme « identIFier » qui contient la sous-chaîne « if ».
    lower = node_type.lower()
    if lower.startswith("function") or lower.startswith("method") or lower.endswith("_function"):
        return CanonicalCategory.FUNCTION_DEF
    if (lower in ("for_statement", "while_statement", "do_statement", "loop_statement")
            or lower.startswith("for_") or lower.startswith("while_")):
        return CanonicalCategory.LOOP
    if (lower in ("if_statement", "if", "elif_clause", "conditional_expression")
            or lower.startswith("if_")):
        return CanonicalCategory.IF
    if "return" in lower:
        return CanonicalCategory.RETURN
    if "assign" in lower:
        return CanonicalCategory.ASSIGN
    if lower.endswith("_call") or lower.startswith("call") or "invocation" in lower:
        return CanonicalCategory.CALL
    if "binary" in lower:
        return CanonicalCategory.BINARY_OP
    if "literal" in lower or "constant" in lower:
        return CanonicalCategory.LITERAL

    return None

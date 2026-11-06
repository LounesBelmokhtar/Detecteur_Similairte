"""
Module de tokenisation (analyse lexicale) multi-langages.

Ce module extrait une séquence ordonnée de tokens à partir du code source.
Il utilise prioritairement tree-sitter pour une extraction précise tenant compte
de la grammaire exacte du langage, et fournit un mécanisme de repli robuste par
expressions régulières si tree-sitter échoue ou si le langage n'a pas de grammaire chargée.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

# Tentative d'importation de tree-sitter
TREE_SITTER_AVAILABLE = False
try:
    import tree_sitter
    from tree_sitter import Language, Parser
    import tree_sitter_python
    import tree_sitter_java
    import tree_sitter_c
    import tree_sitter_javascript
    try:
        import tree_sitter_cpp
        CPP_AVAILABLE = True
    except ImportError:
        CPP_AVAILABLE = False

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class Token:
    """Représentation d'une unité lexicale (token) avec son positionnement."""
    type: str         # Catégorie : identifier, keyword, number, string, operator, punctuation, comment, unknown
    value: str        # Texte brut du token
    line: int         # Ligne de début (indexée à 1)
    column: int       # Colonne de début (indexée à 0)
    end_line: int     # Ligne de fin (indexée à 1)
    end_column: int   # Colonne de fin (indexée à 0)

    @property
    def is_comment(self) -> bool:
        return self.type == "comment"

    @property
    def is_identifier(self) -> bool:
        return self.type == "identifier"

    @property
    def is_literal(self) -> bool:
        return self.type in ("number", "string", "boolean", "character")


# Initialisation paresseuse des analyseurs tree-sitter
_PARSERS: Dict[str, Parser] = {}

def _get_tree_sitter_parser(language: str) -> Optional[Parser]:
    """Récupère ou instancie l'analyseur tree-sitter pour le langage spécifié."""
    if not TREE_SITTER_AVAILABLE:
        return None

    if language in _PARSERS:
        return _PARSERS[language]

    try:
        mod = None
        if language == "python":
            mod = tree_sitter_python
        elif language == "java":
            mod = tree_sitter_java
        elif language == "c":
            mod = tree_sitter_c
        elif language == "javascript":
            mod = tree_sitter_javascript
        elif language == "cpp" and CPP_AVAILABLE:
            mod = tree_sitter_cpp

        if mod is not None:
            lang = Language(mod.language())
            parser = Parser(lang)
            _PARSERS[language] = parser
            return parser
    except Exception:
        pass

    return None


def _classify_tree_sitter_leaf(node_type: str, text: str) -> str:
    """Classifie le type de nœud feuille tree-sitter en catégorie unifiée."""
    if "comment" in node_type:
        return "comment"
    if node_type in ("identifier", "name", "field_identifier", "type_identifier", "property_identifier"):
        return "identifier"
    if node_type in ("integer", "float", "number", "decimal_integer_literal", "number_literal"):
        return "number"
    if node_type in ("string", "string_literal", "raw_string", "concatenated_string", "char_literal", "character"):
        return "string"
    if node_type in ("true", "false", "boolean_literal"):
        return "boolean"
    if node_type in ("=", "+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "!", "&", "|", "^", "~", "<<", ">>", "+=", "-=", "*=", "/="):
        return "operator"
    if node_type in (";", ",", ".", ":", "(", ")", "[", "]", "{", "}"):
        return "punctuation"
    # Mots-clés courants
    if node_type in ("if", "else", "for", "while", "do", "return", "def", "function", "class", "import", "from", "public", "private", "protected", "static", "void", "int", "float", "double", "char", "bool", "let", "const", "var", "switch", "case", "break", "continue", "try", "catch", "throw", "finally", "new", "struct", "include"):
        return "keyword"
    return "keyword" if node_type.isidentifier() else "punctuation"


def tokenize_with_tree_sitter(code: str, language: str) -> Optional[List[Token]]:
    """Tokenise le code source via tree-sitter en parcourant les feuilles de l'AST."""
    parser = _get_tree_sitter_parser(language)
    if parser is None:
        return None

    try:
        source_bytes = code.encode("utf-8", errors="replace")
        tree = parser.parse(source_bytes)
        tokens: List[Token] = []

        # Types de nœuds qui doivent être émis comme un token unique
        # (sinon leurs enfants anonymes — guillemets, fragments de chaîne —
        # seraient tokenisés séparément et la valeur du littéral serait perdue).
        ATOMIC_NODE_TYPES = {
            "string", "string_literal", "raw_string", "concatenated_string",
            "char_literal", "character",
            "comment", "line_comment", "block_comment",
        }

        def walk(node):
            raw_text = node.text.decode("utf-8", errors="replace") if node.text else ""
            if node.type in ATOMIC_NODE_TYPES or len(node.children) == 0:
                cat = _classify_tree_sitter_leaf(node.type, raw_text)
                tokens.append(Token(
                    type=cat,
                    value=raw_text,
                    line=node.start_point[0] + 1,
                    column=node.start_point[1],
                    end_line=node.end_point[0] + 1,
                    end_column=node.end_point[1]
                ))
            else:
                for child in node.children:
                    walk(child)

        walk(tree.root_node)
        return tokens
    except Exception:
        return None


# Expressions régulières de repli pour la tokenisation
REGEX_PATTERNS = [
    ("comment_multiline", r"/\*[\s\S]*?\*/|'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\""),
    ("comment_single", r"//[^\n]*|#[^\n]*"),
    ("string", r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\""),
    ("number", r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
    ("identifier", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
    ("operator", r"==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|<<|>>|[+\-*/%<>=!&|^~]"),
    ("punctuation", r"[{}()\[\];,:.]"),
    ("whitespace", r"[ \t\f\v]+"),
    ("newline", r"\n"),
    ("unknown", r"."),
]

COMPILED_FALLBACK_REGEX = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in REGEX_PATTERNS)
)

KEYWORDS_SET = {
    "def", "class", "return", "if", "elif", "else", "for", "while", "import", "from",
    "as", "try", "except", "finally", "with", "lambda", "yield", "pass", "break",
    "continue", "and", "or", "not", "is", "in", "public", "private", "protected",
    "static", "void", "int", "float", "double", "char", "boolean", "bool", "switch",
    "case", "default", "const", "let", "var", "function", "new", "this", "super",
    "struct", "typedef", "include", "null", "true", "false", "None", "True", "False"
}


def tokenize_with_regex(code: str) -> List[Token]:
    """Tokenisation de secours par expressions régulières (générique multi-langages)."""
    tokens: List[Token] = []
    line = 1
    column = 0

    for match in COMPILED_FALLBACK_REGEX.finditer(code):
        kind = match.lastgroup
        value = match.group()

        if kind == "newline":
            line += 1
            column = 0
            continue
        elif kind == "whitespace":
            column += len(value)
            continue

        start_line = line
        start_col = column

        # Compter les retours à la ligne dans les commentaires multi-lignes ou chaînes
        newlines_in_value = value.count("\n")
        if newlines_in_value > 0:
            end_line = line + newlines_in_value
            last_line_idx = value.rfind("\n")
            end_col = len(value) - last_line_idx - 1
            line = end_line
            column = end_col
        else:
            end_line = line
            column += len(value)
            end_col = column

        token_type = "unknown"
        if kind in ("comment_multiline", "comment_single"):
            token_type = "comment"
        elif kind == "string":
            token_type = "string"
        elif kind == "number":
            token_type = "number"
        elif kind == "operator":
            token_type = "operator"
        elif kind == "punctuation":
            token_type = "punctuation"
        elif kind == "identifier":
            if value in KEYWORDS_SET:
                token_type = "keyword"
            elif value in ("true", "false", "True", "False"):
                token_type = "boolean"
            else:
                token_type = "identifier"

        tokens.append(Token(
            type=token_type,
            value=value,
            line=start_line,
            column=start_col,
            end_line=end_line,
            end_column=end_col
        ))

    return tokens


def tokenize(code: str, language: str = "unknown") -> List[Token]:
    """
    Fonction principale de tokenisation.
    Tente tree-sitter en priorité, se rabat sur la tokenisation regex en cas d'indisponibilité.
    """
    if not code:
        return []

    if TREE_SITTER_AVAILABLE and language != "unknown":
        ts_tokens = tokenize_with_tree_sitter(code, language)
        if ts_tokens is not None and len(ts_tokens) > 0:
            return ts_tokens

    return tokenize_with_regex(code)


def filter_tokens(
    tokens: List[Token],
    ignore_comments: bool = True,
    ignore_punctuation: bool = False
) -> List[Token]:
    """Filtre les tokens selon les options choisies (suppression des commentaires, etc.)."""
    filtered = []
    for t in tokens:
        if ignore_comments and t.is_comment:
            continue
        if ignore_punctuation and t.type == "punctuation":
            continue
        filtered.append(t)
    return filtered

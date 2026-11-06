"""
Configuration centrale du détecteur de similarité de code.

Ce fichier regroupe l'ensemble des constantes, seuils, poids d'agrégation,
tailles de fenêtres algorithmiques et palettes de couleurs utilisées par
les modules d'analyse, l'interface graphique et les rapports.
"""

from typing import Dict, List, Set

# ==============================================================================
# 1. MESSAGE ÉTHIQUE ET DÉONTOLOGIQUE
# ==============================================================================
ETHICAL_WARNING: str = (
    "Un score de similarité ne constitue pas, à lui seul, une preuve de plagiat. "
    "Il signale des ressemblances statistiques et structurelles devant impérativement "
    "faire l'objet d'un examen critique par un humain qualifié."
)

# ==============================================================================
# 2. SEUILS D'ALERTE ET NIVEAUX DE RISQUE
# ==============================================================================
THRESHOLD_LOW: float = 30.0    # En dessous de 30% : similarité faible (vert)
THRESHOLD_HIGH: float = 70.0   # Au dessus de 70% : similarité élevée (rouge)
# Entre THRESHOLD_LOW et THRESHOLD_HIGH : similarité modérée (orange)

ALERT_LABELS: Dict[str, str] = {
    "low": "Faible",
    "medium": "Modéré",
    "high": "Élevé",
}

ALERT_COLORS: Dict[str, str] = {
    "low": "#16a34a",     # Vert
    "medium": "#ea580c",  # Orange
    "high": "#dc2626",    # Rouge
}

# ==============================================================================
# 3. PARAMÈTRES DU NIVEAU 1 — COMPARAISON TEXTUELLE
# ==============================================================================
# Poids de la combinaison pondérée (total = 1.0)
WEIGHTS_LEVEL1: Dict[str, float] = {
    "sequence_matcher": 0.35,   # Ratio difflib SequenceMatcher
    "levenshtein": 0.25,        # Similarité de Levenshtein normalisée
    "jaccard_ngrams": 0.25,     # Jaccard sur n-grammes de tokens textuels
    "lcs_lines": 0.15,          # Plus longue sous-séquence commune (lignes)
}

LEVEL1_NGRAM_SIZE: int = 4          # Taille n des n-grammes de caractères/mots
LEVEL1_MIN_MATCHING_LINES: int = 3  # Longueur min d'un bloc commun pour surlignage

# ==============================================================================
# 4. PARAMÈTRES DU NIVEAU 2 — TOKENS ET TRANSFORMATIONS
# ==============================================================================
# Poids de la combinaison pondérée (total = 1.0)
WEIGHTS_LEVEL2: Dict[str, float] = {
    "winnowing": 0.30,          # Empreintes Winnowing (algorithme MOSS)
    "gst": 0.35,                # Greedy String Tiling (algorithme JPlag)
    "function_matching": 0.20,  # Appariement glouton des fonctions/méthodes
    "ast_subtrees": 0.15,       # Hash des sous-arbres normalisés
}

LEVEL2_KGRAM_SIZE: int = 5           # Taille des k-grammes de tokens
LEVEL2_WINNOWING_WINDOW: int = 4    # Taille de la fenêtre w pour Winnowing
LEVEL2_GST_MIN_TILE_LENGTH: int = 4 # Longueur minimale m d'une tuile GST

# ==============================================================================
# 5. PARAMÈTRES DU NIVEAU 3 — COMPARAISON STRUCTURELLE INTER-LANGAGES
# ==============================================================================
# Poids de la combinaison pondérée (total = 1.0)
# Justification (cf. docs/rapport.md) : la séquence canonique est la mesure la plus
# discriminante entre algorithmes (testée empiriquement) ; les descripteurs corroborent
# la « silhouette » structurelle ; l'édition d'arbre capte la disposition imbriquée ;
# les motifs pèsent peu car heuristiques mais sont très tranchants quand ils fusent.
WEIGHTS_LEVEL3: Dict[str, float] = {
    "canonical_sequence": 0.50,  # K-grammes + LCS sur séquence de nœuds canoniques
    "structural_vector": 0.20,   # Distance de variation totale des descripteurs
    "tree_similarity": 0.15,     # Édition d'arbre réduit, appariement par catégorie
    "pattern_heuristics": 0.15,  # Reconnaissance heuristique de motifs algorithmiques
}

# Calibrage inter-langages : facteur d'échelle multiplicatif doux pour compenser
# la baisse mécanique des scores due aux particularités de syntaxe de chaque langage.
LEVEL3_SCALE_FACTOR: float = 1.15

# ==============================================================================
# 6. LISTE BLANCHE DES IDENTIFIANTS DES BIBLIOTHÈQUES STANDARDS
# ==============================================================================
# Ces identifiants ne sont PAS renommés en "ID" lors de la normalisation de niveau 2,
# afin de conserver l'information discriminante sur les appels système et fonctions utilitaires.
STDLIB_IDENTIFIERS: Dict[str, Set[str]] = {
    "python": {
        "print", "len", "range", "str", "int", "float", "bool", "list", "dict",
        "set", "tuple", "min", "max", "sum", "abs", "open", "zip", "enumerate",
        "sorted", "map", "filter", "any", "all", "round", "pow", "isinstance",
        "type", "append", "extend", "insert", "remove", "pop", "clear", "index",
        "count", "sort", "reverse", "copy", "keys", "values", "items", "get",
        "update", "add", "discard", "split", "join", "strip", "replace", "format"
    },
    "java": {
        "System", "out", "println", "print", "printf", "Math", "String", "Integer",
        "Double", "Boolean", "List", "ArrayList", "Map", "HashMap", "Set", "HashSet",
        "Collections", "Arrays", "max", "min", "abs", "pow", "sqrt", "floor", "ceil",
        "length", "size", "add", "get", "set", "remove", "contains", "toString",
        "equals", "compareTo", "sort", "stream", "Scanner", "in", "nextInt", "nextLine"
    },
    "c": {
        "printf", "scanf", "malloc", "calloc", "realloc", "free", "sizeof",
        "strlen", "strcmp", "strcpy", "strncpy", "strcat", "memcpy", "memset",
        "memmove", "NULL", "exit", "abs", "pow", "sqrt", "floor", "ceil",
        "FILE", "fopen", "fclose", "fread", "fwrite", "fprintf", "fscanf", "fgets"
    },
    "javascript": {
        "console", "log", "warn", "error", "Math", "max", "min", "abs", "pow",
        "sqrt", "floor", "ceil", "round", "random", "length", "push", "pop",
        "shift", "unshift", "slice", "splice", "indexOf", "includes", "map",
        "filter", "reduce", "forEach", "parseInt", "parseFloat", "toString",
        "join", "split", "substring", "trim", "replace", "Object", "keys", "values"
    },
    "cpp": {
        "std", "cout", "cin", "endl", "vector", "string", "map", "set", "unordered_map",
        "unordered_set", "pair", "make_pair", "max", "min", "abs", "swap", "sort",
        "size", "push_back", "pop_back", "begin", "end", "find", "length", "printf"
    }
}

# ==============================================================================
# 7. EXTENSIONS DE FICHIERS ET MAPPING DE LANGAGES
# ==============================================================================
SUPPORTED_EXTENSIONS: Dict[str, str] = {
    ".py": "python",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
}

# ==============================================================================
# 8. PALETTE DE COULEURS POUR LE SURLIGNAGE DES FRAGMENTS (DIFF VIEW)
# ==============================================================================
# Couleurs pastel translucides bien distinctes pour les correspondances côte à côte
FRAGMENT_COLORS: List[str] = [
    "#FFD1DC",  # Rose pastel
    "#BFE6FF",  # Bleu ciel pastel
    "#C8F7C5",  # Vert menthe pastel
    "#FFE4B5",  # Moccasin orangé
    "#E6C8F7",  # Lavande pastel
    "#FFFACD",  # Jaune citron doux
    "#D5F5E3",  # Émeraude pâle
    "#FADBD8",  # Corail doux
    "#D4EFDF",  # Sauge douce
    "#FCF3CF",  # Ambre pâle
    "#E8DAEF",  # Violet très doux
    "#D6EAF8",  # Azur doux
]

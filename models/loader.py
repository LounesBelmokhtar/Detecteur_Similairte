"""
Module de chargement et de détection de langage des fichiers sources.

Ce module assure :
1. La lecture robuste des fichiers avec détection automatique de l'encodage (utf-8, latin-1, cp1252).
2. La détection du langage par extension et par heuristiques textuelles.
3. Le parcours récursif de répertoires de codes sources.
4. La gestion gracieuse des cas limites (fichiers vides, fichiers binaires, erreurs d'E/S).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from models.config import SUPPORTED_EXTENSIONS


@dataclass
class SourceFile:
    """Représentation en mémoire d'un fichier de code source."""
    path: str
    filename: str
    language: str
    raw_content: str
    lines: List[str] = field(default_factory=list)
    is_valid: bool = True
    error_message: Optional[str] = None

    @property
    def line_count(self) -> int:
        """Nombre total de lignes dans le fichier."""
        return len(self.lines)

    @property
    def is_empty(self) -> bool:
        """Vérifie si le fichier est vide ou composé uniquement d'espaces."""
        return len(self.raw_content.strip()) == 0


def detect_language(file_path: str, content: str = "") -> str:
    """
    Détecte le langage de programmation à partir de l'extension du fichier
    et de motifs syntaxiques caractéristiques (heuristiques).
    """
    ext = Path(file_path).suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[ext]

    # Heuristiques basées sur le contenu si l'extension n'est pas reconnue
    sample = content[:2000]
    if "#include" in sample:
        if "std::" in sample or "cout" in sample or "template<" in sample:
            return "cpp"
        return "c"
    if "public class " in sample or "import java." in sample or "System.out.println" in sample:
        return "java"
    if "def " in sample and (":" in sample or "import " in sample):
        return "python"
    if "console.log" in sample or "function(" in sample or "const " in sample or "let " in sample:
        return "javascript"

    return "unknown"


def load_source_file(file_path: str) -> SourceFile:
    """
    Charge un fichier source avec tentative successive des encodages courants
    et vérification de non-binarité.
    """
    abs_path = os.path.abspath(file_path)
    filename = os.path.basename(file_path)

    if not os.path.exists(abs_path):
        return SourceFile(
            path=abs_path,
            filename=filename,
            language="unknown",
            raw_content="",
            lines=[],
            is_valid=False,
            error_message="Fichier introuvable."
        )

    if os.path.isdir(abs_path):
        return SourceFile(
            path=abs_path,
            filename=filename,
            language="unknown",
            raw_content="",
            lines=[],
            is_valid=False,
            error_message="Le chemin spécifié est un répertoire, pas un fichier."
        )

    # Lecture binaire pour détecter les fichiers binaires (caractère NULL)
    try:
        with open(abs_path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return SourceFile(
                    path=abs_path,
                    filename=filename,
                    language="unknown",
                    raw_content="",
                    lines=[],
                    is_valid=False,
                    error_message="Fichier binaire non pris en charge."
                )
    except Exception as exc:
        return SourceFile(
            path=abs_path,
            filename=filename,
            language="unknown",
            raw_content="",
            lines=[],
            is_valid=False,
            error_message=f"Erreur de lecture : {exc}"
        )

    # Essais successifs d'encodage
    content: Optional[str] = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(abs_path, "r", encoding=encoding) as f:
                content = f.read()
                break
        except (UnicodeDecodeError, OSError):
            continue

    if content is None:
        return SourceFile(
            path=abs_path,
            filename=filename,
            language="unknown",
            raw_content="",
            lines=[],
            is_valid=False,
            error_message="Impossible de décoder le fichier avec les encodages supportés."
        )

    # Normalisation des sauts de ligne pour un traitement cohérent
    normalized_content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized_content.split("\n")
    lang = detect_language(abs_path, normalized_content)

    return SourceFile(
        path=abs_path,
        filename=filename,
        language=lang,
        raw_content=normalized_content,
        lines=lines,
        is_valid=True,
        error_message=None
    )


def load_directory(dir_path: str, recursive: bool = True) -> List[SourceFile]:
    """
    Parcourt un dossier et charge tous les fichiers sources dont l'extension
    correspond aux langages pris en charge.
    """
    results: List[SourceFile] = []
    abs_dir = os.path.abspath(dir_path)

    if not os.path.isdir(abs_dir):
        return results

    if recursive:
        for root, _, files in os.walk(abs_dir):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    results.append(load_source_file(file_path))
    else:
        for item in os.listdir(abs_dir):
            item_path = os.path.join(abs_dir, item)
            if os.path.isfile(item_path):
                ext = Path(item).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    results.append(load_source_file(item_path))

    return results

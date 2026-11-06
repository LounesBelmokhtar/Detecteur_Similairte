"""
Interface commune des méthodes de comparaison de similarité.
Définit le contrat `SimilarityMethod` et la structure `SimilarityResult`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Protocol, runtime_checkable

from models.fragments import Fragment
from models.loader import SourceFile


@dataclass
class SimilarityResult:
    """Résultat d'une comparaison entre un fichier de référence et un candidat."""
    candidate_path: str
    language: str
    score: float                        # 0.0 à 100.0
    sub_scores: Dict[str, float] = field(default_factory=dict)
    fragments: List[Fragment] = field(default_factory=list)
    time_ms: float = 0.0
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Garantir que le score reste borné dans [0, 100]
        self.score = max(0.0, min(100.0, float(self.score)))


@runtime_checkable
class SimilarityMethod(Protocol):
    """Protocole que toute méthode de comparaison (niveau 1, 2 ou 3) doit respecter."""

    level: int
    name: str

    def compare(self, reference: SourceFile, candidate: SourceFile) -> SimilarityResult:
        """Compare la référence au candidat et retourne un SimilarityResult."""
        ...

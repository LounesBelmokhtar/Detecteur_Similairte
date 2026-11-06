"""
Classement, seuils et niveaux d'alerte des candidats.

Regroupe la logique de tri, de classification (🟢 / 🟠 / 🔴)
et l'agrégation pondérée des sous-scores en un score global unique.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from models.config import (
    ALERT_COLORS,
    ALERT_LABELS,
    ETHICAL_WARNING,
    THRESHOLD_HIGH,
    THRESHOLD_LOW,
)


@dataclass
class CandidateRank:
    """Ligne de résultats classée : un candidat et son évaluation complète."""
    rank: int = 0
    path: str = ""
    filename: str = ""
    language: str = ""
    score: float = 0.0
    alert: str = "low"                       # low | medium | high
    sub_scores: Dict[str, float] = field(default_factory=dict)
    fragments: list = field(default_factory=list)
    time_ms: float = 0.0
    notes: List[str] = field(default_factory=list)

    @property
    def alert_label(self) -> str:
        return ALERT_LABELS.get(self.alert, self.alert)

    @property
    def alert_color(self) -> str:
        return ALERT_COLORS.get(self.alert, "#999999")

    @property
    def alert_emoji(self) -> str:
        return {"low": "🟢", "medium": "🟠", "high": "🔴"}.get(self.alert, "⚪")


def classify_alert(score: float, low_threshold: float = THRESHOLD_LOW,
                   high_threshold: float = THRESHOLD_HIGH) -> str:
    """Classe un score [0, 100] en niveau d'alerte : low / medium / high."""
    if score > high_threshold:
        return "high"
    if score >= low_threshold:
        return "medium"
    return "low"


def weighted_score(sub_scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Combine les sous-scores en un score global pondéré.
    Les sous-scores absents sont ignorés et les poids renormalisés sur ceux présents.
    Résultat borné à [0, 100].
    """
    total_weight = 0.0
    acc = 0.0
    for key, weight in weights.items():
        value = sub_scores.get(key)
        if value is None:
            continue
        acc += max(0.0, min(100.0, value)) * weight
        total_weight += weight

    if total_weight <= 0:
        return 0.0

    return round(min(100.0, acc / total_weight), 2)


def rank_candidates(results: List["object"]) -> List["object"]:
    """
    Trie les résultats par score décroissant et attribue un rang (1 = plus similaire).
    Accepte tout objet possédant un attribut `.score`.
    Le niveau d'alerte est recalculé à partir du score.
    """
    sorted_results = sorted(results, key=lambda r: r.score, reverse=True)
    for idx, result in enumerate(sorted_results, start=1):
        result.rank = idx
        result.alert = classify_alert(result.score)
    return sorted_results


def build_summary(results: List[CandidateRank]) -> Dict[str, object]:
    """Résumé global des comparaisons (moyenne, max, compteurs d'alerte)."""
    if not results:
        return {
            "count": 0,
            "mean": 0.0,
            "max": 0.0,
            "min": 0.0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "ethical_warning": ETHICAL_WARNING,
        }

    scores = [r.score for r in results]
    return {
        "count": len(results),
        "mean": round(sum(scores) / len(scores), 2),
        "max": round(max(scores), 2),
        "min": round(min(scores), 2),
        "high": sum(1 for r in results if r.alert == "high"),
        "medium": sum(1 for r in results if r.alert == "medium"),
        "low": sum(1 for r in results if r.alert == "low"),
        "ethical_warning": ETHICAL_WARNING,
    }

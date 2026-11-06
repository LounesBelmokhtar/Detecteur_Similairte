"""
Représentation et manipulation des fragments de code similaires.

Un fragment correspond à une plage de lignes dans le fichier de référence
mise en correspondance avec une plage de lignes dans le fichier candidat.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Fragment:
    """
    Représente un fragment de code source similaire identifié entre deux fichiers.

    Les numéros de ligne (ref_start, ref_end, cand_start, cand_end) sont indexés à 1
    pour correspondre aux numéros affichés dans l'éditeur et l'interface graphique.
    """
    ref_start: int     # Ligne de début dans le fichier de référence (incluse)
    ref_end: int       # Ligne de fin dans le fichier de référence (incluse)
    cand_start: int    # Ligne de début dans le fichier candidat (incluse)
    cand_end: int      # Ligne de fin dans le fichier candidat (incluse)
    score: float = 1.0 # Similarité locale du fragment (0.0 à 1.0 ou 0 à 100)
    label: str = ""    # Étiquette optionnelle (ex: "GST", "Fonction 'bubble_sort'", "Bloc")

    @property
    def ref_length(self) -> int:
        """Nombre de lignes couvertes dans la référence."""
        return max(0, self.ref_end - self.ref_start + 1)

    @property
    def cand_length(self) -> int:
        """Nombre de lignes couvertes dans le candidat."""
        return max(0, self.cand_end - self.cand_start + 1)

    def overlaps_ref(self, other: Fragment) -> bool:
        """Vérifie si les plages de référence se chevauchent."""
        return not (self.ref_end < other.ref_start or other.ref_end < self.ref_start)

    def overlaps_cand(self, other: Fragment) -> bool:
        """Vérifie si les plages du candidat se chevauchent."""
        return not (self.cand_end < other.cand_start or other.cand_end < self.cand_start)


def merge_adjacent_fragments(fragments: List[Fragment], max_gap: int = 1) -> List[Fragment]:
    """
    Fusionne les fragments adjacents ou très proches pour éviter la fragmentation excessive
    dans l'affichage et simplifier la lecture visuelle.
    """
    if not fragments:
        return []

    # Tri par position de référence puis candidat
    sorted_frags = sorted(fragments, key=lambda f: (f.ref_start, f.cand_start))
    merged: List[Fragment] = [sorted_frags[0]]

    for current in sorted_frags[1:]:
        last = merged[-1]
        # Condition de continuité : écart faible et progression coordonnée
        ref_gap = current.ref_start - last.ref_end - 1
        cand_gap = current.cand_start - last.cand_end - 1

        if 0 <= ref_gap <= max_gap and 0 <= cand_gap <= max_gap:
            # Fusion
            new_ref_end = max(last.ref_end, current.ref_end)
            new_cand_end = max(last.cand_end, current.cand_end)
            merged[-1] = Fragment(
                ref_start=last.ref_start,
                ref_end=new_ref_end,
                cand_start=last.cand_start,
                cand_end=new_cand_end,
                score=max(last.score, current.score),
                label=last.label or current.label
            )
        else:
            merged.append(current)

    return merged

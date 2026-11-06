"""
Vue côte à côte (diff) avec surlignage des fragments similaires.

Référence à gauche, candidat à droite, numéros de ligne,
couleur par fragment, défilement synchronisé entre les deux panneaux.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, List

from models.config import ALERT_COLORS, ETHICAL_WARNING, FRAGMENT_COLORS
from models.ranking import CandidateRank
from views import theme


class DiffView(tk.Toplevel):
    """
    Fenêtre secondaire affichant la référence et un candidat côte à côte
    avec les fragments correspondants surlignés en couleurs assorties.
    """

    def __init__(self, parent: tk.Widget,
                 reference_lines: List[str],
                 reference_filename: str,
                 reference_language: str,
                 candidate_lines: List[str],
                 result: CandidateRank) -> None:
        super().__init__(parent)
        self.title(f"Comparaison — {reference_filename} ↔ {result.filename}")
        self.geometry("1280x760")
        self.minsize(900, 500)
        theme.apply_theme(self)

        self.reference_lines = reference_lines
        self.candidate_lines = candidate_lines
        self.result = result
        self._syncing = False

        # --- En-tête -------------------------------------------------------------
        header = ttk.Frame(self, style="Header.TFrame", padding=(16, 12))
        header.pack(fill="x")

        ttk.Label(
            header,
            text=(
                f"Référence : {reference_filename} ({reference_language})    ↔    "
                f"Candidat : {result.filename} ({result.language})"
            ),
            style="Title.TLabel", font=(theme.FONT, 12, "bold"),
        ).pack(side="left")

        ttk.Label(
            header,
            text=f"{result.score:.1f} %   {result.alert_emoji} {result.alert_label}",
            background=ALERT_COLORS.get(result.alert, "#999"), foreground="#ffffff",
            font=(theme.FONT, 11, "bold"), padding=(10, 4),
        ).pack(side="right")

        ttk.Label(
            self,
            text="⚠ " + ETHICAL_WARNING,
            style="Banner.TLabel",
            font=(theme.FONT, 8, "italic"),
            wraplength=1180, justify="left", padding=(12, 6),
        ).pack(fill="x", padx=8, pady=(0, 6))

        # --- Sous-scores ------------------------------------------------------------
        subs = ttk.LabelFrame(self, text="Sous-scores", style="Card.TLabelframe", padding=(10, 6))
        subs.pack(fill="x", padx=8, pady=(0, 6))
        sub_text = "   |   ".join(f"{k} : {v:.1f}%" for k, v in result.sub_scores.items())
        ttk.Label(subs, text=sub_text or "Aucun sous-score disponible.",
                  style="Surface.TLabel", font=(theme.MONO, 9)).pack(anchor="w")

        # --- Panneaux côte à côte ----------------------------------------------------
        panes = ttk.Frame(self, padding=4)
        panes.pack(fill="both", expand=True)

        # Référence (gauche)
        left_frame = ttk.LabelFrame(panes, text=f"Référence — {reference_filename}",
                                    style="Card.TLabelframe", padding=4)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.left_text = tk.Text(
            left_frame, wrap="none", font=(theme.MONO, 10),
            state="normal", spacing1=1, spacing3=1,
            background=theme.SURFACE, foreground=theme.TEXT, relief="flat", padx=4,
        )
        left_vsb = ttk.Scrollbar(left_frame, orient="vertical", command=self.left_text.yview)
        left_hsb = ttk.Scrollbar(left_frame, orient="horizontal", command=self.left_text.xview)
        self.left_text.configure(yscrollcommand=self._on_left_scroll, xscrollcommand=left_hsb.set)
        left_vsb.configure(command=self.left_text.yview)

        self.left_text.grid(row=0, column=0, sticky="nsew")
        left_vsb.grid(row=0, column=1, sticky="ns")
        left_hsb.grid(row=1, column=0, sticky="ew")
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)

        # Candidat (droite)
        right_frame = ttk.LabelFrame(panes, text=f"Candidat — {result.filename}",
                                     style="Card.TLabelframe", padding=4)
        right_frame.pack(side="right", fill="both", expand=True, padx=(4, 0))

        self.right_text = tk.Text(
            right_frame, wrap="none", font=(theme.MONO, 10),
            state="normal", spacing1=1, spacing3=1,
            background=theme.SURFACE, foreground=theme.TEXT, relief="flat", padx=4,
        )
        right_vsb = ttk.Scrollbar(right_frame, orient="vertical", command=self.right_text.yview)
        right_hsb = ttk.Scrollbar(right_frame, orient="horizontal", command=self.right_text.xview)
        self.right_text.configure(yscrollcommand=self._on_right_scroll, xscrollcommand=right_hsb.set)
        right_vsb.configure(command=self.right_text.yview)

        self.right_text.grid(row=0, column=0, sticky="nsew")
        right_vsb.grid(row=0, column=1, sticky="ns")
        right_hsb.grid(row=1, column=0, sticky="ew")
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

        # --- Remplissage avec surlignage -----------------------------------------------
        self._populate_panels()

        # --- Légende des fragments -------------------------------------------------------
        legend = ttk.LabelFrame(self, text="Légende des fragments",
                                style="Card.TLabelframe", padding=6)
        legend.pack(fill="x", padx=8, pady=(0, 8))

        if result.fragments:
            for idx, frag in enumerate(result.fragments):
                color = FRAGMENT_COLORS[idx % len(FRAGMENT_COLORS)]
                lbl = ttk.Label(
                    legend,
                    text=f"  Réf. L{frag.ref_start}–{frag.ref_end} ↔ "
                         f"Cand. L{frag.cand_start}–{frag.cand_end}"
                         + (f" — {frag.label}" if frag.label else ""),
                    background=color,
                    foreground=theme.TEXT,
                    padding=(6, 3),
                    font=(theme.FONT, 8),
                )
                lbl.pack(side="left", padx=(0, 6), pady=2)
        else:
            ttk.Label(legend, text="Aucun fragment similaire suffisamment long détecté.",
                      style="Muted.TLabel").pack(anchor="w")

    # =========================================================================
    # Remplissage et surlignage
    # =========================================================================
    def _populate_panels(self) -> None:
        """Insère les lignes dans les deux Text et applique le surlignage."""
        # Carte ligne → index de fragment (gauche et droite)
        left_colors: Dict[int, str] = {}
        right_colors: Dict[int, str] = {}

        for idx, frag in enumerate(self.result.fragments):
            color = FRAGMENT_COLORS[idx % len(FRAGMENT_COLORS)]
            for ln in range(frag.ref_start, frag.ref_end + 1):
                left_colors[ln] = color
            for ln in range(frag.cand_start, frag.cand_end + 1):
                right_colors[ln] = color

        # Référence
        self.left_text.delete("1.0", "end")
        for line_no, line_text in enumerate(self.reference_lines, start=1):
            tag = f"frag{line_no}"
            display = f"{line_no:>5} │ {line_text}\n"
            self.left_text.insert("end", display)
            if line_no in left_colors:
                self.left_text.tag_add(tag, f"{line_no}.0", f"{line_no}.0+{len(display)}c")
                self.left_text.tag_config(tag, background=left_colors[line_no])

        # Candidat
        self.right_text.delete("1.0", "end")
        for line_no, line_text in enumerate(self.candidate_lines, start=1):
            tag = f"frag{line_no}"
            display = f"{line_no:>5} │ {line_text}\n"
            self.right_text.insert("end", display)
            if line_no in right_colors:
                self.right_text.tag_add(tag, f"{line_no}.0", f"{line_no}.0+{len(display)}c")
                self.right_text.tag_config(tag, background=right_colors[line_no])

        # Colorer aussi les numéros de ligne (distinguer les zones)
        self.left_text.tag_config("lineno", foreground="#888")
        self.right_text.tag_config("lineno", foreground="#888")

        # Désactiver l'édition
        self.left_text.config(state="disabled")
        self.right_text.config(state="disabled")

    # =========================================================================
    # Défilement synchronisé
    # =========================================================================
    def _on_left_scroll(self, *args) -> None:
        """Réplique le défilement vertical gauche → droite (sans récursion)."""
        self.right_text.yview_moveto(args[0])
        # Propager aussi l'événement natif
        # (les scrollbars sont reconfigurées dans le constructeur)

    def _on_right_scroll(self, *args) -> None:
        """Réplique le défilement vertical droite → gauche (sans récursion)."""
        self.left_text.yview_moveto(args[0])

"""
Thème visuel moderne de l'interface graphique.

Centralise la palette de couleurs, les polices et les styles ttk afin
d'obtenir une apparence cohérente (barre latérale sombre, cartes claires,
accent indigo). Le thème ttk « clam » est imposé car il autorise la
personnalisation complète des couleurs, contrairement au thème natif Windows.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

# ==============================================================================
# PALETTE
# ==============================================================================
BG: str = "#f4f6fb"            # Fond général (gris-bleu très clair)
SURFACE: str = "#ffffff"       # Surfaces / cartes
BORDER: str = "#e2e5ee"        # Bordures discrètes

SIDEBAR_BG: str = "#1f2937"    # Barre latérale (ardoise foncée)
SIDEBAR_ALT: str = "#2b3648"   # Éléments posés sur la barre latérale
SIDEBAR_TEXT: str = "#e5e7eb"
SIDEBAR_MUTED: str = "#9aa4b2"

TEXT: str = "#1f2937"
TEXT_MUTED: str = "#6b7280"

ACCENT: str = "#4f46e5"        # Indigo
ACCENT_DARK: str = "#4338ca"
ACCENT_SOFT: str = "#eef2ff"
ACCENT_TEXT: str = "#c7d2fe"

SUCCESS: str = "#16a34a"
SUCCESS_SOFT: str = "#e7f6ec"
WARNING: str = "#ea580c"
DANGER: str = "#dc2626"
DANGER_SOFT: str = "#fdeaea"

FONT: str = "Segoe UI"
MONO: str = "Cascadia Code"


# ==============================================================================
# APPLICATION DU THÈME
# ==============================================================================
def apply_theme(root: tk.Misc) -> ttk.Style:
    """Applique la palette et configure tous les styles ttk utilisés par l'IHM."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    if isinstance(root, (tk.Tk, tk.Toplevel)):
        root.configure(background=BG)

    # --- Base ----------------------------------------------------------------
    style.configure(".", font=(FONT, 10), background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("Surface.TFrame", background=SURFACE)
    style.configure("Card.TFrame", background=SURFACE)
    style.configure("Banner.TFrame", background="#fff8e6")
    style.configure("Header.TFrame", background=SURFACE)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Surface.TLabel", background=SURFACE, foreground=TEXT)
    style.configure("Muted.TLabel", background=SURFACE, foreground=TEXT_MUTED)
    style.configure("Title.TLabel", background=SURFACE, foreground=TEXT,
                    font=(FONT, 16, "bold"))
    style.configure("Subtitle.TLabel", background=SURFACE, foreground=TEXT_MUTED,
                    font=(FONT, 9))
    style.configure("Section.TLabel", background=BG, foreground=TEXT,
                    font=(FONT, 11, "bold"))
    style.configure("Banner.TLabel", background="#fff8e6", foreground="#8a6d00",
                    font=(FONT, 9))
    style.configure("Caption.TLabel", background=SURFACE, foreground=TEXT_MUTED,
                    font=(FONT, 8))
    style.configure("Value.TLabel", background=SURFACE, foreground=TEXT,
                    font=(FONT, 19, "bold"))

    # --- Cartes (LabelFrame) -------------------------------------------------
    style.configure("Card.TLabelframe", background=SURFACE, bordercolor=BORDER,
                    relief="solid", borderwidth=1)
    style.configure("Card.TLabelframe.Label", background=SURFACE, foreground=ACCENT,
                    font=(FONT, 10, "bold"))
    style.configure("Stats.TLabelframe", background=SURFACE, bordercolor=BORDER,
                    relief="solid", borderwidth=1)
    style.configure("Stats.TLabelframe.Label", background=SURFACE,
                    foreground=ACCENT_TEXT, font=(FONT, 1))

    # --- Boutons -------------------------------------------------------------
    style.configure("Primary.TButton", background=ACCENT, foreground="#ffffff",
                    borderwidth=0, focusthickness=0, padding=(14, 10),
                    font=(FONT, 11, "bold"))
    style.map("Primary.TButton",
              background=[("active", ACCENT_DARK), ("disabled", "#c7cad9")],
              foreground=[("disabled", "#f2f3f7")])

    style.configure("Secondary.TButton", background=SURFACE, foreground=TEXT,
                    borderwidth=1, bordercolor=BORDER, focusthickness=0,
                    padding=(10, 6), font=(FONT, 9))
    style.map("Secondary.TButton",
              background=[("active", ACCENT_SOFT), ("disabled", SURFACE)],
              foreground=[("disabled", "#b8bcc8")])

    # --- Tableau -------------------------------------------------------------
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE,
                    foreground=TEXT, rowheight=30, borderwidth=0, font=(FONT, 10))
    style.configure("Treeview.Heading", background=ACCENT_SOFT, foreground=ACCENT,
                    font=(FONT, 10, "bold"), relief="flat", padding=(6, 7))
    style.map("Treeview.Heading", background=[("active", "#e0e7ff")])
    style.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#ffffff")])

    # --- Progression ---------------------------------------------------------
    style.configure("TProgressbar", background=ACCENT, troughcolor=BORDER,
                    borderwidth=0, thickness=10)
    style.configure("Sidebar.Horizontal.TProgressbar", background=ACCENT,
                    troughcolor=SIDEBAR_ALT, borderwidth=0, thickness=8)

    # --- Barres de défilement ------------------------------------------------
    style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG,
                    bordercolor=BG, arrowcolor=ACCENT, borderwidth=0)
    style.configure("Horizontal.TScrollbar", background=BORDER, troughcolor=BG,
                    bordercolor=BG, arrowcolor=ACCENT, borderwidth=0)

    # --- Contrôles -----------------------------------------------------------
    style.configure("TEntry", fieldbackground=SURFACE, bordercolor=BORDER, padding=4)
    style.configure("Horizontal.TSeparator", background=BORDER)
    style.configure("Card.Horizontal.TSeparator", background=BORDER)

    return style


# ==============================================================================
# BOUTON AVEC EFFET DE SURVOL (widgets tk, fond sombre entièrement colorable)
# ==============================================================================
class HoverButton(tk.Button):
    """Bouton plat avec changement de couleur au survol.

    Les widgets ``tk.Button`` sont préférés à ``ttk`` sur la barre latérale
    sombre car leur fond est personnalisable sans dépendre du moteur de thème.
    """

    def __init__(self, master: tk.Misc, normal_bg: str, hover_bg: str,
                 normal_fg: str = "#ffffff", hover_fg: Optional[str] = None,
                 cursor: str = "hand2", **kwargs) -> None:
        self._normal_bg = normal_bg
        self._hover_bg = hover_bg
        self._normal_fg = normal_fg
        self._hover_fg = hover_fg if hover_fg is not None else normal_fg
        super().__init__(
            master,
            background=normal_bg,
            foreground=normal_fg,
            activebackground=hover_bg,
            activeforeground=self._hover_fg,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor=cursor,
            **kwargs,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event: object) -> None:
        if str(self["state"]) != "disabled":
            self.configure(background=self._hover_bg, foreground=self._hover_fg)

    def _on_leave(self, _event: object) -> None:
        if str(self["state"]) != "disabled":
            self.configure(background=self._normal_bg, foreground=self._normal_fg)


def configure_disabled(button: tk.Button, enabled: bool,
                       normal_bg: str, disabled_bg: str,
                       normal_fg: str = "#ffffff",
                       disabled_fg: str = "#8b93a3") -> None:
    """Bascule un :class:`HoverButton` entre l'état actif et désactivé."""
    if enabled:
        button.configure(state="normal", background=normal_bg, foreground=normal_fg,
                         cursor="hand2")
    else:
        button.configure(state="disabled", background=disabled_bg,
                         foreground=disabled_fg, cursor="")

"""
Fenêtre principale (V du modèle MVC).

Cette vue ne contient que la construction et la mise à jour des widgets.
Toute la logique métier (chargement, comparaison, exports) est déléguée au
contrôleur, branché via :meth:`MainWindow.attach`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Tuple

from models.config import ETHICAL_WARNING, THRESHOLD_HIGH, THRESHOLD_LOW
from models.ranking import CandidateRank
from views import theme
from views.control_panel import ControlPanel
from views.diff_view import DiffView
from views.results_view import ResultsView


class MainWindow(tk.Tk):
    """Fenêtre principale : en-tête, barre latérale, résultats et barre d'état."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Détecteur de similarité entre codes sources")
        self.geometry("1440x900")
        self.minsize(1024, 640)
        # Maximiser la fenêtre au démarrage pour que tout soit visible
        try:
            self.state("zoomed")
        except tk.TclError:
            pass

        theme.apply_theme(self)

        # Le contrôleur est branché après construction (inversion de dépendance).
        self.controller: Optional[object] = None

        # --- En-tête -------------------------------------------------------------
        header = ttk.Frame(self, style="Header.TFrame", padding=(22, 16))
        header.pack(side="top", fill="x")

        title_box = ttk.Frame(header, style="Header.TFrame")
        title_box.pack(side="left", anchor="w")
        ttk.Label(title_box, text="Détecteur de similarité entre codes sources",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_box,
                  text="Comparaison textuelle, lexicale et structurelle  ·  Python · Java · C · C++ · JavaScript",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))

        badges = ttk.Frame(header, style="Header.TFrame")
        badges.pack(side="right")
        self._header_badge(badges, theme.SUCCESS, f"≤ {THRESHOLD_LOW:.0f}% faible")
        self._header_badge(badges, theme.WARNING, f"{THRESHOLD_LOW:.0f}–{THRESHOLD_HIGH:.0f}% modéré")
        self._header_badge(badges, theme.DANGER, f"≥ {THRESHOLD_HIGH:.0f}% élevé")

        ttk.Separator(self, orient="horizontal").pack(side="top", fill="x")

        # --- Corps : barre latérale + zone principale ----------------------------
        body = ttk.Frame(self)
        body.pack(side="top", fill="both", expand=True)

        self.control_panel = ControlPanel(body, on_compare=self._request_compare)
        self.control_panel.pack(side="left", fill="y")

        main_frame = ttk.Frame(body, padding=(16, 14, 16, 10))
        main_frame.pack(side="right", fill="both", expand=True)

        self.results_view = ResultsView(main_frame, on_open_diff=self._request_diff)
        self.results_view.pack(fill="both", expand=True)

        # --- Barre d'état ------------------------------------------------------------
        ttk.Separator(self, orient="horizontal").pack(side="bottom", fill="x")
        self.status_bar = tk.Label(
            self, text=f"Prêt.   ⚠  {ETHICAL_WARNING}",
            anchor="w", justify="left", padx=14, pady=5,
            font=(theme.FONT, 8), background=theme.SURFACE,
            foreground=theme.TEXT_MUTED,
        )
        self.status_bar.pack(side="bottom", fill="x")

    # =========================================================================
    # Branchement du contrôleur
    # =========================================================================
    def attach(self, controller: object) -> None:
        """Branche le contrôleur et câble les commandes d'export."""
        self.controller = controller
        self.control_panel.export_csv_btn.config(command=self._request_export_csv)
        self.control_panel.export_html_btn.config(command=self._request_export_html)

    def _request_compare(self) -> None:
        if self.controller is not None:
            self.controller.start_comparison()  # type: ignore[attr-defined]

    def _request_export_csv(self) -> None:
        if self.controller is not None:
            self.controller.export_csv()  # type: ignore[attr-defined]

    def _request_export_html(self) -> None:
        if self.controller is not None:
            self.controller.export_html()  # type: ignore[attr-defined]

    def _request_diff(self, result: CandidateRank) -> None:
        if self.controller is not None:
            self.controller.open_diff(result)  # type: ignore[attr-defined]

    def _header_badge(self, parent: tk.Misc, color: str, text: str) -> None:
        """Ajoute une pastille colorée d'aide à la lecture des seuils."""
        tk.Label(parent, text=text, background=color, foreground="#ffffff",
                 font=(theme.FONT, 8, "bold"), padx=8, pady=3).pack(side="left", padx=(6, 0))

    # =========================================================================
    # API de rendu appelée par le contrôleur
    # =========================================================================
    def get_config(self) -> Dict[str, object]:
        """Retourne la configuration saisie dans le panneau de contrôle."""
        return self.control_panel.get_config()

    def set_progress(self, value: float, status: str = "") -> None:
        self.control_panel.set_progress(value, status)

    def set_export_enabled(self, enabled: bool) -> None:
        self.control_panel.set_export_enabled(enabled)

    def set_status(self, text: str) -> None:
        self.status_bar.config(text=text)

    def display_results(self, results: List[CandidateRank], method_name: str) -> None:
        """Affiche le classement final et met à jour les indicateurs."""
        self.results_view.set_results(results)
        self.control_panel.set_progress(
            100, f"Terminé — {method_name} — {len(results)} candidat(s).")
        self.control_panel.set_export_enabled(True)
        self.set_status(f"Comparaison terminée ({method_name}).   ⚠  {ETHICAL_WARNING}")

    # =========================================================================
    # Boîtes de dialogue
    # =========================================================================
    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        messagebox.showwarning(title, message)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def ask_save_path(self, title: str, defaultextension: str,
                      filetypes: List[Tuple[str, str]]) -> str:
        """Ouvre une boîte « Enregistrer sous » et retourne le chemin choisi."""
        return filedialog.asksaveasfilename(
            title=title, defaultextension=defaultextension,
            filetypes=filetypes,
        )

    # =========================================================================
    # Fenêtre côte à côte
    # =========================================================================
    def show_diff(self, reference_lines: List[str], reference_filename: str,
                  reference_language: str, candidate_lines: List[str],
                  result: CandidateRank) -> None:
        DiffView(
            self,
            reference_lines=reference_lines,
            reference_filename=reference_filename,
            reference_language=reference_language,
            candidate_lines=candidate_lines,
            result=result,
        )

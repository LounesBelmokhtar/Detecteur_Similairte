"""
Vue des résultats : bandeau éthique, cartes de synthèse, tableau classé
(ttk.Treeview) et graphique à barres horizontales coloré selon l'alerte.

Le graphique utilise matplotlib (FigureCanvasTkAgg) avec repli sur un
histogramme dessiné en Canvas pur si matplotlib est indisponible.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Tuple

from models.config import ALERT_COLORS, ETHICAL_WARNING
from models.ranking import CandidateRank
from views import theme

# Tentative d'import matplotlib pour l'intégration Tkinter
MATPLOTLIB_AVAILABLE = False
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    pass


class ResultsView(ttk.Frame):
    """
    Tableau de classement + graphique de barres interactif.
    Un double-clic sur une ligne ouvre la vue côte à côte (diff).
    """

    def __init__(self, parent: tk.Widget,
                 on_open_diff: Callable[[CandidateRank], None]) -> None:
        super().__init__(parent)
        self.on_open_diff = on_open_diff
        self.results: List[CandidateRank] = []

        # --- Bandeau éthique permanent -----------------------------------------
        banner = ttk.Frame(self, style="Banner.TFrame", padding=10)
        banner.pack(fill="x", pady=(0, 10))
        ttk.Label(banner, text="⚠  " + ETHICAL_WARNING, style="Banner.TLabel",
                  wraplength=880, justify="left").pack(anchor="w")

        # --- Cartes de synthèse -------------------------------------------------
        self.summary_frame = ttk.LabelFrame(self, text="Synthèse", style="Stats.TLabelframe",
                                            padding=(4, 10, 4, 10))
        self.summary_frame.pack(fill="x", pady=(0, 10))
        self._stat_values: List[tk.Label] = []
        stats = [
            ("Candidats analysés", theme.TEXT, theme.ACCENT),
            ("Alertes élevées", theme.DANGER, theme.DANGER_SOFT),
            ("Score moyen", theme.ACCENT, theme.ACCENT_SOFT),
            ("Meilleur score", theme.SUCCESS, theme.SUCCESS_SOFT),
        ]
        for i, (caption, color, accent_bg) in enumerate(stats):
            if i:
                ttk.Separator(self.summary_frame, orient="vertical").pack(
                    side="left", fill="y", padx=2, pady=6)
            self._stat_values.append(
                self._stat_card(self.summary_frame, caption, color, accent_bg))
        self._update_summary([])

        # --- Tableau ------------------------------------------------------------
        table_card = ttk.LabelFrame(self, text="Classement des candidats",
                                    style="Card.TLabelframe", padding=(10, 6))
        table_card.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("rank", "file", "language", "score", "alert", "fragments", "time_ms")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=7)

        headings = {
            "rank": ("Rang", 55),
            "file": ("Fichier", 240),
            "language": ("Langage", 90),
            "score": ("Score (%)", 100),
            "alert": ("Alerte", 120),
            "fragments": ("Fragments", 85),
            "time_ms": ("Temps (ms)", 90),
        }
        for col, (title, width) in headings.items():
            self.tree.heading(col, text=title,
                              command=lambda c=col: self._sort_by(c, False))
            self.tree.column(col, width=width, anchor="center" if col != "file" else "w")

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        # Coloration des lignes selon l'alerte
        for alert, color in ALERT_COLORS.items():
            self.tree.tag_configure(alert, background=color, foreground="#ffffff")

        # Double-clic → vue côte à côte
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # --- Sous-scores / détails ------------------------------------------------
        detail_card = ttk.LabelFrame(self, text="Détail du candidat sélectionné",
                                     style="Card.TLabelframe", padding=(10, 6))
        detail_card.pack(fill="x", pady=(0, 10))
        self.detail_text = tk.Text(
            detail_card, height=4, font=(theme.MONO, 9), state="disabled",
            background=theme.SURFACE, foreground=theme.TEXT, relief="flat",
            wrap="word", padx=6, pady=4,
        )
        self.detail_text.pack(fill="x")

        # --- Graphique --------------------------------------------------------------
        chart_card = ttk.LabelFrame(self, text="Répartition des scores",
                                    style="Card.TLabelframe", padding=6)
        chart_card.pack(fill="x")

        if MATPLOTLIB_AVAILABLE:
            self.fig = Figure(figsize=(7, 3.0), dpi=90, facecolor=theme.SURFACE)
            self.canvas = FigureCanvasTkAgg(self.fig, master=chart_card)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            self.chart_canvas = tk.Canvas(chart_card, height=210, bg=theme.SURFACE,
                                          highlightthickness=0)
            self.chart_canvas.pack(fill="both", expand=True)
            self.fig = None
            self.canvas = None

    # =========================================================================
    # Construction des cartes de synthèse
    # =========================================================================
    def _stat_card(self, parent: tk.Misc, caption: str, color: str,
                   accent_bg: str) -> tk.Label:
        """Crée une carte de statistique et renvoie l'étiquette de la valeur."""
        card = tk.Frame(parent, background=theme.SURFACE)
        card.pack(side="left", fill="x", expand=True, padx=8)
        chip = tk.Frame(card, background=accent_bg, highlightthickness=0,
                        highlightbackground=accent_bg)
        chip.pack(fill="x")
        value = tk.Label(chip, text="—", background=accent_bg, foreground=color,
                         font=(theme.FONT, 19, "bold"), anchor="w", padx=10, pady=6)
        value.pack(fill="x")
        tk.Label(card, text=caption, background=theme.SURFACE,
                 foreground=theme.TEXT_MUTED, font=(theme.FONT, 9),
                 anchor="w").pack(fill="x", pady=(6, 0))
        return value

    def _update_summary(self, results: List[CandidateRank]) -> None:
        """Actualise les cartes de synthèse à partir des résultats."""
        if not results:
            for lbl in self._stat_values:
                lbl.config(text="—")
            return
        scores = [r.score for r in results]
        high = sum(1 for r in results if r.alert == "high")
        self._stat_values[0].config(text=str(len(results)))
        self._stat_values[1].config(text=str(high))
        self._stat_values[2].config(text=f"{sum(scores) / len(scores):.1f}%")
        self._stat_values[3].config(text=f"{max(scores):.1f}%")

    # =========================================================================
    # Mise à jour des données
    # =========================================================================
    def set_results(self, results: List[CandidateRank]) -> None:
        """Remplit le tableau et redessine le graphique avec les nouveaux résultats."""
        self.results = results

        # Nettoyage
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insertion
        for r in results:
            self.tree.insert(
                "", "end",
                values=(
                    r.rank,
                    r.filename,
                    r.language,
                    f"{r.score:.1f}",
                    f"{r.alert_emoji} {r.alert_label}",
                    len(r.fragments),
                    f"{r.time_ms:.1f}",
                ),
                tags=(r.alert,),
            )

        self._update_summary(results)
        self._redraw_chart()

        # Détail par défaut : premier résultat
        if results:
            self._show_detail(results[0])

    def _sort_by(self, col: str, reverse: bool) -> None:
        """Tri le tableau par colonne (clic sur l'en-tête)."""
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0], reverse=reverse)
        for index, (_, k) in enumerate(data):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda: self._sort_by(col, not reverse))

    def _result_for_item(self, item: str) -> Tuple[CandidateRank, ...]:
        """Retrouve l'objet résultat associé à une ligne du tableau."""
        values = self.tree.item(item, "values")
        if not values:
            return ()
        rank = int(values[0])
        return tuple(r for r in self.results if r.rank == rank)

    def _on_select(self, _event) -> None:
        """Met à jour le détail quand la sélection change (clic simple)."""
        selection = self.tree.selection()
        if not selection:
            return
        matches = self._result_for_item(selection[0])
        if matches:
            self._show_detail(matches[0])

    def _on_double_click(self, _event) -> None:
        """Ouvre la vue côte à côte pour la ligne sélectionnée."""
        selection = self.tree.selection()
        if not selection:
            return
        matches = self._result_for_item(selection[0])
        if matches:
            self._show_detail(matches[0])
            self.on_open_diff(matches[0])

    def _show_detail(self, result: CandidateRank) -> None:
        """Affiche le détail des sous-scores et des notes."""
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")

        lines = [f"Fichier : {result.filename}   ·   Langage : {result.language}   ·   "
                 f"Score : {result.score:.1f} %   ({result.alert_emoji} {result.alert_label})"]
        for key, val in result.sub_scores.items():
            lines.append(f"   • {key:<24} : {val:6.2f} %")
        notes = [n for n in result.notes if n]
        if notes:
            lines.append("Notes : " + " / ".join(notes))
        lines.append(f"Fragments : {len(result.fragments)}   ·   Temps : {result.time_ms:.1f} ms")

        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.config(state="disabled")

    # =========================================================================
    # Graphique de barres
    # =========================================================================
    def _redraw_chart(self) -> None:
        """Dessine le graphique à barres horizontales des scores."""
        if not self.results:
            if self.fig is not None:
                self.fig.clear()
                self.canvas.draw()
            return

        if MATPLOTLIB_AVAILABLE and self.fig is not None:
            self.fig.clear()
            ax = self.fig.add_subplot(111)

            names = [r.filename for r in self.results]
            scores = [r.score for r in self.results]
            colors = [ALERT_COLORS.get(r.alert, "#999") for r in self.results]

            y_pos = range(len(names))
            ax.barh(list(y_pos), scores, color=colors, edgecolor="none", height=0.65)
            ax.set_yticks(list(y_pos))
            ax.set_yticklabels(names, fontsize=8)
            ax.invert_yaxis()  # Plus haut score en haut
            ax.set_xlim(0, 100)
            ax.set_xlabel("Score de similarité (%)", fontsize=9)
            ax.axvline(30, color=theme.SUCCESS, linestyle="--", linewidth=0.9, alpha=0.8)
            ax.axvline(70, color=theme.DANGER, linestyle="--", linewidth=0.9, alpha=0.8)
            ax.grid(axis="x", linestyle=":", alpha=0.4)
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)
            ax.spines["left"].set_color(theme.BORDER)
            ax.spines["bottom"].set_color(theme.BORDER)

            for i, (score, color) in enumerate(zip(scores, colors)):
                ax.text(score + 1, i, f"{score:.1f}%", va="center", fontsize=8,
                        color=theme.TEXT, fontweight="bold")

            self.fig.subplots_adjust(left=0.28, right=0.97, top=0.92, bottom=0.22)
            self.canvas.draw()
        else:
            self._redraw_chart_canvas()

    def _redraw_chart_canvas(self) -> None:
        """Repli : dessine les barres directement dans un widget Canvas."""
        canvas = getattr(self, "chart_canvas", None)
        if canvas is None:
            return

        canvas.delete("all")
        width = canvas.winfo_width() or 600
        height = canvas.winfo_height() or 210
        n = len(self.results)
        if n == 0:
            return

        margin_left = 160
        margin_right = 50
        bar_area = width - margin_left - margin_right
        bar_height = max(8, min(24, (height - 30) // n - 4))

        for i, r in enumerate(self.results):
            y = 15 + i * (bar_height + 6)
            bar_len = (r.score / 100.0) * bar_area
            color = ALERT_COLORS.get(r.alert, "#999")
            canvas.create_text(margin_left - 8, y + bar_height / 2, anchor="e",
                               text=r.filename[:28], font=(theme.FONT, 8))
            canvas.create_rectangle(margin_left, y, margin_left + bar_len, y + bar_height,
                                    fill=color, outline="")
            canvas.create_text(margin_left + bar_len + 6, y + bar_height / 2,
                               anchor="w", text=f"{r.score:.1f}%", font=(theme.FONT, 8, "bold"))

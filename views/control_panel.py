"""
Panneau de contrôle de l'application.

Barre latérale sombre regroupant la sélection de la référence, des candidats,
du niveau et des paramètres, ainsi que le lancement de la comparaison et les
exports. Le fond sombre contraste avec la zone de résultats claire.

Mise en page : la zone de configuration est défilable, tandis que le bouton
« Comparer », la barre de progression et les exports restent toujours visibles
en bas du panneau (pas de défilement nécessaire pour lancer la comparaison).
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Callable, Dict, List, Optional

from models.config import (
    LEVEL2_GST_MIN_TILE_LENGTH,
    LEVEL2_KGRAM_SIZE,
    LEVEL1_MIN_MATCHING_LINES,
    SUPPORTED_EXTENSIONS,
    THRESHOLD_HIGH,
    THRESHOLD_LOW,
)
from views import theme


class ControlPanel(tk.Frame):
    """Panneau latéral de configuration et de lancement des comparaisons."""

    WIDTH: int = 344

    def __init__(self, parent: tk.Widget, on_compare: Callable[[], None]) -> None:
        super().__init__(parent, width=self.WIDTH, background=theme.SIDEBAR_BG)
        self.pack_propagate(False)
        self.on_compare = on_compare

        # --- État interne ------------------------------------------------------
        self.reference_path: Optional[str] = None
        self.candidate_paths: List[str] = []

        pad = 16

        # =====================================================================
        # BAS FIXE : bouton Comparer + progression + exports (toujours visibles)
        # =====================================================================
        bottom = tk.Frame(self, background=theme.SIDEBAR_BG)
        bottom.pack(side="bottom", fill="x")

        # Ligne de séparation
        tk.Frame(bottom, background=theme.SIDEBAR_ALT, height=1).pack(fill="x")

        bottom_content = tk.Frame(bottom, background=theme.SIDEBAR_BG)
        bottom_content.pack(fill="x", padx=pad, pady=pad)

        # --- Lancement ---------------------------------------------------------
        self.compare_btn = theme.HoverButton(
            bottom_content, normal_bg=theme.ACCENT, hover_bg=theme.ACCENT_DARK,
            text="▶   Comparer", font=(theme.FONT, 11, "bold"), pady=10,
            command=self.on_compare,
        )
        self.compare_btn.pack(fill="x")

        self.progress = ttk.Progressbar(
            bottom_content, mode="determinate", maximum=100,
            style="Sidebar.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", pady=(10, 4))

        self.status_label = tk.Label(
            bottom_content, text="Prêt.", background=theme.SIDEBAR_BG,
            foreground=theme.SIDEBAR_MUTED, font=(theme.FONT, 8),
            anchor="w", justify="left", wraplength=self.WIDTH - 2 * pad,
        )
        self.status_label.pack(fill="x")

        # --- Exports -----------------------------------------------------------
        tk.Frame(bottom_content, background=theme.SIDEBAR_ALT, height=1).pack(
            fill="x", pady=12)
        export_frame = tk.Frame(bottom_content, background=theme.SIDEBAR_BG)
        export_frame.pack(fill="x")
        self.export_csv_btn = theme.HoverButton(
            export_frame, normal_bg=theme.SIDEBAR_ALT, hover_bg=theme.ACCENT,
            text="Exporter CSV", font=(theme.FONT, 9), pady=6,
        )
        self.export_csv_btn.pack(side="left", fill="x", expand=True)
        self.export_html_btn = theme.HoverButton(
            export_frame, normal_bg=theme.SIDEBAR_ALT, hover_bg=theme.ACCENT,
            text="Rapport HTML", font=(theme.FONT, 9), pady=6,
        )
        self.export_html_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.set_export_enabled(False)

        # =====================================================================
        # HAUT DÉFILABLE : configuration (référence, candidats, niveau, params)
        # =====================================================================
        container = tk.Frame(self, background=theme.SIDEBAR_BG)
        container.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(container, background=theme.SIDEBAR_BG,
                           highlightthickness=0, width=self.WIDTH)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, background=theme.SIDEBAR_BG)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def _configure_scrollregion(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _configure_width(event):
            canvas.itemconfig(content_window, width=event.width)

        content.bind("<Configure>", _configure_scrollregion)
        canvas.bind("<Configure>", _configure_width)

        # Support molette souris (uniquement quand le curseur est sur le panneau)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        content.bind("<MouseWheel>", _on_mousewheel)
        self._canvas = canvas
        self._scrollbar = scrollbar

        # --- Titre -------------------------------------------------------------
        tk.Label(content, text="Configuration", background=theme.SIDEBAR_BG,
                 foreground="#ffffff", font=(theme.FONT, 15, "bold"),
                 anchor="w").pack(fill="x", padx=pad, pady=(pad, 0))
        tk.Label(content, text="Analyse multi-niveaux de codes sources",
                 background=theme.SIDEBAR_BG, foreground=theme.SIDEBAR_MUTED,
                 font=(theme.FONT, 9), anchor="w").pack(fill="x", pady=(0, 14), padx=pad)

        # --- 1. Référence ------------------------------------------------------
        self._section(content, "① Fichier de référence")
        ref_card = tk.Frame(content, background=theme.SIDEBAR_ALT)
        ref_card.pack(fill="x", pady=(2, 6), padx=pad)
        self.ref_label = tk.Label(
            ref_card, text="Aucun fichier sélectionné", background=theme.SIDEBAR_ALT,
            foreground=theme.SIDEBAR_MUTED, font=(theme.FONT, 9),
            anchor="w", justify="left", padx=10, pady=8, wraplength=200,
        )
        self.ref_label.pack(side="left", fill="x", expand=True)
        theme.HoverButton(
            ref_card, normal_bg=theme.ACCENT, hover_bg=theme.ACCENT_DARK,
            text="Parcourir", font=(theme.FONT, 9, "bold"), padx=10, pady=6,
            command=self._choose_reference,
        ).pack(side="right", padx=(4, 4), pady=4)

        # --- 2. Candidats ------------------------------------------------------
        self._section(content, "② Fichiers candidats")
        cand_btns = tk.Frame(content, background=theme.SIDEBAR_BG)
        cand_btns.pack(fill="x", pady=(2, 6), padx=pad)
        theme.HoverButton(
            cand_btns, normal_bg=theme.SIDEBAR_ALT, hover_bg=theme.ACCENT,
            text="Ajouter des fichiers", font=(theme.FONT, 9), pady=6,
            command=self._add_candidates,
        ).pack(side="left", fill="x", expand=True)
        theme.HoverButton(
            cand_btns, normal_bg=theme.SIDEBAR_ALT, hover_bg=theme.ACCENT,
            text="Dossier", font=(theme.FONT, 9), padx=10, pady=6,
            command=self._add_directory,
        ).pack(side="left", padx=(6, 0))

        list_frame = tk.Frame(content, background=theme.SIDEBAR_ALT)
        list_frame.pack(fill="both", expand=False, pady=(0, 6), padx=pad)
        self.cand_listbox = tk.Listbox(
            list_frame, height=4, selectmode="extended", font=(theme.FONT, 9),
            background=theme.SIDEBAR_ALT, foreground=theme.SIDEBAR_TEXT,
            selectbackground=theme.ACCENT, selectforeground="#ffffff",
            highlightthickness=0, borderwidth=0, activestyle="none",
        )
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.cand_listbox.yview)
        self.cand_listbox.configure(yscrollcommand=scroll.set)
        self.cand_listbox.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)
        scroll.pack(side="right", fill="y")

        theme.HoverButton(
            content, normal_bg=theme.SIDEBAR_BG, hover_bg=theme.SIDEBAR_ALT,
            normal_fg=theme.SIDEBAR_MUTED, hover_fg="#ffd7d7",
            text="✕  Retirer la sélection", font=(theme.FONT, 9), anchor="w",
            command=self._remove_selected,
        ).pack(fill="x", pady=(0, 12), padx=pad)

        # --- 3. Niveau ---------------------------------------------------------
        self._section(content, "③ Niveau de comparaison")
        self.level_var = tk.StringVar(value="2")
        level_frame = tk.Frame(content, background=theme.SIDEBAR_BG)
        level_frame.pack(fill="x", pady=(2, 10), padx=pad)
        levels = [
            ("1", "Textuel — lignes brutes"),
            ("2", "Tokens — empreintes & GST"),
            ("3", "Structure — inter-langages"),
            ("auto", "Auto — choix par couple"),
        ]
        for val, label in levels:
            tk.Radiobutton(
                level_frame, text=label, value=val, variable=self.level_var,
                background=theme.SIDEBAR_BG, foreground=theme.SIDEBAR_TEXT,
                activebackground=theme.SIDEBAR_BG, activeforeground="#ffffff",
                selectcolor=theme.SIDEBAR_ALT, font=(theme.FONT, 9),
                anchor="w", highlightthickness=0, borderwidth=0, cursor="hand2",
            ).pack(fill="x")

        # --- 4. Paramètres -----------------------------------------------------
        self._section(content, "④ Paramètres avancés")
        params = tk.Frame(content, background=theme.SIDEBAR_ALT)
        params.pack(fill="x", pady=(2, 12), padx=pad)
        params.columnconfigure(0, weight=1)

        self.kgram_var = tk.IntVar(value=LEVEL2_KGRAM_SIZE)
        self.gst_var = tk.IntVar(value=LEVEL2_GST_MIN_TILE_LENGTH)
        self.minfrag_var = tk.IntVar(value=LEVEL1_MIN_MATCHING_LINES)
        self.threshold_var = tk.IntVar(value=int(THRESHOLD_HIGH))

        rows = [
            ("k-grammes (niv. 2)", self.kgram_var, 2, 12),
            ("Tuile min. (GST)", self.gst_var, 2, 20),
            ("Bloc min. (lignes)", self.minfrag_var, 1, 20),
            ("Seuil d'alerte (%)", self.threshold_var, 0, 100),
        ]
        for i, (label, var, frm, to) in enumerate(rows):
            tk.Label(params, text=label, background=theme.SIDEBAR_ALT,
                     foreground=theme.SIDEBAR_TEXT, font=(theme.FONT, 9),
                     anchor="w").grid(row=i, column=0, sticky="w", padx=(10, 4), pady=4)
            tk.Spinbox(
                params, from_=frm, to=to, textvariable=var, width=5,
                background=theme.SIDEBAR_BG, foreground="#ffffff",
                buttonbackground=theme.SIDEBAR_BG, insertbackground="#ffffff",
                relief="flat", highlightthickness=1, highlightbackground=theme.SIDEBAR_ALT,
                highlightcolor=theme.ACCENT, font=(theme.FONT, 9), justify="center",
            ).grid(row=i, column=1, sticky="e", padx=(4, 10), pady=4)

        self.strip_comments_var = tk.BooleanVar(value=True)
        self.ignore_imports_var = tk.BooleanVar(value=True)
        for i, (text, var) in enumerate([
            ("Ignorer les commentaires", self.strip_comments_var),
            ("Ignorer les imports", self.ignore_imports_var),
        ], start=len(rows)):
            tk.Checkbutton(
                params, text=text, variable=var,
                background=theme.SIDEBAR_ALT, foreground=theme.SIDEBAR_TEXT,
                activebackground=theme.SIDEBAR_ALT, activeforeground="#ffffff",
                selectcolor=theme.SIDEBAR_BG, font=(theme.FONT, 9),
                anchor="w", highlightthickness=0, borderwidth=0, cursor="hand2",
            ).grid(row=i, column=0, columnspan=2, sticky="w", padx=10, pady=(2, 4))

        # Espacement final pour que le défilement soit confortable
        tk.Frame(content, background=theme.SIDEBAR_BG, height=8).pack(fill="x")

    # =========================================================================
    # Aides de construction
    # =========================================================================
    def _section(self, parent: tk.Misc, text: str) -> None:
        """Ajoute un intitulé de section contrasté."""
        pad = 16
        tk.Label(parent, text=text, background=theme.SIDEBAR_BG,
                 foreground=theme.ACCENT_TEXT, font=(theme.FONT, 10, "bold"),
                 anchor="w").pack(fill="x", pady=(4, 0), padx=pad)

    # =========================================================================
    # Sélection de fichiers
    # =========================================================================
    def _choose_reference(self) -> None:
        path = filedialog.askopenfilename(
            title="Choisir le fichier de référence",
            filetypes=[("Fichiers sources", " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)),
                       ("Tous les fichiers", "*.*")],
        )
        if path:
            self.reference_path = path
            self.ref_label.config(text=os.path.basename(path), foreground="#ffffff")

    def _add_candidates(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Ajouter des fichiers candidats",
            filetypes=[("Fichiers sources", " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)),
                       ("Tous les fichiers", "*.*")],
        )
        for p in paths:
            if p not in self.candidate_paths:
                self.candidate_paths.append(p)
                self.cand_listbox.insert("end", os.path.basename(p))

    def _add_directory(self) -> None:
        directory = filedialog.askdirectory(title="Ajouter un dossier de candidats")
        if not directory:
            return
        for root, _, files in os.walk(directory):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    full = os.path.join(root, fname)
                    if full not in self.candidate_paths:
                        self.candidate_paths.append(full)
                        self.cand_listbox.insert("end", os.path.relpath(full, directory))

    def _remove_selected(self) -> None:
        selection = list(self.cand_listbox.curselection())
        for idx in reversed(selection):
            self.cand_listbox.delete(idx)
            del self.candidate_paths[idx]

    # =========================================================================
    # Accesseurs pour la logique applicative
    # =========================================================================
    def get_config(self) -> Dict[str, object]:
        """Retourne la configuration courante sous forme de dictionnaire."""
        return {
            "reference_path": self.reference_path,
            "candidate_paths": list(self.candidate_paths),
            "level": self.level_var.get(),
            "kgram_size": self.kgram_var.get(),
            "gst_min_tile": self.gst_var.get(),
            "min_fragment_lines": self.minfrag_var.get(),
            "threshold_high": float(self.threshold_var.get()),
            "strip_comments": self.strip_comments_var.get(),
            "ignore_imports": self.ignore_imports_var.get(),
        }

    def set_progress(self, value: float, status: str = "") -> None:
        """Met à jour la barre de progression et le statut."""
        self.progress["value"] = value
        if status:
            self.status_label.config(text=status)
        self.update_idletasks()

    def set_export_enabled(self, enabled: bool) -> None:
        """Active ou désactive les boutons d'export."""
        theme.configure_disabled(self.export_csv_btn, enabled,
                                 normal_bg=theme.SIDEBAR_ALT,
                                 disabled_bg=theme.SIDEBAR_BG)
        theme.configure_disabled(self.export_html_btn, enabled,
                                 normal_bg=theme.SIDEBAR_ALT,
                                 disabled_bg=theme.SIDEBAR_BG)
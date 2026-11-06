#!/usr/bin/env python3
"""
Point d'entrée graphique du Détecteur de similarité entre codes sources.

Architecture MVC :
    - models/       : logique métier (chargement, analyse, classement, exports)
    - views/        : interface Tkinter (aucune logique métier)
    - controllers/  : orchestration entre le modèle et la vue

Lancement :
    python main.py
"""

from controllers.app_controller import AppController
from views.main_window import MainWindow


def run_app() -> None:
    """Construit la fenêtre, branche le contrôleur puis lance la boucle Tk."""
    window = MainWindow()
    AppController(window)
    window.mainloop()


if __name__ == "__main__":
    run_app()

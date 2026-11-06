"""
Configuration pytest pour le projet de détecteur de similarité.

Ajoute la racine du projet au `sys.path` afin que les tests puissent importer
les paquets `models`, `views`, `controllers`, `evaluation`, etc., quel que soit
le répertoire de lancement (`py -m pytest` depuis la racine recommandé).
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -*- mode: python ; coding: utf-8 -*-
"""
Spécification PyInstaller — Détecteur de similarité entre codes sources.

Construction :
    py -m PyInstaller detecteur_similarite.spec --noconfirm

Génère dist\DetecteurDeSimilarite\DetecteurDeSimilarite.exe (mode onedir :
démarrage rapide, dossier de distribution transparent).
"""

import sys

block_cipher = None

# Les grammaires tree-sitter sont chargées dynamiquement (import conditionnel)
# : elles doivent être déclarées explicitement comme imports cachés.
hidden_imports = [
    "tree_sitter",
    "tree_sitter_python",
    "tree_sitter_java",
    "tree_sitter_c",
    "tree_sitter_cpp",
    "tree_sitter_javascript",
    "matplotlib.backends.backend_tkagg",
    "models.report.export_csv",
    "models.report.export_html",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter.test", "unittest", "pydoc_data"],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DetecteurDeSimilarite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # application graphique : pas de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DetecteurDeSimilarite",
)

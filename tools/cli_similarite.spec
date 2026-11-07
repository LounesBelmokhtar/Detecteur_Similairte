# -*- mode: python ; coding: utf-8 -*-
r"""
Spécification PyInstaller — CLI du détecteur de similarité.

Construction (depuis la racine du projet) :
    py -m PyInstaller tools/cli_similarite.spec --noconfirm

Génère dist\CLI-Similarite\CLI-Similarite.exe (mode console).
"""

import os

# Racine du projet : le fichier .spec se trouve dans tools/.
PROJECT_ROOT = os.path.dirname(SPECPATH)

block_cipher = None

hidden_imports = [
    "tree_sitter",
    "tree_sitter_python",
    "tree_sitter_java",
    "tree_sitter_c",
    "tree_sitter_cpp",
    "tree_sitter_javascript",
    "models.report.export_csv",
    "models.report.export_html",
]

a = Analysis(
    [os.path.join(PROJECT_ROOT, "cli.py")],
    pathex=[PROJECT_ROOT],
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
    name="CLI-Similarite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,           # application console
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
    name="CLI-Similarite",
)

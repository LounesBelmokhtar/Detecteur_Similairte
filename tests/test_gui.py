"""
Tests de fumée de l'interface graphique (Tkinter).

Ces tests instancient la vue réelle, branchent le contrôleur, lancent une
comparaison en mode auto et vérifient les scores obtenus. Ils sont ignorés si
Tkinter n'est pas disponible sur la machine (environnement sans affichage).
"""

import os

import pytest

tk = pytest.importorskip("tkinter", reason="Tkinter non disponible")

from models.loader import load_source_file
from tests.conftest import SAMPLES


@pytest.fixture(scope="module")
def app():
    """Instance unique partagée : créer/détruire plusieurs racines Tk dans un
    même processus est instable sur certains systèmes (TclError)."""
    from controllers.app_controller import AppController
    from views.main_window import MainWindow
    try:
        window = MainWindow()
        controller = AppController(window)
        window.update()
    except tk.TclError as exc:
        pytest.skip(f"Tkinter indisponible sur cette machine : {exc}")
    yield controller
    window.destroy()


def _load(rel: str):
    return load_source_file(os.path.join(SAMPLES, rel.replace("/", os.sep)))


def _run(controller, level: str):
    controller.reference_source = _load("identical/bubble_sort_ref.py")
    controller.candidate_sources = {
        "renamed": _load("modified/bubble_sort_renamed.py"),
        "java": _load("cross_language/BubbleSort.java"),
        "gcd": _load("unrelated/gcd.py"),
    }
    cfg = {
        "level": level,
        "threshold_high": 70.0,
        "min_fragment_lines": 3,
        "strip_comments": True,
        "kgram_size": 5,
        "gst_min_tile": 4,
    }
    controller._run_comparison(cfg)
    controller.view.update()
    return {os.path.basename(r.path): r for r in controller.results}


def test_app_instantiates(app):
    assert app.view is not None


def test_auto_mode_per_candidate(app):
    """Le mode auto choisit le niveau par couple : les scores doivent être cohérents."""
    results = _run(app, "auto")
    assert results["bubble_sort_renamed.py"].score >= 80.0   # niveau 2
    assert results["BubbleSort.java"].score >= 55.0          # niveau 3
    assert results["gcd.py"].score < 30.0                    # sans relation


def test_explicit_level2(app):
    results = _run(app, "2")
    assert results["bubble_sort_renamed.py"].score >= 80.0
    # Au niveau 2, le cross-langage reste faible (attendu)
    assert results["BubbleSort.java"].score < 40.0


def test_alerts_classified(app):
    results = _run(app, "auto")
    assert results["bubble_sort_renamed.py"].alert == "high"
    assert results["gcd.py"].alert == "low"

"""
Fixtures partagées des tests : chemins vers les échantillons et chargeurs.
"""

import os

import pytest

from models.loader import load_source_file

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(PROJECT_ROOT, "samples")


def sample(relative: str):
    """Charge un échantillon relatif à `samples/` (séparateur `/` accepté)."""
    return load_source_file(os.path.join(SAMPLES, relative.replace("/", os.sep)))


@pytest.fixture(scope="session")
def bubble_ref():
    return sample("identical/bubble_sort_ref.py")


@pytest.fixture(scope="session")
def bubble_copy():
    return sample("identical/bubble_sort_copy.py")


@pytest.fixture(scope="session")
def bubble_reformat():
    return sample("identical/bubble_sort_reformat.py")


@pytest.fixture(scope="session")
def bubble_renamed():
    return sample("modified/bubble_sort_renamed.py")


@pytest.fixture(scope="session")
def bubble_reordered():
    return sample("modified/bubble_sort_reordered.py")


@pytest.fixture(scope="session")
def bubble_while():
    return sample("modified/bubble_sort_while.py")


@pytest.fixture(scope="session")
def bubble_dead_code():
    return sample("modified/bubble_sort_dead_code.py")


@pytest.fixture(scope="session")
def bubble_combo():
    return sample("modified/bubble_sort_combo.py")


@pytest.fixture(scope="session")
def binary_search():
    return sample("unrelated/binary_search.py")


@pytest.fixture(scope="session")
def factorial():
    return sample("unrelated/factorial.py")


@pytest.fixture(scope="session")
def gcd():
    return sample("unrelated/gcd.py")

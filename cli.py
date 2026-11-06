#!/usr/bin/env python3
"""
Interface en ligne de commande (point d'entrée de la CLI).

Exemples :
    python cli.py --ref reference.py --cands a.py b.py c.py --level 2
    python cli.py --ref main.c --cands-dir ./candidats --level 3 --csv rapport.csv
    python cli.py --ref tri.py --cands tri.java tri.c --level auto --html rapport.html
"""

from __future__ import annotations

import sys
from typing import List

from controllers.cli_controller import CLIController
from views.console import build_parser, configure_utf8


def main(argv: List[str] | None = None) -> int:
    configure_utf8()
    args = build_parser().parse_args(argv)
    return CLIController(args).run()


if __name__ == "__main__":
    sys.exit(main())

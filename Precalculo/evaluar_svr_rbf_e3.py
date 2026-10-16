"""Evaluación E3 independiente de SVR con kernel RBF."""
from __future__ import annotations

import argparse

from evaluar_svr_rbf_raffle_e3 import run


def main(force: bool = False) -> None:
    run(model="svr_rbf", force=force)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recalcular los folds y el test de SVR RBF, sustituyendo sus artefactos.",
    )
    args = parser.parse_args()
    main(force=args.force)

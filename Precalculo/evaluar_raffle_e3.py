"""Evaluación E3 independiente del bosque RaFFLE."""
from __future__ import annotations

import argparse

from evaluar_svr_rbf_raffle_e3 import run


def main(force: bool = False) -> None:
    run(model="raffle", force=force)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recalcular los folds y el test de RaFFLE, sustituyendo sus artefactos.",
    )
    args = parser.parse_args()
    main(force=args.force)

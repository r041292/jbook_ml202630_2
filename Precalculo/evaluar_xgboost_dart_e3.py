"""Evaluación E3 independiente de DART-XGBoost."""
from __future__ import annotations

import argparse

from evaluar_xgboost_variantes_e3 import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recalcular los folds de DART-XGBoost.")
    args = parser.parse_args()
    run(model="dart", force=args.force)

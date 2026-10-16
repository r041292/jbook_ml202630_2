"""Control E3 de XGBoost gbtree con búsqueda aleatoria ampliada."""
from __future__ import annotations

import argparse

from evaluar_xgboost_variantes_e3 import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recalcular los folds del control gbtree ampliado.")
    args = parser.parse_args()
    run(model="gbtree", force=args.force)

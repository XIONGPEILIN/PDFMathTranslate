# ruff: noqa: E402
import sys
from pathlib import Path

for mod in list(sys.modules):
    if mod.startswith("pdf2zh"):
        sys.modules.pop(mod)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

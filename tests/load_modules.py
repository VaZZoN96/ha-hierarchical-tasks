"""Load the pure model WITHOUT importing the Home Assistant integration."""
from importlib import import_module
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATH = ROOT / "custom_components" / "hierarchical_tasks"
if "ht_test_package" not in sys.modules:
    package = types.ModuleType("ht_test_package")
    package.__path__ = [str(PACKAGE_PATH)]
    sys.modules[package.__name__] = package
model = import_module("ht_test_package.model")
storage = import_module("ht_test_package.storage")

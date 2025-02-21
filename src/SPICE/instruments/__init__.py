import sys
sys.path.insert(0, "/".join(__file__.split("/")[:-5]))
from src.SPICE.instruments.diviner import DIVINERInstrument

__all__ = ["DIVINERInstrument"]
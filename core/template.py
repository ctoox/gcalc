"""Report template v2 — uses FusionV2 calibrated engine."""
from core.fusion_v2 import FusionV2

_engine = FusionV2()

def analyze(y, m, d, h=12, name="", gender="男", rank=2):
    return _engine.analyze(y, m, d, h, name, gender, rank)

def system_metadata():
    return _engine.metadata()

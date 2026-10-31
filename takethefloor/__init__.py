"""TakeTheFloor — meeting equity & leadership coaching engine.

Built for the 305 EmpowHER Edition October 2026 hackathon.
"""

from .parser import Turn, parse_transcript
from .analysis import analyze

__all__ = ["Turn", "parse_transcript", "analyze"]
__version__ = "1.0.0"

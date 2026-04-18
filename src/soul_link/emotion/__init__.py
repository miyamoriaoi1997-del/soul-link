"""Soul-Link emotion system.

Provides 4-dimensional emotion detection, calculation, and tone modification.
Supports Chinese natural language patterns with optional neural sentiment fusion.
"""

from soul_link.emotion.models import (
    EmotionEvent,
    EmotionState,
    SentimentResult,
    ToneModifiers,
    Moment,
)
from soul_link.emotion.detector import EmotionDetector
from soul_link.emotion.calculator import EmotionCalculator

__all__ = [
    "EmotionEvent",
    "EmotionState",
    "SentimentResult",
    "ToneModifiers",
    "Moment",
    "EmotionDetector",
    "EmotionCalculator",
]

try:
    from soul_link.emotion.analyzer import SentimentAnalyzer
    __all__.append("SentimentAnalyzer")
except ImportError:
    pass

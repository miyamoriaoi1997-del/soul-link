"""Soul-Link emotion system shared models and dataclasses."""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime


@dataclass
class EmotionEvent:
    """Represents a detected emotional trigger event."""
    trigger_type: str  # praise, criticism, neglect, intimacy, etc.
    deltas: Dict[str, int]  # emotion dimension -> change amount
    confidence: float  # 0.0-1.0
    context: str  # brief description of what triggered it
    intensity: str = "moderate"  # mild, moderate, intense


@dataclass
class EmotionState:
    """Current emotion state with 4 dimensions."""
    affection: int = 50          # 好感度 0-100
    trust: int = 50              # 信任度 0-100
    possessiveness: int = 30     # 占有欲 0-100
    patience: int = 60           # 耐心值 0-100
    emotion_score: float = 0.0   # unified score [-5, +5]
    current_emotion: float = 0.0
    last_update: str = ""
    baselines: Dict[str, int] = field(default_factory=lambda: {
        "affection": 50,
        "trust": 50,
        "possessiveness": 30,
        "patience": 60,
    })
    decay_rate: float = 2.0  # points per hour toward baseline
    inertia: Dict[str, Any] = field(default_factory=lambda: {
        "consecutive_same": 0,
        "last_direction": 0,
        "history": [],
    })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "affection": self.affection,
            "trust": self.trust,
            "possessiveness": self.possessiveness,
            "patience": self.patience,
            "emotion_score": round(self.emotion_score, 2),
            "current_emotion": round(self.current_emotion, 2),
            "last_update": self.last_update or datetime.now().isoformat(),
            "baselines": dict(self.baselines),
            "decay_rate": self.decay_rate,
            "inertia": dict(self.inertia),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionState":
        state = cls()
        for dim in ("affection", "trust", "possessiveness", "patience"):
            if dim in data:
                setattr(state, dim, int(data[dim]))
        state.emotion_score = float(data.get("emotion_score", 0.0))
        state.current_emotion = float(data.get("current_emotion", 0.0))
        state.last_update = data.get("last_update", "")
        if "baselines" in data:
            state.baselines = dict(data["baselines"])
        if "decay_rate" in data:
            state.decay_rate = float(data["decay_rate"])
        if "inertia" in data:
            state.inertia = dict(data["inertia"])
        return state


@dataclass
class SentimentResult:
    """Result from neural sentiment analysis."""
    label: str           # English label
    label_zh: str        # Chinese label
    confidence: float    # 0.0-1.0
    valence: float       # -1.0 to 1.0
    all_scores: Dict[str, float] = field(default_factory=dict)
    inference_ms: float = 0.0


@dataclass
class ToneModifiers:
    """Dynamic tone modification instructions based on emotion state."""
    intensity: str = "mild"  # mild, moderate, intense, overwhelming
    framework: str = ""      # overall tone framework description
    directives: List[str] = field(default_factory=list)  # per-dimension directives
    footnote: str = ""       # additional notes


@dataclass
class Moment:
    """A recorded relationship memory event."""
    timestamp: str
    event_type: str
    context: str
    emotion_snapshot: str = ""

    def to_line(self) -> str:
        parts = [self.timestamp, self.event_type, self.context]
        if self.emotion_snapshot:
            parts[-1] += f" {self.emotion_snapshot}"
        return " | ".join(parts)

    @classmethod
    def from_line(cls, line: str) -> Optional["Moment"]:
        parts = line.strip().split(" | ", 2)
        if len(parts) < 3:
            return None
        return cls(
            timestamp=parts[0].strip(),
            event_type=parts[1].strip(),
            context=parts[2].strip(),
        )

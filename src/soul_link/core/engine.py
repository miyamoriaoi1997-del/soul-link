"""Soul-Link core engine.

The main orchestrator that ties persona, emotion, behavior, and LLM together.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from soul_link.core.config import SoulLinkConfig
from soul_link.persona.loader import PersonaLoader
from soul_link.emotion.detector import EmotionDetector, EmotionEvent
from soul_link.emotion.calculator import EmotionCalculator
from soul_link.emotion.models import EmotionState, ToneModifiers
from soul_link.behavior.strategies import match_strategy
from soul_link.behavior.controller import BehaviorStrategyController

logger = logging.getLogger(__name__)


class SoulLinkEngine:
    """Main Soul-Link engine that orchestrates all subsystems.

    Usage:
        config = SoulLinkConfig.load("soul-link.yaml")
        engine = SoulLinkEngine(config)

        # Process a user message
        system_prompt = engine.process_message("你好！")

        # Get current emotion state
        state = engine.get_emotion_state()

        # Get recent moments
        moments = engine.get_recent_moments()
    """

    def __init__(self, config: SoulLinkConfig):
        self.config = config
        self.persona = PersonaLoader(config.persona_dir)

        # Initialize emotion system
        self._emotion_detector: Optional[EmotionDetector] = None
        self._emotion_calculator: Optional[EmotionCalculator] = None
        self._behavior_controller: Optional[BehaviorStrategyController] = None

        # Current state cache
        self._current_state: Optional[EmotionState] = None

        if config.emotion.enabled:
            self._init_emotion_system()

        if config.behavior.enabled:
            self._init_behavior_system()

        logger.info("Soul-Link engine initialized")

    def _init_emotion_system(self):
        """Initialize the emotion detection and calculation system."""
        # Build agent profile from config
        agent_profile = {
            "names": self.config.agent_names or self.persona.get_agent_names(),
        }
        self._emotion_detector = EmotionDetector(agent_profile=agent_profile)
        self._emotion_calculator = EmotionCalculator(
            baselines=self.config.emotion.baselines
        )
        # Load current state from STATE.md
        self._load_state()

    def _init_behavior_system(self):
        """Initialize the behavior strategy system."""
        self._behavior_controller = BehaviorStrategyController()

    def _load_state(self) -> EmotionState:
        """Load emotion state from STATE.md."""
        fm, body = self.persona.load_state()
        if fm and "emotion_state" in fm:
            self._current_state = EmotionState.from_dict(fm["emotion_state"])
        else:
            self._current_state = EmotionState(
                baselines=dict(self.config.emotion.baselines)
            )
        return self._current_state

    def _save_state(self):
        """Save current emotion state to STATE.md."""
        if not self._current_state:
            return

        state_dict = self._current_state.to_dict()

        # Build state body text
        body = self._build_state_body()

        fm = {
            "emotion_state": state_dict,
        }
        self.persona.save_state(fm, body)

    def _build_state_body(self) -> str:
        """Build human-readable state body for STATE.md."""
        if not self._current_state:
            return ""

        s = self._current_state
        lines = [
            "## 当前情绪状态",
            "",
            f"好感度: {s.affection}/100",
            f"信任度: {s.trust}/100",
            f"占有欲: {s.possessiveness}/100",
            f"耐心值: {s.patience}/100",
            f"情绪分值: {s.emotion_score:+.2f} / 5.00",
        ]
        return "\n".join(lines)

    def process_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Process a user message and return the enriched system prompt.

        This is the main entry point for integrations. It:
        1. Detects emotional triggers in the user message
        2. Updates emotion state (with time decay)
        3. Selects behavior strategy
        4. Assembles the full system prompt

        Args:
            user_message: The latest user message text
            conversation_history: Optional list of {"role": "user/assistant", "content": "..."}

        Returns:
            Complete system prompt string with all persona layers and dynamic modifiers
        """
        emotion_modifier = ""
        behavior_directive = ""

        if self.config.emotion.enabled and self._emotion_detector:
            emotion_modifier = self._process_emotion(user_message)

        if self.config.behavior.enabled and self._behavior_controller:
            behavior_directive = self._process_behavior(
                user_message, conversation_history
            )

        return self.persona.build_system_prompt(
            emotion_modifier=emotion_modifier,
            behavior_directive=behavior_directive,
        )

    def _process_emotion(self, user_message: str) -> str:
        """Detect emotion triggers and update state. Returns tone modifier string."""
        if not self._emotion_detector or not self._emotion_calculator:
            return ""

        # Wrap string message into message list format
        messages = [{"role": "user", "content": user_message}]
        
        # Detect trigger
        event = self._emotion_detector.detect_emotion_event(messages)

        if not self._current_state:
            self._load_state()

        state = self._current_state

        if event:
            # Apply time decay first
            from datetime import datetime
            last_update = datetime.fromisoformat(state.last_update) if state.last_update else datetime.now()
            
            # Build emotion dict for decay (only 4 dimensions)
            emotion_dict = {
                "affection": state.affection,
                "trust": state.trust,
                "possessiveness": state.possessiveness,
                "patience": state.patience,
            }
            decayed = self._emotion_calculator.apply_decay(emotion_dict, last_update)
            
            # Update state with decayed values
            state.affection = decayed["affection"]
            state.trust = decayed["trust"]
            state.possessiveness = decayed["possessiveness"]
            state.patience = decayed["patience"]

            # Apply emotion deltas
            emotion_dict_for_deltas = {
                "affection": state.affection,
                "trust": state.trust,
                "possessiveness": state.possessiveness,
                "patience": state.patience,
            }
            updated = self._emotion_calculator.apply_deltas(emotion_dict_for_deltas, event.deltas)
            
            # Update state with new values
            state.affection = updated["affection"]
            state.trust = updated["trust"]
            state.possessiveness = updated["possessiveness"]
            state.patience = updated["patience"]

            # Update emotion score
            emotion_dict_for_score = {
                "affection": state.affection,
                "trust": state.trust,
                "possessiveness": state.possessiveness,
                "patience": state.patience,
            }
            state.emotion_score = self._emotion_calculator.compute_emotion_score(emotion_dict_for_score)
            state.current_emotion = state.emotion_score
            state.last_update = datetime.now().isoformat()

            # Record moment
            self._record_moment(event, state)

            # Save updated state
            self._save_state()

            logger.info(
                f"Emotion event: {event.trigger_type} ({getattr(event, 'intensity', 'moderate')}) "
                f"-> aff={state.affection} trust={state.trust} "
                f"poss={state.possessiveness} pat={state.patience}"
            )

        # Generate tone modifiers
        emotion_dict_for_tone = {
            "affection": state.affection,
            "trust": state.trust,
            "possessiveness": state.possessiveness,
            "patience": state.patience,
        }
        tone = self._emotion_calculator.get_tone_modifiers(emotion_dict_for_tone)
        if isinstance(tone, dict):
            return self._format_tone_modifier(tone)
        elif isinstance(tone, str):
            return tone
        return ""

    def _format_tone_modifier(self, tone: Dict[str, Any]) -> str:
        """Format tone modifiers into XML block for prompt injection."""
        parts = []
        framework = tone.get("framework", "")
        directives = tone.get("directives", [])
        footnote = tone.get("footnote", "")

        if framework or directives:
            parts.append("<emotion_modifier>")
            if framework:
                parts.append(framework)
            for d in directives:
                parts.append(f"- {d}")
            if footnote:
                parts.append(f"\n{footnote}")
            parts.append("</emotion_modifier>")

        return "\n".join(parts)

    def _process_behavior(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Select behavior strategy and return directive string."""
        if not self._behavior_controller or not self._current_state:
            return ""

        try:
            # Build messages list from history + current user message
            messages = []
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": user_message})
            
            return self._behavior_controller.get_behavior_directive(
                emotion_state=self._current_state,
                messages=messages,
            )
        except Exception as e:
            logger.error(f"Behavior strategy error: {e}")
            return ""

    def _record_moment(self, event: EmotionEvent, state: EmotionState):
        """Record a significant emotional moment."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            snapshot = (
                f"[好感:{state.affection} 信任:{state.trust} "
                f"占有:{state.possessiveness} 耐心:{state.patience}]"
            )
            intensity = getattr(event, 'intensity', 'moderate')
            intensity_tag = f"[{intensity}] " if intensity != "moderate" else ""
            line = f"{timestamp} | {event.trigger_type} | {intensity_tag}{event.context} {snapshot}"
            self.persona.append_moment(line)
        except Exception as e:
            logger.error(f"Failed to record moment: {e}")

    def get_emotion_state(self) -> Optional[Dict[str, Any]]:
        """Get current emotion state as dict."""
        if self._current_state:
            return self._current_state.to_dict()
        return None

    def get_recent_moments(self, count: int = 10) -> List[str]:
        """Get recent relationship moments."""
        return self.persona.load_moments(last_n=count)

    def update_persona_file(self, filename: str, content: str):
        """Update a persona file (SOUL.md, USER.md, MEMORY.md)."""
        if filename not in ["SOUL.md", "USER.md", "MEMORY.md"]:
            raise ValueError(f"Cannot directly update {filename}")
        self.persona._write_file(filename, content)

    def get_persona_file(self, filename: str) -> str:
        """Read a persona file."""
        return self.persona._read_file(filename)

    def get_config_dict(self) -> Dict[str, Any]:
        """Get current config as dict (for Web UI)."""
        return self.config.to_dict()

    def update_config(self, updates: Dict[str, Any]):
        """Update config from dict (from Web UI)."""
        current = self.config.to_dict()
        current.update(updates)
        self.config = SoulLinkConfig.from_dict(current)

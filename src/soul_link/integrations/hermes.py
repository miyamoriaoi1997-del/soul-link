"""
Hermes Agent Integration Adapter

This adapter allows Soul-Link to integrate seamlessly with Hermes Agent,
replacing or augmenting Hermes' built-in personality system.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

from soul_link.core.engine import SoulLinkEngine
from soul_link.persona.loader import PersonaLoader
from soul_link.emotion.detector import EmotionDetector
from soul_link.emotion.calculator import EmotionCalculator
from soul_link.persona.state import EmotionStateManager
from soul_link.behavior.controller import BehaviorStrategyController


class HermesAdapter:
    """
    Adapter for integrating Soul-Link with Hermes Agent.
    
    Usage in Hermes:
        from soul_link.integrations.hermes import HermesAdapter
        
        adapter = HermesAdapter(persona_path="~/.hermes/personas/my-character")
        
        # In run_agent.py, before constructing system prompt:
        personality_layers = adapter.get_personality_layers()
        emotion_modifier = adapter.get_emotion_modifier(messages)
        behavior_directive = adapter.get_behavior_directive(messages)
        
        # After conversation:
        adapter.update_state(messages)
    """
    
    def __init__(
        self,
        persona_path: str,
        hermes_home: Optional[str] = None,
        use_neural_emotion: bool = False
    ):
        """
        Initialize Hermes adapter.
        
        Args:
            persona_path: Path to persona directory (contains SOUL.md, USER.md, etc.)
            hermes_home: Hermes home directory (defaults to ~/.hermes)
            use_neural_emotion: Enable neural emotion detection
        """
        self.persona_path = Path(persona_path).expanduser()
        self.hermes_home = Path(hermes_home or "~/.hermes").expanduser()
        
        # Load persona
        self.loader = PersonaLoader(str(self.persona_path))
        self.persona = self.loader.load()
        
        # Initialize emotion system
        self.emotion_detector = EmotionDetector(use_neural_model=use_neural_emotion)
        self.emotion_calculator = EmotionCalculator()
        self.state_manager = EmotionStateManager(str(self.hermes_home))
        
        # Initialize behavior system
        self.behavior_controller = BehaviorStrategyController()
    
    def get_personality_layers(self) -> Dict[str, str]:
        """
        Get all personality layers for injection into Hermes system prompt.
        
        Returns:
            Dict with keys: soul, user, memory, state, moments
        """
        return {
            "soul": self.persona.soul,
            "user": self.persona.user,
            "memory": self.persona.memory,
            "state": self._get_state_content(),
            "moments": self._get_recent_moments()
        }
    
    def get_emotion_modifier(self, messages: List[Dict[str, Any]]) -> str:
        """
        Get emotion modifier prompt based on current state.
        
        Args:
            messages: Conversation history
            
        Returns:
            Emotion modifier prompt string
        """
        state = self.state_manager.get_current_state()
        tone_modifiers = self.emotion_calculator.get_tone_modifiers(
            state["affection"],
            state["trust"],
            state["possessiveness"],
            state["patience"]
        )
        
        return self._format_emotion_modifier(tone_modifiers)
    
    def get_behavior_directive(self, messages: List[Dict[str, Any]]) -> str:
        """
        Get behavior directive based on context and emotions.
        
        Args:
            messages: Conversation history
            
        Returns:
            Behavior directive prompt string
        """
        state = self.state_manager.get_current_state()
        
        directive = self.behavior_controller.get_behavior_directive(
            messages=messages,
            affection=state["affection"],
            trust=state["trust"],
            possessiveness=state["possessiveness"],
            patience=state["patience"]
        )
        
        return directive if directive else ""
    
    def update_state(self, messages: List[Dict[str, Any]]) -> None:
        """
        Update emotion state based on conversation.
        
        Args:
            messages: Full conversation history
        """
        self.state_manager.update_emotion_state(messages)
    
    def get_proactive_chat_config(self) -> Optional[Dict[str, Any]]:
        """
        Get proactive chat configuration if enabled.
        
        Returns:
            Config dict or None if disabled
        """
        config_path = self.persona_path / "config.yaml"
        if not config_path.exists():
            return None
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        proactive = config.get("proactive", {})
        if not proactive.get("enabled", False):
            return None
        
        return proactive
    
    def _get_state_content(self) -> str:
        """Get current STATE.md content."""
        state_path = self.hermes_home / "STATE.md"
        if state_path.exists():
            return state_path.read_text()
        return ""
    
    def _get_recent_moments(self, limit: int = 5) -> str:
        """Get recent relationship moments."""
        moments_path = self.hermes_home / "MOMENTS.md"
        if not moments_path.exists():
            return ""
        
        lines = moments_path.read_text().strip().split("\n")
        # Skip header if present
        if lines and lines[0].startswith("#"):
            lines = lines[1:]
        
        recent = lines[-limit:] if len(lines) > limit else lines
        return "\n".join(recent)
    
    def _format_emotion_modifier(self, tone_modifiers: Dict[str, Any]) -> str:
        """Format emotion modifier for Hermes prompt."""
        if not tone_modifiers:
            return ""
        
        intensity = tone_modifiers.get("intensity", "moderate")
        framework = tone_modifiers.get("framework", "")
        dimensions = tone_modifiers.get("dimensions", {})
        footnote = tone_modifiers.get("footnote", "")
        
        parts = [
            f"<emotion_modifier>",
            f"当前情绪状态强烈程度：{intensity}",
            "",
            framework,
            ""
        ]
        
        if dimensions:
            parts.append("具体维度指令：")
            for dim, instruction in dimensions.items():
                if instruction:
                    parts.append(f"- {dim}: {instruction}")
            parts.append("")
        
        if footnote:
            parts.append(footnote)
        
        parts.append("</emotion_modifier>")
        
        return "\n".join(parts)


class HermesPersonaInjector:
    """
    Helper to inject Soul-Link persona into Hermes runtime.
    
    This modifies Hermes' prompt construction to use Soul-Link layers.
    """
    
    @staticmethod
    def inject_into_prompt(
        adapter: HermesAdapter,
        messages: List[Dict[str, Any]],
        base_prompt: str
    ) -> str:
        """
        Inject Soul-Link personality into Hermes system prompt.
        
        Args:
            adapter: HermesAdapter instance
            messages: Conversation history
            base_prompt: Original Hermes system prompt
            
        Returns:
            Modified system prompt with Soul-Link layers
        """
        layers = adapter.get_personality_layers()
        emotion_modifier = adapter.get_emotion_modifier(messages)
        behavior_directive = adapter.get_behavior_directive(messages)
        
        # Build layered prompt
        prompt_parts = [base_prompt]
        
        # Core personality (SOUL.md)
        if layers["soul"]:
            prompt_parts.append(f"\n<soul>\n{layers['soul']}\n</soul>")
        
        # User profile
        if layers["user"]:
            prompt_parts.append(f"\n<user_profile>\n{layers['user']}\n</user_profile>")
        
        # Long-term memory
        if layers["memory"]:
            prompt_parts.append(f"\n<memory>\n{layers['memory']}\n</memory>")
        
        # Current emotional state
        if emotion_modifier:
            prompt_parts.append(f"\n{emotion_modifier}")
        
        # Behavior directive
        if behavior_directive:
            prompt_parts.append(f"\n{behavior_directive}")
        
        # Relationship moments
        if layers["moments"]:
            prompt_parts.append(
                f"\n<relationship_memory>\n"
                f"以下是我们之间最近的重要记忆片段，回复时可自然融入这些记忆：\n"
                f"{layers['moments']}\n"
                f"</relationship_memory>"
            )
        
        return "\n".join(prompt_parts)

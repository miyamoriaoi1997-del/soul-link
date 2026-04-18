"""
OpenClaw Integration Adapter

This adapter allows Soul-Link to integrate with OpenClaw framework,
providing persistent personality and emotion tracking.
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


class OpenClawAdapter:
    """
    Adapter for integrating Soul-Link with OpenClaw framework.
    
    Usage in OpenClaw:
        from soul_link.integrations.openclaw import OpenClawAdapter
        
        adapter = OpenClawAdapter(persona_path="./personas/my-character")
        
        # Before generating response:
        system_prompt = adapter.build_system_prompt(conversation_history)
        
        # After response:
        adapter.process_turn(user_message, assistant_response)
    """
    
    def __init__(
        self,
        persona_path: str,
        data_dir: Optional[str] = None,
        use_neural_emotion: bool = False
    ):
        """
        Initialize OpenClaw adapter.
        
        Args:
            persona_path: Path to persona directory
            data_dir: Directory for state/cache (defaults to ./data)
            use_neural_emotion: Enable neural emotion detection
        """
        self.persona_path = Path(persona_path).expanduser()
        self.data_dir = Path(data_dir or "./data").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load persona
        self.loader = PersonaLoader(str(self.persona_path))
        
        # Initialize emotion system
        self.emotion_detector = EmotionDetector(use_model=use_neural_emotion)
        self.emotion_calculator = EmotionCalculator()
        self.state_manager = EmotionStateManager(str(self.data_dir))
        
        # Initialize behavior system
        self.behavior_controller = BehaviorStrategyController()
    
    def build_system_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Build complete system prompt with all Soul-Link layers.
        
        Args:
            messages: Conversation history [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            Complete system prompt string
        """
        parts = []
        
        # Core personality
        soul = self.loader.load_soul()
        if soul:
            parts.append(f"# Core Personality\n\n{soul}")
        
        # User profile
        user = self.loader.load_user()
        if user:
            parts.append(f"\n# User Profile\n\n{user}")
        
        # Long-term memory
        memory = self.loader.load_memory()
        if memory:
            parts.append(f"\n# Memory\n\n{memory}")
        
        # Current emotional state
        state = self.state_manager.get_current_emotion_state()
        emotion_prompt = self._build_emotion_prompt(state)
        if emotion_prompt:
            parts.append(f"\n{emotion_prompt}")
        
        # Behavior directive
        from soul_link.emotion.models import EmotionState
        emotion_state = EmotionState(
            affection=state["affection"],
            trust=state["trust"],
            possessiveness=state["possessiveness"],
            patience=state["patience"]
        )
        directive = self.behavior_controller.get_behavior_directive(
            emotion_state=emotion_state,
            messages=messages
        )
        if directive:
            parts.append(f"\n{directive}")
        
        # Recent moments
        moments = self._get_recent_moments()
        if moments:
            parts.append(
                f"\n# Recent Relationship Moments\n\n{moments}"
            )
        
        return "\n".join(parts)
    
    def process_turn(
        self,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a conversation turn and update state.
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata (timestamp, platform, etc.)
            
        Returns:
            Updated state information
        """
        # Build message list for emotion detection
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response}
        ]
        
        # Update emotion state
        self.state_manager.update_emotion_state(messages)
        
        # Get updated state
        state = self.state_manager.get_current_emotion_state()
        
        return {
            "emotion_state": state,
            "timestamp": metadata.get("timestamp") if metadata else None
        }
    
    def get_current_emotions(self) -> Dict[str, int]:
        """
        Get current emotion values.
        
        Returns:
            Dict with affection, trust, possessiveness, patience
        """
        state = self.state_manager.get_current_emotion_state()
        return {
            "affection": state["affection"],
            "trust": state["trust"],
            "possessiveness": state["possessiveness"],
            "patience": state["patience"]
        }
    
    def reset_emotions(self) -> None:
        """Reset emotions to baseline values."""
        config_path = self.persona_path / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            baseline = config.get("emotion", {}).get("baseline", {})
        else:
            baseline = {}
        
        self.state_manager.reset_to_baseline(baseline)
    
    def export_state(self) -> Dict[str, Any]:
        """
        Export complete state for backup or transfer.
        
        Returns:
            Dict containing all state information
        """
        return {
            "emotions": self.get_current_emotions(),
            "moments": self._get_all_moments(),
            "persona_path": str(self.persona_path),
            "data_dir": str(self.data_dir)
        }
    
    def import_state(self, state_data: Dict[str, Any]) -> None:
        """
        Import state from backup.
        
        Args:
            state_data: State dict from export_state()
        """
        # Restore emotions
        emotions = state_data.get("emotions", {})
        if emotions:
            self.state_manager.set_emotions(
                affection=emotions.get("affection", 70),
                trust=emotions.get("trust", 80),
                possessiveness=emotions.get("possessiveness", 50),
                patience=emotions.get("patience", 75)
            )
    
    def _build_emotion_prompt(self, state: Dict[str, Any]) -> str:
        """Build emotion modifier prompt."""
        tone_modifiers = self.emotion_calculator.get_tone_modifiers(state)
        
        if not tone_modifiers:
            return ""
        
        intensity = tone_modifiers.get("intensity", "moderate")
        framework = tone_modifiers.get("framework", "")
        dimensions = tone_modifiers.get("dimensions", {})
        
        parts = [
            "# Current Emotional State",
            "",
            f"Intensity: {intensity}",
            "",
            framework
        ]
        
        if dimensions:
            parts.append("\nDimension-specific guidance:")
            for dim, instruction in dimensions.items():
                if instruction:
                    parts.append(f"- {dim}: {instruction}")
        
        return "\n".join(parts)
    
    def _get_recent_moments(self, limit: int = 5) -> str:
        """Get recent relationship moments."""
        moments_path = self.data_dir / "MOMENTS.md"
        if not moments_path.exists():
            return ""
        
        lines = moments_path.read_text().strip().split("\n")
        if lines and lines[0].startswith("#"):
            lines = lines[1:]
        
        recent = lines[-limit:] if len(lines) > limit else lines
        return "\n".join(recent)
    
    def _get_all_moments(self) -> List[str]:
        """Get all relationship moments."""
        moments_path = self.data_dir / "MOMENTS.md"
        if not moments_path.exists():
            return []
        
        lines = moments_path.read_text().strip().split("\n")
        if lines and lines[0].startswith("#"):
            lines = lines[1:]
        
        return [line for line in lines if line.strip()]


class OpenClawMiddleware:
    """
    Middleware for automatic Soul-Link integration in OpenClaw.
    
    Usage:
        from soul_link.integrations.openclaw import OpenClawMiddleware
        
        middleware = OpenClawMiddleware(persona_path="./personas/my-character")
        
        # In your OpenClaw request handler:
        @app.post("/chat")
        async def chat(request: ChatRequest):
            # Pre-process
            system_prompt = middleware.pre_process(request.messages)
            
            # Generate response
            response = await llm.generate(system_prompt, request.messages)
            
            # Post-process
            middleware.post_process(request.messages[-1], response)
            
            return response
    """
    
    def __init__(self, persona_path: str, **kwargs):
        self.adapter = OpenClawAdapter(persona_path, **kwargs)
    
    def pre_process(self, messages: List[Dict[str, str]]) -> str:
        """Pre-process: build system prompt."""
        return self.adapter.build_system_prompt(messages)
    
    def post_process(self, user_message: str, assistant_response: str) -> None:
        """Post-process: update state."""
        self.adapter.process_turn(user_message, assistant_response)

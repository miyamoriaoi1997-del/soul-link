"""Soul-Link configuration management."""

import os
import yaml
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_NAME = "soul-link.yaml"


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "openai"  # openai, anthropic, custom
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class EmotionConfig:
    """Emotion system configuration."""
    enabled: bool = True
    baselines: Dict[str, int] = field(default_factory=lambda: {
        "affection": 50,
        "trust": 50,
        "possessiveness": 30,
        "patience": 60,
    })
    decay_rate: float = 2.0  # points per hour toward baseline
    neural_enabled: bool = False  # requires transformers + torch
    neural_model: str = "Johnson8187/Chinese-Emotion-Small"


@dataclass
class BehaviorConfig:
    """Behavior strategy configuration."""
    enabled: bool = True


@dataclass
class ProactiveChatConfig:
    """Proactive chat configuration."""
    enabled: bool = False
    quiet_hours: List[int] = field(default_factory=lambda: list(range(1, 9)))
    high_affection_interval_hours: float = 2.0
    medium_affection_interval_hours: float = 5.0
    low_affection_interval_hours: float = 8.0
    jitter_percent: float = 20.0


@dataclass
class PlatformConfig:
    """Platform adapter configuration."""
    type: str = "rest"  # rest, telegram, discord
    token: str = ""
    webhook_url: str = ""
    allowed_users: List[str] = field(default_factory=list)


@dataclass
class WebUIConfig:
    """Web UI configuration."""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8765
    secret_key: str = ""


@dataclass
class SoulLinkConfig:
    """Main Soul-Link configuration."""
    persona_dir: str = "./persona"
    data_dir: str = "./data"
    llm: LLMConfig = field(default_factory=LLMConfig)
    emotion: EmotionConfig = field(default_factory=EmotionConfig)
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)
    proactive_chat: ProactiveChatConfig = field(default_factory=ProactiveChatConfig)
    platforms: List[PlatformConfig] = field(default_factory=list)
    web_ui: WebUIConfig = field(default_factory=WebUIConfig)
    agent_names: List[str] = field(default_factory=list)  # names the agent responds to

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SoulLinkConfig":
        config = cls()
        if "persona_dir" in data:
            config.persona_dir = data["persona_dir"]
        if "data_dir" in data:
            config.data_dir = data["data_dir"]
        if "agent_names" in data:
            config.agent_names = data["agent_names"]

        if "llm" in data:
            d = data["llm"]
            config.llm = LLMConfig(
                provider=d.get("provider", "openai"),
                model=d.get("model", "gpt-4o"),
                api_key=d.get("api_key", ""),
                base_url=d.get("base_url", "https://api.openai.com/v1"),
                max_tokens=d.get("max_tokens", 4096),
                temperature=d.get("temperature", 0.7),
            )

        if "emotion" in data:
            d = data["emotion"]
            config.emotion = EmotionConfig(
                enabled=d.get("enabled", True),
                baselines=d.get("baselines", config.emotion.baselines),
                decay_rate=d.get("decay_rate", 2.0),
                neural_enabled=d.get("neural_enabled", False),
                neural_model=d.get("neural_model", "Johnson8187/Chinese-Emotion-Small"),
            )

        if "behavior" in data:
            config.behavior = BehaviorConfig(
                enabled=data["behavior"].get("enabled", True),
            )

        if "proactive_chat" in data:
            d = data["proactive_chat"]
            config.proactive_chat = ProactiveChatConfig(
                enabled=d.get("enabled", False),
                quiet_hours=d.get("quiet_hours", list(range(1, 9))),
                high_affection_interval_hours=d.get("high_affection_interval_hours", 2.0),
                medium_affection_interval_hours=d.get("medium_affection_interval_hours", 5.0),
                low_affection_interval_hours=d.get("low_affection_interval_hours", 8.0),
                jitter_percent=d.get("jitter_percent", 20.0),
            )

        if "platforms" in data:
            config.platforms = []
            for p in data["platforms"]:
                config.platforms.append(PlatformConfig(
                    type=p.get("type", "rest"),
                    token=p.get("token", ""),
                    webhook_url=p.get("webhook_url", ""),
                    allowed_users=p.get("allowed_users", []),
                ))

        if "web_ui" in data:
            d = data["web_ui"]
            config.web_ui = WebUIConfig(
                enabled=d.get("enabled", True),
                host=d.get("host", "0.0.0.0"),
                port=d.get("port", 8765),
                secret_key=d.get("secret_key", ""),
            )

        return config

    @classmethod
    def load(cls, path: Optional[str] = None) -> "SoulLinkConfig":
        """Load config from YAML file."""
        if path is None:
            path = os.environ.get("SOUL_LINK_CONFIG", DEFAULT_CONFIG_NAME)

        path = os.path.expanduser(path)
        if not os.path.exists(path):
            logger.info(f"Config file {path} not found, using defaults")
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to dict for YAML output."""
        result = {
            "persona_dir": self.persona_dir,
            "data_dir": self.data_dir,
            "agent_names": self.agent_names,
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "api_key": self.llm.api_key,
                "base_url": self.llm.base_url,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
            },
            "emotion": {
                "enabled": self.emotion.enabled,
                "baselines": dict(self.emotion.baselines),
                "decay_rate": self.emotion.decay_rate,
                "neural_enabled": self.emotion.neural_enabled,
                "neural_model": self.emotion.neural_model,
            },
            "behavior": {
                "enabled": self.behavior.enabled,
            },
            "proactive_chat": {
                "enabled": self.proactive_chat.enabled,
                "quiet_hours": self.proactive_chat.quiet_hours,
                "high_affection_interval_hours": self.proactive_chat.high_affection_interval_hours,
                "medium_affection_interval_hours": self.proactive_chat.medium_affection_interval_hours,
                "low_affection_interval_hours": self.proactive_chat.low_affection_interval_hours,
                "jitter_percent": self.proactive_chat.jitter_percent,
            },
            "platforms": [
                {
                    "type": p.type,
                    "token": p.token,
                    "webhook_url": p.webhook_url,
                    "allowed_users": p.allowed_users,
                }
                for p in self.platforms
            ],
            "web_ui": {
                "enabled": self.web_ui.enabled,
                "host": self.web_ui.host,
                "port": self.web_ui.port,
            },
        }
        return result

    def save(self, path: Optional[str] = None):
        """Save config to YAML file."""
        if path is None:
            path = DEFAULT_CONFIG_NAME
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)

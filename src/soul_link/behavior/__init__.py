"""Soul-Link behavior strategy system.

Personality-agnostic behavior strategies that describe human emotional
reaction patterns. SOUL.md decides the specific expression.
"""

from soul_link.behavior.strategies import (
    BehaviorStrategy,
    STRATEGIES,
    match_strategy,
)
from soul_link.behavior.controller import BehaviorStrategyController

__all__ = [
    "BehaviorStrategy",
    "STRATEGIES",
    "match_strategy",
    "BehaviorStrategyController",
]

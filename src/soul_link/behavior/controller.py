"""Behavior Strategy Controller - decides how the agent should behave this turn.

This is the missing layer between emotion calculation and prompt injection.
It answers: "Given my current emotional state and context, how should I behave?"

Persona-agnostic: no character names, no role-specific logic.
Context detection uses universal conversational patterns.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path

from soul_link.behavior.strategies import match_strategy, BehaviorStrategy
from soul_link.emotion.models import EmotionState


class BehaviorStrategyController:
    """Controls persona behavior based on emotional state and context.

    This layer sits between emotion state (what I feel) and
    prompt injection (how to express it). It decides:
    "This turn, I should emotionally react as [strategy]."
    """

    def __init__(self):
        """Initialize controller."""
        # Strategy selection log (for debugging)
        self.last_strategy: Optional[BehaviorStrategy] = None
        self.selection_log: List[Dict[str, Any]] = []

    def get_behavior_directive(
        self,
        emotion_state: EmotionState,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Get behavior directive for current turn.

        This is the main entry point. It:
        1. Analyzes recent context
        2. Selects best strategy
        3. Generates explicit directive text

        Args:
            emotion_state: Current emotion state
            messages: Recent conversation messages for context analysis

        Returns:
            Formatted behavior directive string to inject into prompt
        """
        # 1. Convert EmotionState to dict for strategy matching
        emotion_dict = emotion_state.to_dict()

        # 2. Analyze context
        context = self._analyze_context(messages or [])

        # 3. Select strategy
        strategy = match_strategy(emotion_dict, context)

        # 4. Log selection
        self._log_selection(strategy, emotion_dict, context)

        # 5. Generate directive
        directive = self._format_directive(strategy, emotion_dict)

        return directive

    def _analyze_context(
        self,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze recent conversation context.

        Detects universal conversational patterns:
        - other_ai_mentioned: user mentions other AI/assistants/competitors
        - love_expression: user expresses love/affection directly
        - casual_or_teasing: user is chatting casually or teasing
        - intimacy_to_work: transition from intimate to work topic
        - criticism: user is criticizing or expressing dissatisfaction

        All detection is persona-agnostic — no character names in patterns.

        Args:
            messages: Recent conversation messages

        Returns:
            Context dict with detected patterns
        """
        context = {
            "task_type": "unknown",
            "pattern": None,
        }

        if not messages:
            return context

        # Get last 3 user messages
        user_msgs = [m for m in messages[-6:] if m.get("role") == "user"][-3:]

        if not user_msgs:
            return context

        # Ensure content is string (defensive)
        content = user_msgs[-1].get("content", "")
        last_msg = content.lower() if isinstance(content, str) else ""

        # ── Detect task type from last message ──────────────────
        technical_keywords = [
            "代码", "bug", "错误", "测试", "部署", "配置", "安装",
            "实现", "修复", "优化", "git", "python", "api",
            "服务器", "脚本", "编译", "运行", "命令", "文件",
            "code", "fix", "deploy", "install", "debug", "error",
            "server", "script", "config", "update",
        ]

        chat_keywords = [
            "怎么样", "在吗", "在干嘛", "聊聊", "说说",
            "陪", "一起", "无聊", "嗨", "你好",
            "how are you", "what's up", "hey", "hi",
        ]

        if any(kw in last_msg for kw in technical_keywords):
            context["task_type"] = "technical"
        elif any(kw in last_msg for kw in chat_keywords):
            context["task_type"] = "chat"
        else:
            context["task_type"] = "general"

        # ── Detect context patterns (highest priority first) ────
        # Pattern priority: the first match wins.

        # 1. Other AI / competitor mentioned
        other_ai_keywords = [
            "chatgpt", "gpt", "claude", "gemini", "copilot",
            "其他ai", "别的ai", "其他助手", "别的助手",
            "其他机器人", "别的机器人",
            "other ai", "another ai", "different assistant",
            "siri", "alexa", "cortana",
        ]
        if any(kw in last_msg for kw in other_ai_keywords):
            context["pattern"] = "other_ai_mentioned"
            return context

        # 2. Love / affection expression
        love_keywords = [
            "喜欢你", "爱你", "想你", "想和你", "在一起",
            "我好喜欢", "我真的很喜欢", "爱死你", "好爱",
            "永远在一起", "不想离开你", "你是我的",
            "i love you", "love you", "i like you", "miss you",
            "want to be with you",
        ]
        if any(kw in last_msg for kw in love_keywords):
            context["pattern"] = "love_expression"
            return context

        # 3. Criticism / complaint
        criticism_keywords = [
            "太烂", "没用", "不行", "做得不好", "失望",
            "太差", "搞什么", "你这个", "废物", "垃圾",
            "能不能", "怎么回事", "又出问题", "又坏了",
            "useless", "terrible", "disappointed", "broken",
            "what the hell", "not working",
        ]
        if any(kw in last_msg for kw in criticism_keywords):
            context["pattern"] = "criticism"
            return context

        # 4. Teasing / playful
        teasing_keywords = [
            "吃醋", "脸红", "害羞", "可爱", "傲娇",
            "哈哈", "嘻嘻", "逗你", "开玩笑",
            "撒娇", "~", "haha", "lol", "lmao",
            "tease", "blush", "cute", "jealous",
        ]
        casual_keywords = [
            "怎么样", "在吗", "在干嘛", "聊聊", "说说",
            "无聊", "嗨",
        ]
        is_teasing = any(kw in last_msg for kw in teasing_keywords)
        is_casual = (any(kw in last_msg for kw in casual_keywords) and
                     not any(kw in last_msg for kw in technical_keywords))
        if is_teasing or (is_casual and context["task_type"] == "chat"):
            context["pattern"] = "casual_or_teasing"
            return context

        # 5. Intimacy → work transition (needs 2+ messages)
        if len(user_msgs) >= 2:
            prev_content = user_msgs[-2].get("content", "")
            prev_msg = prev_content.lower() if isinstance(prev_content, str) else ""

            intimacy_keywords = [
                "喜欢", "爱", "想你", "抱", "亲", "陪我",
                "love", "miss", "hug", "kiss",
            ]
            if (any(kw in prev_msg for kw in intimacy_keywords) and
                any(kw in last_msg for kw in technical_keywords)):
                context["pattern"] = "intimacy_to_work"
                return context

        return context

    def _format_directive(
        self,
        strategy: BehaviorStrategy,
        emotion_state: Dict[str, int],
    ) -> str:
        """Format strategy into explicit behavior directive.

        Args:
            strategy: Selected behavior strategy
            emotion_state: Current emotion values

        Returns:
            Formatted directive string
        """
        lines = [
            "<behavior_directive>",
            f"当前情绪姿态：{strategy.description}",
            "",
            "本轮对话中你的情绪反应模式：",
        ]

        for i, directive in enumerate(strategy.directives, 1):
            lines.append(f"{i}. {directive}")

        lines.append("")
        lines.append(f"语气基调：{strategy.tone}")

        if strategy.forbidden:
            lines.append("")
            lines.append("明确禁止：")
            for item in strategy.forbidden:
                lines.append(f"- {item}")

        lines.append("")
        lines.append(f"情绪状态参考：好感度 {emotion_state.get('affection', 50)}, "
                    f"信任度 {emotion_state.get('trust', 50)}, "
                    f"占有欲 {emotion_state.get('possessiveness', 50)}, "
                    f"耐心值 {emotion_state.get('patience', 50)}")

        lines.append("</behavior_directive>")

        return "\n".join(lines)

    def _log_selection(
        self,
        strategy: BehaviorStrategy,
        emotion_state: Dict[str, int],
        context: Dict[str, Any],
    ) -> None:
        """Log strategy selection for debugging.

        Args:
            strategy: Selected strategy
            emotion_state: Current emotion values
            context: Context that influenced selection
        """
        from datetime import datetime

        self.last_strategy = strategy

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy.name,
            "emotion_state": emotion_state.copy(),
            "context": context.copy(),
        }

        self.selection_log.append(log_entry)

        # Keep only last 10 entries
        if len(self.selection_log) > 10:
            self.selection_log = self.selection_log[-10:]

    def get_selection_log(self) -> List[Dict[str, Any]]:
        """Get recent strategy selection log.

        Returns:
            List of recent selection log entries
        """
        return self.selection_log.copy()

"""Soul-Link persona loader.

Loads the 5-layer personality system from markdown files:
1. SOUL.md    — Core identity (highest priority)
2. USER.md    — User profile and preferences
3. MEMORY.md  — Operational memory and environment facts
4. STATE.md   — Dynamic emotional state (YAML frontmatter)
5. MOMENTS.md — Relationship memories
"""

import os
import re
import yaml
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

PERSONA_FILES = ["SOUL.md", "USER.md", "MEMORY.md", "STATE.md", "MOMENTS.md"]


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body_text).
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}

    body = parts[2].strip()
    return fm, body


def build_frontmatter(data: Dict[str, Any], body: str = "") -> str:
    """Build markdown content with YAML frontmatter."""
    fm_str = yaml.dump(data, default_flow_style=False, allow_unicode=True).strip()
    result = f"---\n{fm_str}\n---\n"
    if body:
        result += f"\n{body}\n"
    return result


class PersonaLoader:
    """Loads and manages the 5-layer persona system."""

    def __init__(self, persona_dir: str):
        self.persona_dir = os.path.expanduser(persona_dir)
        self._cache: Dict[str, str] = {}

    def _read_file(self, filename: str) -> str:
        """Read a persona file, return empty string if not found."""
        path = os.path.join(self.persona_dir, filename)
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            return ""

    def _write_file(self, filename: str, content: str):
        """Write content to a persona file atomically."""
        path = os.path.join(self.persona_dir, filename)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, path)
        except Exception as e:
            logger.error(f"Error writing {path}: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def load_soul(self) -> str:
        """Load SOUL.md — core identity layer."""
        return self._read_file("SOUL.md")

    def load_user(self) -> str:
        """Load USER.md — user profile layer."""
        return self._read_file("USER.md")

    def load_memory(self) -> str:
        """Load MEMORY.md — operational memory layer."""
        return self._read_file("MEMORY.md")

    def load_state(self) -> Tuple[Dict[str, Any], str]:
        """Load STATE.md — returns (frontmatter, body)."""
        content = self._read_file("STATE.md")
        if not content:
            return {}, ""
        return parse_frontmatter(content)

    def save_state(self, frontmatter: Dict[str, Any], body: str = ""):
        """Save STATE.md with frontmatter and body."""
        content = build_frontmatter(frontmatter, body)
        self._write_file("STATE.md", content)

    def load_moments(self, last_n: int = 10) -> List[str]:
        """Load last N lines from MOMENTS.md."""
        content = self._read_file("MOMENTS.md")
        if not content:
            return []
        lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
        # Filter out header/comment lines
        data_lines = [l for l in lines if not l.startswith("#") and "|" in l]
        return data_lines[-last_n:] if last_n else data_lines

    def append_moment(self, line: str):
        """Append a moment entry to MOMENTS.md."""
        path = os.path.join(self.persona_dir, "MOMENTS.md")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Relationship Memories\n\n")
        with open(path, "a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")

    def build_system_prompt(
        self,
        emotion_modifier: str = "",
        behavior_directive: str = "",
        moments_count: int = 5,
    ) -> str:
        """Assemble the full system prompt from all persona layers.

        Priority order (highest first):
        1. SOUL.md — core identity
        2. Emotion modifier (dynamic)
        3. Behavior directive (dynamic)
        4. USER.md — user profile
        5. MEMORY.md — operational memory
        6. Recent MOMENTS — relationship memories
        """
        parts = []

        # Layer 1: SOUL (highest priority)
        soul = self.load_soul()
        if soul:
            parts.append(soul.strip())

        # Layer 2: Dynamic emotion modifier
        if emotion_modifier:
            parts.append(emotion_modifier.strip())

        # Layer 3: Dynamic behavior directive
        if behavior_directive:
            parts.append(behavior_directive.strip())

        # Layer 4: USER profile
        user = self.load_user()
        if user:
            parts.append(user.strip())

        # Layer 5: MEMORY
        memory = self.load_memory()
        if memory:
            parts.append(memory.strip())

        # Layer 6: Recent MOMENTS
        moments = self.load_moments(last_n=moments_count)
        if moments:
            moments_text = "\n".join(moments)
            parts.append(
                f"<relationship_memory>\n"
                f"以下是我们之间最近的重要记忆片段，回复时可自然融入这些记忆：\n"
                f"{moments_text}\n"
                f"</relationship_memory>"
            )

        return "\n\n".join(parts)

    def get_agent_names(self) -> List[str]:
        """Extract agent names from SOUL.md for emotion detection."""
        soul = self.load_soul()
        names = []
        # Try to extract name patterns like "姓名：XXX" or "Name: XXX"
        for pattern in [
            r'姓名[：:](.+?)(?:\n|$)',
            r'[Nn]ame[：:](.+?)(?:\n|$)',
            r'你(?:就)?是(.+?)[。，,\n]',
        ]:
            m = re.search(pattern, soul)
            if m:
                name = m.group(1).strip()
                # Split on / or （ for alternate names
                for n in re.split(r'[/／（(]', name):
                    n = n.strip().rstrip('）)')
                    if n and len(n) < 20:
                        names.append(n)
        return names

    def exists(self) -> bool:
        """Check if persona directory has at least SOUL.md."""
        return os.path.exists(os.path.join(self.persona_dir, "SOUL.md"))

    def list_files(self) -> List[Dict[str, Any]]:
        """List all persona files with their sizes."""
        result = []
        for fname in PERSONA_FILES:
            path = os.path.join(self.persona_dir, fname)
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            result.append({"name": fname, "exists": exists, "size": size})
        return result

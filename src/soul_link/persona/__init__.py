"""Soul-Link persona system.

5-layer personality architecture:
1. SOUL    — Core identity
2. USER    — User profile
3. MEMORY  — Operational memory
4. STATE   — Dynamic emotional state
5. MOMENTS — Relationship memories
"""

from soul_link.persona.loader import PersonaLoader, parse_frontmatter, build_frontmatter

__all__ = [
    "PersonaLoader",
    "parse_frontmatter",
    "build_frontmatter",
]

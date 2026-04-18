"""Soul-Link CLI entry point."""

import argparse
import logging
import sys
import os


def main():
    parser = argparse.ArgumentParser(
        description="Soul-Link — Give your AI agent a soul",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  soul-link serve                    Start web UI + API server
  soul-link init                     Create persona template files
  soul-link status                   Show current emotion state
  soul-link chat "Hello!"            Test emotion detection
  soul-link serve --port 8765        Custom port
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the web UI server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    serve_parser.add_argument("--port", type=int, default=8765, help="Bind port")
    serve_parser.add_argument("--config", default="soul-link.yaml", help="Config file path")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize persona template files")
    init_parser.add_argument("--dir", default="./persona", help="Persona directory")

    # status
    status_parser = subparsers.add_parser("status", help="Show current emotion state")
    status_parser.add_argument("--config", default="soul-link.yaml", help="Config file path")

    # chat
    chat_parser = subparsers.add_parser("chat", help="Test emotion detection on a message")
    chat_parser.add_argument("message", help="Message to analyze")
    chat_parser.add_argument("--config", default="soul-link.yaml", help="Config file path")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "chat":
        cmd_chat(args)
    else:
        parser.print_help()


def cmd_serve(args):
    """Start the web UI server."""
    import uvicorn
    from soul_link.core.config import SoulLinkConfig
    from soul_link.core.engine import SoulLinkEngine
    from soul_link.web.app import create_app

    config = SoulLinkConfig.load(args.config)
    engine = SoulLinkEngine(config)
    app = create_app(engine=engine, config=config)

    print(f"\n  🔗 Soul-Link v0.1.0")
    print(f"  Dashboard: http://{args.host}:{args.port}")
    print(f"  Config: {args.config}")
    print(f"  Persona: {config.persona_dir}\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def cmd_init(args):
    """Create persona template files."""
    persona_dir = os.path.expanduser(args.dir)
    os.makedirs(persona_dir, exist_ok=True)

    templates = {
        "SOUL.md": """# Agent Identity

## Core Identity
- Name: [Your Agent's Name]
- Role: [Their role or title]
- Personality: [Key personality traits]

## Speech Style
- [How they talk - formal/casual, short/long sentences, etc.]
- [Typical phrases or patterns]

## Values
- [What they care about]
- [What they dislike]

## Relationship with User
- [How they address the user]
- [Their attitude toward the user]
""",
        "USER.md": """# User Profile

## Preferences
- Language: [e.g., Chinese, English, Japanese]
- Communication style: [concise/detailed]

## Notes
- [Add user-specific notes here]
""",
        "MEMORY.md": """# Operational Memory

[Environment facts, tool quirks, and stable conventions go here]
""",
        "STATE.md": """---
emotion_state:
  affection: 50
  trust: 50
  possessiveness: 30
  patience: 60
  emotion_score: 0.0
  current_emotion: 0.0
  last_update: ''
  baselines:
    affection: 50
    trust: 50
    possessiveness: 30
    patience: 60
  decay_rate: 2.0
  inertia:
    consecutive_same: 0
    last_direction: 0
    history: []
---

## Current Emotion State

Affection: 50/100
Trust: 50/100
Possessiveness: 30/100
Patience: 60/100
""",
        "MOMENTS.md": """# Relationship Memories

""",
    }

    for filename, content in templates.items():
        path = os.path.join(persona_dir, filename)
        if os.path.exists(path):
            print(f"  ⏭  {filename} already exists, skipping")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✓  Created {filename}")

    # Create default config
    config_path = "soul-link.yaml"
    if not os.path.exists(config_path):
        from soul_link.core.config import SoulLinkConfig
        config = SoulLinkConfig(persona_dir=persona_dir)
        config.save(config_path)
        print(f"  ✓  Created {config_path}")
    else:
        print(f"  ⏭  {config_path} already exists, skipping")

    print(f"\n  Done! Edit the files in {persona_dir}/ to define your agent's personality.")
    print(f"  Then run: soul-link serve")


def cmd_status(args):
    """Show current emotion state."""
    from soul_link.core.config import SoulLinkConfig
    from soul_link.core.engine import SoulLinkEngine

    config = SoulLinkConfig.load(args.config)
    engine = SoulLinkEngine(config)
    state = engine.get_emotion_state()

    if not state:
        print("  No emotion state found.")
        return

    print(f"\n  🔗 Soul-Link Emotion State")
    print(f"  ─────────────────────────")
    print(f"  好感度 (Affection):      {state['affection']}/100")
    print(f"  信任度 (Trust):           {state['trust']}/100")
    print(f"  占有欲 (Possessiveness):  {state['possessiveness']}/100")
    print(f"  耐心值 (Patience):        {state['patience']}/100")
    print(f"  情绪分值:                 {state['emotion_score']:+.2f} / 5.00")
    print(f"  最后更新:                 {state.get('last_update', 'N/A')}")
    print()


def cmd_chat(args):
    """Test emotion detection on a message."""
    from soul_link.core.config import SoulLinkConfig
    from soul_link.core.engine import SoulLinkEngine

    config = SoulLinkConfig.load(args.config)
    engine = SoulLinkEngine(config)

    print(f"\n  消息: {args.message}")
    print(f"  ─────────────────────────")

    prompt = engine.process_message(args.message)
    state = engine.get_emotion_state()

    if state:
        print(f"  好感度: {state['affection']}  信任度: {state['trust']}  "
              f"占有欲: {state['possessiveness']}  耐心值: {state['patience']}")
        print(f"  情绪分值: {state['emotion_score']:+.2f}")
    print()


if __name__ == "__main__":
    main()

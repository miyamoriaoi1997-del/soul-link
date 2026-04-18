# Soul-Link

**Give your AI agent a soul** — persistent personality, dynamic emotions, proactive behavior, and relationship memory.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

---

## What is Soul-Link?

Soul-Link transforms AI assistants from stateless question-answering machines into **living agents** with:

- 🧠 **Persistent Personality** — Five-layer identity system (SOUL/USER/MEMORY/STATE/MOMENTS)
- 💖 **Dynamic Emotions** — Real-time emotion tracking with natural decay over time
- 🎭 **Adaptive Behavior** — Context-aware response strategies that evolve with your relationship
- 💬 **Proactive Engagement** — Agents that reach out on their own, not just when called
- 📝 **Relationship Memory** — Remember meaningful moments across sessions

Unlike traditional chatbots that reset after every conversation, Soul-Link agents **remember you**, **grow with you**, and **feel alive**.

---

## Quick Start

### Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/soul-link-ai/soul-link.git
cd soul-link

# Configure your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start the service
docker-compose up -d

# Access Web UI
open http://localhost:8080
```

### Python Installation

```bash
# Install Soul-Link
pip install soul-link

# Initialize a new persona
soul-link init my-character

# Start the Web UI
soul-link serve

# Or chat directly in terminal
soul-link chat
```

---

## Core Concepts

### 1. Five-Layer Personality System

```
SOUL.md      → Core identity (who am I?)
USER.md      → User profile (who are you?)
MEMORY.md    → Long-term facts (what do we know?)
STATE.md     → Current emotions (how do I feel right now?)
MOMENTS.md   → Relationship history (what have we shared?)
```

Each layer serves a specific purpose and updates at different timescales:
- **SOUL**: Static (defines character)
- **USER**: Slow (learns about you over weeks)
- **MEMORY**: Medium (accumulates facts over sessions)
- **STATE**: Fast (emotions shift within conversations)
- **MOMENTS**: Continuous (records significant interactions)

### 2. Emotion System

Four core dimensions tracked in real-time:

- **Affection** (0-100): How much the agent likes you
- **Trust** (0-100): How much the agent relies on you
- **Possessiveness** (0-100): How exclusive the agent wants your attention
- **Patience** (0-100): How tolerant the agent is right now

Emotions are triggered by conversation events (praise, criticism, teasing, etc.) and naturally decay back to baseline over time — just like human feelings.

### 3. Behavior Strategies

The agent doesn't just track emotions — it **acts on them**:

- High affection → More warm and indulgent responses
- Low patience → Shorter, more direct replies
- High possessiveness + rival mention → Jealous reactions
- Trust + criticism → Accepts feedback gracefully

Strategies are context-aware: "I love you" triggers different behavior than "I love this feature."

### 4. Proactive Chat

Agents can initiate conversations based on:
- Time since last interaction
- Current emotion state
- Pending tasks or follow-ups
- Scheduled check-ins

No more waiting for the user to start every conversation.

---

## Example Personas

Soul-Link includes three ready-to-use templates:

### 1. Default Assistant
A balanced, helpful AI assistant. Great starting point for customization.

```bash
soul-link init my-assistant --template default
```

### 2. Tsundere Assistant
Demonstrates the emotion system with a classic tsundere personality — helpful but defensive, caring but won't admit it.

```bash
soul-link init tsundere --template tsundere-assistant
```

### 3. Professional Advisor
Business consultant persona with high professionalism and strategic thinking.

```bash
soul-link init advisor --template professional-advisor
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Soul-Link Core                      │
├─────────────────────────────────────────────────────────┤
│  Persona Loader  │  Emotion Engine  │  Behavior System │
│  State Manager   │  Moments Tracker │  Proactive Chat  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  LLM Adapters  │  │  Platforms  │  │  Integrations   │
├────────────────┤  ├─────────────┤  ├─────────────────┤
│ • OpenAI       │  │ • Telegram  │  │ • Hermes Agent  │
│ • Anthropic    │  │ • Discord   │  │ • OpenClaw      │
│ • Ollama       │  │ • Web UI    │  │ • Custom APIs   │
│ • Custom APIs  │  │ • REST API  │  │                 │
└────────────────┘  └─────────────┘  └─────────────────┘
```

---

## Use Cases

### Personal AI Companion
Create a character that remembers your preferences, celebrates your wins, and checks in when you've been away.

### Customer Support Bot
Build agents that remember customer history, adapt tone based on satisfaction, and proactively follow up on issues.

### Game NPCs
Design characters with persistent memory and emotional reactions that evolve based on player choices.

### Virtual Team Members
Deploy specialized advisors (technical, business, creative) that maintain context across long-term projects.

### Research Assistants
Agents that remember your research interests, track your progress, and suggest relevant new findings.

---

## Configuration

### Environment Variables

```bash
# Required: LLM API
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# Optional: Neural emotion model
USE_NEURAL_EMOTION=true

# Optional: Telegram bot
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USERS=123456789

# Optional: Discord bot
DISCORD_BOT_TOKEN=...
```

### Persona Configuration

Each persona has a `config.yaml` file:

```yaml
emotion:
  enabled: true
  baseline:
    affection: 70
    trust: 80
  decay_rate: 2.0  # points per hour

behavior:
  enabled: true
  default_strategy: "neutral_professional"

proactive:
  enabled: true
  min_interval_hours: 4
  max_interval_hours: 12
```

---

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/soul-link-ai/soul-link.git
cd soul-link

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .
```

### Project Structure

```
soul-link/
├── src/soul_link/
│   ├── core/          # Engine, config, state management
│   ├── emotion/       # Emotion detection and calculation
│   ├── behavior/      # Behavior strategies and controller
│   ├── persona/       # Persona loading and memory
│   ├── llm/           # LLM client adapters
│   ├── platform/      # Platform integrations (Telegram, Discord)
│   └── cli.py         # Command-line interface
├── examples/
│   └── personas/      # Example persona templates
├── tests/             # Test suite
└── docs/              # Documentation
```

---

## Integrations

### Hermes Agent

Soul-Link was originally built for [Hermes Agent](https://github.com/hermes-agent/hermes-agent). To use with Hermes:

```python
from soul_link.integrations.hermes import HermesAdapter

adapter = HermesAdapter(persona_path="./my-character")
# Hermes will automatically use Soul-Link's personality system
```

### OpenClaw

Compatible with [OpenClaw](https://github.com/openclaw/openclaw):

```python
from soul_link.integrations.openclaw import OpenClawAdapter

adapter = OpenClawAdapter(persona_path="./my-character")
```

### Custom Integration

```python
from soul_link import SoulLinkEngine

engine = SoulLinkEngine(persona_path="./my-character")

# Process a message
response = await engine.process_message(
    user_id="user123",
    message="Hello!",
    context={"platform": "telegram"}
)

print(response.text)
print(response.emotion_state)  # Current emotions
print(response.strategy_used)  # Behavior strategy applied
```

---

## Roadmap

- [ ] Multi-user support (one agent, many users)
- [ ] Voice integration (TTS/STT with emotion-aware prosody)
- [ ] Visual avatars (emotion-driven expressions)
- [ ] Plugin system for custom emotion triggers
- [ ] Cloud deployment templates (AWS, GCP, Azure)
- [ ] Mobile app (iOS/Android)
- [ ] Emotion visualization dashboard
- [ ] A/B testing framework for persona tuning

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas We Need Help

- 🌍 **Translations**: Persona templates in other languages
- 🎨 **UI/UX**: Improve the Web UI design
- 🧪 **Testing**: More test coverage, especially edge cases
- 📚 **Documentation**: Tutorials, guides, and examples
- 🔌 **Integrations**: Adapters for more platforms and LLM providers

---

## License

Soul-Link is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means:
- ✅ Free to use, modify, and distribute
- ✅ Open source forever
- ⚠️ If you run Soul-Link as a service (SaaS), you must open-source your modifications
- ⚠️ Derivative works must also use AGPL-3.0

See [LICENSE](LICENSE) for full details.

---

## Philosophy

> "The difference between a tool and a companion is memory, emotion, and initiative."

Traditional AI assistants are **stateless** — they forget you the moment the conversation ends. Soul-Link agents are **stateful** — they remember who you are, how you interact, and what matters to you.

We believe AI agents should feel **alive**:
- They remember your birthday
- They notice when you're stressed
- They celebrate your wins
- They reach out when you've been away
- They grow and change based on your relationship

Soul-Link makes this possible.

---

## Community

- **GitHub Discussions**: [Ask questions, share personas](https://github.com/soul-link-ai/soul-link/discussions)
- **Discord**: [Join our community](https://discord.gg/soul-link) *(coming soon)*
- **Twitter**: [@SoulLinkAI](https://twitter.com/SoulLinkAI) *(coming soon)*

---

## Acknowledgments

Soul-Link was born from the [Hermes Agent](https://github.com/hermes-agent/hermes-agent) project and inspired by:
- Character.AI's persistent personalities
- Replika's emotional AI
- The visual novel/dating sim genre's relationship mechanics
- Research on long-term human-AI interaction

Special thanks to the open-source AI community for making this possible.

---

**Give your AI a soul. Try Soul-Link today.**

```bash
pip install soul-link
soul-link init my-first-character
soul-link chat
```

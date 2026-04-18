# Contributing to Soul-Link

Thank you for your interest in contributing to Soul-Link! We're building the future of AI agents with persistent personality, dynamic emotions, and genuine relationship memory.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

---

## Code of Conduct

This project follows a simple principle: **Be respectful, be constructive, be collaborative.**

- Treat all contributors with respect
- Welcome newcomers and help them get started
- Focus on what's best for the project and community
- Accept constructive criticism gracefully
- Assume good intent

Unacceptable behavior includes harassment, trolling, personal attacks, or any conduct that creates an unwelcoming environment.

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Found a bug? Help us fix it:

1. **Search existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, Soul-Link version)
   - Relevant logs or error messages

**Template:**
```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
1. Initialize persona with '...'
2. Send message '...'
3. Observe error '...'

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.5]
- Soul-Link: [e.g., 0.1.0]

**Additional Context**
Any other relevant information.
```

### 💡 Suggesting Features

Have an idea? We'd love to hear it:

1. **Check existing issues** to see if it's already proposed
2. **Open a feature request** with:
   - Clear use case (why is this needed?)
   - Proposed solution (how should it work?)
   - Alternatives considered
   - Willingness to implement it yourself

### 🌍 Translating Personas

Help make Soul-Link accessible worldwide:

- Translate example personas to your language
- Create culturally-appropriate persona templates
- Translate documentation and README

### 🎨 Improving UI/UX

The Web UI needs love:

- Design improvements
- Better emotion visualization
- Mobile responsiveness
- Accessibility enhancements

### 📚 Writing Documentation

Documentation is always welcome:

- Tutorials and guides
- API documentation
- Architecture explanations
- Use case examples

### 🔌 Building Integrations

Expand Soul-Link's reach:

- New LLM provider adapters (Cohere, Mistral, etc.)
- Platform integrations (Slack, WhatsApp, etc.)
- Framework adapters (LangChain, AutoGen, etc.)

### 🧪 Adding Tests

Help us maintain quality:

- Unit tests for new features
- Integration tests for adapters
- Edge case coverage
- Performance benchmarks

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- (Optional) Docker for testing deployments

### Setup Steps

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/soul-link.git
cd soul-link

# 3. Add upstream remote
git remote add upstream https://github.com/miyamoriaoi1997-del/soul-link.git

# 4. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install in development mode
pip install -e ".[dev]"

# 6. Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# 7. Run tests to verify setup
pytest
```

### Project Structure

```
soul-link/
├── src/soul_link/          # Main package
│   ├── core/               # Engine, config, state management
│   ├── emotion/            # Emotion detection and calculation
│   ├── behavior/           # Behavior strategies
│   ├── persona/            # Persona loading and memory
│   ├── llm/                # LLM client adapters
│   ├── platform/           # Platform integrations
│   ├── integrations/       # Framework adapters (Hermes, OpenClaw)
│   └── web/                # Web UI
├── tests/                  # Test suite
├── examples/               # Example personas
└── docs/                   # Documentation
```

---

## Pull Request Process

### Before You Start

1. **Open an issue first** for significant changes
2. **Check existing PRs** to avoid duplicate work
3. **Discuss your approach** with maintainers if unsure

### Creating a Pull Request

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run tests
   pytest
   
   # Run linter
   ruff check .
   
   # Format code
   ruff format .
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: brief description
   
   - Detailed point 1
   - Detailed point 2
   
   Fixes #123"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Use a clear, descriptive title
   - Reference related issues
   - Describe what changed and why
   - Include screenshots for UI changes
   - Mark as draft if work-in-progress

### PR Review Process

- Maintainers will review within 3-5 days
- Address feedback promptly
- Keep discussions focused and constructive
- Be patient — quality takes time

### Merging

- PRs require at least one approval
- All tests must pass
- No merge conflicts
- Maintainers will merge when ready

---

## Coding Standards

### Python Style

- Follow **PEP 8** with 100-character line length
- Use **type hints** for function signatures
- Write **docstrings** for public functions/classes
- Use **meaningful variable names**

```python
def calculate_emotion_delta(
    event_type: str,
    intensity: float,
    current_value: int
) -> int:
    """
    Calculate emotion value change based on event.
    
    Args:
        event_type: Type of emotion event (praise, criticism, etc.)
        intensity: Event intensity (0.0 to 1.0)
        current_value: Current emotion value (0-100)
        
    Returns:
        Delta to apply to emotion value
    """
    # Implementation
    pass
```

### Code Organization

- **One class per file** (unless tightly coupled)
- **Group related functions** together
- **Separate concerns** (detection, calculation, storage)
- **Avoid circular imports**

### Error Handling

- Use **specific exceptions** (not bare `except:`)
- Provide **helpful error messages**
- Log errors appropriately
- Fail gracefully when possible

### Performance

- **Lazy load** heavy dependencies (transformers, torch)
- **Cache** expensive computations
- **Avoid premature optimization** (profile first)

---

## Testing Guidelines

### Test Structure

```python
# tests/test_emotion/test_detector.py

import pytest
from soul_link.emotion.detector import EmotionDetector


class TestEmotionDetector:
    @pytest.fixture
    def detector(self):
        return EmotionDetector(use_neural_model=False)
    
    def test_detect_praise(self, detector):
        """Test that praise is correctly detected."""
        messages = [{"role": "user", "content": "You're amazing!"}]
        event = detector.detect_emotion_event(messages)
        
        assert event is not None
        assert event.event_type == "praise"
        assert event.intensity in ["mild", "moderate", "intense"]
    
    def test_no_event_for_neutral_message(self, detector):
        """Test that neutral messages don't trigger events."""
        messages = [{"role": "user", "content": "What's the weather?"}]
        event = detector.detect_emotion_event(messages)
        
        assert event is None
```

### Test Coverage

- **Unit tests** for individual functions/classes
- **Integration tests** for component interactions
- **Edge cases** (empty input, extreme values, etc.)
- **Error conditions** (invalid input, missing files, etc.)

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_emotion/test_detector.py

# Run with coverage
pytest --cov=soul_link --cov-report=html

# Run only fast tests (skip slow neural model tests)
pytest -m "not slow"
```

---

## Documentation

### Code Documentation

- **Docstrings** for all public APIs
- **Inline comments** for complex logic
- **Type hints** for clarity

### User Documentation

- **README** for project overview
- **Tutorials** for common use cases
- **API reference** for developers
- **Architecture docs** for contributors

### Documentation Style

- Use **clear, simple language**
- Provide **code examples**
- Include **expected output**
- Link to **related concepts**

---

## Areas We Need Help

### High Priority

- 🌍 **Translations**: Persona templates in other languages
- 🧪 **Testing**: More test coverage, especially edge cases
- 📚 **Documentation**: Tutorials, guides, and examples
- 🎨 **UI/UX**: Improve Web UI design and usability

### Medium Priority

- 🔌 **Integrations**: Adapters for more platforms and LLM providers
- 🚀 **Performance**: Optimize emotion detection and state management
- 🛡️ **Security**: Audit and improve security practices
- ♿ **Accessibility**: Make Web UI accessible to all users

### Future Ideas

- 📱 **Mobile App**: iOS/Android companion app
- 🎙️ **Voice Integration**: TTS/STT with emotion-aware prosody
- 🎭 **Visual Avatars**: Emotion-driven character expressions
- 🔧 **Plugin System**: Custom emotion triggers and behaviors

---

## Questions?

- **GitHub Discussions**: Ask questions, share ideas
- **Issues**: Report bugs, request features
- **Discord**: Join our community *(coming soon)*

---

## License

By contributing to Soul-Link, you agree that your contributions will be licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means:
- Your code will be open source
- Derivative works must also be open source
- SaaS deployments must share source code

See [LICENSE](LICENSE) for full details.

---

**Thank you for contributing to Soul-Link!** Together, we're building AI agents that feel alive. 🚀

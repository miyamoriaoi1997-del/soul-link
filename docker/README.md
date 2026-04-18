# Soul-Link Docker Deployment Guide

## Quick Start

### 1. Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### 2. Configuration

Create a `.env` file in the project root:

```bash
# Required: LLM API Configuration
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# Optional: Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ALLOWED_USERS=123456789,987654321

# Optional: Discord Bot
DISCORD_BOT_TOKEN=your-discord-token
DISCORD_ALLOWED_GUILDS=guild-id-1,guild-id-2

# Optional: Neural Emotion Model
USE_NEURAL_EMOTION=false

# Optional: Logging
LOG_LEVEL=INFO
```

### 3. Start the Service

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### 4. Access Web UI

Open http://localhost:8080 in your browser.

## Directory Structure

```
soul-link/
├── data/              # Persistent data (auto-created)
│   ├── personas/      # Persona files (SOUL.md, USER.md, etc.)
│   ├── cache/         # Session cache
│   └── logs/          # Application logs
├── examples/
│   └── personas/      # Example persona templates
└── docker-compose.yml
```

## Custom Personas

Place your persona files in `./data/personas/your-character/`:

```
data/personas/my-character/
├── SOUL.md      # Core personality
├── USER.md      # User profile
├── MEMORY.md    # Long-term memory
└── config.yaml  # Character-specific config
```

## Advanced Configuration

### Use Custom Base Image

Edit `Dockerfile` to use a different Python version:

```dockerfile
FROM python:3.12-slim as builder
```

### Enable Neural Emotion Model

Uncomment the `emotion-model` service in `docker-compose.yml` and set:

```bash
USE_NEURAL_EMOTION=true
```

### Expose Additional Ports

Add to `docker-compose.yml`:

```yaml
ports:
  - "8080:8080"  # Web UI
  - "8090:8090"  # Additional API endpoint
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs soul-link
```

### Permission issues

Ensure data directory is writable:
```bash
chmod -R 755 ./data
```

### API connection fails

Verify environment variables:
```bash
docker-compose exec soul-link env | grep OPENAI
```

## Production Deployment

### Use Docker Swarm or Kubernetes

For production, consider:
- Reverse proxy (nginx/Traefik) with SSL
- Persistent volume for `/data`
- Health check monitoring
- Log aggregation (ELK/Loki)

### Security Recommendations

1. Never commit `.env` file
2. Use secrets management (Docker secrets, Vault)
3. Restrict network access with firewall rules
4. Enable HTTPS for Web UI
5. Regularly update base images

## Building from Source

```bash
# Build image
docker build -t soul-link:latest .

# Run without compose
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/data:/data \
  -e OPENAI_API_KEY=your-key \
  soul-link:latest
```

## Multi-Architecture Support

Build for ARM64 (e.g., Raspberry Pi):

```bash
docker buildx build --platform linux/arm64 -t soul-link:arm64 .
```

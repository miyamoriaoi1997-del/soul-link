"""Soul-Link Web UI — configuration and monitoring dashboard.

Provides a web interface for:
- Editing persona files (SOUL/USER/MEMORY)
- Viewing/adjusting emotion state
- Configuring LLM and platform settings
- Viewing relationship moments
- Real-time emotion monitoring
"""

import os
import logging
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from soul_link.core.config import SoulLinkConfig
from soul_link.core.engine import SoulLinkEngine

logger = logging.getLogger(__name__)

# Paths
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


def create_app(engine: Optional[SoulLinkEngine] = None, config: Optional[SoulLinkConfig] = None) -> FastAPI:
    """Create the FastAPI application."""

    app = FastAPI(
        title="Soul-Link",
        description="AI Agent Personality & Emotion System",
        version="0.1.0",
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # Store engine reference
    app.state.engine = engine
    app.state.config = config or (engine.config if engine else SoulLinkConfig())

    # ── Pages ──

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "title": "Soul-Link Dashboard",
        })

    # ── API: Config ──

    @app.get("/api/config")
    async def get_config():
        cfg = app.state.config
        data = cfg.to_dict()
        # Mask API key
        if data.get("llm", {}).get("api_key"):
            key = data["llm"]["api_key"]
            data["llm"]["api_key"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        return data

    class ConfigUpdate(BaseModel):
        config: dict

    @app.post("/api/config")
    async def update_config(update: ConfigUpdate):
        try:
            eng = app.state.engine
            if eng:
                eng.update_config(update.config)
                eng.config.save()
            return {"status": "ok"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ── API: Persona Files ──

    @app.get("/api/persona/{filename}")
    async def get_persona_file(filename: str):
        if filename not in ["SOUL.md", "USER.md", "MEMORY.md", "STATE.md", "MOMENTS.md"]:
            raise HTTPException(status_code=400, detail="Invalid filename")
        eng = app.state.engine
        if not eng:
            raise HTTPException(status_code=503, detail="Engine not initialized")
        content = eng.get_persona_file(filename)
        return {"filename": filename, "content": content}

    class PersonaUpdate(BaseModel):
        content: str

    @app.post("/api/persona/{filename}")
    async def update_persona_file(filename: str, update: PersonaUpdate):
        if filename not in ["SOUL.md", "USER.md", "MEMORY.md"]:
            raise HTTPException(status_code=400, detail="Cannot edit this file directly")
        eng = app.state.engine
        if not eng:
            raise HTTPException(status_code=503, detail="Engine not initialized")
        eng.update_persona_file(filename, update.content)
        return {"status": "ok", "filename": filename}

    @app.get("/api/persona")
    async def list_persona_files():
        eng = app.state.engine
        if not eng:
            return {"files": []}
        return {"files": eng.persona.list_files()}

    # ── API: Emotion State ──

    @app.get("/api/emotion")
    async def get_emotion_state():
        eng = app.state.engine
        if not eng:
            return {"state": None}
        return {"state": eng.get_emotion_state()}

    class EmotionOverride(BaseModel):
        affection: Optional[int] = None
        trust: Optional[int] = None
        possessiveness: Optional[int] = None
        patience: Optional[int] = None

    @app.post("/api/emotion")
    async def override_emotion(override: EmotionOverride):
        eng = app.state.engine
        if not eng or not eng._current_state:
            raise HTTPException(status_code=503, detail="Emotion system not active")
        if override.affection is not None:
            eng._current_state.affection = max(0, min(100, override.affection))
        if override.trust is not None:
            eng._current_state.trust = max(0, min(100, override.trust))
        if override.possessiveness is not None:
            eng._current_state.possessiveness = max(0, min(100, override.possessiveness))
        if override.patience is not None:
            eng._current_state.patience = max(0, min(100, override.patience))
        eng._save_state()
        return {"status": "ok", "state": eng.get_emotion_state()}

    # ── API: Moments ──

    @app.get("/api/moments")
    async def get_moments(count: int = 20):
        eng = app.state.engine
        if not eng:
            return {"moments": []}
        return {"moments": eng.get_recent_moments(count=count)}

    # ── API: Chat (for testing) ──

    class ChatMessage(BaseModel):
        message: str

    @app.post("/api/chat")
    async def chat_test(msg: ChatMessage):
        """Test endpoint — processes message through emotion/behavior pipeline."""
        eng = app.state.engine
        if not eng:
            raise HTTPException(status_code=503, detail="Engine not initialized")
        prompt = eng.process_message(msg.message)
        state = eng.get_emotion_state()
        return {
            "system_prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "emotion_state": state,
        }

    return app

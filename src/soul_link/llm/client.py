"""Soul-Link LLM adapter.

Provides a unified interface for LLM calls via OpenAI-compatible API.
Works with any OpenAI-compatible endpoint (OpenAI, Anthropic via proxy,
local models via vLLM/llama.cpp, etc.)
"""

import logging
from typing import Dict, Any, Optional, List, AsyncIterator

import httpx

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI-compatible LLM client.

    Supports any endpoint that follows the OpenAI chat completions API format.

    Usage:
        client = LLMClient(
            api_key="sk-...",
            base_url="https://api.openai.com/v1",
            model="gpt-4o",
        )
        response = client.chat("Hello!", system_prompt="You are helpful.")
        # or with full message history:
        response = client.chat_messages([
            {"role": "system", "content": "..."},
            {"role": "user", "content": "Hello!"},
        ])
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    def chat(
        self,
        user_message: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> str:
        """Simple chat interface.

        Args:
            user_message: The user's message
            system_prompt: System prompt (assembled by SoulLinkEngine)
            history: Optional conversation history
            **kwargs: Additional API parameters

        Returns:
            Assistant response text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        return self.chat_messages(messages, **kwargs)

    def chat_messages(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        """Chat with full message list.

        Args:
            messages: List of {"role": "system/user/assistant", "content": "..."}
            **kwargs: Additional API parameters (temperature, max_tokens, etc.)

        Returns:
            Assistant response text
        """
        client = self._get_client()

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }

        # Pass through any extra params
        for k, v in kwargs.items():
            if k not in ("max_tokens", "temperature"):
                payload[k] = v

        try:
            response = client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            if not choices:
                logger.error(f"No choices in response: {data}")
                return ""

            content = choices[0].get("message", {}).get("content", "")

            # Log token usage
            usage = data.get("usage", {})
            if usage:
                logger.debug(
                    f"Tokens: {usage.get('prompt_tokens', 0)} in, "
                    f"{usage.get('completion_tokens', 0)} out"
                )

            return content

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __del__(self):
        self.close()


class AsyncLLMClient:
    """Async version of LLMClient for use with FastAPI/async frameworks."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def chat(
        self,
        user_message: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return await self.chat_messages(messages, **kwargs)

    async def chat_messages(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        client = await self._get_client()

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }

        for k, v in kwargs.items():
            if k not in ("max_tokens", "temperature"):
                payload[k] = v

        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            if not choices:
                return ""

            return choices[0].get("message", {}).get("content", "")

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

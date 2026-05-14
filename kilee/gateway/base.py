"""Base platform adapter — inspired by hermes-agent's gateway architecture.

Every platform (Telegram, Discord, etc.) implements this interface.
The GatewayRunner manages all registered adapters in one event loop.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MessageEvent:
    platform: str
    chat_id: str
    user_id: str
    text: str
    message_id: Optional[str] = None
    reply_to_id: Optional[str] = None
    username: Optional[str] = None
    raw: Any = None


@dataclass
class SendResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class PlatformAdapter(ABC):
    name: str = ""

    @abstractmethod
    async def start(self):
        ...

    @abstractmethod
    async def stop(self):
        ...

    @abstractmethod
    async def send_message(self, chat_id: str, text: str, **kwargs) -> SendResult:
        ...

    @abstractmethod
    async def send_typing(self, chat_id: str):
        ...

    def on_message(self, handler):
        self._message_handler = handler

    async def _dispatch(self, event: MessageEvent):
        if handler := getattr(self, "_message_handler", None):
            await handler(event)

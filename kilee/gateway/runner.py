"""GatewayRunner — unified multi-platform message routing.

Manages startup/shutdown of all platform adapters.
Dispatches incoming messages to the agent and sends responses back.
Inspired by hermes-agent's GatewayRunner architecture.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from rich.console import Console

from kilee import config, theme
from kilee.gateway.agent_session import GatewayAgent
from kilee.gateway.base import MessageEvent, PlatformAdapter

logger = logging.getLogger(__name__)
console = Console(highlight=False)


class GatewayRunner:
    def __init__(self):
        self.adapters: dict[str, PlatformAdapter] = {}
        self.sessions: dict[str, GatewayAgent] = {}
        self._bg_tasks: list[asyncio.Task] = []

    def register(self, adapter: PlatformAdapter):
        self.adapters[adapter.name] = adapter
        adapter.on_message(self._on_message)

    async def start(self):
        console.print(f"  [{theme.C['accent']}]Gateway starting...[/]")
        for name, adapter in self.adapters.items():
            try:
                await adapter.start()
                console.print(f"  [{theme.C['ok']}]✓[/] [{theme.C['accent2']}]{name}[/] connected")
                if hasattr(adapter, "poll"):
                    task = asyncio.create_task(adapter.poll())
                    self._bg_tasks.append(task)
            except Exception as e:
                console.print(f"  [{theme.C['error']}]✗[/] [{theme.C['accent2']}]{name}[/] {e}")

        if self._bg_tasks:
            console.print(f"  [{theme.C['dim']}]Listening for messages...[/]")
            await asyncio.gather(*self._bg_tasks)

    async def stop(self):
        for task in self._bg_tasks:
            task.cancel()
        for adapter in self.adapters.values():
            await adapter.stop()

    async def _on_message(self, event: MessageEvent):
        if event.text.startswith("/"):
            response = await self._handle_command(event)
        else:
            response = await self._handle_chat(event)

        if response and event.platform in self.adapters:
            await self.adapters[event.platform].send_message(
                event.chat_id, response,
            )

    async def _handle_command(self, event: MessageEvent) -> Optional[str]:
        cmd = event.text.split()[0].lower()
        if cmd == "/start":
            return (
                "🤖 *KiLee Agent*\n\n"
                "I'm your AI assistant. Send me a message or use:\n"
                f"`/help` — show commands\n"
                f"`/status` — current session info\n"
                f"`/new` — reset conversation\n"
                f"`/model` — show active model"
            )
        elif cmd == "/help":
            return (
                "*Commands:*\n"
                "`/help` — this menu\n"
                "`/status` — session info\n"
                "`/new` — new session\n"
                "`/model` — show model\n"
                "`/approval auto|suggest|never` — set approval mode"
            )
        elif cmd == "/status":
            cfg = config.load()
            return (
                f"*Session*\n"
                f"model: `{cfg.get('model', 'deepseek-chat')}`\n"
                f"approval: `{cfg.get('approval_mode', 'suggest')}`"
            )
        elif cmd == "/new":
            if event.chat_id in self.sessions:
                self.sessions[event.chat_id].reset()
            return "✅ Session reset."
        elif cmd == "/model":
            return f"Active model: `{config.get('model')}`"
        elif cmd == "/approval":
            parts = event.text.split()
            if len(parts) > 1:
                from kilee.approval import ApprovalMode
                mode = parts[1].lower()
                if mode in ApprovalMode.CHOICES:
                    ApprovalMode.set_mode(mode)
                    return f"Approval mode set to: `{mode}`"
                return f"Invalid mode. Use: auto / suggest / never"
            return f"Current: `{config.get('approval_mode')}`"
        return None

    async def _handle_chat(self, event: MessageEvent) -> Optional[str]:
        if event.chat_id not in self.sessions:
            self.sessions[event.chat_id] = GatewayAgent(event.chat_id)
        session = self.sessions[event.chat_id]

        adapter = self.adapters.get(event.platform)
        typing_task = None
        if adapter:
            typing_task = asyncio.create_task(self._periodic_typing(adapter, event.chat_id))

        try:
            response = await session.process_message(event.text)
            return response
        finally:
            if typing_task:
                typing_task.cancel()

    async def _periodic_typing(self, adapter: PlatformAdapter, chat_id: str):
        while True:
            try:
                await adapter.send_typing(chat_id)
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception:
                break

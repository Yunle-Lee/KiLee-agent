"""Telegram Bot adapter — long-polling via Bot API.

Inspired by hermes-agent's telegram adapter + openclaw's TDLib driver.
Uses httpx (already a dependency) — no extra packages needed.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from kilee.gateway.base import MessageEvent, PlatformAdapter, SendResult

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org/bot{token}/{method}"

TELEGRAM_MAX_UTF16 = 4096


class TelegramAdapter(PlatformAdapter):
    name = "telegram"

    def __init__(self, token: str, proxy: Optional[str] = None):
        self.token = token
        self._offset = 0
        self._running = False
        client_kwargs = {"timeout": httpx.Timeout(connect=10, read=25, write=10, pool=5)}
        if proxy:
            client_kwargs["proxies"] = proxy
        self._http = httpx.AsyncClient(**client_kwargs)

    async def start(self):
        me = await self._api("getMe")
        logger.info("Telegram bot @%s connected", me.get("username", "?"))
        self._running = True

    async def stop(self):
        self._running = False
        await self._http.aclose()

    async def _api(self, method: str, **kwargs) -> dict:
        url = API_BASE.format(token=self.token, method=method)
        resp = await self._http.post(url, json=kwargs)
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API {method}: {data.get('description', 'unknown error')}")
        return data["result"]

    async def send_message(self, chat_id: str, text: str, **kwargs) -> SendResult:
        try:
            result = await self._api(
                "sendMessage",
                chat_id=int(chat_id),
                text=text,
                parse_mode=kwargs.get("parse_mode", "Markdown"),
                disable_web_page_preview=True,
            )
            return SendResult(success=True, message_id=str(result["message_id"]))
        except Exception as e:
            return SendResult(success=False, error=str(e))

    async def send_typing(self, chat_id: str):
        try:
            await self._api("sendChatAction", chat_id=int(chat_id), action="typing")
        except Exception:
            pass

    async def poll(self):
        while self._running:
            try:
                updates = await self._api(
                    "getUpdates",
                    offset=self._offset,
                    timeout=20,
                    allowed_updates=["message"],
                )
                for update in updates:
                    self._offset = update["update_id"] + 1
                    if msg := update.get("message"):
                        await self._handle_message(msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Telegram poll error: %s", e)
                await asyncio.sleep(3)

    async def _handle_message(self, msg: dict):
        chat = msg.get("chat", {})
        text = msg.get("text", "").strip()
        if not text:
            return

        event = MessageEvent(
            platform="telegram",
            chat_id=str(chat.get("id")),
            user_id=str(msg.get("from", {}).get("id", "")),
            text=text,
            message_id=str(msg.get("message_id", "")),
            username=msg.get("from", {}).get("username") or msg.get("from", {}).get("first_name", ""),
            raw=msg,
        )
        await self._dispatch(event)

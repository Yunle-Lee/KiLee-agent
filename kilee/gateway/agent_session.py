"""Headless agent session for platform gateway.

Each chat gets its own message history and runs the full LLM + tool-calling
loop with auto-approval (no interactive user to confirm tool calls).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from openai import RateLimitError, APITimeoutError

from kilee import config
from kilee.agent import _call_llm, build_system_prompt, get_client
from kilee.approval import ApprovalMode
from kilee.tools import dispatch

logger = logging.getLogger(__name__)


class GatewayAgent:
    """Per-chat agent session for headless gateway usage.

    Each GatewayAgent holds its own message history. All tool calls
    run under auto-approval since there is no interactive user.
    """

    def __init__(self, chat_id: str):
        self.chat_id = chat_id
        self.messages: list[dict] = [
            {"role": "system", "content": build_system_prompt()},
        ]

    def reset(self):
        self.messages = [{"role": "system", "content": build_system_prompt()}]

    async def process_message(self, text: str) -> str:
        self.messages.append({"role": "user", "content": text})

        orig_mode = ApprovalMode.from_config()
        was_auto = orig_mode == ApprovalMode.Auto
        if not was_auto:
            ApprovalMode.set_mode(ApprovalMode.Auto)

        try:
            result = await asyncio.to_thread(self._run_sync)
        finally:
            if not was_auto:
                ApprovalMode.set_mode(orig_mode)

        return result

    def _run_sync(self) -> str:
        client, cfg = get_client()

        while True:
            try:
                chunks = _call_llm(client, cfg, self.messages)
            except RateLimitError:
                return "⚠ API 速率限制，请稍后再试"
            except APITimeoutError:
                return "⚠ API 请求超时"
            except Exception as e:
                err = str(e).lower()
                if "401" in err or "unauthorized" in err:
                    return "⚠ API 认证失败，请运行: kilee login"
                if "insufficient_quota" in err or "429" in err:
                    return "⚠ API 配额不足"
                logger.error("Gateway agent error: %s", e)
                return f"⚠ 处理出错: {e}"

            full_content, tool_calls_map, finish_reason = self._parse_chunks(chunks)

            if not full_content and finish_reason == "stop":
                return "(空回复)"

            if finish_reason == "tool_calls" and tool_calls_map:
                assistant_msg: dict = {
                    "role": "assistant",
                    "content": full_content or None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments"],
                            },
                        }
                        for tc in tool_calls_map.values()
                    ],
                }
                self.messages.append(assistant_msg)

                for tc in tool_calls_map.values():
                    name = tc["name"]
                    try:
                        args = json.loads(tc["arguments"])
                    except json.JSONDecodeError:
                        args = {}
                    result = dispatch(name, args)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
                continue

            if full_content:
                self.messages.append({"role": "assistant", "content": full_content})
                return full_content

            return "(空回复)"

    @staticmethod
    def _parse_chunks(chunks: list) -> tuple:
        full_content = ""
        tool_calls_map: dict[int, dict] = {}
        finish_reason = None

        for chunk in chunks:
            choice = chunk.choices[0]
            delta = choice.delta
            finish_reason = choice.finish_reason

            if delta.content:
                full_content += delta.content

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    i = tc.index
                    if i not in tool_calls_map:
                        tool_calls_map[i] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_calls_map[i]["id"] = tc.id
                    if tc.function.name:
                        tool_calls_map[i]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls_map[i]["arguments"] += tc.function.arguments

        return full_content, tool_calls_map, finish_reason

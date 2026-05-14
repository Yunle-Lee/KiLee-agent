"""持久化记忆模块 — 跨会话记住用户信息和偏好"""
import json
import os
from datetime import datetime
from pathlib import Path

MEMORY_FILE = os.path.expanduser("~/.kilee/memory.json")

def _load() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"facts": [], "updated_at": None}

def _save(data: dict):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_context() -> str:
    """返回注入系统提示的记忆块"""
    data = _load()
    facts = data.get("facts", [])
    if not facts:
        return ""
    lines = "\n".join(f"- {f}" for f in facts[-30:])  # 最多30条
    return f"<memory-context>\n[关于用户的已知信息]\n{lines}\n</memory-context>"

def save_fact(fact: str):
    data = _load()
    # 避免重复
    if fact not in data["facts"]:
        data["facts"].append(fact)
    _save(data)

def clear():
    _save({"facts": []})

def list_facts() -> list:
    return _load().get("facts", [])

# 工具 schema — AI 可以主动调用来保存记忆
SCHEMA = {
    "type": "function",
    "function": {
        "name": "save_memory",
        "description": "保存关于用户的重要信息到持久记忆，跨会话可用。用于记住用户偏好、项目信息、重要事实等。",
        "parameters": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "要记住的信息，一句话描述"},
            },
            "required": ["fact"],
        },
    },
}

def run(fact: str) -> str:
    save_fact(fact)
    return f"已记住: {fact}"

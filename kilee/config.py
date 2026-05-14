import json
import os

CONFIG_PATH = os.path.expanduser("~/.kilee/config.json")

DEFAULTS = {
    "api_key": "",
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com",
    "auto_allow_readonly": True,
    "trust_all_tools": False,
    "max_tokens": 8192,
    "approval_mode": "suggest",
}

def load() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return {**DEFAULTS, **json.load(f)}
    return DEFAULTS.copy()

def save(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def get(key: str):
    return load().get(key, DEFAULTS.get(key))

def set_value(key: str, value):
    cfg = load()
    cfg[key] = value
    save(cfg)

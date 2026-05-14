"""Interactive first-run setup wizard for KiLee."""
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich import box
from kilee import config, theme

console = Console(highlight=False)

_AC  = theme.C["accent"]
_AC2 = theme.C["accent2"]
_DM  = theme.C["dim"]
_OK  = theme.C["ok"]
_ERR = theme.C["error"]
_BDR = theme.C["border"]


def _prompt(label: str, default: str = "", secret: bool = False) -> str:
    import getpass
    console.print(f"  [{_AC}]{label}[/]", end=" ")
    if default:
        console.print(f"[{_DM}](default: {default})[/] ", end="")
    try:
        if secret:
            val = getpass.getpass("")
        else:
            val = input()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n[{_DM}]setup cancelled[/]")
        sys.exit(0)
    return val.strip() or default


def run_setup() -> bool:
    """Run the interactive setup wizard. Returns True if setup completed."""
    console.print()
    console.print(Panel(
        f"[bold {_AC}]Welcome to KiLee![/]\n\n"
        f"[{_DM}]Let's configure your API key and preferences.[/]\n"
        f"[{_DM}]Config is stored at [/][{_AC2}]~/.kilee/config.json[/]",
        border_style=_BDR,
        padding=(1, 2),
    ))
    console.print()

    # ── Step 1: API Provider
    console.print(f"  [{_AC}]Step 1/3[/] [{_DM}]— Choose your AI provider[/]")
    console.print()
    providers = [
        ("1", "DeepSeek",      "https://api.deepseek.com",      "deepseek-chat"),
        ("2", "OpenAI",        "https://api.openai.com/v1",      "gpt-4o"),
        ("3", "Groq",          "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
        ("4", "OpenRouter",    "https://openrouter.ai/api/v1",   "deepseek/deepseek-chat"),
        ("5", "Custom / Other","",                               ""),
    ]
    for num, name, url, _ in providers:
        console.print(f"  [{_AC}]{num}[/]  [{_DM}]{name:<16}[/] [{_DM}]{url}[/]")
    console.print()

    choice = _prompt("Provider [1-5]:", default="1")
    if choice not in [p[0] for p in providers]:
        choice = "1"

    _, pname, base_url, default_model = providers[int(choice) - 1]

    if choice == "5":
        base_url     = _prompt("Base URL:", default="https://api.openai.com/v1")
        default_model = _prompt("Default model:", default="gpt-4o")

    console.print()

    # ── Step 2: API Key
    console.print(f"  [{_AC}]Step 2/3[/] [{_DM}]— Enter your API key[/]")
    if pname == "DeepSeek":
        console.print(f"  [{_DM}]Get your key at: [/][{_AC2}]https://platform.deepseek.com/api_keys[/]")
    console.print()

    api_key = _prompt("API Key (hidden):", secret=True)
    if not api_key:
        console.print(f"  [{_ERR}]API key is required.[/]")
        return False

    console.print()

    # ── Step 3: Model
    console.print(f"  [{_AC}]Step 3/3[/] [{_DM}]— Choose default model[/]")
    console.print()
    if pname == "DeepSeek":
        models = ["deepseek-chat", "deepseek-reasoner"]
        for i, m in enumerate(models, 1):
            console.print(f"  [{_AC}]{i}[/]  [{_DM}]{m}[/]")
        console.print()
        mchoice = _prompt("Model [1-2]:", default="1")
        model = models[int(mchoice) - 1] if mchoice in ("1", "2") else default_model
    else:
        model = _prompt("Model name:", default=default_model)

    console.print()

    # ── Save
    cfg = config.load()
    cfg["api_key"]  = api_key
    cfg["base_url"] = base_url
    cfg["model"]    = model
    config.save(cfg)

    console.print(Panel(
        f"[{_OK}]✓ Setup complete![/]\n\n"
        f"  [{_DM}]provider[/]  [{_AC}]{pname}[/]\n"
        f"  [{_DM}]model   [/]  [{_AC}]{model}[/]\n"
        f"  [{_DM}]config  [/]  [{_AC2}]~/.kilee/config.json[/]\n\n"
        f"[{_DM}]Run [/][{_AC}]kilee[/][{_DM}] to start chatting.[/]",
        border_style=_OK,
        padding=(1, 2),
    ))
    console.print()
    return True

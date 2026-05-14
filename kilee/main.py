import os
import sys
import click
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from kilee import config, theme
from kilee.agent import run_agent, build_system_prompt, print_welcome, get_client
from kilee.tools import memory as mem_tool
from kilee.compressor import maybe_compress

console = Console(highlight=False)
HISTORY_FILE = os.path.expanduser("~/.kilee/history")

PROMPT_STYLE = Style.from_dict({"prompt": "#00BFBF bold"})

SLASH_HELP = [
    ("/clear",        "clear conversation history"),
    ("/compact",      "compress context"),
    ("/memory",       "view persistent memory"),
    ("/memory clear", "wipe all memory"),
    ("/model [name]", "view / switch model"),
    ("/approval [mode]", "view / set approval: auto|suggest|never"),
    ("/tips",         "show random usage tips"),
    ("/help",         "show this help"),
    ("/exit",         "quit"),
]

_AC  = theme.C["accent"]
_AC2 = theme.C["accent2"]
_DM  = theme.C["dim"]
_OK  = theme.C["ok"]
_ERR = theme.C["error"]
_WRN = theme.C["warn"]

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """KiLee - DeepSeek 驱动的终端 AI Agent"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)

@cli.command()
def chat():
    """与 KiLee 对话"""
    cfg = config.load()
    if not cfg.get("api_key"):
        from kilee.setup import run_setup
        run_setup()
        cfg = config.load()
        if not cfg.get("api_key"):
            sys.exit(1)

    print_welcome()
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

    messages = [{"role": "system", "content": build_system_prompt()}]
    session = PromptSession(
        history=FileHistory(HISTORY_FILE),
        style=PROMPT_STYLE,
        mouse_support=False,
    )

    while True:
        try:
            user_input = session.prompt(HTML(f"<style fg='#00BFBF'><b>{theme.PROMPT_SYMBOL}</b></style>")).strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[{_DM}]bye[/]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            _handle_slash(user_input, messages)
            if user_input.lower() in ("/exit", "/quit"):
                break
            continue

        # 用户消息：gemini-cli 风格 "> " 前缀
        console.print(f"\n[{_AC}]>[/] {user_input}\n")

        messages.append({"role": "user", "content": user_input})
        try:
            run_agent(messages)
        except KeyboardInterrupt:
            console.print(f"\n[{_DM}]已中断[/]")
        except Exception as e:
            console.print(f"\n[{_ERR}]错误: {e}[/]")

        total_chars = sum(len(str(m.get("content") or "")) for m in messages)
        console.print(f"\n  [{_DM}]~{total_chars//4} tokens[/]")

def _handle_slash(cmd_str: str, messages: list):
    parts = cmd_str.split()
    cmd = parts[0].lower()

    if cmd in ("/exit", "/quit"):
        console.print(f"[{_DM}]bye[/]")

    elif cmd == "/clear":
        messages.clear()
        messages.append({"role": "system", "content": build_system_prompt()})
        console.print(f"  [{_DM}]对话已清空[/]")

    elif cmd == "/compact":
        new_msgs, did = maybe_compress(messages, console)
        if did:
            messages.clear()
            messages.extend(new_msgs)
        else:
            console.print(f"  [{_DM}]上下文较短，无需压缩[/]")

    elif cmd == "/memory":
        if len(parts) > 1 and parts[1] == "clear":
            mem_tool.clear()
            console.print(f"  [{_DM}]记忆已清除[/]")
        else:
            facts = mem_tool.list_facts()
            if facts:
                for i, f in enumerate(facts, 1):
                    console.print(f"  [{_AC2}]{i}.[/] [{_DM}]{f}[/]")
            else:
                console.print(f"  [{_DM}]暂无记忆[/]")

    elif cmd == "/tips":
        from kilee.tips import TIPS
        import random
        for tip in random.sample(TIPS, min(5, len(TIPS))):
            console.print(f"  [{_AC}]◈[/] [{_DM}]{tip}[/]")

    elif cmd == "/model":
        if len(parts) > 1:
            config.set_value("model", parts[1])
            console.print(f"  [{_DM}]模型已切换: {parts[1]}[/]")
        else:
            cfg = config.load()
            console.print(f"  [{_AC}]当前:[/] [{_AC2}]{cfg['model']}[/]")
            console.print(f"  [{_DM}]可用: deepseek-chat  deepseek-reasoner[/]")

    elif cmd == "/approval":
        from kilee.approval import ApprovalMode
        if len(parts) > 1:
            mode = parts[1].lower()
            if mode in ApprovalMode.CHOICES:
                ApprovalMode.set_mode(mode)
                console.print(f"  [{_DM}]审批模式已切换: {mode}[/]")
            else:
                console.print(f"  [{_ERR}]模式 {mode} 无效，可用: {' / '.join(ApprovalMode.CHOICES)}[/]")
        else:
            current = ApprovalMode.from_config()
            console.print(f"  [{_AC}]当前:[/] [{_AC2}]{current}[/]")
            console.print(f"  [{_DM}]  auto    — 自动批准所有操作[/]")
            console.print(f"  [{_DM}]  suggest — 危险操作需确认[/]")
            console.print(f"  [{_DM}]  never   — 拒绝所有危险操作[/]")

    elif cmd == "/help":
        for c, d in SLASH_HELP:
            console.print(f"  [{_AC}]{c:<20}[/] [{_DM}]{d}[/]")

    else:
        console.print(f"  [{_DM}]未知命令: {cmd}  输入 /help 查看[/]")


@cli.command()
@click.argument("text", nargs=-1)
def translate(text):
    """自然语言转 shell 命令"""
    cfg = config.load()
    if not cfg.get("api_key"):
        console.print(f"[{_ERR}]未设置 API Key，请先运行: kilee login[/]")
        sys.exit(1)
    query = " ".join(text) or click.prompt(theme.PROMPT_SYMBOL)
    client, cfg = get_client()
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": "将用户描述转为shell命令。只输出命令本身，不加任何解释或代码块。"},
            {"role": "user", "content": query},
        ],
    )
    cmd = resp.choices[0].message.content.strip()
    console.print(f"\n  [{_AC}]$ {cmd}[/]\n")
    if click.confirm("  执行？", default=False):
        import subprocess
        subprocess.run(cmd, shell=True)

@cli.command()
def setup():
    """Run the interactive setup wizard"""
    from kilee.setup import run_setup
    run_setup()

@cli.command()
def login():
    """设置 DeepSeek API Key"""
    key = click.prompt("API Key", hide_input=True)
    config.set_value("api_key", key)
    console.print(f"  [{_DM}]已保存[/]")

@cli.command()
def logout():
    config.set_value("api_key", "")
    console.print(f"  [{_DM}]已登出[/]")

@cli.command()
def whoami():
    cfg = config.load()
    console.print(f"  [{_DM}]model[/]    [{_AC}]{cfg['model']}[/]")
    console.print(f"  [{_DM}]api_key[/]  [{_AC2}]{'已设置' if cfg.get('api_key') else '未设置'}[/]")
    console.print(f"  [{_DM}]base_url[/] [{_DM}]{cfg['base_url']}[/]")

@cli.command()
def doctor():
    import shutil
    checks = [
        ("python 3.10+", sys.version_info >= (3, 10)),
        ("api key",      bool(config.get("api_key"))),
        ("curl",         bool(shutil.which("curl"))),
        ("git",          bool(shutil.which("git"))),
    ]
    for name, ok in checks:
        mark = f"[{_OK}]✓[/]" if ok else f"[{_ERR}]✗[/]"
        console.print(f"  {mark}  [{_DM}]{name}[/]")

@cli.command()
@click.argument("mode", type=click.Choice(["auto", "suggest", "never"]), required=False)
def approval(mode):
    """Set tool approval mode: auto|suggest|never"""
    from kilee.approval import ApprovalMode
    if mode:
        ApprovalMode.set_mode(mode)
        console.print(f"  [{_DM}]审批模式已切换: {mode}[/]")
    else:
        current = ApprovalMode.from_config()
        console.print(f"  [{_AC}]当前审批模式:[/] [{_AC2}]{current}[/]")

@cli.command()
@click.argument("image", type=click.Path(exists=True), required=False)
@click.option("--width", default=60, type=int, help="ASCII output width")
@click.option("--chars", default="blocks", type=click.Choice(["detailed", "blocks", "classic", "minimal"]),
              help="Character set")
@click.option("--name", default="KiLee", help="Agent name for banner")
@click.option("--tagline", default="Agent v0.3", help="Tagline for banner")
@click.option("--set-default", is_flag=True, help="Save as default startup banner")
def banner(image, width, chars, name, tagline, set_default):
    """Generate custom ASCII banner from an image"""
    from kilee.banner import image_to_ascii, build_banner, save_banner_config

    if not image:
        console.print(f"\n  [{_AC}]KiLee Banner Generator[/]")
        console.print(f"  [{_DM}]Usage: kilee banner <image_path> [options][/]")
        console.print(f"\n  [{_DM}]Options:[/]")
        console.print(f"    [{_AC}]--width[/]    [{_DM}]ASCII width (default: 60)[/]")
        console.print(f"    [{_AC}]--chars[/]    [{_DM}]detailed | blocks | classic | minimal[/]")
        console.print(f"    [{_AC}]--name[/]     [{_DM}]Agent name (default: KiLee)[/]")
        console.print(f"    [{_AC}]--tagline[/]  [{_DM}]Tagline text[/]")
        console.print(f"    [{_AC}]--set-default[/]  [{_DM}]Save as startup banner[/]")
        return

    ascii_art = image_to_ascii(image, width=width, char_set=chars)
    if ascii_art is None:
        console.print(f"  [{_ERR}]需要安装 Pillow: pip install Pillow[/]")
        return

    banner_str = build_banner(ascii_art=ascii_art, name=name, tagline=tagline, width=width)
    console.print(f"\n{banner_str}\n", markup=False, highlight=False)

    if set_default:
        save_banner_config({
            "logo": str(Path(image).resolve()),
            "name": name,
            "tagline": tagline,
        })
        console.print(f"  [{_OK}]✓ 已保存为启动默认 Banner[/]")

@cli.command()
@click.option("--telegram-token", envvar="KILEE_TELEGRAM_TOKEN", default="", help="Telegram Bot API token")
def gateway(telegram_token):
    """Start the multi-platform gateway (Telegram, etc.)"""
    import asyncio
    from kilee.gateway.runner import GatewayRunner
    from kilee.gateway.telegram import TelegramAdapter

    runner = GatewayRunner()

    if telegram_token:
        adapter = TelegramAdapter(token=telegram_token)
        runner.register(adapter)
        console.print(f"  [{_DM}]Telegram gateway configured[/]")
    else:
        console.print(f"  [{_DM}]No adapters configured. Set KILEE_TELEGRAM_TOKEN or use --telegram-token[/]")
        return

    try:
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        console.print(f"\n  [{_DM}]Gateway stopped[/]")

@cli.command()
def settings():
    import json
    cfg = {k: v for k, v in config.load().items() if k != "api_key"}
    console.print_json(json.dumps(cfg, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    cli()

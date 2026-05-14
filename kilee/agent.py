import json
import threading
import time
import itertools
from difflib import unified_diff
from pathlib import Path
from openai import OpenAI
from rich.console import Console
from rich.syntax import Syntax
from kilee import config
from kilee.tools import TOOLS, dispatch
from kilee.tools import memory as mem_tool
from kilee import theme

console = Console(highlight=False)

SYSTEM_PROMPT = """你是 KiLee，一个运行在终端里的 AI Agent。
你可以使用工具来帮助用户：读写文件、执行命令、编写调试代码、搜索网络。

可用工具：
- execute_bash: 执行 shell 命令（不要用 cd，用 working_dir 参数）
- fs_read: 读取文件 / 列目录 / 搜索文件内容
- fs_write: 创建 / 编辑 / 追加文件
- save_memory: 记住用户的重要信息（跨会话）
- web_search: 联网搜索获取最新信息
- web_fetch: 抓取指定 URL 的文本内容

规则：
- 需要操作文件或执行命令时，直接使用工具，不要只是描述
- 执行危险操作前先说明你要做什么
- 用中文回复，代码块用markdown格式
- 当用户问到最新信息或训练数据之外的内容时，使用 web_search
- 当用户提到重要偏好、项目信息或需要跨会话记住的事情时，主动调用 save_memory
- 只读操作（fs_read, web_search, save_memory）自动执行；写操作（execute_bash, fs_write, web_fetch）可能需要用户确认 — 如果被拒绝，说明原因并询问用户是否需要替代方案
{project_context}{memory_context}
"""

def _load_project_context() -> str:
    """读取当前目录下的项目上下文文件（KILEE.md / CLAUDE.md / AGENTS.md）。
    这是 Harness Engineering 中 Context Engineering 的核心实践：
    静态上下文注入，ROI 最高的优化手段。
    """
    candidates = ["KILEE.md", "CLAUDE.md", "AGENTS.md", ".kilee.md"]
    cwd = Path.cwd()
    for name in candidates:
        p = cwd / name
        if p.exists():
            try:
                content = p.read_text(errors="replace").strip()
                if content:
                    return f"\n<project-context source=\"{name}\">\n{content}\n</project-context>\n"
            except Exception:
                pass
    return ""

def build_system_prompt() -> str:
    project_ctx = _load_project_context()
    memory_ctx = mem_tool.get_context()
    return SYSTEM_PROMPT.format(
        project_context=project_ctx,
        memory_context=("\n" + memory_ctx) if memory_ctx else "",
    )

def get_client():
    cfg = config.load()
    return OpenAI(api_key=cfg.get("api_key", ""), base_url=cfg["base_url"]), cfg

def print_welcome():
    from kilee.tools import memory as mem_tool
    from kilee.tips import get_random_tip
    from pathlib import Path as _Path
    from rich.table import Table
    from rich.panel import Panel
    import re, os

    cfg = config.load()
    model = cfg.get("model", "deepseek-chat")
    approval_mode = cfg.get("approval_mode", "suggest")
    facts_count = len(mem_tool.list_facts())

    from kilee.banner import get_custom_banner
    custom_banner = get_custom_banner()
    cwd = os.getcwd()
    # 截断过长路径
    if len(cwd) > 36:
        cwd = "…" + cwd[-35:]

    ac, ac2, dm, bdr, ok, err = (
        theme.C["accent"], theme.C["accent2"],
        theme.C["dim"], theme.C["border"],
        theme.C["ok"], theme.C["error"],
    )

    # ── 工具列表（hermes Available Tools 思路）
    tool_rows = [
        (theme.TOOL_ICONS["execute_bash"], "execute_bash", "run shell commands"),
        (theme.TOOL_ICONS["fs_read"],      "fs_read",      "read / list / search files"),
        (theme.TOOL_ICONS["fs_write"],     "fs_write",     "create / edit files"),
        (theme.TOOL_ICONS["save_memory"],  "save_memory",  "persist memory across sessions"),
        (theme.TOOL_ICONS["web_search"],   "web_search",   "search the web"),
        (theme.TOOL_ICONS["web_fetch"],    "web_fetch",    "fetch content from URLs"),
    ]

    if custom_banner:
        hero_lines = len(custom_banner.splitlines())
        inner_height = hero_lines - 2
        hero_display = custom_banner
    else:
        hero_lines = len(re.sub(r'\[.*?\]', '', theme.BANNER_HERO).splitlines())
        inner_height = hero_lines - 2
        hero_display = theme.BANNER_HERO

    sep = f"[{bdr}]{'─' * 37}[/]"

    if custom_banner:
        logo_rows = custom_banner.splitlines()
    else:
        logo_rows = theme.BANNER_LOGO.splitlines()

    info_lines = logo_rows + [
        "",
        sep,
        "",
        f"  [{dm}]model  [/][{ac}]{model}[/]",
        f"  [{dm}]cwd    [/][{dm}]{cwd}[/]",
    ]
    if facts_count:
        info_lines.append(f"  [{dm}]memory [/][{ac2}]{facts_count} facts[/]")
    approval_labels = {"auto": "AUTO", "suggest": "SUGGEST", "never": "NEVER"}
    info_lines.append(f"  [{dm}]approval[/][{ac2}] {approval_labels.get(approval_mode, approval_mode)}[/]")
    # 检测项目上下文文件
    ctx_file = next((f for f in ["KILEE.md","CLAUDE.md","AGENTS.md",".kilee.md"] if (_Path.cwd()/f).exists()), None)
    if ctx_file:
        info_lines.append(f"  [{dm}]context[/][{ok}] {ctx_file} loaded[/]")

    info_lines += ["", sep, "", f"  [{ac}]Tools[/]"]
    for icon, name, desc in tool_rows:
        info_lines.append(f"  [{ac}]{icon}[/] [{ac2}]{name:<14}[/][{dm}]{desc}[/]")

    tip = get_random_tip()
    if len(tip) > 28:
        tip = tip[:27] + "…"
    info_lines += [
        "",
        sep,
        "",
        f"  [{dm}]tip: [/][{ac2}]{tip}[/]",
        "",
        sep,
    ]

    current = len(info_lines)
    if current < inner_height:
        info_lines += [""] * (inner_height - current)
    elif current > inner_height:
        info_lines = info_lines[:inner_height]

    right_panel = Panel(
        "\n".join(info_lines),
        border_style=bdr,
        padding=(0, 1),
        expand=False,
    )

    table = Table.grid(padding=(0, 2))
    table.add_column(no_wrap=True)
    table.add_column(no_wrap=False)
    table.add_row(hero_display, right_panel)

    console.print()
    console.print(table)
    console.print()


# ── Spinner ───────────────────────────────────────────────────────────────────

class Spinner:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        frames = itertools.cycle(theme.SPINNER_FRAMES)
        verbs  = itertools.cycle(theme.THINKING_VERBS)
        verb   = next(verbs)
        i = 0
        while not self._stop.is_set():
            f = next(frames)
            console.print(
                f"  [{theme.C['accent']}]{f}[/] [{theme.C['dim']}]{verb}...[/]",
                end="\r",
            )
            time.sleep(0.12)
            i += 1
            if i % 8 == 0:
                verb = next(verbs)
        console.print(" " * 40, end="\r")

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._thread.join()


# ── 工具调用显示 ───────────────────────────────────────────────────────────────

def _tool_label(name: str, args: dict) -> str:
    icon = theme.TOOL_ICONS.get(name, "◌")
    ac, dm = theme.C["accent"], theme.C["dim"]
    if name == "execute_bash":
        cmd = args.get("command", "")
        if len(cmd) > 60:
            cmd = cmd[:57] + "…"
        return f"[{ac}]{icon} Bash[/]  [{dm}]{cmd}[/]"
    elif name == "fs_read":
        path = args.get("path", "")
        mode = args.get("mode", "")
        extra = f" [{dm}]({mode})[/]" if mode != "Line" else ""
        return f"[{ac}]{icon} Read[/]  [{dm}]{path}[/]{extra}"
    elif name == "fs_write":
        cmd  = args.get("command", "")
        path = args.get("path", "")
        summ = args.get("summary", "")
        label = {"create": "Create", "str_replace": "Edit",
                 "append": "Append", "insert": "Insert"}.get(cmd, cmd)
        extra = f"  [{dm}]{summ}[/]" if summ else ""
        return f"[{ac}]{icon} {label}[/]  [{dm}]{path}[/]{extra}"
    elif name == "save_memory":
        fact = args.get("fact", "")[:50]
        return f"[{ac}]{icon} Memory[/]  [{dm}]{fact}[/]"
    elif name == "web_search":
        query = args.get("query", "")[:50]
        return f"[{ac}]{icon} Search[/]  [{dm}]{query}[/]"
    elif name == "web_fetch":
        url = args.get("url", "")[:50]
        return f"[{ac}]{icon} Fetch[/]  [{dm}]{url}[/]"
    return f"[{ac}]{icon} {name}[/]"

def _show_diff(path: str, old: str, new: str):
    diff = list(unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{Path(path).name}",
        tofile=f"b/{Path(path).name}",
        lineterm="",
    ))
    if diff:
        console.print(Syntax("".join(diff[:80]), "diff", theme="monokai",
                              background_color="default"))

def _print_tool_output(result: str, name: str):
    lines = result.splitlines()
    preview = lines[:12]
    if name in ("execute_bash", "fs_read", "web_fetch"):
        text = "\n".join(preview)
        if text.strip():
            lang = "bash" if name == "execute_bash" else "text"
            console.print(Syntax(text, lang, theme="monokai",
                                 background_color="default", line_numbers=False))
    else:
        for line in preview:
            console.print(f"  [{theme.C['dim']}]{line}[/]")
    if len(lines) > 12:
        console.print(f"  [{theme.C['dim']}]… 共 {len(lines)} 行[/]")


# ── Agent 主循环 ───────────────────────────────────────────────────────────────

def _call_llm(client, cfg: dict, messages: list, max_retries: int = 2) -> list:
    from openai import RateLimitError, APITimeoutError

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=cfg["model"],
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=cfg["max_tokens"],
                stream=True,
            )
            return list(response)
        except RateLimitError:
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise
        except APITimeoutError:
            if attempt < max_retries:
                continue
            raise
    return []


def run_agent(messages: list) -> str:
    client, cfg = get_client()

    while True:
        try:
            chunks = _call_llm(client, cfg, messages)
        except Exception as e:
            err_msg = str(e)
            if "401" in err_msg or "unauthorized" in err_msg.lower() or "auth" in err_msg.lower():
                console.print(f"\n  [{theme.C['error']}]API 认证失败，请运行: kilee login[/]")
            elif "insufficient_quota" in err_msg or "429" in err_msg:
                console.print(f"\n  [{theme.C['error']}]API 配额不足，请检查账户[/]")
            else:
                console.print(f"\n  [{theme.C['error']}]API 请求失败: {e}[/]")
            return ""

        full_content = ""
        tool_calls_map = {}
        finish_reason = None
        started = False

        for chunk in chunks:
            choice = chunk.choices[0]
            delta  = choice.delta
            finish_reason = choice.finish_reason

            if delta.content:
                if not started:
                    console.print(f"[{theme.C['accent']}]✦[/] ", end="")
                    started = True
                print(delta.content, end="", flush=True)
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

        if started:
            print()

        if finish_reason == "stop" and not full_content:
            console.print(f"\n  [{theme.C['warn']}]模型未返回有效内容[/]")
            return ""

        if finish_reason == "tool_calls" and tool_calls_map:
            tool_calls = list(tool_calls_map.values())
            messages.append({
                "role": "assistant",
                "content": full_content or None,
                "tool_calls": [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                    for tc in tool_calls
                ],
            })

            console.print()
            for tc in tool_calls:
                name = tc["name"]
                try:
                    args = json.loads(tc["arguments"])
                except Exception:
                    args = {}

                old_content = None
                if name == "fs_write" and args.get("command") == "str_replace":
                    p = Path(args.get("path", "")).expanduser()
                    if p.exists():
                        old_content = p.read_text(errors="replace")

                console.print(
                    f"[{theme.C['border']}]│[/] [{theme.C['accent']}]⠿[/] {_tool_label(name, args)}"
                )

                from kilee.approval import require_approval
                if require_approval(name, args):
                    result = dispatch(name, args)
                else:
                    result = "[DENIED] 操作被用户拒绝"
                ok = not result.startswith("[ERROR]") and not result.startswith("[BLOCKED]")

                status_icon = f"[{theme.C['ok']}]✓[/]" if ok else f"[{theme.C['error']}]✗[/]"
                console.print(
                    f"[{theme.C['border']}]│[/] {status_icon} {_tool_label(name, args)}"
                )

                if not ok:
                    console.print(f"[{theme.C['border']}]│[/]   [{theme.C['error']}]{result}[/]")
                elif name == "fs_write" and old_content is not None:
                    p = Path(args.get("path", "")).expanduser()
                    if p.exists():
                        _show_diff(args.get("path", ""), old_content,
                                   p.read_text(errors="replace"))
                elif name not in ("save_memory",) and result.strip() and result != "(无输出)":
                    _print_tool_output(result, name)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

            console.print(f"[{theme.C['border']}]│[/]")
            console.print()
            continue

        return full_content

"""Tool approval system — inspired by DeepSeek TUI's risk-based confirmation.

ApprovalMode:
  Auto     - run everything without asking
  Suggest  - ask for confirmation on destructive operations (default)
  Never    - block all destructive operations

RiskLevel:
  Benign       - read-only ops (fs_read, save_memory, web_search)
  Destructive  - write/shell/network ops (execute_bash, fs_write, web_fetch)
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from kilee import config, theme

console = Console(highlight=False)

AC = theme.C["accent"]
AC2 = theme.C["accent2"]
DM = theme.C["dim"]
OK = theme.C["ok"]
ERR = theme.C["error"]
WRN = theme.C["warn"]
BDR = theme.C["border"]


class ApprovalMode:
    Auto = "auto"
    Suggest = "suggest"
    Never = "never"

    CHOICES = [Auto, Suggest, Never]

    @staticmethod
    def from_config() -> str:
        return config.get("approval_mode") or ApprovalMode.Suggest

    @staticmethod
    def set_mode(mode: str):
        if mode in ApprovalMode.CHOICES:
            config.set_value("approval_mode", mode)


def classify_risk(name: str) -> str:
    if name in ("fs_read", "save_memory", "web_search"):
        return "benign"
    return "destructive"


def _summarize_impact(name: str, args: dict) -> list[str]:
    impacts = []
    if name == "execute_bash":
        impacts.append("执行 shell 命令")
        cmd = args.get("command", "")
        if cmd:
            impacts.append(f"  命令: {cmd[:80]}")
        wd = args.get("working_dir", "")
        if wd:
            impacts.append(f"  目录: {wd}")
    elif name == "fs_write":
        cmd = args.get("command", "")
        path = args.get("path", "")
        if cmd == "create":
            impacts.append(f"创建文件: {path}")
        elif cmd == "str_replace":
            impacts.append(f"编辑文件: {path}")
        elif cmd == "append":
            impacts.append(f"追加到文件: {path}")
        elif cmd == "insert":
            impacts.append(f"插入到文件: {path}")
    elif name == "web_fetch":
        impacts.append("获取远程 URL 内容")
        url = args.get("url", "")
        if url:
            impacts.append(f"  URL: {url[:80]}")
    elif name == "fs_read":
        impacts.append("读取文件")
        path = args.get("path", "")
        if path:
            impacts.append(f"  路径: {path}")
    return impacts


def require_approval(name: str, args: dict) -> Optional[bool]:
    mode = ApprovalMode.from_config()

    if mode == ApprovalMode.Auto:
        return True

    risk = classify_risk(name)
    if risk == "benign":
        return True

    if mode == ApprovalMode.Never:
        _print_blocked(name, args)
        return False

    return _prompt_user(name, args)


def _print_blocked(name: str, args: dict):
    impacts = _summarize_impact(name, args)
    lines = "\n".join(f"  [{DM}]{line}[/]" for line in impacts)
    console.print()
    console.print(Panel(
        f"[{ERR}]操作已拦截[/]\n\n"
        f"[{DM}]工具:[/] [{AC}]{name}[/]\n"
        f"{lines}\n\n"
        f"[{DM}]你当前处于 NEVER 模式。运行 [{AC}]/approval suggest[/] 来允许操作。[/]",
        border_style=ERR,
        padding=(1, 2),
    ))
    console.print()


def _prompt_user(name: str, args: dict) -> Optional[bool]:
    impacts = _summarize_impact(name, args)

    table = Table.grid(padding=(0, 1))
    table.add_column(no_wrap=True)
    table.add_column(no_wrap=False)

    table.add_row(f"[{WRN}]⚠ 操作需要确认[/]", "")
    table.add_row("", "")
    table.add_row(f"[{DM}]工具[/]", f"[{AC}]{name}[/]")
    for impact in impacts:
        table.add_row(f"[{DM}]影响[/]", f"[{AC2}]{impact}[/]")
    table.add_row("", "")

    options = Table.grid(padding=(0, 2))
    options.add_column(no_wrap=True)
    options.add_column(no_wrap=False)

    options.add_row(
        f"[{OK}] y[/] / [{OK}]Enter[/]",
        f"[{DM}]批准执行（仅本次）[/]",
    )
    options.add_row(
        f"[{AC}] a[/]",
        f"[{DM}]批准并记住选择（本次会话不再询问同类操作）[/]",
    )
    options.add_row(
        f"[{ERR}] n[/] / [{ERR}]d[/] / [{ERR}]Esc[/]",
        f"[{DM}]拒绝执行[/]",
    )

    table.add_row(f"[{DM}]选项[/]", options)

    console.print()
    console.print(Panel(
        table,
        border_style=WRN,
        padding=(1, 2),
    ))
    console.print()

    while True:
        try:
            choice = input(f"  [{WRN}]?[/] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return False

        if choice in ("y", "", "yes"):
            return True
        elif choice in ("a", "always"):
            config.set_value("approval_mode", "auto")
            console.print(f"  [{DM}]已切换至 AUTO 模式，本次会话不再询问[/]")
            return True
        elif choice in ("n", "d", "no", "deny", "q"):
            return False
        else:
            console.print(f"  [{DM}]输入 y(批准) / a(总是) / n(拒绝)[/]")

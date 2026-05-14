import os
import re
from pathlib import Path

SCHEMA = {
    "type": "function",
    "function": {
        "name": "fs_read",
        "description": "读取文件、目录或搜索文件内容。",
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["Line", "Directory", "Search"],
                    "description": "Line=读文件内容, Directory=列目录, Search=搜索文件内容",
                },
                "path": {"type": "string", "description": "文件或目录路径"},
                "start_line": {"type": "integer", "description": "起始行（Line模式）"},
                "end_line": {"type": "integer", "description": "结束行（Line模式）"},
                "pattern": {"type": "string", "description": "搜索模式（Search模式）"},
                "depth": {"type": "integer", "description": "目录深度（Directory模式）"},
            },
            "required": ["mode", "path"],
        },
    },
}

def run(mode: str, path: str, start_line: int = 1, end_line: int = -1,
        pattern: str = None, depth: int = 2) -> str:
    p = Path(path).expanduser()

    if mode == "Line":
        if not p.exists():
            return f"[ERROR] 文件不存在: {path}"
        try:
            lines = p.read_text(errors="replace").splitlines()
            total = len(lines)
            s = max(0, start_line - 1)
            e = total if end_line == -1 else min(end_line, total)
            numbered = [f"{i+s+1:4d} | {line}" for i, line in enumerate(lines[s:e])]
            return "\n".join(numbered)
        except Exception as ex:
            return f"[ERROR] {ex}"

    elif mode == "Directory":
        if not p.exists():
            return f"[ERROR] 目录不存在: {path}"
        lines = []
        def walk(d: Path, prefix: str, cur_depth: int):
            if cur_depth > depth:
                return
            try:
                entries = sorted(d.iterdir(), key=lambda x: (x.is_file(), x.name))
            except PermissionError:
                return
            for entry in entries:
                if entry.name.startswith(".") or entry.name in ("node_modules", "__pycache__", ".git"):
                    continue
                lines.append(f"{prefix}{'📁 ' if entry.is_dir() else '📄 '}{entry.name}")
                if entry.is_dir():
                    walk(entry, prefix + "  ", cur_depth + 1)
        walk(p, "", 0)
        return "\n".join(lines) or "(空目录)"

    elif mode == "Search":
        if not pattern:
            return "[ERROR] Search模式需要pattern参数"
        results = []
        try:
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", ".git")]
                for fname in files:
                    fpath = Path(root) / fname
                    try:
                        text = fpath.read_text(errors="replace")
                        for i, line in enumerate(text.splitlines(), 1):
                            if re.search(pattern, line, re.IGNORECASE):
                                results.append(f"{fpath}:{i}: {line.strip()}")
                    except Exception:
                        pass
        except Exception as ex:
            return f"[ERROR] {ex}"
        return "\n".join(results[:100]) or "(无匹配)"

    return f"[ERROR] 未知模式: {mode}"

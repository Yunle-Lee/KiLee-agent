from pathlib import Path

SCHEMA = {
    "type": "function",
    "function": {
        "name": "fs_write",
        "description": "创建或编辑文件。",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["create", "str_replace", "insert", "append"],
                    "description": "create=创建/覆盖, str_replace=替换内容, insert=插入行后, append=追加",
                },
                "path": {"type": "string", "description": "文件路径"},
                "file_text": {"type": "string", "description": "create命令的文件内容"},
                "old_str": {"type": "string", "description": "str_replace要替换的原文本"},
                "new_str": {"type": "string", "description": "str_replace/insert的新文本"},
                "insert_line": {"type": "integer", "description": "insert命令在此行后插入"},
                "summary": {"type": "string", "description": "修改说明"},
            },
            "required": ["command", "path"],
        },
    },
}

def run(command: str, path: str, file_text: str = None, old_str: str = None,
        new_str: str = None, insert_line: int = None, summary: str = None) -> str:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)

    try:
        if command == "create":
            p.write_text(file_text or "")
            return f"已创建: {path}"

        elif command == "append":
            text = p.read_text() if p.exists() else ""
            with open(p, "a") as f:
                if text and not text.endswith("\n"):
                    f.write("\n")
                f.write((new_str or "") + "\n")
            return f"已追加到: {path}"

        elif command == "str_replace":
            if not p.exists():
                return f"[ERROR] 文件不存在: {path}"
            content = p.read_text()
            if old_str not in content:
                return f"[ERROR] 未找到要替换的内容"
            if content.count(old_str) > 1:
                return f"[ERROR] 找到多处匹配，请提供更多上下文"
            p.write_text(content.replace(old_str, new_str or "", 1))
            return f"已替换: {path}"

        elif command == "insert":
            if not p.exists():
                return f"[ERROR] 文件不存在: {path}"
            lines = p.read_text().splitlines(keepends=True)
            idx = min(insert_line or 0, len(lines))
            lines.insert(idx, (new_str or "") + "\n")
            p.write_text("".join(lines))
            return f"已插入到第{idx}行后: {path}"

        return f"[ERROR] 未知命令: {command}"
    except Exception as e:
        return f"[ERROR] {e}"

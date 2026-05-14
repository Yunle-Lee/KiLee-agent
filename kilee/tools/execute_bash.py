import os
import subprocess
from pathlib import Path

SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_bash",
        "description": "执行bash命令。NEVER用cd切换目录，用working_dir参数代替。",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的bash命令"},
                "working_dir": {"type": "string", "description": "工作目录，支持~展开"},
                "summary": {"type": "string", "description": "命令用途的简短说明"},
            },
            "required": ["command"],
        },
    },
}

# 危险命令模式
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"dd\s+.*of=/dev/",
    r"mkfs",
    r">\s*/dev/sd",
    r"chmod\s+-R\s+777\s+/",
    r":(){ :|:& };:",  # fork bomb
]

def run(command: str, working_dir: str = None, summary: str = None) -> str:
    import re
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return f"[BLOCKED] 危险命令被拦截: {command}"

    cwd = Path(working_dir).expanduser() if working_dir else None
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return output.strip() or "(无输出)"
    except subprocess.TimeoutExpired:
        return "[ERROR] 命令超时（30s）"
    except Exception as e:
        return f"[ERROR] {e}"

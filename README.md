

# KiLee Agent

![pic1](https://github.com/Yunle-Lee/Pics_of_all_my-projects/blob/main/bbc5aa3142acfb4610b515c15ebdfeaf.png)

> A DeepSeek-powered terminal AI Agent — read files, run commands, write code, search the web.
>
> 一个基于 DeepSeek 的终端 AI 智能体 — 读写文件、执行命令、编写代码、搜索网络。

```
  ██╗  ██╗██╗██╗     ███████╗███████╗
  ██║ ██╔╝██║██║     ██╔════╝██╔════╝
  █████╔╝ ██║██║     █████╗  █████╗
  ██╔═██╗ ██║██║     ██╔══╝  ██╔══╝
  ██║  ██╗██║███████╗███████╗███████╗
  ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝
        ◈ A G E N T  v0.3 ◈
```

## Features / 功能

| English | 中文 |
|---|---|
| **6 built-in tools** — `execute_bash`, `fs_read`, `fs_write`, `save_memory`, `web_search`, `web_fetch` | **6 个内置工具** — 执行命令、读写文件、持久记忆、联网搜索、网页抓取 |
| **Persistent memory** — remembers facts across sessions (`~/.kilee/memory.json`) | **持久记忆** — 跨会话记住用户偏好和项目信息 |
| **Context Engineering** — auto-loads `KILEE.md` / `CLAUDE.md` / `AGENTS.md` | **上下文工程** — 自动加载项目上下文文件 |
| **Context compression** — auto-compresses long conversations to save tokens | **上下文压缩** — 长对话自动压缩，节省 Token |
| **Multi-provider** — DeepSeek, OpenAI, Groq, OpenRouter, any OpenAI-compatible API | **多模型供应商** — 支持 DeepSeek / OpenAI / Groq / OpenRouter 等 |
| **Rich terminal UI** — colored output, spinners, diff previews, banners | **丰富终端 UI** — 彩色输出、加载动效、差异预览、启动 Banner |
| **Multi-platform gateway** — Telegram integration with full agent loop | **多平台网关** — Telegram 集成，完整 Agent 循环 |
| **Risk-based approval** — auto / suggest / never modes via Rich panels | **风险审批系统** — 自动 / 建议 / 拒绝三种模式 |

## Quick Start / 快速开始

```bash
# 1. Install / 安装
pip install -e .

# 2. First run — setup wizard launches automatically / 首次运行自动配置
kilee

# Or manually / 或手动配置
kilee setup
```

### Environment / 环境要求

- Python 3.10+
- `openai`, `rich`, `click`, `prompt-toolkit`, `httpx`
- `Pillow` (optional — needed for `kilee banner` command, install via `pip install Pillow`)
- `pytest`, `mypy`, `ruff` (optional — development)

## Usage / 使用

```
kilee                        Start interactive chat / 启动交互式对话
kilee setup                  Setup wizard / 配置向导
kilee login                  Set API key / 设置 API Key
kilee logout                 Clear API key / 清除 API Key
kilee whoami                 Show current config / 查看当前配置
kilee doctor                 Check dependencies / 检查依赖
kilee settings               Show full config / 显示完整配置
kilee approval [mode]        View / set approval mode / 设置审批模式
kilee banner                  Generate ASCII banner from image / 生成启动 Banner
kilee banner --set-default    Save banner as default on startup
kilee gateway                 Start multi-platform gateway (Telegram etc.)
kilee translate <text>       Convert natural language to shell command
```

### Slash Commands / 斜杠命令

| Command | Description |
|---|---|
| `/help` | Show all commands |
| `/clear` | Clear conversation |
| `/compact` | Compress context manually |
| `/memory` | View persistent memory |
| `/memory clear` | Wipe all memory |
| `/model [name]` | View / switch model |
| `/approval [mode]` | View / set approval mode (auto/suggest/never) |
| `/tips` | Show usage tips |
| `/exit` | Quit |

### Project Context / 项目上下文

Create a `KILEE.md` in your project root to give KiLee project-specific context:

```markdown
# My Project

## Stack
- Python 3.11, FastAPI, PostgreSQL

## Conventions
- Use type hints everywhere
- Tests in pytest
```

KiLee auto-loads this file on startup. Also supports `CLAUDE.md` and `AGENTS.md`.

## Gateway / 多平台网关

KiLee supports multi-platform messaging via a gateway architecture. Currently supports Telegram.

```bash
# Start Telegram gateway (token from env var or --telegram-token)
export KILEE_TELEGRAM_TOKEN="your_bot_token"
kilee gateway

# Or inline
kilee gateway --telegram-token "your_bot_token"
```

The gateway runs the full agent loop for each chat — tools, memory, approval, everything.

### Gateway Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/status` | Show model and approval mode |
| `/new` | Reset conversation |
| `/model` | Show active model |
| `/approval auto\|suggest\|never` | Set approval mode |

## Configuration / 配置

Config file: `~/.kilee/config.json`

```json
{
  "api_key": "sk-...",
  "model": "deepseek-chat",
  "base_url": "https://api.deepseek.com",
  "max_tokens": 8192
}
```

### Supported Providers / 支持的供应商

| Provider | Base URL | Models |
|---|---|---|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat`, `deepseek-reasoner` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4o-mini` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | any model |
| Custom | your URL | any OpenAI-compatible |

## Project Structure / 项目结构

```
kilee/
├── __init__.py
├── main.py          # CLI entry, slash commands
├── agent.py         # Agent loop, system prompt, streaming
├── config.py        # Configuration management
├── compressor.py    # Context compression
├── theme.py         # Visual theme / colors
├── tips.py          # Usage tips
├── setup.py         # First-run wizard
├── approval.py      # Risk-based tool approval system
├── banner.py        # Image-to-ASCII banner generator
├── gateway/
│   ├── __init__.py
│   ├── base.py          # PlatformAdapter abstract class
│   ├── telegram.py      # Telegram Bot API adapter
│   ├── runner.py        # GatewayRunner multi-platform dispatcher
│   └── agent_session.py # Headless agent session for gateway
└── tools/
    ├── __init__.py       # Tool registry & dispatch
    ├── execute_bash.py   # Shell command execution
    ├── fs_read.py        # File / directory reading + search
    ├── fs_write.py       # File creation & editing
    ├── memory.py         # Persistent cross-session memory
    ├── web_search.py     # Web search
    └── web_fetch.py      # URL content fetching
```

## Development / 开发

```bash
# Install in dev mode
pip install -e .

# Install dev dependencies
pip install pytest mypy ruff
```

## License / 许可

MIT

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Yunle-Lee/KiLee-agent&type=date&legend=top-left)](https://www.star-history.com/#Yunle-Lee/KiLee-agent&type=date&legend=top-left)

# Changelog

## v0.3.0 (2026-04-22)

### Added
- `kilee/approval.py`: risk-based tool approval system (inspired by DeepSeek TUI)
- Three approval modes: `auto`, `suggest`, `never`
- `/approval [mode]` slash command + `kilee approval [mode]` CLI command
- Welcome banner now shows current approval mode
- `kilee/banner.py`: ASCII banner generator (inspired by kilee.cn TUI Generator)
- `kilee banner <image>` CLI command — convert images to ASCII startup banners
- Custom banner support — `kilee banner image.png --set-default` replaces welcome art
- Pillow as optional `[banner]` dependency

### Changed
- Destructive tools (`execute_bash`, `fs_write`, `web_fetch`) require confirmation in `suggest` mode
- Benign tools (`fs_read`, `save_memory`, `web_search`) run silently
- System prompt updated to inform model about approval policy
- Version bumped to 0.3.0

## v0.2.0 (2026-04-22)

### Added
- `web_search` tool: search the web via DuckDuckGo
- `web_fetch` tool: fetch and extract content from URLs
- `kilee/tools/__init__.py`: centralized tool registry and dispatch
- `KILEE.md`: project context documentation for KiLee itself

### Changed
- Improved streaming output with better formatting
- Enhanced error handling in agent loop
- Better type hints across all modules
- Updated README with bilingual (English/Chinese) documentation
- Restructured project layout for clarity

### Fixed
- Graceful handling of API errors in streaming mode
- Tool call display now properly shows completion status

## v0.1.0 (2026-04-22)

### Added
- Initial release
- 4 core tools: `execute_bash`, `fs_read`, `fs_write`, `save_memory`
- Interactive CLI with prompt_toolkit
- Multi-provider support (DeepSeek, OpenAI, Groq, OpenRouter)
- Context Engineering: auto-load `KILEE.md` / `CLAUDE.md` / `AGENTS.md`
- Context compression (`/compact` command + auto-compress)
- Persistent memory across sessions
- Rich terminal UI with banners, spinners, and syntax highlighting
- Slash commands: `/help`, `/clear`, `/compact`, `/memory`, `/model`, `/tips`, `/exit`
- CLI subcommands: `kilee`, `kilee setup`, `kilee login`, `kilee logout`, `kilee whoami`, `kilee doctor`, `kilee settings`, `kilee translate`
- First-run interactive setup wizard

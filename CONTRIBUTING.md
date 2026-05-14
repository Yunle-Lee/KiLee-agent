# Contributing to KiLee Agent

Thanks for your interest in contributing! 🎉

## How to Contribute

### 1. Report Bugs

Open an issue with:
- A clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version)

### 2. Suggest Features

Open an issue with the `enhancement` tag:
- Describe the problem you're solving
- Propose the solution
- Any alternatives considered

### 3. Submit Code

#### Setup

```bash
git clone https://github.com/Yunle-Lee/KiLee-agent.git
cd KiLee-agent
pip install -e .
pip install pytest mypy ruff
```

#### Code Style

- **Type hints**: All functions must have type annotations
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Line length**: max 100 characters
- **Format**: Follow existing code style (ruff compatible)

#### Adding a New Tool

1. Create `kilee/tools/<name>.py`
2. Define `SCHEMA` dict (OpenAI function-calling format)
3. Implement `run(**kwargs) -> str` function
4. Register in `kilee/tools/__init__.py` (`TOOLS` list + `dispatch`)
5. Add tool icon to `kilee/theme.py` (`TOOL_ICONS` dict)
6. Add display logic in `kilee/agent.py` (`_tool_label` function)

#### Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes
4. Run checks:
   ```bash
   ruff check kilee/
   python -m pytest tests/
   ```
5. Commit with clear messages
6. Push and open a PR

#### Commit Convention

```
<type>: <description>

feat:     new feature
fix:      bug fix
docs:     documentation
style:    formatting
refactor: code restructuring
test:     adding tests
chore:    build/config
```

## Code of Conduct

Be respectful and constructive. Harassment and trolling are not tolerated.

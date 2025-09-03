## Brief overview
This rule ensures consistent Python environment management across all development activities, preventing conflicts with system Python installations and maintaining project isolation.

## Virtual Environment Usage
- Always use the project's virtual environment (`venv`) when executing Python scripts
- Never install packages system-wide or modify system Python
- Create virtual environment in `game-server/backend/venv/` for backend development
- Activate virtual environment before running any Python commands

## Environment Setup
- Use `python3 -m venv venv` to create virtual environments
- Activate with `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- Install dependencies with `pip install -r requirements.txt` after activation
- Deactivate with `deactivate` when finished

## Command Execution
- Always prefix Python commands with virtual environment activation
- Use `python` instead of `python3` after venv activation
- Example: `source venv/bin/activate && python -m pytest tests/`

## Error Prevention
- Avoid "externally-managed-environment" errors by never using system pip
- Use virtual environments to prevent package conflicts
- Keep system Python clean for OS-level operations

## Development Workflow
- Activate venv at start of development session
- Keep venv active during coding/testing cycles
- Only deactivate when switching projects or system maintenance

# AGENTS.md - KuaiDiary Development Guide

## Project Overview

**KuaiDiary** is a lightweight, pure text diary application built with Python and Tkinter (via the `tinui` library). It stores diaries as plain text files in the `./datas` directory.

## Build & Run Commands

### Running the Application

```bash
# Install dependencies first
pip install tinui

# Run the application
python main.py
```

### VS Code Debugging

The project includes a `.vscode/launch.json` configuration for debugging:
- Debug configuration: "Python 调试程序: 当前文件"
- Entry point: `${workspaceFolder}/main.py`
- Console: integratedTerminal

### Linting & Type Checking

No explicit linting or type checking configuration found. If adding, consider:
- `pylint` or `ruff` for linting
- `mypy` for type checking

### Testing

No test suite exists in this project.
## Code Style Guidelines

### General Conventions

- **Language**: Chinese comments and docstrings throughout the codebase
- **Encoding**: UTF-8 for all files
- **Indentation**: 4 spaces (no tabs)
- **Line endings**: Unix-style (LF) preferred

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `class MainWindow`, `class Diary` |
| Functions | snake_case | `def init_work_dir()`, `def save_diary()` |
| Variables | snake_case | `month_dir`, `file_path`, `now_month` |
| Constants | UPPER_SNAKE_CASE | Not heavily used, but follow if present |

### Type Hints

Minimal usage - only when clear benefit:
```python
# Good
def __init__(self, date: datetime.date):
def exist_diary(date: datetime.date) -> bool:

# Less common in this codebase
def save_diary(diary):  # No type hint
```

### Imports

- Standard library first, then third-party, then local
- Absolute imports for local modules:
```python
from ui.mainwindow import MainWindow
from core.files import init_work_dir
from core.settings import init_settings
import data  # Local module
```

### Error Handling

The codebase has inconsistent error handling:
- Avoid bare `except:` clauses
- Prefer specific exceptions:
```python
# Preferred
try:
    e.widget.edit_undo()
except Exception as e:
    pass  # Or log the error
```

### File Organization

```
KuaiDiary/
├── main.py              # Entry point
├── core/                # Core business logic
│   ├── diary.py         # Diary data model
│   ├── files.py         # File I/O operations
|   ├── image_db.py      # Image data base
│   └── settings.py      # Settings management
├── ui/                  # UI components
│   ├── mainwindow.py    # Main window
│   ├── today.py         # Today's diary view
│   ├── dates.py         # Past dates view
│   ├── export.py        # Export functionality
│   └── setting.py       # Settings UI
├── control/             # Controllers/helpers
│   ├── editor.py        # Editor configuration
│   ├── dates_diary.py
│   ├── settings.py
│   └── today_diary.py
├── datas/               # Diary storage (runtime created)
└── settings/            # Settings storage
```

### UI Development

- Uses `tinui` library (Tkinter wrapper)
- Theme support (light/dark) via `data.settings['theme']`
- UI components inherit from `BasicTinUI`, `ExpandPanel`, etc.
- Chinese text for all UI labels

### Database/Storage

- Plain text files in `./datas/`
- Directory structure: `./datas/YYYY-MM/DD`
- UTF-8 encoding for all files
- Auto-save on close

## Development Notes

### Key Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `core/files.py` | All file I/O, save/load operations |
| `ui/mainwindow.py` | Main window and navigation |
| `data.py` | Global data shared across modules |

### Common Patterns

```python
# Global settings access
import data
theme = data.settings.get('theme', 'light')

# Date handling
import datetime
month = datetime.date.today().strftime("%Y-%m")

# File operations
with open(file_path, "w", encoding="utf-8") as f:
    f.write(contents)
```

### Things to Avoid

1. **Hardcoding paths** - Use `data.work_dir` instead
2. **Bare except clauses** - Use specific exceptions
3. **Global state** - Use `data.py` module for shared state
4. **Magic numbers** - Extract to constants

## Adding New Features

1. Follow the existing file organization pattern
2. Use existing imports structure
3. Add Chinese comments/docstrings
4. Test manually by running `python main.py`

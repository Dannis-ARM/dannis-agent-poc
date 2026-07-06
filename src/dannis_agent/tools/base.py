"""Base tool definitions and utilities."""

from pathlib import Path
from typing import Any, Callable, Dict, Tuple

# Project root - restrict file operations to this directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()

# Safe shell commands whitelist
SAFE_COMMANDS = [
    "ls", "dir", "echo", "cat", "type", "pwd", "cd", "mkdir", "rmdir",
    "touch", "cp", "copy", "mv", "move", "rm", "del", "head", "tail",
    "grep", "find", "where", "which", "python", "python3", "pip", "uv",
]


def safe_join_path(base: Path, relative_path: str) -> Tuple[Path, bool]:
    """Safely join paths and ensure it's within the project root."""
    try:
        target = (base / relative_path).resolve()
        base = base.resolve()
        return target, base in target.parents or target == base
    except Exception:
        return base, False

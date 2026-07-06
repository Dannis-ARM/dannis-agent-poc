"""File operation tools for the ReAct Agent."""

from pathlib import Path
from typing import Any, Dict

from .base import PROJECT_ROOT, safe_join_path


def confirm_action(prompt: str) -> bool:
    """Ask user for confirmation before executing potentially dangerous actions."""
    from colorama import Fore, Style

    while True:
        response = input(f"{Fore.YELLOW}{prompt} [y/N] {Style.RESET_ALL}").strip().lower()
        if response in ["y", "yes"]:
            return True
        if response in ["", "n", "no"]:
            return False
        print("Please answer y or n.")


def tool_read_file(kwargs: Dict[str, Any], unsafe_mode: bool = False) -> str:
    """Read a file."""
    file_path = kwargs.get("file_path", "")
    full_path, is_safe = safe_join_path(PROJECT_ROOT, file_path)

    if not is_safe:
        return f"Error: Access to path outside project root is restricted: {file_path}"

    try:
        return full_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


def tool_write_file(kwargs: Dict[str, Any], unsafe_mode: bool = False) -> str:
    """Write to a file."""
    file_path = kwargs.get("file_path", "")
    content = kwargs.get("content", "")
    full_path, is_safe = safe_join_path(PROJECT_ROOT, file_path)

    if not is_safe:
        return f"Error: Access to path outside project root is restricted: {file_path}"

    if not unsafe_mode:
        if full_path.exists():
            if not confirm_action(f"File {file_path} exists, overwrite?"):
                return "Action cancelled by user."
        else:
            if not confirm_action(f"Create new file {file_path}?"):
                return "Action cancelled by user."

    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


def tool_list_dir(kwargs: Dict[str, Any], unsafe_mode: bool = False) -> str:
    """List directory contents."""
    dir_path = kwargs.get("dir_path", ".")
    full_path, is_safe = safe_join_path(PROJECT_ROOT, dir_path)

    if not is_safe:
        return f"Error: Access to path outside project root is restricted: {dir_path}"

    try:
        if not full_path.is_dir():
            return f"Error: Not a directory: {dir_path}"

        items = []
        for item in full_path.iterdir():
            prefix = "[DIR]" if item.is_dir() else "[FILE]"
            items.append(f"{prefix} {item.name}")

        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {e}"

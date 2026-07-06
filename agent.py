#!/usr/bin/env python3
"""
ReAct Agent Demo - COMPATIBILITY WRAPPER
This file exists for backward compatibility. New code should import from
the dannis_agent package.
"""

import sys
from pathlib import Path

# Add src to path so we can import the new package
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Re-export everything for backward compatibility
from dannis_agent.agent import (
    ReActAgent,
    save_log,
    parse_action,
)
from dannis_agent.tools import (
    tool_read_file,
    tool_write_file,
    tool_list_dir,
    tool_run_shell,
    tool_python_repl,
    TOOL_REGISTRY,
    safe_join_path,
    PROJECT_ROOT,
    SAFE_COMMANDS,
)
from dannis_agent.memory import SessionManager

# Also keep the old main function working
from dannis_agent.cli import main

__all__ = [
    "PROJECT_ROOT",
    "SAFE_COMMANDS",
    "SYSTEM_PROMPT",
    "safe_join_path",
    "confirm_action",
    "tool_read_file",
    "tool_write_file",
    "tool_list_dir",
    "tool_run_shell",
    "tool_python_repl",
    "TOOL_REGISTRY",
    "SessionManager",
    "parse_action",
    "ReActAgent",
    "save_log",
    "main",
]

# Import SYSTEM_PROMPT separately
from dannis_agent.llm import SYSTEM_PROMPT


# Add confirm_action for backward compatibility
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


if __name__ == "__main__":
    main()

"""Shell and Python REPL tools for the ReAct Agent."""

import io
import contextlib
import subprocess
from typing import Any, Dict

from .base import SAFE_COMMANDS


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


def tool_run_shell(kwargs: Dict[str, Any], unsafe_mode: bool = False) -> str:
    """Run a shell command."""
    from .base import PROJECT_ROOT

    command = kwargs.get("command", "")

    if not unsafe_mode:
        cmd_parts = command.split()
        if not cmd_parts:
            return "Error: Empty command"

        base_cmd = cmd_parts[0].lower()
        if base_cmd not in SAFE_COMMANDS:
            return f"Error: Command '{base_cmd}' not in whitelist. Use --unsafe to enable all commands."

        if not confirm_action(f"Execute command: {command}?"):
            return "Action cancelled by user."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[Return code: {result.returncode}]"
        return output.strip() or "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {e}"


def tool_python_repl(kwargs: Dict[str, Any], unsafe_mode: bool = False) -> str:
    """Execute Python code."""
    code = kwargs.get("code", "")

    if not unsafe_mode:
        if not confirm_action(f"Execute Python code?\n---\n{code}\n---"):
            return "Action cancelled by user."

    try:
        safe_globals = {
            "__builtins__": {
                "print": print, "len": len, "range": range, "str": str, "int": int,
                "float": float, "list": list, "dict": dict, "set": set, "tuple": tuple,
                "bool": bool, "sum": sum, "min": min, "max": max, "abs": abs, "round": round,
            }
        }

        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, safe_globals, {})

        output = stdout_capture.getvalue()
        return output.strip() or "Code executed successfully (no output)"
    except Exception as e:
        return f"Error executing Python: {type(e).__name__}: {e}"

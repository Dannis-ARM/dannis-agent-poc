"""Tool registry for the ReAct Agent."""

from typing import Any, Callable, Dict

from .files import tool_read_file, tool_write_file, tool_list_dir
from .shell import tool_run_shell, tool_python_repl


ToolFunc = Callable[[Dict[str, Any], bool], str]

TOOL_REGISTRY: Dict[str, ToolFunc] = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "list_dir": tool_list_dir,
    "run_shell": tool_run_shell,
    "python_repl": tool_python_repl,
}

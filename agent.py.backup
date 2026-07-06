#!/usr/bin/env python3
"""
ReAct Agent Demo
A simple ReAct (Reasoning + Acting) agent for learning AI agent concepts.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import colorama
import httpx
from colorama import Fore, Style
from dotenv import load_dotenv

# Initialize colorama for cross-platform colored output
colorama.init()

# Project root - restrict file operations to this directory
PROJECT_ROOT = Path(__file__).parent.resolve()

# Safe shell commands whitelist
SAFE_COMMANDS = [
    "ls", "dir", "echo", "cat", "type", "pwd", "cd", "mkdir", "rmdir",
    "touch", "cp", "copy", "mv", "move", "rm", "del", "head", "tail",
    "grep", "find", "where", "which", "python", "python3", "pip", "uv",
]


SYSTEM_PROMPT = """You are a ReAct (Reasoning + Acting) agent. Your goal is to help the user by reasoning through tasks and using available tools.

CRITICAL: YOU MUST FOLLOW THIS EXACT RESPONSE FORMAT FOR EVERY MESSAGE:

IF YOU NEED TO USE A TOOL:
```
Thought: <your step-by-step reasoning explaining why you chose this tool>
Action: <tool_name>|<json_parameters>
```

IF YOU ARE READY TO GIVE THE FINAL ANSWER:
```
Thought: <your reasoning explaining why you're done and what you've accomplished>
Final Answer: <the final answer to the user>
```

RULES YOU MUST NEVER BREAK:
1. EVERY RESPONSE MUST START WITH "Thought:" - no exceptions!
2. ALWAYS explain your reasoning in the Thought block before taking action
3. Use exactly ONE tool per Action step
4. Wait for Observation before deciding next step
5. When you have enough information, output Final Answer with its own preceding Thought
6. Never skip the Thought block - it's required for both Action and Final Answer!

Available tools:
- read_file(file_path): Read a file
- write_file(file_path, content): Write content to a file
- list_dir(dir_path): List directory contents (default: ".")
- run_shell(command): Execute a shell command
- python_repl(code): Execute Python code

Project root directory: {project_root}
You can only operate within this directory.
"""


def safe_join_path(base: Path, relative_path: str) -> Tuple[Path, bool]:
    """Safely join paths and ensure it's within the project root."""
    try:
        target = (base / relative_path).resolve()
        base = base.resolve()
        return target, base in target.parents or target == base
    except Exception:
        return base, False


def confirm_action(prompt: str) -> bool:
    """Ask user for confirmation before executing potentially dangerous actions."""
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


def tool_run_shell(kwargs: Dict[str, Any], unsafe_mode: bool = False) -> str:
    """Run a shell command."""
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

        import io
        import contextlib

        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, safe_globals, {})

        output = stdout_capture.getvalue()
        return output.strip() or "Code executed successfully (no output)"
    except Exception as e:
        return f"Error executing Python: {type(e).__name__}: {e}"


TOOL_REGISTRY: Dict[str, Callable] = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "list_dir": tool_list_dir,
    "run_shell": tool_run_shell,
    "python_repl": tool_python_repl,
}


class SessionManager:
    """Manages session persistence and retrieval."""

    SESSIONS_DIR = PROJECT_ROOT / "memory"

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or self.SESSIONS_DIR
        self.memory_dir.mkdir(exist_ok=True)

    def generate_session_id(self) -> str:
        """Generate a unique session ID based on current timestamp."""
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    def create_new_session(self) -> str:
        """Create a new empty session file and return its ID."""
        session_id = self.generate_session_id()
        session_file = self.memory_dir / f"session-{session_id}.jsonl"
        session_file.touch()
        return session_id

    def append_message(self, session_id: str, role: str, content: str, timestamp: str) -> None:
        """Append a message to the session file."""
        session_file = self.memory_dir / f"session-{session_id}.jsonl"
        msg = {"role": role, "content": content, "timestamp": timestamp}
        with session_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    def load_session(self, session_id: str) -> List[Dict[str, str]]:
        """Load all messages from a session file."""
        session_file = self.memory_dir / f"session-{session_id}.jsonl"
        if not session_file.exists():
            return []
        messages = []
        for line in session_file.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                messages.append(json.loads(line))
        return messages

    def list_sessions(self) -> List[str]:
        """List session IDs, newest first."""
        session_files = sorted(
            self.memory_dir.glob("session-*.jsonl"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        sessions = []
        for sf in session_files:
            sid = sf.stem.replace("session-", "")
            sessions.append(sid)
        return sessions

    def get_latest_session(self) -> Optional[str]:
        """Return the newest session ID, or None if none exist."""
        sessions = self.list_sessions()
        return sessions[0] if sessions else None

    def session_exists(self, session_id: str) -> bool:
        """Check whether a session file exists."""
        session_file = self.memory_dir / f"session-{session_id}.jsonl"
        return session_file.exists()

    def to_agent_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Convert session messages to agent format (without timestamps)."""
        messages = self.load_session(session_id)
        return [{"role": m["role"], "content": m["content"]} for m in messages]


def parse_action(response: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse Thought, Action (tool_name|params), or Final Answer from response."""
    # First, extract code block if present
    code_block_match = re.search(r"```([\s\S]*?)```", response)
    if code_block_match:
        content = code_block_match.group(1).strip()
    else:
        content = response.strip()

    # Look for Thought - match everything until Action or Final Answer, or end
    thought_match = re.search(r"Thought:\s*(.*?)(?=\n\s*(?:Action|Final Answer):|$)", content, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else None

    # If no Thought found but we have content, maybe the whole thing is thought + something else
    if not thought and content and not re.match(r"^(Action|Final Answer):", content.strip(), re.IGNORECASE):
        # Look for any action or final answer markers
        has_action = "Action:" in content
        has_final = "Final Answer:" in content
        if has_action or has_final:
            # Split before the first marker
            split_idx = content.find("Action:") if has_action else content.find("Final Answer:")
            thought = content[:split_idx].strip() or None
            content = content[split_idx:].strip()

    # Look for Action with | separator
    action_match = re.search(r"Action:\s*(\w+)\s*\|\s*(\{.*?\})", content, re.DOTALL)
    if action_match:
        tool_name = action_match.group(1).strip()
        params_str = action_match.group(2).strip()
        return thought, tool_name, params_str

    # Look for Action without |, just on next line
    action_match2 = re.search(r"Action:\s*(\w+)\s*\n\s*(\{.*?\})", content, re.DOTALL)
    if action_match2:
        tool_name = action_match2.group(1).strip()
        params_str = action_match2.group(2).strip()
        return thought, tool_name, params_str

    # Look for Action with params on same line (maybe not properly formatted)
    action_match3 = re.search(r"Action:\s*(\w+)\s+(\{.*?\})", content, re.DOTALL)
    if action_match3:
        tool_name = action_match3.group(1).strip()
        params_str = action_match3.group(2).strip()
        return thought, tool_name, params_str

    # Look for Final Answer
    final_match = re.search(r"Final Answer:\s*([\s\S]*)", content)
    if final_match:
        return thought, "__FINAL__", final_match.group(1).strip()

    # If no format found but we have content, treat as Final Answer
    if content:
        # Use thought if we have it, otherwise use content as final answer
        if thought:
            return thought, "__FINAL__", content
        else:
            return None, "__FINAL__", content

    return thought, None, None


class ReActAgent:
    """Simple ReAct Agent implementation."""

    def __init__(self, api_key: str, base_url: str, model: str, unsafe_mode: bool = False, verbose: bool = True, streaming: bool = True):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.unsafe_mode = unsafe_mode
        self.verbose = verbose
        self.streaming = streaming
        self.messages: List[Dict[str, str]] = []

    def _call_llm_streaming(self) -> str:
        """Call the LLM with streaming support."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        system_msg = SYSTEM_PROMPT.format(project_root=PROJECT_ROOT)

        payload = {
            "model": self.model,
            "system": system_msg,
            "messages": self.messages,
            "max_tokens": 4096,
            "temperature": 0.7,
            "stream": True,
        }

        full_response = []

        with httpx.Client(timeout=120.0) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()

                # Try to handle SSE streaming format first
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            # Handle different streaming response formats
                            if "delta" in data:
                                delta = data["delta"]
                                if "text" in delta:
                                    text = delta["text"]
                                    full_response.append(text)
                                    if self.verbose:
                                        print(f"{Fore.CYAN}{text}{Style.RESET_ALL}", end="", flush=True)
                            elif "content" in data and len(data["content"]) > 0:
                                text = data["content"][0].get("text", "")
                                if text:
                                    full_response.append(text)
                                    if self.verbose:
                                        print(f"{Fore.CYAN}{text}{Style.RESET_ALL}", end="", flush=True)
                        except json.JSONDecodeError:
                            continue
                    elif line.strip() and not line.startswith(":"):
                        # Fallback: if line doesn't look like SSE, try direct JSON
                        try:
                            data = json.loads(line)
                            if "content" in data and len(data["content"]) > 0:
                                text = data["content"][0].get("text", "")
                                if text:
                                    full_response.append(text)
                                    if self.verbose:
                                        print(f"{Fore.CYAN}{text}{Style.RESET_ALL}", end="", flush=True)
                        except json.JSONDecodeError:
                            continue

        # If streaming didn't get anything (maybe API doesn't support stream=True),
        # fall back to non-streaming
        if not full_response:
            return self._call_llm_non_streaming()

        if self.verbose:
            print()  # New line after streaming completes

        return "".join(full_response)

    def _call_llm_non_streaming(self) -> str:
        """Call the LLM without streaming (fallback)."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        system_msg = SYSTEM_PROMPT.format(project_root=PROJECT_ROOT)

        payload = {
            "model": self.model,
            "system": system_msg,
            "messages": self.messages,
            "max_tokens": 4096,
            "temperature": 0.7,
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            text = result["content"][0]["text"]
            if self.verbose:
                print(f"{Fore.CYAN}{text}{Style.RESET_ALL}")
            return text

    def _call_llm(self) -> str:
        """Call the LLM with streaming option."""
        if self.streaming:
            return self._call_llm_streaming()
        else:
            return self._call_llm_non_streaming()

    def clear_history(self) -> None:
        """Reset conversation history."""
        self.messages = []

    def run(self, user_query: str, max_iterations: int = 10) -> str:
        """Run the agent on a user query, retaining conversation context."""
        self.messages.append({"role": "user", "content": user_query})

        if self.verbose:
            print(f"\n{Fore.CYAN}--- ReAct Agent Started ---{Style.RESET_ALL}")
            print(f"{Fore.GREEN}User: {Style.RESET_ALL}{user_query}\n")

        for i in range(max_iterations):
            if self.verbose:
                print(f"\n{Fore.MAGENTA}Step {i + 1}/{max_iterations}{Style.RESET_ALL}")

            try:
                assistant_msg = self._call_llm()
            except Exception as e:
                return f"Error calling model: {e}"

            thought, action, params_str = parse_action(assistant_msg)

            if self.verbose and not self.streaming:
                if thought:
                    print(f"{Fore.BLUE}Thought: {Style.RESET_ALL}{thought}")
                if action and action != "__FINAL__":
                    print(f"{Fore.CYAN}Action: {Style.RESET_ALL}{action}")

            self.messages.append({"role": "assistant", "content": assistant_msg})

            if action == "__FINAL__":
                final_answer = params_str or thought or "Done."
                if self.verbose:
                    print(f"\n{Fore.GREEN}Final Answer: {Style.RESET_ALL}{final_answer}")
                return final_answer

            if action and action in TOOL_REGISTRY:
                try:
                    params = json.loads(params_str) if params_str else {}
                except json.JSONDecodeError:
                    params = {}

                if self.verbose and params:
                    print(f"{Fore.CYAN}Params: {Style.RESET_ALL}{json.dumps(params, indent=2, ensure_ascii=False)}")

                observation = TOOL_REGISTRY[action](params, self.unsafe_mode)

                if self.verbose:
                    print(f"{Fore.YELLOW}Observation: {Style.RESET_ALL}{observation}\n")

                self.messages.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                if action:
                    observation = f"Unknown tool: {action}"
                else:
                    observation = "Could not parse Action from response. Please use format: Action: tool_name|<json_params>"

                if self.verbose:
                    print(f"{Fore.RED}Observation: {Style.RESET_ALL}{observation}\n")

                self.messages.append({"role": "user", "content": f"Observation: {observation}"})

        return f"Reached max iterations ({max_iterations})."


def save_log(conversation: List[Dict[str, str]], log_dir: Path = PROJECT_ROOT / "logs") -> None:
    """Save conversation to a log file."""
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"conversation_{timestamp}.json"

    log_data = {"timestamp": datetime.now().isoformat(), "messages": conversation}
    log_file.write_text(json.dumps(log_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{Fore.GREEN}Log saved to: {Style.RESET_ALL}{log_file}")


def main():
    parser = argparse.ArgumentParser(description="ReAct Agent Demo")
    parser.add_argument("query", nargs="*", help="User query (if not provided, enter interactive mode)")
    parser.add_argument("--unsafe", action="store_true", help="Disable safety restrictions (use with caution)")
    parser.add_argument("--quiet", action="store_true", help="Disable verbose output")
    parser.add_argument("--max-iter", type=int, default=10, help="Max iterations (default: 10)")
    parser.add_argument("--no-log", action="store_true", help="Don't save conversation log")
    parser.add_argument("--no-streaming", action="store_true", help="Disable streaming output")
    parser.add_argument("--list-sessions", action="store_true", help="List recent sessions")
    parser.add_argument("--resume", type=str, metavar="SESSION_ID", help="Resume a specific session")
    parser.add_argument("--resume-last", action="store_true", help="Resume the most recent session")
    parser.add_argument("--new-session", action="store_true", help="Start a new session (default)")

    args = parser.parse_args()

    load_dotenv()

    api_key = os.getenv("DOUBAO_API_KEY")
    if not api_key:
        print(f"{Fore.RED}Error: DOUBAO_API_KEY not set in .env{Style.RESET_ALL}")
        sys.exit(1)

    base_url = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding")
    model = os.getenv("DOUBAO_MODEL", "doubao-seed-2-0-code-preview-latest")

    session_mgr = SessionManager()

    # Handle --list-sessions
    if args.list_sessions:
        sessions = session_mgr.list_sessions()
        if sessions:
            print(f"\n{Fore.CYAN}Recent sessions:{Style.RESET_ALL}")
            for i, sid in enumerate(sessions, 1):
                sf = session_mgr.memory_dir / f"session-{sid}.jsonl"
                size = sf.stat().st_size
                print(f"  {i}. {sid}  ({size} bytes)")
        else:
            print(f"{Fore.YELLOW}No sessions found.{Style.RESET_ALL}")
        return

    # Resolve session ID
    if args.resume:
        session_id = args.resume
        if not session_mgr.session_exists(session_id):
            print(f"{Fore.RED}Error: Session {session_id} not found.{Style.RESET_ALL}")
            sys.exit(1)
    elif args.resume_last:
        session_id = session_mgr.get_latest_session()
        if not session_id:
            print(f"{Fore.YELLOW}No previous sessions to resume. Starting new session.{Style.RESET_ALL}")
            session_id = session_mgr.create_new_session()
    else:
        session_id = session_mgr.create_new_session()

    agent = ReActAgent(
        api_key=api_key,
        base_url=base_url,
        model=model,
        unsafe_mode=args.unsafe,
        verbose=not args.quiet,
        streaming=not args.no_streaming
    )

    # Load existing session messages into agent
    existing_messages = session_mgr.to_agent_messages(session_id)
    if existing_messages:
        agent.messages = existing_messages
        if not args.quiet:
            print(f"{Fore.CYAN}Resumed session: {session_id} ({len(existing_messages)} messages){Style.RESET_ALL}")

    if args.query:
        query = " ".join(args.query)
        result = agent.run(query, max_iterations=args.max_iter)
        # Save to session
        timestamp = datetime.now().isoformat()
        session_mgr.append_message(session_id, "user", query, timestamp)
        session_mgr.append_message(session_id, "assistant", result, timestamp)
        if not args.no_log:
            save_log(agent.messages)
        print()
    else:
        if not args.resume and not args.resume_last:
            print(f"{Fore.CYAN}Session: {session_id}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╔════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║     ReAct Agent Interactive Mode       ║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║  Type 'exit' or 'quit' to exit         ║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚════════════════════════════════════════╝{Style.RESET_ALL}")
        print()

        while True:
            try:
                query = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "q"]:
                    break

                timestamp = datetime.now().isoformat()
                result = agent.run(query, max_iterations=args.max_iter)
                # Save to session
                session_mgr.append_message(session_id, "user", query, timestamp)
                session_mgr.append_message(session_id, "assistant", result, timestamp)
                print()
            except KeyboardInterrupt:
                print("\n^C")
                break
            except EOFError:
                print()
                break

        if not args.no_log:
            save_log(agent.messages)


if __name__ == "__main__":
    main()

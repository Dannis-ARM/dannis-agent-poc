"""LLM client for the ReAct Agent."""

import json
from pathlib import Path
from typing import Any, Dict, List

import httpx
from colorama import Fore, Style

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()

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


class LLMClient:
    """LLM client with streaming support."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        verbose: bool = True,
        streaming: bool = True
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.verbose = verbose
        self.streaming = streaming

    def complete(self, messages: List[Dict[str, str]]) -> str:
        """Call the LLM with the given messages."""
        if self.streaming:
            return self._complete_streaming(messages)
        else:
            return self._complete_non_streaming(messages)

    def _complete_streaming(self, messages: List[Dict[str, str]]) -> str:
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
            "messages": messages,
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
            return self._complete_non_streaming(messages)

        if self.verbose:
            print()  # New line after streaming completes

        return "".join(full_response)

    def _complete_non_streaming(self, messages: List[Dict[str, str]]) -> str:
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
            "messages": messages,
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

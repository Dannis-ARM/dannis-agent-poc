"""Core ReAct Agent implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from colorama import Fore, Style

from ..llm import LLMClient
from ..tools import TOOL_REGISTRY
from .parser import parse_action

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()


class ReActAgent:
    """Simple ReAct Agent implementation."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        unsafe_mode: bool = False,
        verbose: bool = True,
        streaming: bool = True
    ):
        self.llm_client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            verbose=verbose,
            streaming=streaming
        )
        self.unsafe_mode = unsafe_mode
        self.verbose = verbose
        self.messages: List[Dict[str, str]] = []

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
                assistant_msg = self.llm_client.complete(self.messages)
            except Exception as e:
                return f"Error calling model: {e}"

            thought, action, params_str = parse_action(assistant_msg)

            if self.verbose and not self.llm_client.streaming:
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

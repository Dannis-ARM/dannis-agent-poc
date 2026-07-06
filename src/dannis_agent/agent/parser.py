"""Response parsing for the ReAct Agent."""

import re
import json
from typing import Any, Dict, Optional, Tuple


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

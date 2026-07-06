"""Session management for the ReAct Agent."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Project root - restrict file operations to this directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()


class Session:
    """A single conversation session."""

    def __init__(self, session_id: str, messages: Optional[List[Dict[str, str]]] = None):
        self.session_id = session_id
        self.messages = messages or []


class Conversation:
    """A conversation with user and assistant messages."""

    def __init__(self, messages: Optional[List[Dict[str, str]]] = None):
        self.messages = messages or []


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

    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
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

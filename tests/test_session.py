"""Tests for SessionManager."""
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import from the agent module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import SessionManager


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_session_manager_creates_memory_dir(self, tmp_path):
        """It should create the memory directory if it doesn't exist."""
        memory_dir = tmp_path / "memory"
        assert not memory_dir.exists()

        manager = SessionManager(memory_dir=memory_dir)
        assert memory_dir.exists()

    def test_generate_session_id(self, tmp_path):
        """It should generate session IDs in the correct format."""
        manager = SessionManager(memory_dir=tmp_path / "memory")
        session_id = manager.generate_session_id()
        # Verify format: YYYYMMDD-HHMMSS
        parts = session_id.split("-")
        assert len(parts) == 2
        assert len(parts[0]) == 8  # 8 digits for date
        assert len(parts[1]) == 6  # 6 digits for time

    def test_create_new_session(self, tmp_path):
        """It should create a new session file."""
        memory_dir = tmp_path / "memory"
        manager = SessionManager(memory_dir=memory_dir)

        session_id = manager.create_new_session()

        assert session_id is not None
        session_file = memory_dir / f"session-{session_id}.jsonl"
        assert session_file.exists()
        # New session file should be empty
        assert session_file.read_text().strip() == ""

    def test_save_and_load_session(self, tmp_path):
        """It should save and load messages to/from a session file."""
        memory_dir = tmp_path / "memory"
        manager = SessionManager(memory_dir=memory_dir)
        session_id = manager.create_new_session()

        messages = [
            {"role": "user", "content": "Hello", "timestamp": "2025-07-03T14:30:00"},
            {"role": "assistant", "content": "Hi there", "timestamp": "2025-07-03T14:30:01"},
        ]

        # Save messages
        for msg in messages:
            manager.append_message(session_id, msg["role"], msg["content"], msg["timestamp"])

        # Load messages
        loaded = manager.load_session(session_id)

        assert len(loaded) == 2
        assert loaded[0]["role"] == "user"
        assert loaded[0]["content"] == "Hello"
        assert loaded[1]["role"] == "assistant"
        assert loaded[1]["content"] == "Hi there"

    def test_list_sessions(self, tmp_path):
        """It should list sessions in order from newest to oldest."""
        import time

        memory_dir = tmp_path / "memory"
        manager = SessionManager(memory_dir=memory_dir)

        # Create sessions with different timestamps (session_id is second-precise)
        session_ids = []
        for _ in range(3):
            sid = manager.create_new_session()
            session_ids.append(sid)
            time.sleep(1.1)  # Ensure unique session_id (second-precise)

        sessions = manager.list_sessions()

        assert len(sessions) == 3
        assert sessions[0] == session_ids[2]  # newest first
        assert sessions[1] == session_ids[1]
        assert sessions[2] == session_ids[0]

    def test_get_latest_session(self, tmp_path):
        """It should return the most recent session."""
        import time

        memory_dir = tmp_path / "memory"
        manager = SessionManager(memory_dir=memory_dir)

        # Create sessions with time gap
        sid1 = manager.create_new_session()
        time.sleep(1.1)
        sid2 = manager.create_new_session()

        assert manager.get_latest_session() == sid2

    def test_get_latest_session_none_when_empty(self, tmp_path):
        """It should return None when there are no sessions."""
        memory_dir = tmp_path / "memory"
        manager = SessionManager(memory_dir=memory_dir)

        assert manager.get_latest_session() is None

    def test_session_exists(self, tmp_path):
        """It should check if a session exists."""
        memory_dir = tmp_path / "memory"
        manager = SessionManager(memory_dir=memory_dir)

        session_id = manager.create_new_session()

        assert manager.session_exists(session_id) is True
        assert manager.session_exists("nonexistent-session") is False

    def test_to_agent_messages(self, tmp_path):
        """It should convert session messages to agent message format."""
        memory_dir = tmp_path / "memory"
        manager = SessionManager(memory_dir=memory_dir)
        session_id = manager.create_new_session()

        manager.append_message(session_id, "user", "Hello", "2025-07-03T14:30:00")
        manager.append_message(session_id, "assistant", "Hi there", "2025-07-03T14:30:01")

        messages = manager.to_agent_messages(session_id)

        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "Hello"}
        assert messages[1] == {"role": "assistant", "content": "Hi there"}

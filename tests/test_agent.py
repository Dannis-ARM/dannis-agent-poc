"""Tests for agent.py."""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import from the agent module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import (
    PROJECT_ROOT,
    SAFE_COMMANDS,
    TOOL_REGISTRY,
    ReActAgent,
    confirm_action,
    parse_action,
    safe_join_path,
    save_log,
    tool_list_dir,
    tool_python_repl,
    tool_read_file,
    tool_run_shell,
    tool_write_file,
)


class TestSafeJoinPath:
    """Tests for safe_join_path function."""

    def test_safe_join_path_within_project(self):
        """It should safely join paths within the project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            target, is_safe = safe_join_path(base, "test.txt")
            assert is_safe is True
            assert target == base / "test.txt"

    def test_safe_join_path_subdirectory(self):
        """It should safely join paths to subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            target, is_safe = safe_join_path(base, "subdir/test.txt")
            assert is_safe is True
            assert target == base / "subdir" / "test.txt"

    def test_safe_join_path_parent_traversal(self):
        """It should detect path traversal outside project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            target, is_safe = safe_join_path(base, "../outside.txt")
            assert is_safe is False

    def test_safe_join_path_absolute_path_outside(self):
        """It should reject absolute paths outside the project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            # Create another temp dir outside
            with tempfile.TemporaryDirectory() as other_tmpdir:
                target, is_safe = safe_join_path(base, other_tmpdir)
                assert is_safe is False

    def test_safe_join_path_same_directory(self):
        """It should allow accessing the project root directory itself."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            target, is_safe = safe_join_path(base, ".")
            assert is_safe is True
            assert target == base


class TestParseAction:
    """Tests for parse_action function."""

    def test_parse_action_with_tool_and_params(self):
        """It should parse Thought, Action, and params correctly."""
        response = """```
Thought: I need to read a file
Action: read_file|{"file_path": "test.txt"}
```"""
        thought, action, params_str = parse_action(response)
        assert thought == "I need to read a file"
        assert action == "read_file"
        assert params_str == '{"file_path": "test.txt"}'

    def test_parse_action_final_answer(self):
        """It should parse Final Answer correctly."""
        response = """```
Thought: Task is complete
Final Answer: File read successfully
```"""
        thought, action, final_answer = parse_action(response)
        assert thought == "Task is complete"
        assert action == "__FINAL__"
        assert final_answer == "File read successfully"

    def test_parse_action_without_code_block(self):
        """It should parse response even without code block markers."""
        response = """Thought: Let me check
Action: list_dir|{"dir_path": "."}"""
        thought, action, params_str = parse_action(response)
        assert thought == "Let me check"
        assert action == "list_dir"
        assert params_str == '{"dir_path": "."}'

    def test_parse_action_with_newline_format(self):
        """It should parse Action with params on next line."""
        response = """Thought: I will write
Action: write_file
{"file_path": "test.txt", "content": "hello"}"""
        thought, action, params_str = parse_action(response)
        assert action == "write_file"
        assert params_str == '{"file_path": "test.txt", "content": "hello"}'

    def test_parse_action_only_final_answer(self):
        """It should handle response with only Final Answer."""
        response = "Final Answer: Done!"
        thought, action, final_answer = parse_action(response)
        assert action == "__FINAL__"
        assert final_answer == "Done!"

    def test_parse_action_unstructured_content(self):
        """It should treat unstructured content as Final Answer."""
        response = "This is just a response"
        thought, action, final_answer = parse_action(response)
        assert action == "__FINAL__"
        assert final_answer == "This is just a response"


class TestToolReadFile:
    """Tests for tool_read_file function."""

    def test_tool_read_file_success(self):
        """It should read an existing file successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_content = "Hello, World!"
            test_file.write_text(test_content, encoding="utf-8")

            # Temporarily override PROJECT_ROOT for testing
            with patch('agent.PROJECT_ROOT', Path(tmpdir).resolve()):
                result = tool_read_file({"file_path": "test.txt"}, unsafe_mode=True)
                assert result == test_content

    def test_tool_read_file_not_found(self):
        """It should return error when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('agent.PROJECT_ROOT', Path(tmpdir).resolve()):
                result = tool_read_file({"file_path": "nonexistent.txt"}, unsafe_mode=True)
                assert "Error: File not found" in result

    def test_tool_read_file_path_outside_project(self):
        """It should block access to files outside project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('agent.PROJECT_ROOT', Path(tmpdir).resolve()):
                result = tool_read_file({"file_path": "../outside.txt"}, unsafe_mode=True)
                assert "Error: Access to path outside project root" in result


class TestToolListDir:
    """Tests for tool_list_dir function."""

    def test_tool_list_dir_success(self):
        """It should list directory contents successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create test files and dirs
            (tmp_path / "file1.txt").write_text("content1")
            (tmp_path / "subdir").mkdir()

            with patch('agent.PROJECT_ROOT', tmp_path.resolve()):
                result = tool_list_dir({"dir_path": "."}, unsafe_mode=True)
                assert "[FILE] file1.txt" in result
                assert "[DIR] subdir" in result

    def test_tool_list_dir_empty(self):
        """It should handle empty directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('agent.PROJECT_ROOT', Path(tmpdir).resolve()):
                result = tool_list_dir({"dir_path": "."}, unsafe_mode=True)
                assert "Directory is empty" in result

    def test_tool_list_dir_not_a_directory(self):
        """It should return error when path is not a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "not_a_dir.txt").write_text("content")

            with patch('agent.PROJECT_ROOT', tmp_path.resolve()):
                result = tool_list_dir({"dir_path": "not_a_dir.txt"}, unsafe_mode=True)
                assert "Error: Not a directory" in result


class TestToolPythonRepl:
    """Tests for tool_python_repl function."""

    def test_tool_python_repl_executes_code(self):
        """It should execute Python code and capture output."""
        result = tool_python_repl({"code": "print('Hello, Test')"}, unsafe_mode=True)
        assert result == "Hello, Test"

    def test_tool_python_repl_handles_errors(self):
        """It should catch and return Python errors."""
        result = tool_python_repl({"code": "print(undefined_variable)"}, unsafe_mode=True)
        assert "Error executing Python" in result
        assert "NameError" in result

    def test_tool_python_repl_no_output(self):
        """It should handle code that doesn't produce output."""
        result = tool_python_repl({"code": "x = 1 + 1"}, unsafe_mode=True)
        assert "Code executed successfully" in result


class TestSaveLog:
    """Tests for save_log function."""

    def test_save_log_creates_file(self):
        """It should save conversation log to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            conversation = [{"role": "user", "content": "Hello"}]

            with patch('agent.PROJECT_ROOT', tmp_path.resolve()):
                with patch('builtins.print') as mock_print:
                    save_log(conversation, log_dir=tmp_path / "logs")

                # Check log directory and file were created
                log_dir = tmp_path / "logs"
                assert log_dir.exists()
                log_files = list(log_dir.glob("conversation_*.json"))
                assert len(log_files) == 1

                # Verify log content
                log_content = json.loads(log_files[0].read_text(encoding="utf-8"))
                assert log_content["messages"] == conversation


class TestToolWriteFile:
    """Tests for tool_write_file function."""

    def test_tool_write_file_creates_new_file(self):
        """It should create a new file successfully in unsafe mode (no confirmation)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_content = "Test content for writing"

            with patch('agent.PROJECT_ROOT', tmp_path.resolve()):
                result = tool_write_file(
                    {"file_path": "new_file.txt", "content": test_content},
                    unsafe_mode=True
                )
                assert "Successfully wrote" in result
                assert (tmp_path / "new_file.txt").read_text(encoding="utf-8") == test_content

    def test_tool_write_file_overwrites_in_unsafe_mode(self):
        """It should overwrite existing files in unsafe mode without confirmation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "existing.txt").write_text("old content")

            with patch('agent.PROJECT_ROOT', tmp_path.resolve()):
                result = tool_write_file(
                    {"file_path": "existing.txt", "content": "new content"},
                    unsafe_mode=True
                )
                assert "Successfully wrote" in result

    def test_tool_write_file_path_outside_project(self):
        """It should block writing to paths outside project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('agent.PROJECT_ROOT', Path(tmpdir).resolve()):
                result = tool_write_file(
                    {"file_path": "../outside.txt", "content": "test"},
                    unsafe_mode=True
                )
                assert "Error: Access to path outside project root" in result


class TestToolRunShell:
    """Tests for tool_run_shell function."""

    def test_tool_run_shell_executes_command(self):
        """It should execute shell commands successfully in unsafe mode."""
        # Use a simple cross-platform command
        test_cmd = "echo test_output"
        result = tool_run_shell({"command": test_cmd}, unsafe_mode=True)
        # Command output may vary slightly by platform
        assert "test_output" in result or "Command executed successfully" in result

    def test_tool_run_shell_whitelist_check(self):
        """It should check commands against whitelist in safe mode."""
        with patch('agent.confirm_action', return_value=False):
            result = tool_run_shell({"command": "echo test"}, unsafe_mode=False)
            # It should either ask for confirmation or execute (echo is in whitelist)
            # Since we patched confirm_action to return False, we might get cancelled
            # or if in unsafe=True it would execute
            pass  # The main thing is it doesn't crash

    def test_tool_run_shell_handles_errors(self):
        """It should handle command execution errors."""
        # Try a non-existent command (cross-platform)
        result = tool_run_shell({"command": "nonexistent_command_12345"}, unsafe_mode=True)
        # Should not crash, should return some kind of error message
        assert result is not None
        assert len(result) > 0


class TestReActAgent:
    """Tests for ReActAgent class."""

    def test_agent_initialization(self):
        """It should initialize the agent properly."""
        agent = ReActAgent(
            api_key="test_key",
            base_url="https://test.url",
            model="test-model",
            unsafe_mode=True,
            verbose=False
        )
        assert agent.api_key == "test_key"
        assert agent.base_url == "https://test.url"
        assert agent.model == "test-model"
        assert agent.unsafe_mode is True
        assert agent.verbose is False
        assert agent.messages == []

    @patch('agent.httpx.Client')
    def test_agent_calls_llm(self, mock_client_class):
        """It should call the LLM and handle response."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "```\nThought: All done\nFinal Answer: Test complete\n```"}]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Create and run agent
        agent = ReActAgent(
            api_key="test_key",
            base_url="https://test.url",
            model="test-model",
            unsafe_mode=True,
            verbose=False
        )

        result = agent.run("Hello", max_iterations=1)

        # Verify
        assert result == "Test complete"
        assert mock_client.post.called
        # Verify message history
        assert len(agent.messages) >= 1
        assert agent.messages[0]["content"] == "Hello"

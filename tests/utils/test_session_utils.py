#!/usr/bin/env python3
"""
Unit tests for the session_utils module using pytest
"""

import tempfile
from pathlib import Path
from unittest import mock

from strands_agents_builder.utils.session_utils import (
    create_session_manager,
    display_agent_history,
    generate_session_id,
    get_session_info,
    get_sessions_directory,
    handle_session_commands,
    list_available_sessions,
    list_sessions_command,
    session_exists,
    setup_session_management,
)


class TestGetSessionsDirectory:
    """Test cases for get_sessions_directory function"""

    def test_returns_none_when_no_path_provided(self):
        """Test that function returns None when no session path is provided"""
        result = get_sessions_directory(None)
        assert result is None

    def test_returns_none_when_empty_path_provided(self):
        """Test that function returns None when empty session path is provided"""
        result = get_sessions_directory("")
        assert result is None

    def test_returns_path_object_when_valid_path_provided(self):
        """Test that function returns Path object when valid path is provided"""
        test_path = "/tmp/test_sessions"
        result = get_sessions_directory(test_path)
        assert isinstance(result, Path)
        assert str(result) == test_path

    def test_creates_directory_when_create_is_true(self):
        """Test that function creates directory when create=True"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = str(Path(temp_dir) / "new_sessions")

            # Directory shouldn't exist initially
            assert not Path(test_path).exists()

            result = get_sessions_directory(test_path, create=True)

            # Directory should be created
            assert result is not None
            assert result.exists()
            assert result.is_dir()

    def test_does_not_create_directory_when_create_is_false(self):
        """Test that function doesn't create directory when create=False"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = str(Path(temp_dir) / "new_sessions")

            # Directory shouldn't exist initially
            assert not Path(test_path).exists()

            result = get_sessions_directory(test_path, create=False)

            # Directory should not be created, but Path object returned
            assert result is not None
            assert not result.exists()


class TestListAvailableSessions:
    """Test cases for list_available_sessions function"""

    def test_returns_empty_list_when_no_base_path(self):
        """Test that function returns empty list when no base path is provided"""
        result = list_available_sessions(None)
        assert result == []

    def test_returns_empty_list_when_directory_does_not_exist(self):
        """Test that function returns empty list when directory doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_path = str(Path(temp_dir) / "non_existent")
            result = list_available_sessions(non_existent_path)
            assert result == []

    def test_returns_empty_list_when_directory_is_empty(self):
        """Test that function returns empty list when directory is empty"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = list_available_sessions(temp_dir)
            assert result == []

    def test_returns_session_ids_when_present(self):
        """Test that function returns session IDs when session directories exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = temp_dir

            # Create some test session directories (as expected by the function)
            (Path(temp_dir) / "session_test-123-abc").mkdir()
            (Path(temp_dir) / "session_test-456-def").mkdir()
            (Path(temp_dir) / "not_a_session").mkdir()  # Should be ignored

            result = list_available_sessions(base_path)

            # Should only return session IDs (without "session_" prefix)
            assert len(result) == 2
            assert "test-123-abc" in result
            assert "test-456-def" in result
            assert "not_a_session" not in result

    def test_sorts_session_ids_alphabetically(self):
        """Test that function returns session IDs sorted alphabetically"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = temp_dir

            # Create session directories in non-alphabetical order
            (Path(temp_dir) / "session_zebra-session").mkdir()
            (Path(temp_dir) / "session_alpha-session").mkdir()
            (Path(temp_dir) / "session_beta-session").mkdir()

            result = list_available_sessions(base_path)

            assert result == ["alpha-session", "beta-session", "zebra-session"]


class TestCreateSessionManager:
    """Test cases for create_session_manager function"""

    def test_returns_none_when_no_base_path(self):
        """Test that function returns None when no base path is provided"""
        result = create_session_manager(base_path=None)
        assert result is None

    @mock.patch("strands_agents_builder.utils.session_utils.FileSessionManager")
    def test_creates_session_manager_when_base_path_provided(self, mock_file_session_manager):
        """Test that function creates FileSessionManager when base path is provided"""
        mock_manager_instance = mock.MagicMock()
        mock_file_session_manager.return_value = mock_manager_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_session_manager(session_id="test-session", base_path=temp_dir)

            # Verify FileSessionManager was called with correct parameters
            mock_file_session_manager.assert_called_once_with(session_id="test-session", storage_dir=temp_dir)
            assert result == mock_manager_instance

    @mock.patch("strands_agents_builder.utils.session_utils.FileSessionManager")
    def test_generates_session_id_when_none_provided(self, mock_file_session_manager):
        """Test that function generates session ID when none is provided"""
        mock_manager_instance = mock.MagicMock()
        mock_file_session_manager.return_value = mock_manager_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            create_session_manager(base_path=temp_dir)

            # Verify FileSessionManager was called with a generated session ID
            mock_file_session_manager.assert_called_once()
            call_args = mock_file_session_manager.call_args[1]
            assert "session_id" in call_args
            assert call_args["session_id"].startswith("strands-")
            assert call_args["storage_dir"] == temp_dir

    def test_creates_directory_when_it_does_not_exist(self):
        """Test that function creates directory when it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_sessions_dir = str(Path(temp_dir) / "new_sessions_dir")

            # Ensure directory doesn't exist initially
            assert not Path(new_sessions_dir).exists()

            with mock.patch("strands_agents_builder.utils.session_utils.FileSessionManager"):
                create_session_manager(session_id="test", base_path=new_sessions_dir)

            # Verify directory was created
            assert Path(new_sessions_dir).exists()
            assert Path(new_sessions_dir).is_dir()


class TestGenerateSessionId:
    """Test cases for generate_session_id function"""

    def test_generates_unique_session_ids(self):
        """Test that function generates unique session IDs"""
        id1 = generate_session_id()
        id2 = generate_session_id()

        assert id1 != id2
        assert id1.startswith("strands-")
        assert id2.startswith("strands-")

    def test_session_id_format(self):
        """Test that session ID has expected format"""
        session_id = generate_session_id()

        # Should be in format: strands-{timestamp}-{uuid}
        parts = session_id.split("-")
        assert len(parts) == 3
        assert parts[0] == "strands"
        assert parts[1].isdigit()  # timestamp
        assert len(parts[2]) == 8  # short UUID


class TestSessionExists:
    """Test cases for session_exists function"""

    def test_returns_false_when_no_base_path(self):
        """Test that function returns False when no base path is provided"""
        result = session_exists("test-session", None)
        assert result is False

    def test_returns_false_when_session_does_not_exist(self):
        """Test that function returns False when session doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = session_exists("non-existent", temp_dir)
            assert result is False

    def test_returns_true_when_session_exists(self):
        """Test that function returns True when session exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create session directory and file
            session_dir = Path(temp_dir) / "session_test-session"
            session_dir.mkdir()
            (session_dir / "session.json").touch()

            result = session_exists("test-session", temp_dir)
            assert result is True

    def test_returns_false_when_directory_exists_but_no_session_file(self):
        """Test that function returns False when directory exists but no session.json"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create session directory but no session.json
            session_dir = Path(temp_dir) / "session_test-session"
            session_dir.mkdir()

            result = session_exists("test-session", temp_dir)
            assert result is False


class TestGetSessionInfo:
    """Test cases for get_session_info function"""

    def test_returns_none_when_no_base_path(self):
        """Test that function returns None when no base path is provided"""
        result = get_session_info("test-session", None)
        assert result is None

    def test_returns_none_when_session_does_not_exist(self):
        """Test that function returns None when session doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_session_info("non-existent", temp_dir)
            assert result is None

    def test_returns_session_info_when_session_exists(self):
        """Test that function returns session info when session exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create session directory and file
            session_dir = Path(temp_dir) / "session_test-session"
            session_dir.mkdir()
            (session_dir / "session.json").touch()

            # Create some test messages
            agents_dir = session_dir / "agents" / "agent1" / "messages"
            agents_dir.mkdir(parents=True)
            (agents_dir / "msg1.json").touch()
            (agents_dir / "msg2.json").touch()

            result = get_session_info("test-session", temp_dir)

            assert result is not None
            assert result["session_id"] == "test-session"
            assert "created_at" in result
            assert result["total_messages"] == 2
            assert result["path"] == str(session_dir)


class TestIntegration:
    """Integration tests for session utilities"""

    def test_full_session_workflow(self):
        """Test complete session workflow from creation to listing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = temp_dir

            # Test create_session_manager creates directory and manager
            with mock.patch("strands_agents_builder.utils.session_utils.FileSessionManager") as mock_fsm:
                create_session_manager(session_id="test-session", base_path=base_path)
                mock_fsm.assert_called_once()

            # Create some test session directories
            (Path(temp_dir) / "session_test-session-1").mkdir()
            (Path(temp_dir) / "session_test-session-2").mkdir()

            # Test list_available_sessions
            sessions = list_available_sessions(base_path)
            assert len(sessions) == 2
            assert "test-session-1" in sessions
            assert "test-session-2" in sessions

    def test_session_lifecycle(self):
        """Test complete session lifecycle"""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_id = "test-lifecycle-session"

            # Initially session should not exist
            assert not session_exists(session_id, temp_dir)
            assert get_session_info(session_id, temp_dir) is None

            # Create session directory and file
            session_dir = Path(temp_dir) / f"session_{session_id}"
            session_dir.mkdir()
            (session_dir / "session.json").touch()

            # Now session should exist
            assert session_exists(session_id, temp_dir)

            # Should be able to get session info
            info = get_session_info(session_id, temp_dir)
            assert info is not None
            assert info["session_id"] == session_id

            # Should appear in session list
            sessions = list_available_sessions(temp_dir)
            assert session_id in sessions


class TestSessionCommands:
    """Test cases for session command functions"""

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    @mock.patch("strands_agents_builder.utils.session_utils.list_available_sessions")
    def test_list_sessions_command_no_sessions(self, mock_list_sessions, mock_console_print):
        """Test list-sessions command when no sessions exist"""
        # Setup mocks
        mock_list_sessions.return_value = []

        list_sessions_command("/tmp/sessions")

        # Verify appropriate message was called
        mock_console_print.assert_any_call("[yellow]No sessions found.[/yellow]")

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    @mock.patch("strands_agents_builder.utils.session_utils.get_session_info")
    @mock.patch("strands_agents_builder.utils.session_utils.list_available_sessions")
    def test_list_sessions_command_with_sessions(self, mock_list_sessions, mock_get_info, mock_console_print):
        """Test list-sessions command when sessions exist"""
        # Setup mocks
        mock_list_sessions.return_value = ["session1", "session2"]
        mock_get_info.return_value = {
            "session_id": "session1",
            "created_at": 1234567890,
            "total_messages": 5,
            "path": "/tmp/sessions/session_session1",
        }

        list_sessions_command("/tmp/sessions")

        # Verify sessions were listed (list_sessions_command still uses console.print with colors)
        mock_console_print.assert_any_call("[bold cyan]Available sessions:[/bold cyan]")

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    def test_list_sessions_command_no_base_path(self, mock_console_print):
        """Test list-sessions command when no session path is configured"""
        list_sessions_command(None)

        # Verify appropriate error message was called
        mock_console_print.assert_called_with(
            "[red]Error: Session management not enabled. Use --session-path or "
            "set STRANDS_SESSION_PATH environment variable.[/red]"
        )

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    @mock.patch("builtins.print")
    def test_display_agent_history_function(self, mock_print, mock_console_print):
        """Test the display_agent_history function directly"""

        # Test with few messages (no truncation)
        mock_agent = mock.MagicMock()
        mock_agent.messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there! How can I help you?"}]},
        ]

        display_agent_history(mock_agent, "test-session-123")

        # Verify console.print was called for the header panel
        mock_console_print.assert_called()
        # Verify regular print was called for messages (with colorama formatting)
        mock_print.assert_any_call("\x1b[32m~ \x1b[0mHello")
        mock_print.assert_any_call()  # Empty line after user message

        # Test with many messages (should show truncation indicator)
        mock_print.reset_mock()
        mock_console_print.reset_mock()
        mock_agent.messages = [{"role": "user", "content": [{"text": f"Message {i}"}]} for i in range(12)]

        display_agent_history(mock_agent, "test-session-456")

        # Should show console panel with truncation info in subtitle
        mock_console_print.assert_called()

        # Test with no messages
        mock_print.reset_mock()
        mock_agent.messages = []
        display_agent_history(mock_agent, "empty-session")

        # Should not print anything for empty session
        mock_print.assert_not_called()

        # Test with None messages
        mock_print.reset_mock()
        mock_agent.messages = None
        display_agent_history(mock_agent, "none-session")

        # Should not print anything for None messages
        mock_print.assert_not_called()

    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    @mock.patch("strands_agents_builder.utils.session_utils.session_exists")
    def test_setup_session_management_function(self, mock_session_exists, mock_create_manager):
        """Test the setup_session_management function directly"""

        # Test creating new session (no session_id provided)
        mock_manager = mock.MagicMock()
        mock_manager.session_id = "generated-session-123"
        mock_create_manager.return_value = mock_manager

        result_manager, result_id, is_resuming = setup_session_management(None, "/tmp/test_sessions")

        assert result_manager == mock_manager
        assert result_id == "generated-session-123"
        assert is_resuming is False
        mock_create_manager.assert_called_with(None, "/tmp/test_sessions")

        # Test resuming existing session
        mock_session_exists.return_value = True
        mock_manager.session_id = "existing-session"

        result_manager, result_id, is_resuming = setup_session_management("existing-session", "/tmp/test_sessions")

        assert result_manager == mock_manager
        assert result_id == "existing-session"
        assert is_resuming is True

        # Test creating session with provided ID (session doesn't exist)
        mock_session_exists.return_value = False

        result_manager, result_id, is_resuming = setup_session_management("existing-session", "/tmp/test_sessions")

        assert result_manager == mock_manager
        assert result_id == "existing-session"
        assert is_resuming is False

    @mock.patch("builtins.print")
    @mock.patch("strands_agents_builder.utils.session_utils.get_session_info")
    def test_handle_session_commands_function(self, mock_get_info, mock_print):
        """Test the handle_session_commands function directly"""

        # Mock session info
        mock_get_info.return_value = {
            "session_id": "test-session",
            "created_at": 1234567890,
            "total_messages": 5,
            "path": "/tmp/sessions/session_test-session",
        }

        # Test session info command
        result = handle_session_commands("session info", "test-session", "/tmp/sessions")
        assert result is True
        mock_get_info.assert_called_once_with("test-session", "/tmp/sessions")

        # Test non-session command
        result = handle_session_commands("regular command", "test-session", "/tmp/sessions")
        assert result is False

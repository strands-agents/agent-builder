"""
Test configuration and fixtures for pytest
"""

import os
from unittest import mock

import pytest

import strands_agents_builder
from strands_agents_builder import strands


@pytest.fixture
def mock_agent():
    """
    Fixture to mock the Agent class and its instance
    """
    with mock.patch.object(strands, "Agent") as mock_agent_class:
        mock_agent_instance = mock.MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.tool.welcome.return_value = {
            "status": "success",
            "content": [{"text": "Test welcome message"}],
        }
        yield mock_agent_instance


@pytest.fixture
def mock_bedrock():
    """
    Fixture to mock the BedrockModel
    """
    with mock.patch.object(strands_agents_builder.models.bedrock, "BedrockModel") as mock_bedrock:
        yield mock_bedrock


@pytest.fixture
def mock_load_prompt():
    """
    Fixture to mock the load_system_prompt function
    """
    with mock.patch.object(strands, "load_system_prompt") as mock_load_prompt:
        mock_load_prompt.return_value = "Test system prompt"
        yield mock_load_prompt


@pytest.fixture
def mock_user_input():
    """
    Fixture to mock the get_user_input function
    """
    with mock.patch.object(strands, "get_user_input") as mock_input:
        yield mock_input


@pytest.fixture
def mock_welcome_message():
    """
    Fixture to mock the render_welcome_message function
    """
    with mock.patch.object(strands, "render_welcome_message") as mock_welcome:
        yield mock_welcome


@pytest.fixture
def mock_goodbye_message():
    """
    Fixture to mock the render_goodbye_message function
    """
    with mock.patch.object(strands, "render_goodbye_message") as mock_goodbye:
        yield mock_goodbye


@pytest.fixture
def mock_store_conversation():
    """
    Fixture to mock the store_conversation_in_kb function
    """
    with mock.patch.object(strands, "store_conversation_in_kb") as mock_store:
        yield mock_store


@pytest.fixture
def temp_env():
    """
    Fixture to create a clean environment for testing
    """
    old_env = os.environ.copy()
    os.environ.clear()
    yield os.environ
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def temp_file(tmp_path):
    """
    Fixture to create a temporary file
    """

    def _create_file(content, name=".prompt"):
        file_path = tmp_path / name
        file_path.write_text(content)
        return file_path

    return _create_file


@pytest.fixture
def mock_session_manager():
    """
    Fixture to mock the session manager
    """
    with mock.patch("strands_agents_builder.utils.session_utils.FileSessionManager") as mock_manager_class:
        mock_manager_instance = mock.MagicMock()
        mock_manager_class.return_value = mock_manager_instance

        # Set up default return values
        mock_manager_instance.list_sessions.return_value = []
        mock_manager_instance.save_session.return_value = True
        mock_manager_instance.load_session.return_value = {"messages": []}

        yield mock_manager_instance


@pytest.fixture
def temp_session_dir(tmp_path):
    """
    Fixture to create a temporary session directory
    """
    session_dir = tmp_path / "test_sessions"
    session_dir.mkdir()
    return session_dir


@pytest.fixture(autouse=True)
def suppress_console_output():
    """
    Fixture to suppress console output during tests
    """
    # No longer needed since we removed console utils abstraction
    yield

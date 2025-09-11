import os
from unittest import mock

from strands_agents_builder.utils.kb_utils import load_system_prompt, store_conversation_in_kb


def test_load_system_prompt_from_env(temp_env):
    """Test loading system prompt from environment variable"""
    # Set environment variable
    temp_env["STRANDS_SYSTEM_PROMPT"] = "Test prompt from env"

    # Load prompt
    prompt = load_system_prompt()

    # Verify prompt was loaded from environment
    assert prompt == "Test prompt from env"


def test_load_system_prompt_from_file():
    """Test loading system prompt from .prompt file"""
    with (
        mock.patch("src.strands_agents_builder.utils.kb_utils.os.getenv", return_value=None),
        mock.patch("src.strands_agents_builder.utils.kb_utils.os.getcwd", return_value="/test/dir"),
        mock.patch("src.strands_agents_builder.utils.kb_utils.Path") as mock_path_class,
    ):
        # Setup mock path instances
        mock_cwd_path = mock.MagicMock()
        mock_prompt_file = mock.MagicMock()

        # Mock Path constructor to return mock_cwd_path
        mock_path_class.return_value = mock_cwd_path

        # Mock the / operator to return mock_prompt_file
        mock_cwd_path.__truediv__.return_value = mock_prompt_file

        # Setup mock_prompt_file behavior
        mock_prompt_file.exists.return_value = True
        mock_prompt_file.is_file.return_value = True
        mock_prompt_file.read_text.return_value = "Test prompt from file\n"

        # Load prompt
        prompt = load_system_prompt()

        # Verify prompt was loaded from file and stripped
        assert prompt == "Test prompt from file"


def test_load_default_system_prompt():
    """Test loading default system prompt when env and file are not available"""
    with (
        mock.patch("src.strands_agents_builder.utils.kb_utils.os.getenv", return_value=None),
        mock.patch("src.strands_agents_builder.utils.kb_utils.os.getcwd", return_value="/test/dir"),
        mock.patch("src.strands_agents_builder.utils.kb_utils.Path") as mock_path_class,
    ):
        # Setup mock path instances
        mock_cwd_path = mock.MagicMock()
        mock_prompt_file = mock.MagicMock()

        # Mock Path constructor to return mock_cwd_path
        mock_path_class.return_value = mock_cwd_path

        # Mock the / operator to return mock_prompt_file
        mock_cwd_path.__truediv__.return_value = mock_prompt_file

        # Setup mock_prompt_file behavior - file doesn't exist
        mock_prompt_file.exists.return_value = False

        # Load prompt
        prompt = load_system_prompt()

        # Verify default prompt was returned
        assert prompt == "You are a helpful assistant."


def test_load_system_prompt_from_file_exception():
    """Test load_system_prompt when file reading causes an exception"""

    # Environment variable not set
    with (
        mock.patch.dict(os.environ, {}, clear=True),
        mock.patch("pathlib.Path.exists", return_value=True),
        mock.patch("pathlib.Path.is_file", return_value=True),
        mock.patch("pathlib.Path.read_text", side_effect=Exception("File reading error")),
    ):
        # Should fall back to default prompt
        prompt = load_system_prompt()
        assert prompt == "You are a helpful assistant."


def test_load_system_prompt_complex_scenarios():
    """Test load_system_prompt with various path conditions"""

    # Test case 1: No env var, file exists but is not a file
    with (
        mock.patch.dict(os.environ, {}, clear=True),
        mock.patch("pathlib.Path.exists", return_value=True),
        mock.patch("pathlib.Path.is_file", return_value=False),
    ):
        prompt = load_system_prompt()
        assert prompt == "You are a helpful assistant."

    # Test case 2: No env var, file doesn't exist
    with mock.patch.dict(os.environ, {}, clear=True), mock.patch("pathlib.Path.exists", return_value=False):
        prompt = load_system_prompt()
        assert prompt == "You are a helpful assistant."


def test_store_conversation_in_kb():
    """Test storing conversation in knowledge base with reasoning"""
    # Create mock agent
    mock_agent = mock.MagicMock()

    # Create mock response with reasoning and text
    mock_response = mock.MagicMock()
    mock_response.message = [
        {"reasoningContent": {"reasoningText": {"text": "Test reasoning"}}},
        {"text": "Test response"},
    ]

    # Call the function
    store_conversation_in_kb(mock_agent, "Test query", mock_response, "test-kb-id")

    # Verify agent called store_in_kb with correct parameters
    expected_content = "User: Test query\n\nAssistant Reasoning: Test reasoning\n\nAssistant Response: Test response"
    mock_agent.tool.store_in_kb.assert_called_with(
        content=expected_content,
        title="Conversation: Test query",
        knowledge_base_id="test-kb-id",
        record_direct_tool_call=False,
    )


def test_store_conversation_without_reasoning():
    """Test storing conversation without reasoning content"""
    # Create mock agent
    mock_agent = mock.MagicMock()

    # Create mock response with only text
    mock_response = mock.MagicMock()
    mock_response.message = [{"text": "Test response"}]

    # Call the function
    store_conversation_in_kb(mock_agent, "Test query", mock_response, "test-kb-id")

    # Verify agent called store_in_kb with correct parameters
    expected_content = "User: Test query\n\nAssistant: Test response"
    mock_agent.tool.store_in_kb.assert_called_with(
        content=expected_content,
        title="Conversation: Test query",
        knowledge_base_id="test-kb-id",
        record_direct_tool_call=False,
    )


def test_store_conversation_empty_response():
    """Test storing conversation with empty response"""
    # Create mock agent
    mock_agent = mock.MagicMock()

    # Create mock response with empty message that won't raise exception on str()
    class MockResponse:
        def __init__(self):
            self.message = []

        def __str__(self):
            return ""

    mock_response = MockResponse()

    # Call the function
    store_conversation_in_kb(mock_agent, "Test query", mock_response, "test-kb-id")

    # Verify agent called store_in_kb with correct parameters
    mock_agent.tool.store_in_kb.assert_called_once()
    # Check that the content parameter contains the user query
    call_args = mock_agent.tool.store_in_kb.call_args
    called_content = call_args.kwargs["content"]
    assert "User: Test query" in called_content
    assert "knowledge_base_id" in call_args.kwargs
    assert call_args.kwargs["knowledge_base_id"] == "test-kb-id"


def test_store_conversation_direct_mode():
    """Test storing conversation in direct mode (without response)"""
    # Create mock agent
    mock_agent = mock.MagicMock()

    # Call the function with only query and KB ID
    store_conversation_in_kb(mock_agent, "Test query", knowledge_base_id="test-kb-id")

    # Verify agent called store_in_kb with just the user query
    expected_content = "User: Test query"
    mock_agent.tool.store_in_kb.assert_called_with(
        content=expected_content,
        title="Conversation: Test query",
        knowledge_base_id="test-kb-id",
        record_direct_tool_call=False,
    )


def test_store_conversation_no_kb():
    """Test store_conversation_in_kb when no knowledge_base_id is provided"""
    # This should just return without error
    agent_mock = mock.MagicMock()
    result = store_conversation_in_kb(agent_mock, "test input", None, None)
    assert result is None
    agent_mock.assert_not_called()  # Agent should not be used when no KB ID


def test_store_conversation_exception_handling():
    """Test exception handling in store_conversation_in_kb"""
    agent_mock = mock.MagicMock()
    agent_mock.tool.store_in_kb.side_effect = Exception("Test exception")

    with mock.patch("builtins.print") as mock_print:
        store_conversation_in_kb(agent_mock, "test input", None, "test-kb")

        # Verify error was printed
        mock_print.assert_called_once()
        assert "Error storing conversation" in mock_print.call_args[0][0]


def test_store_conversation_response_parsing_error():
    """Test error handling during response parsing in store_conversation_in_kb"""
    agent_mock = mock.MagicMock()

    # Create a response that will cause a parsing error
    complex_response = mock.MagicMock()
    complex_response.message = [{"invalid_structure": True}]

    with mock.patch("builtins.print"):
        store_conversation_in_kb(agent_mock, "test input", complex_response, "test-kb")

        # Verify the function handled the error and continued
        agent_mock.tool.store_in_kb.assert_called_once()

        # The content should include the user input
        call_kwargs = agent_mock.tool.store_in_kb.call_args.kwargs
        assert "test input" in call_kwargs["content"]


def test_store_conversation_exception_in_response_str():
    """Test storing conversation when response string conversion fails"""
    # Create mock agent
    mock_agent = mock.MagicMock()

    # Create mock response that raises exception when stringified
    class ExceptionResponse:
        def __init__(self):
            self.message = [{"complex": "structure"}]

        def __str__(self):
            # This is the case we need to test - when str(response) raises an exception
            raise Exception("Cannot convert to string")

    mock_response = ExceptionResponse()

    # Mock print function to capture errors
    with mock.patch("builtins.print"):
        # Call the function with knowledge_base_id
        store_conversation_in_kb(mock_agent, "Test query", mock_response, "test-kb-id")

        # The function should handle the exception and call store_in_kb
        # The knowledge_base_id parameter should get passed through
        mock_agent.tool.store_in_kb.assert_called_with(
            content="User: Test query\n\nAssistant: ",
            title="Conversation: Test query",
            knowledge_base_id="test-kb-id",
            record_direct_tool_call=False,
        )

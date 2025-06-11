import io
import sys
from pathlib import Path

import pytest
from strands.agent import Agent
from strands.models import BedrockModel

from strands_agents_builder import strands


@pytest.fixture
def test_env(monkeypatch):
    monkeypatch.setenv("STRANDS_TOOL_CONSOLE_MODE", "enabled")
    monkeypatch.setenv("STRANDS_KNOWLEDGE_BASE_ID", "test-kb-cli")


@pytest.fixture
def tmp_file_structure(tmp_path: Path):
    """Creates a temporary directory structure for tool creation and returns paths."""
    tools_dir = tmp_path / ".strand" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    return {"tools_dir": tools_dir, "root_dir": tmp_path}


@pytest.fixture
def bedrock_model():
    return BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        streaming=True,
    )


@pytest.fixture
def calculator_tool_environment(monkeypatch, tmp_file_structure: dict):
    """Sets up environment for calculator tool creation test."""
    monkeypatch.setenv("STRANDS_TOOLS_DIR", str(tmp_file_structure["tools_dir"]))
    original_cwd = Path.cwd()
    monkeypatch.chdir(tmp_file_structure["root_dir"])
    yield
    monkeypatch.chdir(original_cwd)


@pytest.fixture
def mock_user_input_sequence(monkeypatch):
    """
    Factory fixture to mock 'strands.get_user_input' to return a sequence of inputs.
    """

    def _mock_inputs(inputs_iterator):
        if hasattr(strands, "get_user_input"):
            monkeypatch.setattr(strands, "get_user_input", lambda *args, **kwargs: next(inputs_iterator))
        else:
            pass

    return _mock_inputs


def test_mock_cli_create_calculator_then_validate(
    monkeypatch, capsys, tmp_file_structure: dict, test_env, calculator_tool_environment, bedrock_model
):
    """
    Test creating a calculator tool via CLI and validating its functionality.
    """
    test_query = "create a tool that can only calculate sum of two number called calculator"

    monkeypatch.setattr(sys, "argv", ["strands", test_query])
    # Mock sys.stdin for confirmations (3 times is the max retry)
    monkeypatch.setattr("sys.stdin", io.StringIO("y\ny\ny\n"))

    strands.main()

    agent = Agent(
        model=bedrock_model,
        load_tools_from_directory=True,
    )

    assert hasattr(agent, "tool"), "Agent should have a 'tool' attribute after loading."

    test_cases = [("what is 1 plus 2?", "3"), ("calculate 5 plus 7", "12")]

    for question, expected in test_cases:
        response = agent(question)
        response_str = str(response).lower()
        assert expected in response_str, f"Expected '{expected}' in response for '{question}', got '{response_str}'"


def test_cli_query_with_kb(monkeypatch, capsys, test_env):
    """Test CLI query mode with knowledge base integration."""
    test_query = "Retrieve something from the knowledge base"
    monkeypatch.setattr(sys, "argv", ["strands", test_query, "--kb", "test-kb-cli"])

    strands.main()
    out = capsys.readouterr().out
    assert "knowledge base" in out.lower() or "retrieved" in out.lower()


def test_cli_with_custom_tool_load_tool(
    monkeypatch,
    capsys,
    test_env,
    tmp_file_structure,
    calculator_tool_environment,
    mock_user_input_sequence,
):
    """Test loading and using a custom tool via the load_tool function in interactive mode."""
    custom_tool_code = '''from strands import tool

@tool
def reverse_text(text: str) -> dict:
    """Reverse the input text."""
    reversed_text = text[::-1]
    return {
        "status": "success",
        "content": [{"text": reversed_text}]
    }
'''
    tool_file = tmp_file_structure["tools_dir"] / "reverse_tool.py"
    tool_file.write_text(custom_tool_code)

    user_inputs = iter([f"Load the tool from {tool_file}", "Use reverse_text on `hello,world`", "exit"])
    mock_user_input_sequence(user_inputs)

    monkeypatch.setattr(sys, "argv", ["strands"])

    strands.main()

    out = capsys.readouterr().out

    assert "olleh" in out, f"Expected 'dlrow,olleh' in output, but got:\n{out}"


def test_cli_shell_and_interactive_mode(monkeypatch, capsys, test_env, mock_user_input_sequence):
    """Test interactive mode with a shell command."""

    user_inputs = iter(["$echo hello", "y", "exit"])
    mock_user_input_sequence(user_inputs)
    monkeypatch.setattr(sys, "argv", ["strands"])

    strands.main()
    out = capsys.readouterr().out

    assert "hello" in out, "Expected 'hello' (from echo) in output"
    assert "thank you for using strands" in out.lower(), "Expected exit message"

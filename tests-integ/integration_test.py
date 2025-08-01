import io
import sys
from pathlib import Path
from unittest import mock

import pytest
from strands.agent import Agent

from strands_agents_builder import strands


@pytest.fixture
def tmp_file_structure(tmp_path: Path):
    """Creates a temporary directory structure for tool creation and returns paths."""
    tools_dir = tmp_path / ".strands" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    return {"tools_dir": tools_dir, "root_dir": tmp_path}


@mock.patch.object(sys, "stdin")
@mock.patch.object(sys, "argv")
@mock.patch("os.chdir")
@mock.patch("os.getcwd")
@mock.patch.dict("os.environ", {"STRANDS_TOOL_CONSOLE_MODE": "enabled", "STRANDS_KNOWLEDGE_BASE_ID": "test-kb-cli"})
def test_mock_cli_create_calculator_then_validate(
    mock_getcwd, mock_chdir, mock_argv, mock_stdin, capsys, tmp_file_structure: dict
):
    """
    Test creating a calculator tool via CLI and validating its functionality.
    """
    mock_getcwd.return_value = str(tmp_file_structure["root_dir"])

    with mock.patch.dict("os.environ", {"STRANDS_TOOLS_DIR": str(tmp_file_structure["tools_dir"])}):
        test_query = "create a tool that can only calculate sum of two number called calculator"

        mock_argv.__getitem__.side_effect = lambda i: ["strands", test_query][i]
        mock_argv.__len__.return_value = 2
        mock_stdin.return_value = io.StringIO("y\ny\ny\n")

        strands.main()

        agent = Agent(
            load_tools_from_directory=True,
        )

        assert hasattr(agent, "tool"), "Agent should have a 'tool' attribute after loading."

        test_cases = [("what is 1 plus 2?", "3"), ("calculate 5 plus 7", "12")]

        for question, expected in test_cases:
            response = agent(question)
            response_str = str(response).lower()
            assert expected in response_str, f"Expected '{expected}' in response for '{question}', got '{response_str}'"


@mock.patch.object(sys, "argv")
@mock.patch.dict("os.environ", {"STRANDS_TOOL_CONSOLE_MODE": "enabled", "STRANDS_KNOWLEDGE_BASE_ID": "test-kb-cli"})
def test_cli_query_with_kb(mock_argv, capsys):
    """Test CLI query mode with knowledge base integration."""
    test_query = "Retrieve something from the knowledge base"
    mock_argv.__getitem__.side_effect = lambda i: ["strands", test_query, "--kb", "test-kb-cli"][i]
    mock_argv.__len__.return_value = 4

    strands.main()
    out = capsys.readouterr().out
    assert "knowledge base" in out.lower() or "retrieved" in out.lower()


@mock.patch.object(strands, "get_user_input")
@mock.patch.object(sys, "argv")
@mock.patch("os.chdir")
@mock.patch("os.getcwd")
@mock.patch.dict("os.environ", {"STRANDS_TOOL_CONSOLE_MODE": "enabled"})
def test_cli_with_custom_tool_load_tool(
    mock_getcwd, mock_chdir, mock_argv, mock_user_input, capsys, tmp_file_structure
):
    """Test loading and using a custom tool via the load_tool function in interactive mode."""
    # Setup environment
    mock_getcwd.return_value = str(tmp_file_structure["root_dir"])

    with mock.patch.dict("os.environ", {"STRANDS_TOOLS_DIR": str(tmp_file_structure["tools_dir"])}):
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

        mock_argv.__getitem__.side_effect = lambda i: ["strands"][i]
        mock_argv.__len__.return_value = 1

        user_inputs = [f"Load the tool from {tool_file}", "Use reverse_text on `hello,world`", "exit"]
        mock_user_input.side_effect = user_inputs

        strands.main()

        out = capsys.readouterr().out
        assert "olleh" in out, f"Expected 'dlrow,olleh' in output, but got:\n{out}"


@mock.patch.object(strands, "get_user_input")
@mock.patch.object(sys, "argv")
@mock.patch.dict("os.environ", {"STRANDS_TOOL_CONSOLE_MODE": "enabled"})
def test_cli_shell_and_interactive_mode(mock_argv, mock_user_input, capsys):
    """Test interactive mode with a shell command."""
    mock_argv.__getitem__.side_effect = lambda i: ["strands"][i]
    mock_argv.__len__.return_value = 1

    user_inputs = ["$echo hello", "y", "exit"]
    mock_user_input.side_effect = user_inputs

    strands.main()
    out = capsys.readouterr().out

    assert "hello" in out, "Expected 'hello' (from echo) in output"
    assert "thank you for using strands" in out.lower(), "Expected exit message"

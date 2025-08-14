from unittest import mock

from strands_agents_builder import strands


@mock.patch.object(strands, "get_user_input")
@mock.patch.dict("os.environ", {"STRANDS_TOOL_CONSOLE_MODE": "enabled"})
def test_cli_with_custom_tool_from_load_file(mock_user_input, capsys, tmp_file_structure):
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

    user_inputs = [f"Load the tool from {tool_file}", "Use reverse_text on `hello,world`", "exit"]
    mock_user_input.side_effect = user_inputs

    strands.main()

    out = capsys.readouterr().out
    assert (
        "The reverse_text tool worked as expected"
        or "The reverse_text tool worked"
        or ("reverse_text tool" and "The tool successfully reversed") in out
    ), f"Expected 'olleh' in output, but got:\n{out}"
    assert "olleh" in out, f"Expected 'olleh' in output, but got:\n{out}"

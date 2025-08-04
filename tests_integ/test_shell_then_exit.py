from unittest import mock

from strands_agents_builder import strands


@mock.patch.object(strands, "get_user_input")
@mock.patch.dict("os.environ", {"STRANDS_TOOL_CONSOLE_MODE": "enabled"})
def test_cli_shell_and_interactive_mode(mock_user_input, capsys):
    """Test interactive mode with a shell command."""

    user_inputs = ["!echo hello", "exit"]
    mock_user_input.side_effect = user_inputs

    strands.main()
    out = capsys.readouterr().out

    assert "hello" in out, "Expected 'hello' (from echo) in output"
    assert "thank you for using strands" in out.lower(), "Expected exit message"

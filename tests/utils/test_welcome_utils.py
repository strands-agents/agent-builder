from unittest import mock

import strands_agents_builder
from strands_agents_builder.utils.welcome_utils import render_goodbye_message, render_welcome_message


def test_render_welcome_message():
    """Test rendering welcome message"""
    with mock.patch.object(strands_agents_builder.utils.welcome_utils, "console") as mock_console:
        # Call the function
        render_welcome_message("Test welcome message")

        # Verify console.print was called twice (once for the panel, once for newline)
        assert mock_console.print.call_count == 2


def test_render_welcome_message_with_invalid_markdown():
    """Test render_welcome_message with text that causes markdown parsing to fail"""

    # Create text that would cause Markdown to raise an exception
    invalid_markdown = "Test [unclosed link markdown"

    with (
        mock.patch("rich.console.Console.print") as mock_print,
        mock.patch("rich.markdown.Markdown", side_effect=Exception("Markdown parsing error")),
    ):
        render_welcome_message(invalid_markdown)

        # Should still print a panel at some point
        # We can't easily check the content here, just verify the method was called
        mock_print.assert_called()


def test_render_goodbye_message():
    """Test rendering goodbye message"""
    with mock.patch.object(strands_agents_builder.utils.welcome_utils, "console") as mock_console:
        # Call the function
        render_goodbye_message()

        # Verify console.print was called twice (once for newline, once for panel)
        assert mock_console.print.call_count == 2

        # First call should be with newline
        assert mock_console.print.call_args_list[0].args == ("\n",)

#!/usr/bin/env python3
"""
Unit tests for the callback_handler module.
"""

import time
from unittest import mock

from colorama import Fore
from rich.status import Status

import strands_agents_builder
from strands_agents_builder.handlers.callback_handler import CallbackHandler, ToolSpinner, format_message


class TestFormatMessage:
    """Tests for the format_message function."""

    def test_format_message_no_color(self):
        """Test format_message without color."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Style") as mock_style:
            # Mock Style.RESET_ALL to be empty
            mock_style.RESET_ALL = ""
            result = format_message("Test message")
            assert result == "Test message"

    def test_format_message_with_color(self):
        """Test format_message with color."""

        result = format_message("Test message", Fore.RED)
        assert result.startswith(Fore.RED)
        assert "Test message" in result

    def test_format_message_truncate(self):
        """Test format_message truncates long messages."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Style") as mock_style:
            # Mock Style.RESET_ALL to be empty
            mock_style.RESET_ALL = ""
            long_message = "x" * 100
            result = format_message(long_message, max_length=20)
            assert len(result) <= 23  # 20 chars + "..."
            assert result.endswith("...")

    def test_format_message_max_length(self):
        """Test that format_message properly truncates long messages"""
        message = "x" * 100  # A message longer than max_length
        formatted = format_message(message, max_length=20)
        # The formatted string includes ANSI color codes and reset, which affects length
        assert "..." in formatted  # Just verify it contains the ellipsis
        assert "xxxxxxxxxxxxxxxxxxxx..." in formatted  # First part should match


class TestToolSpinner:
    """Tests for the ToolSpinner class."""

    def test_tool_spinner_init(self):
        """Test ToolSpinner initialization."""
        spinner = ToolSpinner("Test message")
        assert spinner.current_text == "Test message"

    def test_tool_spinner_start(self):
        """Test ToolSpinner start method."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.start()

            mock_spinner.start.assert_called_once()

    def test_tool_spinner_start_with_text(self):
        """Test ToolSpinner start method with text update."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.start("New message")

            assert spinner.current_text == "New message"
            mock_spinner.start.assert_called_once()

    def test_tool_spinner_update(self):
        """Test ToolSpinner update method."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.update("Updated message")

            assert spinner.current_text == "Updated message"
            assert mock_spinner.text is not None

    def test_tool_spinner_succeed(self):
        """Test ToolSpinner succeed method."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.succeed()

            mock_spinner.succeed.assert_called_once()

    def test_tool_spinner_succeed_with_text(self):
        """Test ToolSpinner succeed method with text update."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.succeed("Success message")

            assert spinner.current_text == "Success message"
            mock_spinner.succeed.assert_called_once()

    def test_tool_spinner_fail(self):
        """Test ToolSpinner fail method."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.fail()

            mock_spinner.fail.assert_called_once()

    def test_tool_spinner_fail_with_text(self):
        """Test ToolSpinner fail method with text update."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.fail("Error message")

            assert spinner.current_text == "Error message"
            mock_spinner.fail.assert_called_once()

    def test_tool_spinner_info(self):
        """Test ToolSpinner info method."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.info()

            mock_spinner.info.assert_called_once()

    def test_tool_spinner_info_with_text(self):
        """Test ToolSpinner info method with text update."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.info("Info message")

            assert spinner.current_text == "Info message"
            mock_spinner.info.assert_called_once()

    def test_tool_spinner_stop(self):
        """Test ToolSpinner stop method."""
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Halo") as mock_halo:
            mock_spinner = mock.MagicMock()
            mock_halo.return_value = mock_spinner

            spinner = ToolSpinner("Test message")
            spinner.stop()

            mock_spinner.stop.assert_called_once()


class TestCallbackHandler:
    """Tests for the CallbackHandler class."""

    def test_notify(self):
        """Test notify method."""
        handler = CallbackHandler()
        with mock.patch("builtins.print") as mock_print:
            handler.notify("Test Title", "Test Message")
            mock_print.assert_called_once()

    def test_callback_handler_data(self):
        """Test callback_handler with data."""
        handler = CallbackHandler()
        with mock.patch("builtins.print") as mock_print:
            handler.callback_handler(data="Test data", complete=True)
            mock_print.assert_called_once()

    def test_callback_handler_data_incomplete(self):
        """Test callback_handler with incomplete data."""
        handler = CallbackHandler()
        with mock.patch("builtins.print") as mock_print:
            handler.callback_handler(data="Test data", complete=False)
            mock_print.assert_called_once()

    def test_callback_handler_current_tool_use_new(self):
        """Test callback_handler with new tool use."""
        handler = CallbackHandler()

        # Mock the ToolSpinner class
        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "ToolSpinner") as mock_spinner_class:
            mock_spinner = mock.MagicMock()
            mock_spinner_class.return_value = mock_spinner

            # Call callback_handler with tool use data
            handler.callback_handler(
                current_tool_use={"toolUseId": "test-id", "name": "test-tool", "input": "test-input"}
            )

            # Check that ToolSpinner was created and started
            mock_spinner_class.assert_called_once()
            mock_spinner.start.assert_called_once()

            # Check that tool history was recorded
            assert "test-id" in handler.tool_histories
            assert handler.tool_histories["test-id"]["name"] == "test-tool"

    def test_callback_handler_current_tool_use_update(self):
        """Test callback_handler with update to existing tool use."""
        handler = CallbackHandler()

        # Set up existing tool state
        handler.current_tool = "test-id"
        handler.current_spinner = mock.MagicMock()
        handler.tool_histories["test-id"] = {"name": "test-tool", "start_time": time.time(), "input_size": 5}

        # Call callback_handler with updated tool use data
        handler.callback_handler(
            current_tool_use={
                "toolUseId": "test-id",
                "name": "test-tool",
                "input": "test-input-longer",  # Length 16 > previous 5
            }
        )

        # Check that spinner was updated
        handler.current_spinner.update.assert_called_once()

        # Check that input size was updated
        # The string length is 17 (includes quotes), not 16
        assert handler.tool_histories["test-id"]["input_size"] == 17

    def test_callback_handler_message_tool_start(self):
        """Test callback_handler with message indicating tool start."""
        handler = CallbackHandler()
        handler.current_spinner = mock.MagicMock()

        # Call callback_handler with a tool start message
        handler.callback_handler(message={"role": "assistant", "content": [{"toolUse": {"name": "test-tool"}}]})

        # Check that spinner info method was called
        handler.current_spinner.info.assert_called_once()

    def test_callback_handler_message_tool_result_success(self):
        """Test callback_handler with successful tool result message."""
        handler = CallbackHandler()
        handler.current_spinner = mock.MagicMock()
        handler.current_tool = "test-id"

        # Set up existing tool state
        start_time = time.time() - 1  # 1 second ago
        handler.tool_histories["test-id"] = {"name": "test-tool", "start_time": start_time, "input_size": 10}

        # Save original current_spinner before calling
        saved_spinner = handler.current_spinner

        # Call callback_handler with a tool result message
        handler.callback_handler(
            message={"role": "user", "content": [{"toolResult": {"toolUseId": "test-id", "status": "success"}}]}
        )

        # Check that spinner succeed method was called on the saved spinner
        saved_spinner.succeed.assert_called_once()

        # Check that tool history was cleaned up
        assert "test-id" not in handler.tool_histories
        assert handler.current_tool is None
        assert handler.current_spinner is None

    def test_callback_handler_message_tool_result_error(self):
        """Test callback_handler with error tool result message."""
        handler = CallbackHandler()
        handler.current_spinner = mock.MagicMock()
        handler.current_tool = "test-id"

        # Set up existing tool state
        start_time = time.time() - 1  # 1 second ago
        handler.tool_histories["test-id"] = {"name": "test-tool", "start_time": start_time, "input_size": 10}

        # Save original current_spinner before calling
        saved_spinner = handler.current_spinner

        # Call callback_handler with a tool result message
        handler.callback_handler(
            message={"role": "user", "content": [{"toolResult": {"toolUseId": "test-id", "status": "error"}}]}
        )

        # Check that spinner fail method was called on the saved spinner
        saved_spinner.fail.assert_called_once()

        # Check that tool history was cleaned up
        assert "test-id" not in handler.tool_histories
        assert handler.current_tool is None
        assert handler.current_spinner is None

    def test_callback_handler_thinking_spinner(self):
        """Test callback_handler with thinking spinner."""
        handler = CallbackHandler()
        mock_status = mock.MagicMock()

        with mock.patch.object(strands_agents_builder.handlers.callback_handler, "Status") as mock_status_class:
            mock_status_class.return_value = mock_status

            # Call callback_handler to initialize thinking spinner
            handler.callback_handler(init_event_loop=True, console=mock.MagicMock())

            # Check that thinking spinner was created and started
            mock_status_class.assert_called_once()
            mock_status.start.assert_called_once()
            assert handler.thinking_spinner == mock_status

            # Call callback_handler to update thinking spinner
            handler.callback_handler(start_event_loop=True)

            # Check that thinking spinner was updated
            mock_status.update.assert_called_once()

            # Call callback_handler to stop thinking spinner
            handler.callback_handler(force_stop=True)

            # Check that thinking spinner was stopped
            mock_status.stop.assert_called_once()

    def test_callback_handler_reasoningText(self):
        """Test callback_handler with reasoning text."""
        handler = CallbackHandler()
        with mock.patch("builtins.print") as mock_print:
            handler.callback_handler(reasoningText="Test reasoning")
            mock_print.assert_called_once_with("Test reasoning", end="")

    def test_callback_handler_event_loop_throttled(self):
        """Test callback_handler with event loop throttling."""
        handler = CallbackHandler()
        handler.current_spinner = mock.MagicMock()
        mock_console = mock.MagicMock()

        # Call callback_handler with throttling
        handler.callback_handler(event_loop_throttled_delay=5, console=mock_console)

        # Check that spinner was stopped and console print was called
        handler.current_spinner.stop.assert_called_once()
        mock_console.print.assert_called_once()

    def test_callback_handler_exception_handling(self):
        """Test callback_handler handles exceptions gracefully."""
        handler = CallbackHandler()
        handler.thinking_spinner = mock.MagicMock()
        handler.thinking_spinner.stop.side_effect = Exception("Test exception")

        # This should not raise an exception despite the mock raising one
        handler.callback_handler(data="Test data")

        # The test passes if no exception was raised

    def test_callback_handler_event_loop_init(self):
        """Test that callback handler properly initializes an event loop"""
        handler = CallbackHandler()
        console_mock = mock.MagicMock()

        with (
            mock.patch.object(Status, "start") as mock_start,
            mock.patch.object(Status, "__init__", return_value=None) as mock_init,
        ):
            handler.callback_handler(init_event_loop=True, console=console_mock)

            # Verify Status was initialized with correct params
            mock_init.assert_called_once()
            mock_start.assert_called_once()

            # Check that the thinking_spinner is set
            assert handler.thinking_spinner is not None

    def test_callback_handler_start_event_loop(self):
        """Test that callback handler handles start_event_loop"""
        handler = CallbackHandler()
        handler.thinking_spinner = mock.MagicMock()

        handler.callback_handler(start_event_loop=True)

        # Verify update was called with the thinking text
        handler.thinking_spinner.update.assert_called_once_with("[blue] thinking...[/blue]")

    def test_callback_handler_with_reasoning_text(self):
        """Test callback handler with reasoning text"""
        handler = CallbackHandler()

        with mock.patch("builtins.print") as mock_print:
            handler.callback_handler(reasoningText="This is the reasoning")
            mock_print.assert_called_once_with("This is the reasoning", end="")

    def test_callback_handler_exception_paths(self):
        """Test the exception handling paths in callback handler"""
        handler = CallbackHandler()
        handler.thinking_spinner = mock.MagicMock()
        handler.thinking_spinner.stop.side_effect = Exception("Test exception")

        # This should not raise an exception due to the try-except block
        handler.callback_handler(data="Test data")

    def test_callback_handler_throttling(self):
        """Test the event loop throttling path"""
        handler = CallbackHandler()
        handler.current_spinner = mock.MagicMock()
        console_mock = mock.MagicMock()

        handler.callback_handler(event_loop_throttled_delay=10, console=console_mock)

        # Verify spinner is stopped
        handler.current_spinner.stop.assert_called_once()
        # Verify console print is called
        console_mock.print.assert_called_once()

    def test_callback_handler_tool_result_success_notification(self):
        """Test tool result success notification"""
        handler = CallbackHandler()
        handler.current_spinner = mock.MagicMock()
        handler.tool_histories = {
            "tool_123": {
                "name": "test_tool",
                "start_time": 1000,  # Mock timestamp
                "input_size": 100,
            }
        }

        with mock.patch("time.time", return_value=1005), mock.patch.object(handler, "notify"):
            message = {"role": "user", "content": [{"toolResult": {"toolUseId": "tool_123", "status": "success"}}]}

            # Store the current_spinner before it gets cleared
            spinner = handler.current_spinner

            handler.callback_handler(message=message)

            # Check spinner succeed was called
            spinner.succeed.assert_called_once()

            # Verify current_spinner was cleared
            assert handler.current_spinner is None

    def test_callback_handler_tool_result_error_notification(self):
        """Test tool result error notification"""
        handler = CallbackHandler()
        handler.current_spinner = mock.MagicMock()
        handler.tool_histories = {
            "tool_456": {
                "name": "test_tool",
                "start_time": 2000,  # Mock timestamp
                "input_size": 100,
            }
        }

        with mock.patch("time.time", return_value=2005), mock.patch.object(handler, "notify"):
            message = {"role": "user", "content": [{"toolResult": {"toolUseId": "tool_456", "status": "error"}}]}

            # Store the current_spinner before it gets cleared
            spinner = handler.current_spinner

            handler.callback_handler(message=message)

            # Check spinner fail was called
            spinner.fail.assert_called_once()

            # Verify current_spinner was cleared
            assert handler.current_spinner is None

    def test_force_stop(self):
        """Test force_stop parameter stops all spinners"""
        handler = CallbackHandler()
        handler.thinking_spinner = mock.MagicMock()
        handler.current_spinner = mock.MagicMock()

        handler.callback_handler(force_stop=True)

        handler.thinking_spinner.stop.assert_called_once()
        handler.current_spinner.stop.assert_called_once()

    def test_thinking_spinner_stop_on_data(self):
        """Test that thinking spinner is stopped when data is received."""
        handler = CallbackHandler()
        handler.thinking_spinner = mock.MagicMock()

        # Call callback_handler with data
        handler.callback_handler(data="Test data")

        # Check that thinking spinner was stopped
        handler.thinking_spinner.stop.assert_called_once()

    def test_thinking_spinner_stop_on_tool_use(self):
        """Test that thinking spinner is stopped when tool use is received."""
        handler = CallbackHandler()
        handler.thinking_spinner = mock.MagicMock()

        # Call callback_handler with tool use
        handler.callback_handler(current_tool_use={"toolUseId": "test-id", "name": "test-tool", "input": "test-input"})

        # Check that thinking spinner was stopped
        handler.thinking_spinner.stop.assert_called_once()

    def test_message_handling_tool_use_null_content(self):
        """Test handling of message with null content in tool use."""
        handler = CallbackHandler()
        handler.current_spinner = mock.MagicMock()

        # Call callback_handler with a message with null content
        handler.callback_handler(message={"role": "assistant", "content": [None]})

        # Should not raise any exception. The test passes if no exception is raised.
        # Spinner info should not be called since there's no valid tool use
        assert not handler.current_spinner.info.called

    def test_message_handling_tool_result_null_content(self):
        """Test handling of message with null content in tool result."""
        handler = CallbackHandler()

        # Call callback_handler with a message with null content
        handler.callback_handler(message={"role": "user", "content": [None]})

        # Should not raise any exception. The test passes if no exception is raised.

    def test_message_not_dict(self):
        """Test handling of message that is not a dictionary."""
        handler = CallbackHandler()

        # Call callback_handler with a message that is not a dictionary
        handler.callback_handler(message="Not a dict")

        # Should not raise any exception. The test passes if no exception is raised.

    def test_message_without_role(self):
        """Test handling of message that is missing the role field."""
        handler = CallbackHandler()

        # Call callback_handler with a message that is missing the role field
        handler.callback_handler(message={"content": [{"toolUse": {"name": "test-tool"}}]})

        # Should not raise any exception. The test passes if no exception is raised.

    def test_message_with_empty_content(self):
        """Test handling of message with empty content field."""
        handler = CallbackHandler()

        # Call callback_handler with a message that has an empty content field
        handler.callback_handler(message={"role": "assistant", "content": []})

        # Should not raise any exception. The test passes if no exception is raised.

    def test_message_with_non_list_content(self):
        """Test handling of message with content that is not a list."""
        handler = CallbackHandler()

        # Call callback_handler with a message that has content that is not a list
        handler.callback_handler(message={"role": "assistant", "content": "Not a list"})

        # Should not raise any exception. The test passes if no exception is raised.

    def test_handler_without_current_spinner_tool_result(self):
        """Test handling tool result when current_spinner is None."""
        handler = CallbackHandler()
        handler.current_spinner = None
        handler.current_tool = "test-id"

        # Set up existing tool state
        start_time = time.time() - 1  # 1 second ago
        handler.tool_histories["test-id"] = {"name": "test-tool", "start_time": start_time, "input_size": 10}

        # Call callback_handler with a tool result message
        handler.callback_handler(
            message={"role": "user", "content": [{"toolResult": {"toolUseId": "test-id", "status": "success"}}]}
        )

        # Check that tool history was cleaned up
        assert "test-id" not in handler.tool_histories
        assert handler.current_tool is None

    def test_handler_without_current_spinner_tool_start(self):
        """Test handling tool start when current_spinner is None."""
        handler = CallbackHandler()
        handler.current_spinner = None

        # Call callback_handler with a tool start message
        handler.callback_handler(message={"role": "assistant", "content": [{"toolUse": {"name": "test-tool"}}]})

        # Should not raise any exception. The test passes if no exception is raised.

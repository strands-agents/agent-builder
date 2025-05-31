"""
Unit tests for the logging_utils module.
"""

import logging
import os
import tempfile
from unittest import mock

from strands_agents_builder.utils.logging_utils import (
    configure_logging,
    get_available_log_levels,
)


class TestLoggingUtils:
    """Tests for the logging utilities."""

    def setup_method(self):
        """Reset root logger before each test."""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        root.setLevel(logging.WARNING)  # Reset to default

    def test_get_available_log_levels(self):
        """Test get_available_log_levels function."""
        levels = get_available_log_levels()
        assert levels == ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_configure_logging_with_file(self):
        """Test configure_logging with log file."""
        with tempfile.NamedTemporaryFile(suffix=".log") as temp:
            configure_logging(log_level="DEBUG", log_file=temp.name)
            root = logging.getLogger()
            assert root.level == logging.DEBUG
            assert any(isinstance(h, logging.FileHandler) for h in root.handlers)

            # Check specific loggers
            strands_logger = logging.getLogger("strands")
            assert strands_logger.level == logging.DEBUG

    def test_configure_logging_without_file(self):
        """Test configure_logging without log file uses stderr."""
        configure_logging(log_level="INFO", log_file=None)
        root = logging.getLogger()
        assert root.level == logging.INFO
        assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)

    def test_configure_logging_invalid_level(self):
        """Test configure_logging with invalid log level."""
        try:
            configure_logging(log_level="INVALID")
            # If we get here, the function didn't raise an exception
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            # Expected path - test passes
            pass

    def test_create_log_directory(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "logs", "test.log")

            # Ensure directory doesn't exist
            log_dir = os.path.join(temp_dir, "logs")
            assert not os.path.exists(log_dir)

            configure_logging(log_level="INFO", log_file=log_path)

            # Directory should now exist
            assert os.path.exists(log_dir)

            # Cleanup
            if os.path.exists(log_path):
                os.remove(log_path)

    def test_configure_logging_with_exception_fallback_to_stderr(self):
        """Test configure_logging handles exceptions during file creation and falls back to stderr."""
        with (
            mock.patch("logging.FileHandler", side_effect=PermissionError("Access denied")),
            mock.patch("builtins.print") as mock_print,
        ):
            configure_logging(log_level="INFO", log_file="/tmp/test.log")

            # Check that warning is printed and fallback to stderr occurs
            assert mock_print.call_count == 2
            assert "Warning: Failed to create log file" in mock_print.call_args_list[0][0][0]
            assert "Falling back to stderr logging" in mock_print.call_args_list[1][0][0]

            # Should still have a StreamHandler for stderr
            root = logging.getLogger()
            assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)

    def test_logger_hierarchy(self):
        """Test that parent loggers are configured properly."""
        configure_logging(log_level="DEBUG")

        # Check that the main loggers are configured
        strands_logger = logging.getLogger("strands")
        strands_tools_logger = logging.getLogger("strands_tools")
        strands_agents_builder_logger = logging.getLogger("strands_agents_builder")

        assert strands_logger.level == logging.DEBUG
        assert strands_tools_logger.level == logging.DEBUG
        assert strands_agents_builder_logger.level == logging.DEBUG

    def test_reset_logger_with_existing_handlers(self):
        """Test that existing handlers are properly removed when reconfiguring."""
        # First set up a handler
        root = logging.getLogger()
        handler = logging.StreamHandler()
        root.addHandler(handler)

        # Then configure logging (should reset handlers)
        configure_logging(log_level="INFO")

        # Check that old handlers were removed and new ones added
        # We should have exactly one handler (the new StreamHandler)
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)

    def test_config_logger_messages(self):
        """Test that configuration messages are logged properly."""
        with tempfile.NamedTemporaryFile(suffix=".log") as temp:
            # Configure logging
            configure_logging(log_level="INFO", log_file=temp.name)

            # Check that the config logger exists and was configured
            config_logger = logging.getLogger("strands_agents_builder")
            assert config_logger.level == logging.INFO

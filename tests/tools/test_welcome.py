#!/usr/bin/env python3
"""
Unit tests for the welcome tool
"""

from pathlib import Path
from unittest import mock

from tools.welcome import DEFAULT_WELCOME_TEXT, welcome


class TestWelcomeTool:
    """Test cases for the welcome tool"""

    def test_view_welcome_default(self):
        """Test viewing welcome text with default content"""
        with mock.patch("os.path.exists") as mock_exists, mock.patch("builtins.open", mock.mock_open()) as mock_file:
            # Make it seem like the welcome file doesn't exist
            mock_exists.return_value = False

            tool = {"toolUseId": "test-id", "input": {"action": "view"}}

            result = welcome(tool)

            # Check that the result contains the default welcome text
            assert result["status"] == "success"
            assert DEFAULT_WELCOME_TEXT in result["content"][0]["text"]
            assert "welcome to strands" in result["content"][0]["text"]

            # Verify file wasn't opened since it doesn't exist
            mock_file.assert_not_called()

    def test_view_welcome_custom(self):
        """Test viewing welcome text with custom content"""
        with (
            mock.patch("os.path.exists") as mock_exists,
            mock.patch("builtins.open", mock.mock_open(read_data="Custom welcome text")) as mock_file,
        ):
            # Make it seem like the welcome file exists
            mock_exists.return_value = True

            tool = {"toolUseId": "test-id", "input": {"action": "view"}}

            result = welcome(tool)

            # Check that the result contains the custom welcome text
            assert result["status"] == "success"
            assert "Custom welcome text" in result["content"][0]["text"]
            assert "*.*" in result["content"][0]["text"]

            # Verify file was opened for reading
            mock_file.assert_called_once_with(f"{Path.cwd()}/.welcome", "r")

    def test_edit_welcome(self):
        """Test editing welcome text"""
        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            tool = {"toolUseId": "test-id", "input": {"action": "edit", "content": "New welcome text"}}

            result = welcome(tool)

            # Check that operation was successful
            assert result["status"] == "success"
            assert "updated successfully" in result["content"][0]["text"]

            # Verify file was opened for writing with correct content
            mock_file.assert_called_once_with(f"{Path.cwd()}/.welcome", "w")
            mock_file().write.assert_called_once_with("New welcome text")

    def test_edit_welcome_missing_content(self):
        """Test editing welcome text with missing content"""
        tool = {
            "toolUseId": "test-id",
            "input": {
                "action": "edit"
                # Missing content parameter
            },
        }

        result = welcome(tool)

        # Check that an error was returned
        assert result["status"] == "error"
        assert "content is required" in result["content"][0]["text"]

    def test_unknown_action(self):
        """Test welcome with unknown action"""
        tool = {"toolUseId": "test-id", "input": {"action": "unknown"}}

        result = welcome(tool)

        # Check that an error was returned
        assert result["status"] == "error"
        assert "Unknown action" in result["content"][0]["text"]

    def test_file_operation_error(self):
        """Test error during file operations"""
        with mock.patch("os.path.exists") as mock_exists, mock.patch("builtins.open") as mock_file:
            # Make it seem like the welcome file exists
            mock_exists.return_value = True

            # Make open raise an exception
            mock_file.side_effect = PermissionError("Permission denied")

            tool = {"toolUseId": "test-id", "input": {"action": "view"}}

            result = welcome(tool)

            # Check that an error was returned
            assert result["status"] == "error"
            assert "Error" in result["content"][0]["text"]
            assert "Permission denied" in result["content"][0]["text"]

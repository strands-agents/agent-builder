#!/usr/bin/env python3
"""
Unit tests for the rich_interface tool
"""

from unittest import mock

from tools.rich_interface import rich_interface


class TestRichInterface:
    """Test cases for the rich_interface tool"""

    def test_rich_interface_missing_components(self):
        """Test rich_interface with missing components"""
        # Create tool input without components
        tool = {"toolUseId": "test_id", "input": {"interface_definition": {}}}

        # Call the function
        result = rich_interface(tool)

        # Verify error is returned
        assert result["status"] == "error"
        assert "No components defined" in result["content"][0]["text"]

    def test_rich_interface_panel(self):
        """Test rich_interface with panel component"""
        with mock.patch("tools.rich_interface.Console") as mock_console:
            # Create tool input with panel component
            tool = {
                "toolUseId": "test_id",
                "input": {
                    "interface_definition": {
                        "components": [{"type": "panel", "title": "Test Panel", "content": "Test content"}]
                    }
                },
            }

            # Call the function
            result = rich_interface(tool)

            # Verify console.print was called with a Panel
            mock_console.return_value.print.assert_called_once()
            # Check success status
            assert result["status"] == "success"

    def test_rich_interface_table(self):
        """Test rich_interface with table component"""
        with mock.patch("tools.rich_interface.Console") as mock_console:
            # Create tool input with table component
            tool = {
                "toolUseId": "test_id",
                "input": {
                    "interface_definition": {
                        "components": [
                            {
                                "type": "table",
                                "title": "Test Table",
                                "headers": ["Column 1", "Column 2"],
                                "rows": [["Row 1 Cell 1", "Row 1 Cell 2"], ["Row 2 Cell 1", "Row 2 Cell 2"]],
                            }
                        ]
                    }
                },
            }

            # Call the function
            result = rich_interface(tool)

            # Verify console.print was called with a Table
            mock_console.return_value.print.assert_called_once()
            # Check success status
            assert result["status"] == "success"

    def test_rich_interface_progress(self):
        """Test rich_interface with progress component"""
        with mock.patch("tools.rich_interface.Progress") as mock_progress:
            progress_instance = mock.MagicMock()
            mock_progress.return_value.__enter__.return_value = progress_instance

            # Create tool input with progress component
            tool = {
                "toolUseId": "test_id",
                "input": {
                    "interface_definition": {
                        "components": [
                            {"type": "progress", "description": "Test Progress", "total": 100, "completed": 50}
                        ]
                    }
                },
            }

            # Call the function
            result = rich_interface(tool)

            # Verify progress was used
            progress_instance.add_task.assert_called_once()
            progress_instance.update.assert_called_once()
            # Check success status
            assert result["status"] == "success"

    def test_rich_interface_tree(self):
        """Test rich_interface with tree component"""
        with mock.patch("tools.rich_interface.Console") as mock_console:
            # Create tool input with tree component
            tool = {
                "toolUseId": "test_id",
                "input": {
                    "interface_definition": {
                        "components": [
                            {"type": "tree", "label": "Root Node", "items": ["Child 1", "Child 2", "Child 3"]}
                        ]
                    }
                },
            }

            # Call the function
            result = rich_interface(tool)

            # Verify console.print was called
            mock_console.return_value.print.assert_called_once()
            # Check success status
            assert result["status"] == "success"

    def test_rich_interface_markdown(self):
        """Test rich_interface with markdown component"""
        with mock.patch("tools.rich_interface.Console") as mock_console:
            # Create tool input with markdown component
            tool = {
                "toolUseId": "test_id",
                "input": {
                    "interface_definition": {
                        "components": [{"type": "markdown", "content": "# Test Markdown\n\n- Item 1\n- Item 2"}]
                    }
                },
            }

            # Call the function
            result = rich_interface(tool)

            # Verify console.print was called
            mock_console.return_value.print.assert_called_once()
            # Check success status
            assert result["status"] == "success"

    def test_rich_interface_syntax(self):
        """Test rich_interface with syntax component"""
        with mock.patch("tools.rich_interface.Console") as mock_console:
            # Create tool input with syntax component
            tool = {
                "toolUseId": "test_id",
                "input": {
                    "interface_definition": {
                        "components": [{"type": "syntax", "code": "def test():\n    return True", "language": "python"}]
                    }
                },
            }

            # Call the function
            result = rich_interface(tool)

            # Verify console.print was called
            mock_console.return_value.print.assert_called_once()
            # Check success status
            assert result["status"] == "success"

    def test_rich_interface_syntax_default_language(self):
        """Test rich_interface with syntax component and no language specified"""

        # Create a tool use object with a syntax component without language
        tool = {
            "toolUseId": "test_id",
            "input": {
                "interface_definition": {
                    "components": [
                        {
                            "type": "syntax",
                            "code": "print('Hello, World!')",
                            # No language specified - should use default "python"
                        }
                    ]
                }
            },
        }

        with mock.patch("rich.console.Console.print") as mock_print:
            result = rich_interface(tool)

            # Verify the function executed successfully
            assert result["status"] == "success"

            # Check that print was called once
            mock_print.assert_called_once()

            # Verify Syntax object was created and default language was used
            # We can't check lexer_name directly, but we can verify the object was passed to print
            assert mock_print.call_args is not None

    def test_rich_interface_text(self):
        """Test rich_interface with text component"""
        with mock.patch("tools.rich_interface.Console") as mock_console:
            # Create tool input with text component
            tool = {
                "toolUseId": "test_id",
                "input": {"interface_definition": {"components": [{"type": "text", "content": "Simple text content"}]}},
            }

            # Call the function
            result = rich_interface(tool)

            # Verify console.print was called
            mock_console.return_value.print.assert_called_once()
            # Check success status
            assert result["status"] == "success"

    def test_rich_interface_multiple_components(self):
        """Test rich_interface with multiple components"""
        with mock.patch("tools.rich_interface.Console") as mock_console:
            # Create tool input with multiple components
            tool = {
                "toolUseId": "test_id",
                "input": {
                    "interface_definition": {
                        "components": [
                            {"type": "panel", "title": "Test Panel", "content": "Panel content"},
                            {"type": "text", "content": "Text content"},
                            {"type": "markdown", "content": "# Markdown content"},
                        ]
                    }
                },
            }

            # Call the function
            result = rich_interface(tool)

            # Verify console.print was called three times (once for each component)
            assert mock_console.return_value.print.call_count == 3
            # Check success status
            assert result["status"] == "success"

    def test_rich_interface_default_values(self):
        """Test rich_interface with missing optional values"""
        with (
            mock.patch("tools.rich_interface.Console") as mock_console,
            mock.patch("tools.rich_interface.Progress") as mock_progress,
        ):
            # Setup progress mock to handle the context manager __enter__
            progress_instance = mock.MagicMock()
            mock_progress.return_value.__enter__.return_value = progress_instance

            # Create tool input with minimal component definitions
            tool = {
                "toolUseId": "test_id",
                "input": {
                    "interface_definition": {
                        "components": [
                            {"type": "panel"},  # No content or title
                            {"type": "table"},  # No headers or rows
                            {"type": "tree"},  # No label or items
                            {"type": "markdown"},  # No content
                            {"type": "syntax"},  # No code or language
                            {"type": "text"},  # No content
                        ]
                    }
                },
            }

            # Call the function
            result = rich_interface(tool)

            # Verify console.print was called for each component except progress
            # Since it's 6 components and Progress adds a component using context manager
            assert mock_console.return_value.print.call_count == 6
            # Check success status
            assert result["status"] == "success"

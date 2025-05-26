"""Tests for MCP integration in strands.py."""

import json
from unittest.mock import MagicMock, patch

import pytest

from strands_agents_builder import strands


class TestMCPIntegrationInStrands:
    """Tests for MCP integration in the main strands module."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies for strands main."""
        with (
            patch.object(strands, "model_utils") as mock_model_utils,
            patch.object(strands, "mcp_utils") as mock_mcp_utils,
            patch.object(strands, "render_welcome_message") as mock_welcome,
            patch.object(strands, "render_goodbye_message") as mock_goodbye,
            patch.object(strands, "get_user_input") as mock_input,
            patch.object(strands, "store_conversation_in_kb") as mock_store,
            patch.object(strands, "load_system_prompt") as mock_load_prompt,
            patch.object(strands, "Agent") as mock_agent_class,
        ):
            # Setup mock model
            mock_model = MagicMock()
            mock_model_utils.get_model.return_value = mock_model

            # Setup mock system prompt
            mock_load_prompt.return_value = "Test system prompt"

            # Setup mock agent
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            mock_agent.tool = MagicMock()
            mock_agent.tool.mcp_client = MagicMock()
            mock_agent.tool.welcome = MagicMock(return_value={"status": "success", "content": [{"text": "Welcome"}]})

            yield {
                "model_utils": mock_model_utils,
                "mcp_utils": mock_mcp_utils,
                "render_welcome_message": mock_welcome,
                "render_goodbye_message": mock_goodbye,
                "get_user_input": mock_input,
                "store_conversation": mock_store,
                "load_system_prompt": mock_load_prompt,
                "Agent": mock_agent_class,
                "agent": mock_agent,
            }

    def test_mcp_config_argument_parsing(self, mock_dependencies):
        """Test that --mcp-config argument is parsed correctly."""
        test_config = [{"transport": "stdio", "command": "test"}]

        # Mock mcp_utils.load_config to return test config
        mock_dependencies["mcp_utils"].load_config.return_value = test_config

        # Mock user input to exit immediately
        mock_dependencies["get_user_input"].return_value = "exit"

        # Test with JSON string
        with patch("sys.argv", ["strands", "--mcp-config", json.dumps(test_config)]):
            strands.main()

        # Verify load_config was called with the JSON string
        mock_dependencies["mcp_utils"].load_config.assert_called_with(json.dumps(test_config))

    def test_mcp_config_from_file(self, mock_dependencies, tmp_path):
        """Test loading MCP config from file."""
        test_config = [{"transport": "sse", "server_url": "http://localhost:8080"}]
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(json.dumps(test_config))

        mock_dependencies["mcp_utils"].load_config.return_value = test_config
        mock_dependencies["get_user_input"].return_value = "exit"

        with patch("sys.argv", ["strands", "--mcp-config", str(config_file)]):
            strands.main()

        mock_dependencies["mcp_utils"].load_config.assert_called_with(str(config_file))

    def test_mcp_initialization_success(self, mock_dependencies):
        """Test successful MCP initialization."""
        test_config = [
            {"connection_id": "server1", "transport": "stdio", "command": "test1"},
            {"connection_id": "server2", "transport": "stdio", "command": "test2"},
        ]

        mock_dependencies["mcp_utils"].load_config.return_value = test_config
        mock_dependencies["mcp_utils"].initialize_mcp_connections.return_value = {"server1": True, "server2": True}
        mock_dependencies["get_user_input"].return_value = "exit"

        with patch("sys.argv", ["strands", "--mcp-config", json.dumps(test_config)]):
            strands.main()

        # Verify initialization was called
        mock_dependencies["mcp_utils"].initialize_mcp_connections.assert_called_once_with(
            test_config, mock_dependencies["agent"]
        )

    def test_mcp_initialization_partial_success(self, mock_dependencies):
        """Test partial MCP initialization success."""
        test_config = [
            {"connection_id": "server1", "transport": "stdio", "command": "test1"},
            {"connection_id": "server2", "transport": "stdio", "command": "test2"},
        ]

        mock_dependencies["mcp_utils"].load_config.return_value = test_config
        mock_dependencies["mcp_utils"].initialize_mcp_connections.return_value = {"server1": True, "server2": False}
        mock_dependencies["get_user_input"].return_value = "exit"

        with patch("sys.argv", ["strands", "--mcp-config", json.dumps(test_config)]):
            with patch("builtins.print") as mock_print:
                strands.main()

                # Check that partial success message was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("1/2 MCP connection(s) initialized" in str(call) for call in print_calls)

    def test_mcp_initialization_all_failed(self, mock_dependencies):
        """Test when all MCP connections fail."""
        test_config = [{"connection_id": "server1", "transport": "stdio", "command": "test"}]

        mock_dependencies["mcp_utils"].load_config.return_value = test_config
        mock_dependencies["mcp_utils"].initialize_mcp_connections.return_value = {"server1": False}
        mock_dependencies["get_user_input"].return_value = "exit"

        with patch("sys.argv", ["strands", "--mcp-config", json.dumps(test_config)]):
            with patch("builtins.print") as mock_print:
                strands.main()

                # Check that failure message was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("Failed to initialize any MCP connections" in str(call) for call in print_calls)

    def test_mcp_disconnect_on_exit(self, mock_dependencies):
        """Test that MCP connections are disconnected on exit."""
        test_config = [{"connection_id": "server1", "transport": "stdio", "command": "test"}]

        mock_dependencies["mcp_utils"].load_config.return_value = test_config
        mock_dependencies["mcp_utils"].initialize_mcp_connections.return_value = {"server1": True}
        mock_dependencies["get_user_input"].return_value = "exit"

        with patch("sys.argv", ["strands", "--mcp-config", json.dumps(test_config)]):
            strands.main()

        # Verify disconnect_all was called
        mock_dependencies["mcp_utils"].disconnect_all.assert_called_once_with(mock_dependencies["agent"])

    def test_mcp_disconnect_on_keyboard_interrupt(self, mock_dependencies):
        """Test that MCP connections are disconnected on KeyboardInterrupt."""
        test_config = [{"connection_id": "server1", "transport": "stdio", "command": "test"}]

        mock_dependencies["mcp_utils"].load_config.return_value = test_config
        mock_dependencies["mcp_utils"].initialize_mcp_connections.return_value = {"server1": True}
        mock_dependencies["get_user_input"].side_effect = KeyboardInterrupt()

        with patch("sys.argv", ["strands", "--mcp-config", json.dumps(test_config)]):
            strands.main()

        # Verify disconnect_all was called
        mock_dependencies["mcp_utils"].disconnect_all.assert_called_once_with(mock_dependencies["agent"])

    def test_no_mcp_config(self, mock_dependencies):
        """Test running without MCP config."""
        mock_dependencies["mcp_utils"].load_config.return_value = []
        mock_dependencies["get_user_input"].return_value = "exit"

        with patch("sys.argv", ["strands"]):
            strands.main()

        # Verify MCP initialization was not called
        mock_dependencies["mcp_utils"].initialize_mcp_connections.assert_not_called()
        mock_dependencies["mcp_utils"].disconnect_all.assert_not_called()

    def test_mcp_config_with_query_mode(self, mock_dependencies):
        """Test MCP config works with query mode (non-interactive)."""
        test_config = [{"connection_id": "server1", "transport": "stdio", "command": "test"}]

        mock_dependencies["mcp_utils"].load_config.return_value = test_config
        mock_dependencies["mcp_utils"].initialize_mcp_connections.return_value = {"server1": True}

        # Mock agent response - agent is called directly in query mode
        mock_dependencies["agent"].return_value = {"message": "Test response"}

        with patch("sys.argv", ["strands", "--mcp-config", json.dumps(test_config), "Test query"]):
            strands.main()

        # Verify MCP was initialized
        mock_dependencies["mcp_utils"].initialize_mcp_connections.assert_called_once()

        # Verify agent was called with the query
        mock_dependencies["agent"].assert_called_once_with("Test query")

        # Verify no disconnect_all in query mode (non-interactive)
        mock_dependencies["mcp_utils"].disconnect_all.assert_not_called()

    def test_mcp_config_load_with_default_empty_list(self, mock_dependencies):
        """Test that default MCP config is empty list."""
        # Don't provide --mcp-config argument
        mock_dependencies["get_user_input"].return_value = "exit"

        with patch("sys.argv", ["strands"]):
            strands.main()

        # Verify load_config was called with default "[]"
        mock_dependencies["mcp_utils"].load_config.assert_called_with("[]")

    def test_mcp_tool_added_to_agent(self, mock_dependencies):
        """Test that mcp_client tool is added to agent tools."""
        mock_dependencies["get_user_input"].return_value = "exit"

        with patch("sys.argv", ["strands"]):
            strands.main()

        # Get the tools argument passed to Agent
        agent_call = mock_dependencies["Agent"].call_args
        tools = agent_call[1]["tools"]

        # Verify mcp_client is in the tools list
        from strands_tools import mcp_client

        assert mcp_client in tools

"""Tests for mcp_utils module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from strands_agents_builder.utils import mcp_utils


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_empty_string(self):
        """Test loading config with empty string returns empty list."""
        result = mcp_utils.load_config("")
        assert result == []

    def test_load_config_empty_brackets(self):
        """Test loading config with empty brackets returns empty list."""
        result = mcp_utils.load_config("[]")
        assert result == []

    def test_load_config_from_json_string(self):
        """Test loading config from JSON string."""
        config_str = '[{"transport": "stdio", "command": "node", "args": ["server.js"]}]'
        result = mcp_utils.load_config(config_str)
        assert len(result) == 1
        assert result[0]["transport"] == "stdio"
        assert result[0]["command"] == "node"
        assert result[0]["args"] == ["server.js"]

    def test_load_config_from_json_file(self, tmp_path):
        """Test loading config from JSON file."""
        config_data = [
            {
                "connection_id": "test_server",
                "transport": "stdio",
                "command": "python",
                "args": ["mcp_server.py"],
                "auto_load_tools": True,
            }
        ]
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(json.dumps(config_data))

        result = mcp_utils.load_config(str(config_file))
        assert len(result) == 1
        assert result[0]["connection_id"] == "test_server"
        assert result[0]["transport"] == "stdio"
        assert result[0]["command"] == "python"

    def test_load_config_single_dict_to_list(self):
        """Test that single dict config is converted to list."""
        config_str = '{"transport": "sse", "server_url": "http://localhost:8080"}'
        result = mcp_utils.load_config(config_str)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["transport"] == "sse"
        assert result[0]["server_url"] == "http://localhost:8080"

    def test_load_config_from_env_path(self, tmp_path, monkeypatch):
        """Test loading config from STRANDS_MCP_CONFIG_PATH environment variable."""
        config_data = [{"transport": "stdio", "command": "test"}]
        config_file = tmp_path / "env_config.json"
        config_file.write_text(json.dumps(config_data))

        monkeypatch.setenv("STRANDS_MCP_CONFIG_PATH", str(config_file))
        result = mcp_utils.load_config("")
        assert len(result) == 1
        assert result[0]["command"] == "test"

    def test_load_config_amazon_q_format(self):
        """Test loading config in Amazon Q MCP format."""
        config_str = json.dumps(
            {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", "path/to/files"],
                        "disabled": False,
                    },
                    "github": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-github"],
                        "env": {"GITHUB_TOKEN": "test_token"},
                        "disabled": False,
                    },
                    "disabled_server": {"command": "test", "disabled": True},
                }
            }
        )

        result = mcp_utils.load_config(config_str)
        assert len(result) == 2  # Only enabled servers

        # Check filesystem server
        filesystem = next(s for s in result if s["connection_id"] == "filesystem")
        assert filesystem["transport"] == "stdio"
        assert filesystem["command"] == "npx"
        assert filesystem["args"] == ["-y", "@modelcontextprotocol/server-filesystem", "path/to/files"]
        assert filesystem["auto_load_tools"] is True

        # Check github server with env
        github = next(s for s in result if s["connection_id"] == "github")
        assert github["env"] == {"GITHUB_TOKEN": "test_token"}

        # Ensure disabled server is not included
        assert not any(s["connection_id"] == "disabled_server" for s in result)


class TestInitializeMCPConnections:
    """Tests for the initialize_mcp_connections function."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with mcp_client tool."""
        agent = MagicMock()
        agent.tool = MagicMock()
        agent.tool.mcp_client = MagicMock()
        return agent

    def test_initialize_single_connection_success(self, mock_agent):
        """Test successful initialization of a single MCP connection."""
        configs = [
            {
                "connection_id": "test_server",
                "transport": "stdio",
                "command": "node",
                "args": ["server.js"],
                "auto_load_tools": True,
            }
        ]

        # Mock successful responses
        mock_agent.tool.mcp_client.side_effect = [
            {"status": "success", "content": [{"text": "Connected"}]},  # connect
            {"status": "success", "content": [{"text": "Tools loaded"}]},  # load_tools
        ]

        results = mcp_utils.initialize_mcp_connections(configs, mock_agent)

        assert results == {"test_server": True}
        assert mock_agent.tool.mcp_client.call_count == 2

        # Check connect call
        connect_call = mock_agent.tool.mcp_client.call_args_list[0]
        assert connect_call[1]["action"] == "connect"
        assert connect_call[1]["connection_id"] == "test_server"
        assert connect_call[1]["transport"] == "stdio"
        assert connect_call[1]["command"] == "node"
        assert connect_call[1]["args"] == ["server.js"]

    def test_initialize_connection_failure(self, mock_agent):
        """Test failed initialization of MCP connection."""
        configs = [
            {
                "connection_id": "failing_server",
                "transport": "stdio",
                "command": "invalid",
            }
        ]

        mock_agent.tool.mcp_client.return_value = {"status": "error", "content": [{"text": "Connection failed"}]}

        results = mcp_utils.initialize_mcp_connections(configs, mock_agent)

        assert results == {"failing_server": False}
        assert mock_agent.tool.mcp_client.call_count == 1

    def test_initialize_auto_generate_connection_id_stdio(self, mock_agent):
        """Test auto-generation of connection ID for stdio transport."""
        configs = [{"transport": "stdio", "command": "python", "args": ["mcp_server.py"]}]

        mock_agent.tool.mcp_client.return_value = {"status": "success", "content": [{"text": "Connected"}]}

        results = mcp_utils.initialize_mcp_connections(configs, mock_agent)

        # Check that connection_id was auto-generated
        assert len(results) == 1
        connection_id = list(results.keys())[0]
        assert connection_id.startswith("mcp_python_")
        assert results[connection_id] is True

    def test_initialize_auto_generate_connection_id_sse(self, mock_agent):
        """Test auto-generation of connection ID for SSE transport."""
        configs = [{"transport": "sse", "server_url": "http://example.com/mcp"}]

        mock_agent.tool.mcp_client.return_value = {"status": "success", "content": [{"text": "Connected"}]}

        results = mcp_utils.initialize_mcp_connections(configs, mock_agent)

        # Check that connection_id was auto-generated from hostname
        assert len(results) == 1
        connection_id = list(results.keys())[0]
        assert connection_id.startswith("mcp_example_")
        assert results[connection_id] is True

    def test_initialize_multiple_connections(self, mock_agent):
        """Test initialization of multiple MCP connections."""
        configs = [
            {"connection_id": "server1", "transport": "stdio", "command": "node"},
            {"connection_id": "server2", "transport": "sse", "server_url": "http://localhost:8080"},
        ]

        # First server succeeds, second fails
        mock_agent.tool.mcp_client.side_effect = [
            {"status": "success", "content": [{"text": "Connected"}]},  # server1 connect
            {"status": "error", "content": [{"text": "Failed"}]},  # server2 connect
        ]

        results = mcp_utils.initialize_mcp_connections(configs, mock_agent)

        assert results == {"server1": True, "server2": False}

    def test_initialize_with_env_variables(self, mock_agent):
        """Test initialization with environment variables."""
        configs = [
            {
                "connection_id": "github_server",
                "transport": "stdio",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "test_token"},
            }
        ]

        mock_agent.tool.mcp_client.return_value = {"status": "success", "content": [{"text": "Connected"}]}

        results = mcp_utils.initialize_mcp_connections(configs, mock_agent)

        assert results == {"github_server": True}

        # Check env was passed
        connect_call = mock_agent.tool.mcp_client.call_args_list[0]
        assert connect_call[1]["env"] == {"GITHUB_TOKEN": "test_token"}

    def test_initialize_auto_load_tools_false(self, mock_agent):
        """Test initialization with auto_load_tools set to False."""
        configs = [{"connection_id": "no_autoload", "transport": "stdio", "command": "test", "auto_load_tools": False}]

        mock_agent.tool.mcp_client.return_value = {"status": "success", "content": [{"text": "Connected"}]}

        results = mcp_utils.initialize_mcp_connections(configs, mock_agent)

        assert results == {"no_autoload": True}
        # Should only call connect, not load_tools
        assert mock_agent.tool.mcp_client.call_count == 1

    def test_initialize_exception_handling(self, mock_agent):
        """Test exception handling during initialization."""
        configs = [{"connection_id": "exception_server", "transport": "stdio", "command": "test"}]

        mock_agent.tool.mcp_client.side_effect = Exception("Test exception")

        results = mcp_utils.initialize_mcp_connections(configs, mock_agent)

        assert results == {"exception_server": False}


class TestListActiveConnections:
    """Tests for the list_active_connections function."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with mcp_client tool."""
        agent = MagicMock()
        agent.tool = MagicMock()
        agent.tool.mcp_client = MagicMock()
        return agent

    def test_list_active_connections_success(self, mock_agent):
        """Test listing active connections successfully."""
        mock_agent.tool.mcp_client.return_value = {
            "status": "success",
            "content": [{"text": "Active MCP connections:\n\nConnection: server1\nConnection: server2"}],
        }

        result = mcp_utils.list_active_connections(mock_agent)

        assert result == ["server1", "server2"]
        mock_agent.tool.mcp_client.assert_called_once_with(action="list_connections", kwargs={})

    def test_list_active_connections_empty(self, mock_agent):
        """Test listing when no active connections."""
        mock_agent.tool.mcp_client.return_value = {
            "status": "success",
            "content": [{"text": "No active MCP connections"}],
        }

        result = mcp_utils.list_active_connections(mock_agent)

        assert result == []

    def test_list_active_connections_error(self, mock_agent):
        """Test listing connections when error occurs."""
        mock_agent.tool.mcp_client.return_value = {
            "status": "error",
            "content": [{"text": "Error listing connections"}],
        }

        result = mcp_utils.list_active_connections(mock_agent)

        assert result == []

    def test_list_active_connections_exception(self, mock_agent):
        """Test listing connections when exception is raised."""
        mock_agent.tool.mcp_client.side_effect = Exception("Test exception")

        result = mcp_utils.list_active_connections(mock_agent)

        assert result == []


class TestDisconnectAll:
    """Tests for the disconnect_all function."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with mcp_client tool."""
        agent = MagicMock()
        agent.tool = MagicMock()
        agent.tool.mcp_client = MagicMock()
        return agent

    def test_disconnect_all_success(self, mock_agent):
        """Test disconnecting all connections successfully."""
        # Mock list_active_connections to return two connections
        with patch.object(mcp_utils, "list_active_connections", return_value=["server1", "server2"]):
            # Mock successful disconnections
            mock_agent.tool.mcp_client.return_value = {"status": "success", "content": [{"text": "Disconnected"}]}

            mcp_utils.disconnect_all(mock_agent)

            # Should call disconnect for each connection
            assert mock_agent.tool.mcp_client.call_count == 2

            # Check disconnect calls
            calls = mock_agent.tool.mcp_client.call_args_list
            assert calls[0][1]["action"] == "disconnect"
            assert calls[0][1]["connection_id"] == "server1"
            assert calls[1][1]["action"] == "disconnect"
            assert calls[1][1]["connection_id"] == "server2"

    def test_disconnect_all_no_connections(self, mock_agent):
        """Test disconnecting when no active connections."""
        with patch.object(mcp_utils, "list_active_connections", return_value=[]):
            mcp_utils.disconnect_all(mock_agent)

            # Should not call disconnect
            mock_agent.tool.mcp_client.assert_not_called()

    def test_disconnect_all_with_errors(self, mock_agent):
        """Test disconnecting with some errors."""
        with patch.object(mcp_utils, "list_active_connections", return_value=["server1", "server2"]):
            # First disconnect succeeds, second raises exception
            mock_agent.tool.mcp_client.side_effect = [
                {"status": "success", "content": [{"text": "Disconnected"}]},
                Exception("Connection error"),
            ]

            # Should not raise exception
            mcp_utils.disconnect_all(mock_agent)

            # Should still attempt both disconnections
            assert mock_agent.tool.mcp_client.call_count == 2

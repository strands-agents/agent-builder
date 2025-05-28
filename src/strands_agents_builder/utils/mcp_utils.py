"""Utilities for loading and managing MCP clients in strands."""

import json
import os
from typing import Any, Dict, List


def load_config(config: str) -> List[Dict[str, Any]]:
    """Load MCP configuration from a JSON string or file.

    The configuration should be a list of MCP server configurations.
    Each server configuration should contain:
    - connection_id: Unique identifier for the connection (optional, auto-generated if missing)
    - transport: Transport type (stdio or sse)
    - command: Command for stdio transport (required for stdio)
    - args: Arguments for stdio command (optional)
    - server_url: URL for SSE transport (required for sse)
    - auto_load_tools: Whether to automatically load tools (default: True)

    Args:
        config: A JSON string or path to a JSON file containing MCP configurations.
            If empty string or '[]', checks STRANDS_MCP_CONFIG_PATH environment variable.

    Returns:
        List of parsed MCP server configurations.

    Examples:
        # From JSON file
        config = load_config("mcp_config.json")

        # From JSON string (connection_id is optional)
        config = load_config('[{"transport": "stdio", "command": "node", "args": ["server.js"]}]')
    """
    if not config or config == "[]":
        # Check for default config path in environment
        default_path = os.getenv("STRANDS_MCP_CONFIG_PATH")
        if default_path and os.path.exists(default_path):
            config = default_path
        else:
            return []

    if config.endswith(".json"):
        with open(config) as fp:
            data = json.load(fp)
    else:
        data = json.loads(config)

    # Handle Amazon Q MCP format
    if isinstance(data, dict) and "mcpServers" in data:
        servers = []
        for server_id, server_config in data["mcpServers"].items():
            # Skip disabled servers
            if server_config.get("disabled", False):
                continue

            # Convert to our format
            converted = {
                "connection_id": server_id,
                "transport": "stdio",  # Amazon Q format uses stdio by default
                "command": server_config.get("command"),
                "args": server_config.get("args", []),
                "auto_load_tools": True,
            }

            # Add environment variables if present
            if "env" in server_config:
                converted["env"] = server_config["env"]

            servers.append(converted)
        data = servers

    # Ensure it's a list
    if isinstance(data, dict):
        data = [data]

    return data


def initialize_mcp_connections(configs: List[Dict[str, Any]], agent) -> Dict[str, bool]:
    """Initialize MCP connections based on provided configurations.

    Args:
        configs: List of MCP server configurations.
        agent: The strands agent instance to use for MCP client calls.

    Returns:
        Dictionary mapping connection_id to success status.
    """
    results = {}

    for i, config in enumerate(configs):
        connection_id = config.get("connection_id")
        if not connection_id:
            # Auto-generate connection ID based on transport and command/url
            transport = config.get("transport", "stdio")
            if transport == "stdio":
                command = config.get("command", "unknown")
                # Use the command name as basis for ID
                base_name = os.path.basename(command).replace(".", "_")
                connection_id = f"mcp_{base_name}_{i}"
            else:  # sse
                server_url = config.get("server_url", "")
                # Extract hostname or use index
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(server_url)
                    host = parsed.hostname or "server"
                    host = host.replace(".", "_").replace("-", "_")
                    connection_id = f"mcp_{host}_{i}"
                except Exception:
                    connection_id = f"mcp_sse_{i}"

            print(f"📝 Auto-generated connection_id: {connection_id}")
            config["connection_id"] = connection_id

        try:
            # Connect to the MCP server
            connect_params = {"action": "connect", "connection_id": connection_id, "kwargs": {}}

            # Add transport-specific parameters
            if "transport" in config:
                connect_params["transport"] = config["transport"]

            if config.get("transport") == "stdio":
                if "command" in config:
                    connect_params["command"] = config["command"]
                if "args" in config:
                    connect_params["args"] = config["args"]
                if "env" in config:
                    connect_params["env"] = config["env"]
            elif config.get("transport") == "sse":
                if "server_url" in config:
                    connect_params["server_url"] = config["server_url"]

            # Connect to the server
            result = agent.tool.mcp_client(**connect_params)

            if result.get("status") == "success":
                print(f"✓ Connected to MCP server: {connection_id}")

                # Auto-load tools if specified (default: True)
                if config.get("auto_load_tools", True):
                    load_result = agent.tool.mcp_client(action="load_tools", connection_id=connection_id, kwargs={})
                    if load_result.get("status") == "success":
                        print(f"  ✓ Loaded tools from {connection_id}")
                    else:
                        print(f"  ✗ Failed to load tools from {connection_id}")

                results[connection_id] = True
            else:
                print(f"✗ Failed to connect to MCP server: {connection_id}")
                error_msg = result.get("content", [{}])[0].get("text", "Unknown error")
                print(f"  Error: {error_msg}")
                results[connection_id] = False

        except Exception as e:
            print(f"✗ Error connecting to MCP server {connection_id}: {str(e)}")
            results[connection_id] = False

    return results


def list_active_connections(agent) -> List[str]:
    """List all active MCP connections.

    Args:
        agent: The strands agent instance to use for MCP client calls.

    Returns:
        List of active connection IDs.
    """
    try:
        result = agent.tool.mcp_client(action="list_connections", kwargs={})
        if result.get("status") == "success":
            # Parse the response to extract connection IDs
            content = result.get("content", [{}])[0].get("text", "")
            if "No active MCP connections" in content:
                return []

            # Extract connection IDs from the formatted output
            connections = []
            lines = content.split("\n")
            for line in lines:
                if "Connection:" in line:
                    conn_id = line.split("Connection:")[1].strip()
                    connections.append(conn_id)
            return connections
        return []
    except Exception:
        return []


def disconnect_all(agent) -> None:
    """Disconnect all active MCP connections.

    Args:
        agent: The strands agent instance to use for MCP client calls.
    """
    connections = list_active_connections(agent)
    for connection_id in connections:
        try:
            agent.tool.mcp_client(action="disconnect", connection_id=connection_id, kwargs={})
            print(f"✓ Disconnected from MCP server: {connection_id}")
        except Exception as e:
            print(f"✗ Error disconnecting from {connection_id}: {str(e)}")

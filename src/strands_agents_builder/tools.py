import platform
from typing import Any

# Strands tools
from strands_tools import (
    agent_graph,
    calculator,
    cron,
    current_time,
    editor,
    environment,
    file_read,
    file_write,
    generate_image,
    http_request,
    image_reader,
    journal,
    load_tool,
    memory,
    nova_reels,
    retrieve,
    slack,
    speak,
    stop,
    swarm,
    think,
    use_aws,
    use_llm,
    workflow,
)

# Custom tools
from tools import (
    store_in_kb,
    strand,
    welcome,
)


def get_tools() -> dict[str, Any]:
    """
    Returns the platform-specific collection of available agent tools for strands.

    Note:
        Tool availability varies by platform and system configuration.
        Each tool is initialized as a singleton instance.
    """

    tools = {
        "agent_graph": agent_graph,
        "calculator": calculator,
        "current_time": current_time,
        "editor": editor,
        "environment": environment,
        "file_read": file_read,
        "file_write": file_write,
        "generate_image": generate_image,
        "http_request": http_request,
        "image_reader": image_reader,
        "journal": journal,
        "load_tool": load_tool,
        "memory": memory,
        "nova_reels": nova_reels,
        "retrieve": retrieve,
        "slack": slack,
        "speak": speak,
        "stop": stop,
        "swarm": swarm,
        "think": think,
        "use_aws": use_aws,
        "use_llm": use_llm,
        "workflow": workflow,
        # Strands tools
        "store_in_kb": store_in_kb,
        "strand": strand,
        "welcome": welcome,
    }

    # Some tools don't currently work on windows and even fail to import, so we need to dynamically add these
    # (https://github.com/strands-agents/tools/issues/17
    if platform.system() != "Windows":
        from strands_tools import (
            python_repl,
            shell,
        )

        tools |= {
            "cron": cron,
            "python_repl": python_repl,
            "shell": shell,
        }

    return tools

import platform

import pytest

from strands_agents_builder.tools import get_tools


@pytest.mark.skipif(platform.system() == "Windows", reason="Windows cannot import certain tools")
def test_tools_includes_more_tools_on_non_windows():
    tools = get_tools()

    assert "python_repl" in tools
    assert "shell" in tools


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
def test_tools_includes_more_tools_on_non_windows():
    tools = get_tools()

    assert "python_repl" not in tools
    assert "shell" not in tools

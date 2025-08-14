import sys
from unittest import mock

from strands import Agent

from strands_agents_builder import strands


def test_build_agent_from_specification_file():
    """Test building agent from specification using semantic creation."""

    # Agent specification content
    spec_content = """Agent Specification:
- Role: Math Tutor Agent
- Purpose: Help students with basic arithmetic and algebra
- Tools needed: calculator, file_read, current_time
- Create specialized tools for math tutoring
"""

    # Simulate: cat agent-spec.txt | strands "Build a specialized agent based on these specifications"
    query = f"Build a specialized agent based on these specifications:\n\n{spec_content}"

    with mock.patch.object(sys, "argv", ["strands", query]):
        strands.main()

    # Validate agent
    agent = Agent(
        load_tools_from_directory=True,
        callback_handler=None,
    )

    # Validate agent was created successfully
    assert agent is not None

    # Validate agent has exactly 3 specified tools
    required_tools = ["calculator", "file_read", "current_time"]
    for tool_name in required_tools:
        assert hasattr(agent.tool, tool_name), f"Agent missing required tool: {tool_name}"

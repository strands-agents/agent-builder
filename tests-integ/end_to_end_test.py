import re

import pytest
from strands.agent import Agent
from strands.models import BedrockModel


@pytest.fixture
def bedrock_model():
    return BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        streaming=True,
    )


def extract_code_from_response(response):
    """Extract Python code blocks from the agent's response."""
    code_pattern = r"```python\s*(.*?)\s*```"
    matches = re.findall(code_pattern, str(response), re.DOTALL)
    if matches:
        return matches[0].strip()
    return None


def test_agent_creates_calculator_tool(tmp_path, monkeypatch, bedrock_model):
    """End-to-end test: Ask agent to create a tool, validate it, then delete it."""
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir(parents=True)
    monkeypatch.setenv("STRANDS_TOOLS_DIR", str(tools_dir))

    tool_path = tools_dir / "calculator_tool.py"

    try:
        creator_agent = Agent(model=bedrock_model)
        prompt = """
        Create a Python tool named calculator_tool that can perform basic arithmetic operations.
        The tool should:
        1. Take two numbers and an operator ('+', '-', '*', '/')
        2. Return the result of the operation
        3. Include proper docstrings and error handling
        4. Be compatible with the Strands SDK tool system
        
        Provide only the Python code with no additional explanation.
        """
        creation_response = creator_agent(prompt)

        tool_code = extract_code_from_response(creation_response)
        assert tool_code is not None, "Failed to extract tool code from agent response"

        with open(tool_path, "w") as f:
            f.write(tool_code)
        assert tool_path.exists(), f"Tool file was not created at {tool_path}"

        agent = Agent(model=bedrock_model, tools=None, load_tools_from_directory=True)

        test_cases = [
            ("What is 1 + 2?", "3"),
            ("Calculate 2 - 1", "1"),
            ("What is 1 multiplied by 5?", "5"),
            ("Divide 20 by 4", "5"),
        ]

        for question, expected in test_cases:
            response = agent(question)
            response_str = str(response).lower()
            assert expected.lower() in response_str, f"Failed to find '{expected}' in response to '{question}'"

    finally:
        if tool_path.exists():
            tool_path.unlink()

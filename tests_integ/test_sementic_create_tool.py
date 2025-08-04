import io
import sys
from unittest import mock

from strands.agent import Agent

from strands_agents_builder import strands


@mock.patch.object(sys, "stdin")
@mock.patch.dict("os.environ", {"STRANDS_TOOL_CONSOLE_MODE": "enabled"})
def test_interactive_model_create_tool_then_validate(mock_stdin, capsys, tmp_file_structure):
    """
    Test creating a calculator tool via CLI and validating its functionality.
    """
    with mock.patch.dict("os.environ", {"STRANDS_TOOLS_DIR": str(tmp_file_structure["tools_dir"])}):
        test_query = "create a tool that can only calculate sum of two number called calculator"
        mock_stdin.return_value = io.StringIO("y\ny\ny\n")

        with mock.patch.object(sys, "argv", ["strands", test_query]):
            strands.main()

        agent = Agent(
            load_tools_from_directory=True,
        )

        # assert agent has a tool called calculator
        assert hasattr(agent.tool, "calculator"), "Agent should have a 'calculator' tool after creation."

        test_cases = [("what is 1 plus 2?", "3"), ("calculate 5 plus 7", "12")]

        for question, expected in test_cases:
            response = agent(question)
            response_str = str(response).lower()
            assert expected in response_str, f"Expected '{expected}' in response for '{question}', got '{response_str}'"

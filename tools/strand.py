"""
Strand Tool - Provides access to Strands functionality as a Strands tool

This tool allows using Strands (a minimal Strands CLI) from within Strands itself,
enabling nested Strands agent instances with their own tools and system prompts.
"""

import os
import sys
from io import StringIO
from pathlib import Path
from typing import List, Optional

from strands import Agent, tool


@tool
def strand(
    query: str,
    system_prompt: Optional[str] = None,
    tool_names: Optional[List[str]] = None,
) -> dict:
    """
    Run a Strands instance (nested Strands agent) with specified query, tools, and system prompt

    Args:
        query: The query to process with Strands
        system_prompt: Custom system prompt to use for the Strands instance
        tool_names: List of tool names to make available to the Strands instance

    Returns:
        Results from the Strands instance execution
    """
    try:
        # Check for empty query
        if not query:
            return {"status": "error", "content": [{"text": "No query provided to process."}]}

        # Default empty list if None
        if tool_names is None:
            tool_names = []

        # Capture stdout to get the Strands output
        original_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            from strands_agents_builder.tools import get_tools

            all_tools = get_tools()

            # Select requested tools or use all if none specified
            selected_tools = [all_tools[name] for name in tool_names if name in all_tools]
            if not selected_tools:
                selected_tools = list(all_tools.values())

            # Use provided system prompt or default
            if not system_prompt:
                # Try to load system prompt with same logic as in Strands
                system_prompt = os.getenv("STRANDS_SYSTEM_PROMPT")
                if not system_prompt:
                    prompt_file = Path(os.getcwd()) / ".prompt"
                    if prompt_file.exists() and prompt_file.is_file():
                        try:
                            system_prompt = prompt_file.read_text().strip()
                        except Exception:
                            pass
                if not system_prompt:
                    system_prompt = "You are a helpful assistant."

            # Initialize the nested agent
            agent = Agent(tools=selected_tools, messages=[], system_prompt=system_prompt)

            # Process the query
            if query:
                response = agent(query)
                # The agent's response might already be printed to stdout,
                # but we'll also try to capture the return value
                result_str = str(response) if response else ""
            else:
                result_str = "No query provided to process."

            # Get the captured output
            output = captured_output.getvalue()

            # Combine captured output and result
            full_output = output + "\n" + result_str if output and result_str else output or result_str

        finally:
            # Restore stdout
            sys.stdout = original_stdout

        # Return the result
        return {"status": "success", "content": [{"text": f"Strands result:\n\n{full_output.strip()}"}]}

    except Exception as e:
        # Handle errors
        return {"status": "error", "content": [{"text": f"Error running Strands: {str(e)}"}]}

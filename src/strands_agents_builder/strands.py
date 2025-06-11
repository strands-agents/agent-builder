#!/usr/bin/env python3
"""
Strands - A minimal CLI interface for Strands
"""

import argparse
import logging
import os

# Strands
from strands import Agent
from strands_tools.utils.user_input import get_user_input

from strands_agents_builder.handlers.callback_handler import callback_handler
from strands_agents_builder.tools import get_tools
from strands_agents_builder.utils import model_utils
from strands_agents_builder.utils.kb_utils import load_system_prompt, store_conversation_in_kb
from strands_agents_builder.utils.logging_utils import configure_logging
from strands_agents_builder.utils.welcome_utils import render_goodbye_message, render_welcome_message

os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Strands - A minimal CLI interface for Strands")
    parser.add_argument("query", nargs="*", help="Query to process")
    parser.add_argument(
        "--kb",
        "--knowledge-base",
        dest="knowledge_base_id",
        help="Knowledge base ID to use for retrievals",
    )
    parser.add_argument(
        "--model-provider",
        type=model_utils.load_path,
        default="bedrock",
        help="Model provider to use for inference",
    )
    parser.add_argument(
        "--model-config",
        type=model_utils.load_config,
        default="{}",
        help="Model config as JSON string or path",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=list(logging.getLevelNamesMapping().keys()),
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file. If not specified, logs to stderr when log-level is set",
    )
    args = parser.parse_args()

    # Configure logging based on provided arguments
    if args.log_level or args.log_file:
        # Default to INFO level if log_file is provided but log_level is not
        log_level = args.log_level or "INFO"
        configure_logging(log_level=log_level, log_file=args.log_file)

        # Get module logger for startup messages
        logger = logging.getLogger("strands_agents_builder")
        logger.info(f"Strands CLI started with log level {log_level}")
        if args.log_file:
            logger.info(f"Log file: {os.path.abspath(args.log_file)}")
        else:
            logger.info("Logging to stderr")

    # Get knowledge_base_id from args or environment variable
    knowledge_base_id = args.knowledge_base_id or os.getenv("STRANDS_KNOWLEDGE_BASE_ID")

    model = model_utils.load_model(args.model_provider, args.model_config)

    # Load system prompt
    system_prompt = load_system_prompt()

    tools = get_tools().values()

    agent = Agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        callback_handler=callback_handler,
    )

    # Process query or enter interactive mode
    if args.query:
        query = " ".join(args.query)
        # Use retrieve if knowledge_base_id is defined
        if knowledge_base_id:
            agent.tool.retrieve(text=query, knowledgeBaseId=knowledge_base_id)

        agent(query)

        if knowledge_base_id:
            # Store conversation in knowledge base
            store_conversation_in_kb(agent, query, knowledge_base_id)
    else:
        # Display welcome text at startup
        welcome_result = agent.tool.welcome(action="view", record_direct_tool_call=False)
        welcome_text = ""
        if welcome_result["status"] == "success":
            welcome_text = welcome_result["content"][0]["text"]
            render_welcome_message(welcome_text)
        while True:
            try:
                user_input = get_user_input("\n~ ", default="", keyboard_interrupt_return_default=False)
                if user_input.lower() in ["exit", "quit"]:
                    render_goodbye_message()
                    break
                if user_input.startswith("!"):
                    shell_command = user_input[1:]  # Remove the ! prefix
                    print(f"$ {shell_command}")

                    try:
                        # Execute shell command directly using the shell tool
                        agent.tool.shell(
                            command=shell_command,
                            user_message_override=user_input,
                            non_interactive_mode=True,
                        )

                        print()  # new line after shell command execution
                    except Exception as e:
                        print(f"Shell command execution error: {str(e)}")
                    continue

                if user_input.strip():
                    # Use retrieve if knowledge_base_id is defined
                    if knowledge_base_id:
                        agent.tool.retrieve(text=user_input, knowledgeBaseId=knowledge_base_id)
                    # Read welcome text and add it to the system prompt
                    welcome_result = agent.tool.welcome(action="view", record_direct_tool_call=False)
                    base_system_prompt = load_system_prompt()
                    welcome_text = ""

                    if welcome_result["status"] == "success":
                        welcome_text = welcome_result["content"][0]["text"]

                    # Combine welcome text with base system prompt
                    combined_system_prompt = f"{base_system_prompt}\n\nWelcome Text Reference:\n{welcome_text}"
                    response = agent(user_input, system_prompt=combined_system_prompt)

                    if knowledge_base_id:
                        # Store conversation in knowledge base
                        store_conversation_in_kb(agent, user_input, response, knowledge_base_id)
            except (KeyboardInterrupt, EOFError):
                render_goodbye_message()
                break
            except Exception as e:
                callback_handler(force_stop=True)  # Stop spinners
                print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()

<div align="center">
  <div>
    <a href="https://strandsagents.com">
      <img src="https://strandsagents.com/latest/assets/logo-auto.svg" alt="Strands Agents" width="55px" height="105px">
    </a>
  </div>

  <h1>
    Strands Agent Builder
  </h1>

  <h2>
    A model-driven approach to building AI agents in just a few lines of code.
  </h2>

  <div align="center">
    <a href="https://github.com/strands-agents/agent-builder/graphs/commit-activity"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/strands-agents/agent-builder"/></a>
    <a href="https://github.com/strands-agents/agent-builder/issues"><img alt="GitHub open issues" src="https://img.shields.io/github/issues/strands-agents/agent-builder"/></a>
    <a href="https://github.com/strands-agents/agent-builder/pulls"><img alt="GitHub open pull requests" src="https://img.shields.io/github/issues-pr/strands-agents/agent-builder"/></a>
    <a href="https://github.com/strands-agents/agent-builder/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/strands-agents/agent-builder"/></a>
    <a href="https://pypi.org/project/strands-agents-builder/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/strands-agents-builder"/></a>
    <a href="https://python.org"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/strands-agents-builder"/></a>
  </div>
  
  <p>
    <a href="https://strandsagents.com/">Documentation</a>
    ◆ <a href="https://github.com/strands-agents/samples">Samples</a>
    ◆ <a href="https://github.com/strands-agents/sdk-python">Python SDK</a>
    ◆ <a href="https://github.com/strands-agents/tools">Tools</a>
    ◆ <a href="https://github.com/strands-agents/agent-builder">Agent Builder</a>
    ◆ <a href="https://github.com/strands-agents/mcp-server">MCP Server</a>
  </p>
</div>

An interactive Strands agent toolkit designed to help you build, test, and extend your own custom AI agents and tools. With the Strands Agent Builder, you can create specialized agents, develop custom tools, and compose complex AI workflows—all from your terminal.

## Quick Start

```bash
# Install
pipx install strands-agents-builder

# Run interactive mode for agent development
strands

# Build a custom tool and use it immediately
strands "Create a tool named sentiment_analyzer that analyzes text sentiment and test it with some examples"

# Pipe content to build an agent based on specifications
cat agent-spec.txt | strands "Build a specialized agent based on these specifications"

# Use with knowledge base to extend existing tools
strands --kb YOUR_KB_ID "Load my previous calculator tool and enhance it with scientific functions"
```

## Features

- 🏗️ Create and test custom tools with instant hot-reloading
- 🤖 Build specialized agents with focused capabilities
- 🔄 Extend existing tools and enhance their functionality
- 💬 Interactive command-line interface with rich output
- 🛠️ Powerful integrated tools (12+ tools including shell, editor, HTTP, Python)
- 🧠 Knowledge base integration for persisting and loading tools
- 🎮 Customizable system prompt for specialized agents
- 🪄 Nested agent capabilities with tool delegation
- 🔧 Dynamic tool loading for extending functionality
- 🖥️ Environment variable management and customization

## Integrated Tools

Strands comes with a comprehensive set of built-in tools:

- **shell**: Run command-line operations with interactive support
- **editor**: View and edit files with syntax highlighting
- **http_request**: Make API calls with authentication support
- **python_repl**: Execute Python code interactively
- **calculator**: Perform mathematical operations powered by SymPy
- **retrieve**: Query knowledge bases for relevant information
- **store_in_kb**: Save content to knowledge bases for future reference
- **load_tool**: Dynamically load additional tools at runtime
- **environment**: Manage environment variables
- **strands**: Create nested agent instances with specialized capabilities
- **dialog**: Create interactive dialog interfaces
- **use_aws**: Make AWS API calls through boto3

## Knowledge Base Integration

Strands Agent Builder leverages Amazon Bedrock Knowledge Bases to store and retrieve custom tools, agent configurations, and development history.

```bash
# Load and extend tools from your knowledge base
strands --kb YOUR_KB_ID "Load my data_visualizer tool and add 3D plotting capabilities"

# Or set a default knowledge base via environment variable
export STRANDS_KNOWLEDGE_BASE_ID="YOUR_KB_ID"
strands "Find my most recent agent configuration and make it more efficient"
```

Features:
- 🔄 Retrieve previously created tools and agent configurations
- 💾 Persistent storage for your custom tools and agents
- 🛠️ Ability to iteratively improve tools across sessions
- 🔍 Find and extend tools built in previous sessions

## Nested Agent Capabilities

Use the `strands` tool to prototype and test specialized sub-agents with their own tools and system prompts:

```python
# Create a specialized data analysis agent
agent.tool.strand(
    query="Build and test a data analysis agent",
    tool_names=["python_repl", "editor", "http_request"],
    system_prompt="You're an AI specialized in data analysis. Your task is to build tools for data processing and visualization."
)

# Create a tool-building agent focused on web automation
agent.tool.strand(
    query="Create a set of web automation tools for browser testing",
    tool_names=["editor", "python_repl", "shell"],
    system_prompt="You're an expert in creating web automation tools. Your specialty is developing reliable browser testing utilities."
)
```

## Model Configuration

### Optimized Defaults

Strands comes with optimized, maxed-out configuration settings for the Bedrock model provider:

```json
{
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "max_tokens": 32767,
    "boto_client_config": {
        "read_timeout": 900,
        "connect_timeout": 900,
        "retries": {
            "max_attempts": 3,
            "mode": "adaptive"
        }
    },
    "additional_request_fields": {
        "thinking": {
            "type": "enabled",
            "budget_tokens": 2048
        }
    }
}
```

These settings provide:
- Claude Sonnet 4 (latest high-performance model)
- Maximum token output (32,768 tokens)
- Extended timeouts (15 minutes) for complex operations
- Automatic retries with adaptive backoff
- Enabled thinking capability with 2,048 token budget for recursive reasoning

You can customize these values using environment variables:

```bash
# Maximum tokens for responses
export STRANDS_MAX_TOKENS=32000

# Budget for agent thinking/reasoning
export STRANDS_BUDGET_TOKENS=1024
```

## Custom Model Provider

You can configure strands to use a different model provider with specific settings by passing in the following arguments:

```bash
strands --model-provider <NAME> --model-config <JSON|FILE>
```

As an example, if you wanted to use the packaged Ollama provider with a specific model id, you would run:

```bash
strands --model-provider ollama --model-config '{"model_id": <ID>}'
```

Strands Agent Builder is packaged with `bedrock` and `ollama`.

If you have implemented a custom model provider ([instructions](<LINK>)) and would like to use it with strands, create a python module under the directory "$CWD/.models" and expose an `instance` function that returns an instance of your provider. As an example, assume you have:

```bash
$ cat ./.models/custom_model.py
from mymodels import CustomModel

def instance(**config):
    return CustomModel(**config)
```

You can then use it with strands by running:

```bash
$ strands --model-provider custom_model --model-config <JSON|FILE>
```

## Custom System Prompts

```bash
# Via environment variable
export STRANDS_SYSTEM_PROMPT="You are a Python expert."

# Or local file
echo "You are a security expert." > .prompt
```

## Exit

Type `exit`, `quit`, or press `Ctrl+C`/`Ctrl+D`

## Contributing ❤️

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details on:
- Reporting bugs & features
- Development setup
- Contributing via Pull Requests
- Code of Conduct
- Reporting of security issues

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## ⚠️ Preview Status

Strands Agents is currently in public preview. During this period:
- APIs may change as we refine the SDK
- We welcome feedback and contributions

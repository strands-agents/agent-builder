# Strands Agent Builder

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
    "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "max_tokens": 64000,
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
- Claude 3.7 Sonnet (latest high-performance model)
- Maximum token output (64,000 tokens)
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

Strands is packaged with the following providers:
| Name | Config |
| ---- | ------ |
| `bedrock` | [reference](<LINK>) |
| `ollama` | [reference](<LINK>) |

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

## Custom Systm Prompts

```bash
# Via environment variable
export STRANDS_SYSTEM_PROMPT="You are a Python expert."

# Or local file
echo "You are a security expert." > .prompt
```

## Contributing

```bash
git clone https://github.com/strands-agents/agent-builder.git ~/.agent-builder
cd ~/.agent-builder
python3 -m venv venv && source venv/bin/activate
pip3 install -e .
pip3 install -e ".[test]"

# Run tests
hatch run test         # Run all tests with verbose coverage output
hatch run test -k test_pattern  # Run specific tests matching a pattern
```

Testing is managed through hatch scripting in pyproject.toml.

## Exit

Type `exit`, `quit`, or press `Ctrl+C`/`Ctrl+D`

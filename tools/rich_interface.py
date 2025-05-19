import textwrap
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from strands.types.tools import ToolResult, ToolUse

TOOL_SPEC = {
    "name": "rich_interface",
    "description": textwrap.dedent(
        """
        Create rich, interactive console interfaces with various components. Supports panels, tables, trees, markdown,
        syntax highlighting, progress bars, and text with proper styling.

        IMPORTANT ERROR PREVENTION:
        1. Data Structure Errors:
            • Missing "interface_definition" object
            • Missing "components" array
            • Empty components array
            • Invalid component structure

        2. Component-Specific Errors:
            • Table: Mismatched headers and row lengths
            • Progress: Invalid total/completed values
            • Tree: Missing label or invalid items
            • Syntax: Invalid language specification

        3. Data Type Errors:
            • Numbers provided as strings
            • Arrays provided as single values
            • Boolean values as strings
            • Null/undefined values in required fields

        4. Schema Validation:
            • Always verify interface_definition exists
            • Ensure components array is present
            • Check required fields per component
            • Validate data types before rendering

        Key Features:
        1. Component Types:
            • panel: Boxed content with optional title and border
            • table: Structured data with headers and rows
            • progress: Progress bars with description
            • tree: Hierarchical data structure
            • markdown: Formatted text with MD syntax
            • syntax: Code with syntax highlighting
            • text: Simple text with optional styling

        2. Component Requirements:
            • panel: { type: "panel", content: string, title?: string }
            • table: { type: "table", headers: string[], rows: string[][], title?: string }
            • progress: { type: "progress", description: string, total: number, completed: number }
            • tree: { type: "tree", label: string, items: string[] }
            • markdown: { type: "markdown", content: string }
            • syntax: { type: "syntax", code: string, language: string }
            • text: { type: "text", content: string }

        3. Error Prevention:
            a) Common Errors:
                • Missing "components" array
                • Invalid component type
                • Missing required fields
                • Incorrect data types
                • Null/undefined values

            b) Required Validations:
                • Check interface_definition exists
                • Verify components array presence
                • Validate component type
                • Ensure required fields per type
                • Verify data structure integrity

        4. Best Practices:
            a) Structure:
                • Organize related components in panels
                • Use consistent styling
                • Group similar data in tables
                • Maintain clear hierarchy

            b) Data Handling:
                • Pre-validate all data
                • Handle empty states gracefully
                • Use appropriate data types
                • Format data before display

            c) Performance:
                • Limit components per interface
                • Optimize large datasets
                • Cache repeated content
                • Use appropriate component types

        5. Example Usage:
            {
                "interface_definition": {
                "components": [
                    {
                    "type": "panel",
                    "title": "Status",
                    "content": "System operational"
                    },
                    {
                    "type": "table",
                    "headers": ["ID", "Status"],
                    "rows": [["1", "Active"]]
                    }
                ]
                }
            }

        6. Troubleshooting:
            a) Common Issues:
                • Component not rendering
                • Incorrect data display
                • Formatting problems
                • Layout issues

            b) Solutions:
                • Verify component structure
                • Check data types
                • Validate required fields
                • Test component isolation
    """
    ).strip(),
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "interface_definition": {
                    "type": "object",
                    "description": "The interface definition object containing components",
                    "required": ["components"],
                    "properties": {
                        "components": {
                            "type": "array",
                            "description": "Array of component definitions",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": [
                                            "panel",
                                            "table",
                                            "progress",
                                            "tree",
                                            "markdown",
                                            "syntax",
                                            "text",
                                        ],
                                        "description": "Type of the component",
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "Title for panel or table components",
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "Content for panel, markdown, syntax, or text components",
                                    },
                                    "headers": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Headers for table component",
                                    },
                                    "rows": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "description": "Rows for table component",
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Description for progress component",
                                    },
                                    "total": {
                                        "type": "number",
                                        "description": "Total value for progress component",
                                    },
                                    "completed": {
                                        "type": "number",
                                        "description": "Completed value for progress component",
                                    },
                                    "label": {
                                        "type": "string",
                                        "description": "Label for tree component",
                                    },
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Items for tree component",
                                    },
                                    "language": {
                                        "type": "string",
                                        "description": "Language for syntax component",
                                    },
                                },
                                "required": ["type"],
                            },
                        }
                    },
                }
            },
            "required": ["interface_definition"],
        }
    },
}


def rich_interface(tool: ToolUse, **kwargs: Any) -> ToolResult:
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    console = Console()
    interface_definition = tool_input["interface_definition"]

    if "components" not in interface_definition:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "No components defined in the interface definition."}],
        }

    for component in interface_definition["components"]:
        if component["type"] == "panel":
            panel = Panel(component.get("content", ""), title=component.get("title", ""))
            console.print(panel)
        elif component["type"] == "table":
            table = Table(title=component.get("title", ""))
            for header in component.get("headers", []):
                table.add_column(header)
            for row in component.get("rows", []):
                table.add_row(*row)
            console.print(table)
        elif component["type"] == "progress":
            with Progress() as progress:
                task = progress.add_task(component.get("description", ""), total=component.get("total", 100))
                progress.update(task, advance=component.get("completed", 0))
        elif component["type"] == "tree":
            tree = Tree(component.get("label", "Root"))
            for item in component.get("items", []):
                tree.add(item)
            console.print(tree)
        elif component["type"] == "markdown":
            md = Markdown(component.get("content", ""))
            console.print(md)
        elif component["type"] == "syntax":
            syntax = Syntax(
                component.get("code", ""),
                component.get("language", "python"),
                theme="monokai",
            )
            console.print(syntax)
        elif component["type"] == "text":
            text = Text(component.get("content", ""))
            console.print(text)

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": "Interface rendered to terminal"}],
    }

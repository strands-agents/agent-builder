#!/usr/bin/env python3
"""
Welcome message utility functions for Strands
"""

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme

# Create a custom theme for consistent styling
STRANDS_THEME = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "danger": "bold red",
        "success": "green",
        "heading": "bold blue",
        "subheading": "cyan",
        "highlight": "yellow",
        "prompt": "green",
    }
)

# Create the console with the custom theme
console = Console(theme=STRANDS_THEME)


def render_welcome_message(welcome_text):
    """
    Print a beautifully formatted welcome message using Rich.

    Args:
        welcome_text (str): The welcome message text to render

    Returns:
        None: Prints the formatted message to the console
    """
    try:
        # Try to render as markdown first for rich formatting
        md = Markdown(welcome_text)
        panel_content = md
    except Exception:
        # Fallback to simple text if markdown parsing fails
        panel_content = welcome_text

    # Create a centered panel with the welcome message
    welcome_panel = Panel(
        Align.center(panel_content),
        title="[heading]Welcome to Strands[/heading]",
        subtitle="[info]strands[/info]",
        border_style="blue",
        box=ROUNDED,
        expand=False,
        padding=(1, 2),
    )

    # Print the welcome panel
    console.print(welcome_panel)

    # Add an empty line after the welcome message
    console.print()


def render_goodbye_message():
    """Print a goodbye message when Strands is exiting"""
    console.print("\n")
    console.print(
        Panel(
            Align.center("[highlight]Thank you for using Strands![/highlight]"),
            border_style="blue",
            box=ROUNDED,
            expand=False,
            padding=(1, 1),
        )
    )

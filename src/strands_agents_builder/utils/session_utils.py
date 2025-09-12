#!/usr/bin/env python3
"""
Session management utilities for Strands Agent Builder.
"""

import datetime
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

from colorama import Fore, Style
from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from strands.session.file_session_manager import FileSessionManager

# Create console for rich formatting
console = Console()

# Constants
SESSION_PREFIX = "session_"
DEFAULT_DISPLAY_LIMIT = 10

# Set up logging
logger = logging.getLogger(__name__)


def validate_session_id(session_id: str) -> bool:
    """Validate that a session ID is safe to use as a directory name."""
    if not session_id:
        return False

    # Check for basic safety - no path separators, no hidden files, reasonable length
    if any(char in session_id for char in ["/", "\\", "..", "\0"]):
        return False

    if session_id.startswith(".") or len(session_id) > 255:
        return False

    return True


def validate_session_path(path: str) -> bool:
    """Validate that a session path is safe to use."""
    if not path:
        return False

    try:
        # Try to create a Path object and check if it's absolute or relative
        path_obj = Path(path)
        # Basic validation - path should be reasonable
        return len(str(path_obj)) < 4096  # Reasonable path length limit
    except (ValueError, OSError):
        return False


def generate_session_id() -> str:
    """Generate a unique session ID based on timestamp and UUID."""
    timestamp = int(time.time())
    short_uuid = str(uuid.uuid4())[:8]
    return f"strands-{timestamp}-{short_uuid}"


def get_sessions_directory(base_path: Optional[str] = None, create: bool = False) -> Optional[Path]:
    """Get the sessions directory path. Returns None if no base_path provided."""
    if not base_path:
        return None

    sessions_dir = Path(base_path)

    if create:
        sessions_dir.mkdir(parents=True, exist_ok=True)

    return sessions_dir


def create_session_manager(
    session_id: Optional[str] = None, base_path: Optional[str] = None
) -> Optional[FileSessionManager]:
    """Create a FileSessionManager with the given or generated session ID. Returns None if no base_path."""
    if not base_path or not validate_session_path(base_path):
        return None

    if session_id is None:
        session_id = generate_session_id()
    elif not validate_session_id(session_id):
        logger.warning(f"Invalid session ID provided: {session_id}")
        return None

    # Create the sessions directory since we're actually creating a session manager
    sessions_dir = get_sessions_directory(base_path, create=True)
    return FileSessionManager(session_id=session_id, storage_dir=str(sessions_dir))


def list_available_sessions(base_path: Optional[str] = None) -> list[str]:
    """List all available session IDs in the sessions directory."""
    if not base_path or not validate_session_path(base_path):
        return []

    # Don't create directory, just check if it exists
    sessions_dir = get_sessions_directory(base_path, create=False)
    session_ids = []

    if sessions_dir and sessions_dir.exists():
        try:
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir() and session_dir.name.startswith(SESSION_PREFIX):
                    # Extract session ID from directory name (remove "session_" prefix)
                    session_id = session_dir.name[len(SESSION_PREFIX) :]
                    if validate_session_id(session_id):
                        session_ids.append(session_id)
        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to list sessions in {base_path}: {e}")

    return sorted(session_ids)


def session_exists(session_id: str, base_path: Optional[str] = None) -> bool:
    """Check if a session exists."""
    if not base_path or not validate_session_path(base_path) or not validate_session_id(session_id):
        return False

    # Don't create directory, just check if session exists
    sessions_dir = get_sessions_directory(base_path, create=False)
    if not sessions_dir:
        return False

    session_dir = sessions_dir / f"{SESSION_PREFIX}{session_id}"
    return session_dir.exists() and (session_dir / "session.json").exists()


def get_session_info(session_id: str, base_path: Optional[str] = None) -> Optional[dict]:
    """Get basic information about a session."""
    if not base_path or not validate_session_path(base_path) or not validate_session_id(session_id):
        return None

    if not session_exists(session_id, base_path):
        return None

    # Don't create directory, just get the path
    sessions_dir = get_sessions_directory(base_path, create=False)
    if not sessions_dir:
        return None

    session_dir = sessions_dir / f"{SESSION_PREFIX}{session_id}"

    try:
        # Get creation time from directory
        created_at = session_dir.stat().st_ctime

        # Count messages across all agents
        total_messages = 0
        agents_dir = session_dir / "agents"
        if agents_dir.exists():
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir():
                    messages_dir = agent_dir / "messages"
                    if messages_dir.exists():
                        total_messages += len(
                            [f for f in messages_dir.iterdir() if f.is_file() and f.suffix == ".json"]
                        )

        return {
            "session_id": session_id,
            "created_at": created_at,
            "total_messages": total_messages,
            "path": str(session_dir),
        }
    except (OSError, PermissionError) as e:
        logger.warning(f"Failed to get session info for {session_id}: {e}")
        return None


def list_sessions_command(session_base_path: Optional[str]) -> None:
    """Handle the --list-sessions command."""
    if not session_base_path:
        console.print(
            "[red]Error: Session management not enabled. Use --session-path or "
            "set STRANDS_SESSION_PATH environment variable.[/red]"
        )
        return

    sessions = list_available_sessions(session_base_path)
    if not sessions:
        console.print("[yellow]No sessions found.[/yellow]")
    else:
        console.print("[bold cyan]Available sessions:[/bold cyan]")
        for session_id in sessions:
            info = get_session_info(session_id, session_base_path)
            if info:
                created = datetime.datetime.fromtimestamp(info["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
                console.print(f"  [green]{session_id}[/green] (created: {created}, messages: {info['total_messages']})")


def display_agent_history(agent, session_id: str) -> None:
    """Display conversation history from an agent's loaded messages."""
    try:
        if agent.messages and len(agent.messages) > 0:
            # Display last messages completely
            display_limit = DEFAULT_DISPLAY_LIMIT

            # Create header message
            header_text = f"Resuming session: {session_id}"

            # Show indicator if there are more messages
            if len(agent.messages) > display_limit:
                hidden_count = len(agent.messages) - display_limit
                subtitle_text = f"{hidden_count} previous messages not shown"
            else:
                subtitle_text = f"Showing all {len(agent.messages)} messages"

            # Display header with rich formatting
            header_panel = Panel(
                Align.center(f"[bold cyan]{header_text}[/bold cyan]"),
                subtitle=f"[dim]{subtitle_text}[/dim]",
                border_style="blue",
                box=ROUNDED,
                expand=False,
                padding=(1, 3),
            )
            console.print()  # Empty line before
            console.print(header_panel)
            console.print()  # Empty line after

            # Get the messages to display
            recent_messages = agent.messages[-display_limit:] if len(agent.messages) > display_limit else agent.messages

            for msg in recent_messages:
                role = msg.get("role", "unknown")
                content_blocks = msg.get("content", [])

                # Extract text from content blocks
                content = ""
                for block in content_blocks:
                    if isinstance(block, dict) and "text" in block:
                        content += block["text"]

                if role == "user":
                    print(f"{Fore.GREEN}~ {Style.RESET_ALL}{content}")
                    print()  # Empty line after user message
                elif role == "assistant":
                    print(f"{Fore.WHITE}{content}{Style.RESET_ALL}")
                    print()  # Empty line after assistant message

    except Exception as e:
        # If we can't load history, log the error but continue
        logger.warning(f"Failed to display agent history for session {session_id}: {e}")
        console.print("[yellow]Warning: Could not load session history[/yellow]")


def setup_session_management(
    session_id: Optional[str], session_base_path: Optional[str]
) -> Tuple[Optional[FileSessionManager], Optional[str], bool]:
    """Set up session management if enabled. Returns (session_manager, session_id, is_resuming)."""
    session_manager = None
    resolved_session_id = None
    is_resuming = False

    if session_base_path:
        # Check if resuming existing session
        if session_id:
            if session_exists(session_id, session_base_path):
                resolved_session_id = session_id
                is_resuming = True
            else:
                resolved_session_id = session_id

        # Create session manager
        session_manager = create_session_manager(resolved_session_id, session_base_path)
        if session_manager:
            resolved_session_id = session_manager.session_id

    return session_manager, resolved_session_id, is_resuming


def handle_session_commands(command: str, session_id: Optional[str], session_base_path: Optional[str]) -> bool:
    """Handle session-related interactive commands. Returns True if command was handled."""
    if command == "session info" and session_id:
        info = get_session_info(session_id, session_base_path)
        if info:
            created = datetime.datetime.fromtimestamp(info["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
            console.print(f"[bold cyan]Session ID:[/bold cyan] {info['session_id']}")
            console.print(f"[bold cyan]Created:[/bold cyan] {created}")
            console.print(f"[bold cyan]Total messages:[/bold cyan] {info['total_messages']}")
        return True

    elif command == "session list" and session_base_path:
        sessions = list_available_sessions(session_base_path)
        if not sessions:
            console.print("[yellow]No sessions found.[/yellow]")
        else:
            console.print("[bold cyan]Available sessions:[/bold cyan]")
            for sid in sessions:
                info = get_session_info(sid, session_base_path)
                if info:
                    created = datetime.datetime.fromtimestamp(info["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
                    current = " [dim](current)[/dim]" if sid == session_id else ""
                    console.print(
                        f"  [green]{sid}[/green] (created: {created}, messages: {info['total_messages']}){current}"
                    )
        return True

    elif command.startswith("session "):
        if session_base_path:
            console.print("[bold cyan]Available session commands:[/bold cyan]")
            console.print("  [green]!session info[/green]  - Show current session details")
            console.print("  [green]!session list[/green]  - List all available sessions")
        else:
            console.print("[red]Error: Session management not enabled.[/red]")
        return True

    return False

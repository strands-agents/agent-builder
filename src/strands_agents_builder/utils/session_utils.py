#!/usr/bin/env python3
"""
Session management utilities for Strands Agent Builder.
"""

import datetime
import os
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

from colorama import Fore, Style
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.box import ROUNDED
from strands.session.file_session_manager import FileSessionManager

# Create console for rich formatting
console = Console()


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
    if not base_path:
        return None

    if session_id is None:
        session_id = generate_session_id()

    # Create the sessions directory since we're actually creating a session manager
    sessions_dir = get_sessions_directory(base_path, create=True)
    return FileSessionManager(session_id=session_id, storage_dir=str(sessions_dir))


def list_available_sessions(base_path: Optional[str] = None) -> list[str]:
    """List all available session IDs in the sessions directory."""
    if not base_path:
        return []

    # Don't create directory, just check if it exists
    sessions_dir = get_sessions_directory(base_path, create=False)
    session_ids = []

    if sessions_dir and sessions_dir.exists():
        for session_dir in sessions_dir.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith("session_"):
                # Extract session ID from directory name (remove "session_" prefix)
                session_id = session_dir.name[8:]  # len("session_") = 8
                session_ids.append(session_id)

    return sorted(session_ids)


def session_exists(session_id: str, base_path: Optional[str] = None) -> bool:
    """Check if a session exists."""
    if not base_path:
        return False

    # Don't create directory, just check if session exists
    sessions_dir = get_sessions_directory(base_path, create=False)
    if not sessions_dir:
        return False

    session_dir = sessions_dir / f"session_{session_id}"
    return session_dir.exists() and (session_dir / "session.json").exists()


def get_session_info(session_id: str, base_path: Optional[str] = None) -> Optional[dict]:
    """Get basic information about a session."""
    if not base_path or not session_exists(session_id, base_path):
        return None

    # Don't create directory, just get the path
    sessions_dir = get_sessions_directory(base_path, create=False)
    if not sessions_dir:
        return None

    session_dir = sessions_dir / f"session_{session_id}"

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
                    total_messages += len([f for f in messages_dir.iterdir() if f.is_file() and f.suffix == ".json"])

    return {
        "session_id": session_id,
        "created_at": created_at,
        "total_messages": total_messages,
        "path": str(session_dir),
    }


def list_sessions_command(session_base_path: Optional[str]) -> None:
    """Handle the --list-sessions command."""
    if not session_base_path:
        console.print(
            "[red]Error: Session management not enabled. Use --session-path or set STRANDS_SESSION_PATH environment variable.[/red]"
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
            # Display last 10 messages (5 pairs) completely
            display_limit = 10

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
        # If we can't load history, just continue silently
        pass


def setup_session_management(
    session_id: Optional[str], session_base_path: Optional[str]
) -> Tuple[Optional[object], Optional[str], bool]:
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
            print(f"Session ID: {info['session_id']}")
            print(f"Created: {created}")
            print(f"Total messages: {info['total_messages']}")
        return True

    elif command == "session list" and session_base_path:
        sessions = list_available_sessions(session_base_path)
        if not sessions:
            print("No sessions found.")
        else:
            print("Available sessions:")
            for sid in sessions:
                info = get_session_info(sid, session_base_path)
                if info:
                    created = datetime.datetime.fromtimestamp(info["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
                    current = " (current)" if sid == session_id else ""
                    print(f"  {sid} (created: {created}, messages: {info['total_messages']}){current}")
        return True

    elif command.startswith("session "):
        if session_base_path:
            print("Available session commands:")
            print("  !session info  - Show current session details")
            print("  !session list  - List all available sessions")
        else:
            print("Error: Session management not enabled.")
        return True

    return False

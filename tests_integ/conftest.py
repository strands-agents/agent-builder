"""Common fixtures for integration tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_file_structure(tmp_path: Path):
    """Creates a temporary directory structure for tool creation and returns paths."""
    tools_dir = tmp_path / ".strands" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    return {"tools_dir": tools_dir, "root_dir": tmp_path}

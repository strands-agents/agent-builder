#!/usr/bin/env python3
"""
Utility functions for configuring and managing logging in the Strands CLI.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """
    Configure logging for the Strands CLI with file output.

    Args:
        log_level: The logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file. If None, logging is disabled.
        log_format: The format string for log messages

    Returns:
        None
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # If no log file is specified, disable logging and return
    if not log_file:
        # Reset root logger
        root = logging.getLogger()
        if root.handlers:
            for handler in root.handlers[:]:
                root.removeHandler(handler)

        # Set level to CRITICAL to minimize any accidental logging
        root.setLevel(logging.CRITICAL)
        return

    # Create handlers
    handlers: List[logging.Handler] = []

    # Setup file handler
    try:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    except Exception as e:
        print(f"Warning: Failed to create log file {log_file}: {str(e)}")
        print("Logging will be disabled")
        return

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers,
        force=True,  # Force reconfiguration
    )

    # Configure specific Strands loggers
    loggers = ["strands", "strands.agent", "strands.models", "strands.tools", "strands_agents_builder"]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)

    # Log configuration information to the file
    logging.info(f"Logging configured with level: {log_level}")
    logging.info(f"Log file: {os.path.abspath(log_file)}")


def get_available_log_levels() -> List[str]:
    """
    Returns a list of available logging levels.

    Returns:
        List of log level names
    """
    return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def get_logging_status() -> Dict[str, Any]:
    """
    Get the current logging status.

    Returns:
        Dict with information about the current logging configuration
    """
    root_logger = logging.getLogger()
    handlers = root_logger.handlers

    file_handlers = [h for h in handlers if isinstance(h, logging.FileHandler)]
    file_paths = [h.baseFilename for h in file_handlers]

    status = {
        "level": logging.getLevelName(root_logger.level),
        "handlers": {"console": any(isinstance(h, logging.StreamHandler) for h in handlers), "files": file_paths},
        "strands_loggers": {},
    }

    # Get status of strands specific loggers
    for logger_name in ["strands", "strands.agent", "strands.models", "strands.tools", "strands_agents_builder"]:
        logger = logging.getLogger(logger_name)
        status["strands_loggers"][logger_name] = logging.getLevelName(logger.level)

    return status


def set_log_level_for_module(module_name: str, log_level: Union[str, int]) -> None:
    """
    Set log level for a specific module.

    Args:
        module_name: The name of the module logger
        log_level: The log level to set (can be string or logging constant)

    Returns:
        None
    """
    if isinstance(log_level, str):
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {log_level}")
    else:
        numeric_level = log_level

    logger = logging.getLogger(module_name)
    logger.setLevel(numeric_level)
    logging.debug(f"Set log level for {module_name} to {log_level}")

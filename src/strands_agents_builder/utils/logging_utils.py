"""
Utility functions for configuring and managing logging in the Strands Agent Builder.
"""

import logging
import os
from typing import List, Optional


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """
    Configure logging for the Strands Agent Builder.

    Args:
        log_level: The logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file. If None, logs to stderr.
        log_format: The format string for log messages

    Returns:
        None
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Reset root logger
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers[:]:
            root.removeHandler(handler)

    # Create handlers list
    handlers: List[logging.Handler] = []

    if log_file:
        # Setup file handler
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            handlers.append(logging.FileHandler(log_file))
        except Exception as e:
            print(f"Warning: Failed to create log file {log_file}: {str(e)}")
            print("Falling back to stderr logging")
            handlers.append(logging.StreamHandler())
    else:
        # If no log file specified, use stderr
        handlers.append(logging.StreamHandler())

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers,
        force=True,  # Force reconfiguration
    )

    # Configure specific Strands loggers (parent loggers will handle children)
    loggers = ["strands", "strands_tools", "strands_agents_builder"]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)

    # Log configuration information
    config_logger = logging.getLogger("strands_agents_builder")
    config_logger.info(f"Logging configured with level: {log_level}")
    if log_file:
        config_logger.info(f"Log file: {os.path.abspath(log_file)}")
    else:
        config_logger.info("Logging to stderr")


def get_available_log_levels() -> List[str]:
    """
    Returns a list of available logging levels.

    Returns:
        List of log level names
    """
    return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

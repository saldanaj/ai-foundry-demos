"""
Utility functions for the Healthcare Demo
"""
import logging
import time
from functools import wraps
from typing import Callable, Any


def setup_logging(level: str = "INFO"):
    """
    Setup logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def timing_decorator(func: Callable) -> Callable:
    """
    Decorator to measure function execution time

    Args:
        func: Function to measure

    Returns:
        Wrapped function that logs execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time

        logger = logging.getLogger(func.__module__)
        logger.info(f"{func.__name__} executed in {duration:.2f} seconds")

        return result

    return wrapper


def format_entity_for_display(entity_dict: dict) -> str:
    """
    Format entity dictionary for display

    Args:
        entity_dict: Dictionary with entity category counts

    Returns:
        Formatted string for display
    """
    if not entity_dict:
        return "No PII/PHI detected"

    lines = []
    for category, count in sorted(entity_dict.items()):
        lines.append(f"• {category}: {count}")

    return "\n".join(lines)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def create_citation_markdown(citations: list[dict]) -> str:
    """
    Create markdown formatted citations

    Args:
        citations: List of citation dictionaries

    Returns:
        Markdown formatted citations
    """
    if not citations:
        return "*No web sources cited*"

    lines = ["### 🔗 Web Sources"]
    for i, citation in enumerate(citations, 1):
        title = citation.get('title', 'Web Source')
        url = citation.get('url', '#')
        lines.append(f"{i}. [{title}]({url})")

    return "\n".join(lines)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    return sanitized


def estimate_tokens(text: str) -> int:
    """
    Rough estimation of token count

    Args:
        text: Input text

    Returns:
        Estimated token count (rough approximation)
    """
    # Simple estimation: ~4 characters per token
    return len(text) // 4

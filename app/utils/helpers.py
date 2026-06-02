"""Utility functions."""
import logging
from typing import Optional


logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        debug: Enable debug logging
    """
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def sanitize_text(text: str) -> str:
    """Sanitize text for processing.
    
    Args:
        text: Raw text
        
    Returns:
        Sanitized text
    """
    # Remove extra whitespace
    text = " ".join(text.split())
    # Remove control characters
    text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t\r")
    return text.strip()

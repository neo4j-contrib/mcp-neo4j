"""
Utility functions for sizing calculations.
"""

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with consistent configuration."""
    return logging.getLogger(name)


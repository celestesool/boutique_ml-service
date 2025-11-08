"""
Logger configuration using loguru
"""

import sys
from loguru import logger as loguru_logger
from app.config import settings


# Remove default logger
loguru_logger.remove()

# Add console logger
loguru_logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)

# Add file logger
loguru_logger.add(
    settings.LOG_FILE_PATH,
    rotation="500 MB",
    retention="10 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.LOG_LEVEL
)

logger = loguru_logger

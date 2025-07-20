"""
Logging configuration for Infra Mind.

Uses Loguru for structured, colorful, and performant logging.
This is a modern alternative to Python's built-in logging module.
"""

import sys
from pathlib import Path
from loguru import logger
from .config import settings


def setup_logging() -> None:
    """
    Configure application logging.
    
    Learning Note: Loguru provides a much simpler and more powerful
    logging experience compared to Python's built-in logging module.
    """
    
    # Remove default handler
    logger.remove()
    
    # Console logging with colors and formatting
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for production
    if settings.environment == "production":
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Application logs
        logger.add(
            log_dir / "infra_mind.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="gz",
            backtrace=True,
            diagnose=False,  # Don't include sensitive data in production logs
        )
        
        # Error logs
        logger.add(
            log_dir / "errors.log",
            format=log_format,
            level="ERROR",
            rotation="1 week",
            retention="12 weeks",
            compression="gz",
            backtrace=True,
            diagnose=True,
        )
    
    # Log startup information
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Environment: {settings.environment}")
    logger.info(f"🐛 Debug mode: {settings.debug}")


def get_logger(name: str):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Usually __name__ from the calling module
        
    Returns:
        Configured logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("This is a log message")
    """
    return logger.bind(name=name)
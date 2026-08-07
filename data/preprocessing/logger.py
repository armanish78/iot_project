import logging
import os
from datetime import datetime
from config.preprocessing_config import LOGS_DIR


def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a configured logger that writes to both console and file.

    Args:
        name (str): The name of the logger (usually __name__).

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if logger is requested multiple times
    if logger.hasHandlers():
        return logger

    # Formatting
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    log_file = (
        LOGS_DIR / f"preprocessing_{datetime.now().strftime('%Y%m%d')}.log"
    )
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Ensure logs from basicConfig don't propagate multiple times
    logger.propagate = False

    return logger

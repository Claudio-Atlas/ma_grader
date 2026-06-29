"""
logger.py — Centralized logging configuration for MA-Grader

Logs to both console and file. Creates timestamped log files in the output folder.
"""
import logging
import os
from datetime import datetime

# Module-level logger instance
_logger = None
_file_handler = None


def setup_logger(output_folder: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the MA-Grader logger.
    
    Args:
        output_folder: Where to save log files (optional)
        level: Logging level (default INFO)
    
    Returns:
        Configured logger instance
    """
    global _logger, _file_handler
    
    # Get or create the logger
    logger = logging.getLogger("ma_grader")
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.setLevel(level)
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console_format = logging.Formatter('[%(levelname)s] %(message)s')
    console.setFormatter(console_format)
    logger.addHandler(console)
    
    # File handler (if output folder provided)
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(output_folder, f"grading_log_{timestamp}.txt")
        _file_handler = logging.FileHandler(log_file, encoding='utf-8')
        _file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        _file_handler.setFormatter(file_format)
        logger.addHandler(_file_handler)
        logger.info(f"Log file created: {log_file}")
    
    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the MA-Grader logger instance.
    
    If not yet configured, returns a basic logger with console output.
    """
    global _logger
    
    if _logger is None:
        # Create a basic logger if setup_logger hasn't been called
        _logger = logging.getLogger("ma_grader")
        if not _logger.handlers:
            _logger.setLevel(logging.INFO)
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console_format = logging.Formatter('[%(levelname)s] %(message)s')
            console.setFormatter(console_format)
            _logger.addHandler(console)
    
    return _logger


def close_logger():
    """
    Close and clean up the logger, especially the file handler.
    Call this at the end of a pipeline run.
    """
    global _logger, _file_handler
    
    if _file_handler:
        _file_handler.close()
        if _logger:
            _logger.removeHandler(_file_handler)
        _file_handler = None

import logging
from pathlib import Path
from datetime import datetime

def setup_logger(name, log_file=None):
    """Set up logger with file and console handlers
    
    Args:
        name (str): Logger name
        log_file (str): Log file path
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if not exists
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Add file handler if log_file specified
    if log_file:
        file_path = log_dir / f"{log_file}_{datetime.now().strftime('%Y-%m-%d')}.log"
        fh = logging.FileHandler(file_path, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # Add console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger
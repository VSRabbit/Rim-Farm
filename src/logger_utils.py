import logging
from pathlib import Path
from datetime import datetime
import logging.handlers

class DailyRotatingFileHandler(logging.Handler):
    """Custom handler that creates new log file each day"""
    
    def __init__(self, name, log_dir):
        super().__init__()
        self.name = name
        self.log_dir = Path(log_dir)
        self.current_date = None
        self.file_handler = None
        self._update_file_handler()
    
    def _update_file_handler(self):
        """Update file handler if date has changed"""
        today = datetime.now().date()
        if today != self.current_date:
            # Close existing handler if any
            if self.file_handler:
                self.file_handler.close()
            
            # Create new file handler with current date
            file_path = self.log_dir / f"{self.name}_{today.strftime('%Y-%m-%d')}.log"
            self.file_handler = logging.FileHandler(file_path, encoding='utf-8')
            self.file_handler.setFormatter(self.formatter)
            self.current_date = today
    
    def emit(self, record):
        """Emit log record to current day's file"""
        self._update_file_handler()
        self.file_handler.emit(record)
    
    def setFormatter(self, formatter):
        """Set formatter for both handler and future handlers"""
        super().setFormatter(formatter)
        if self.file_handler:
            self.file_handler.setFormatter(formatter)

def setup_logger(name, log_file=None):
    """Set up logger with daily rotating file handler and console handler"""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Add daily rotating file handler
    if log_file:
        daily_handler = DailyRotatingFileHandler(log_file, log_dir)
        daily_handler.setFormatter(formatter)
        logger.addHandler(daily_handler)
    
    # Add console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger
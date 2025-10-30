"""
Structured Logging Configuration
Centralized logging setup for the stock analysis system
"""
import logging
import logging.config
import sys
from typing import Dict, Any
from datetime import datetime
import json
import traceback


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


class StockAnalysisLogger:
    """Centralized logger for stock analysis system"""
    
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger with structured formatting"""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
            
            # Remove existing handlers
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # Create console handler with structured formatter
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(StructuredFormatter())
            logger.addHandler(console_handler)
            
            # Prevent duplicate logs
            logger.propagate = False
            
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def setup_logging(cls, config: Dict[str, Any] = None):
        """Setup logging configuration"""
        default_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structured": {
                    "()": StructuredFormatter,
                },
                "simple": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "structured",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "structured",
                    "filename": "logs/stock_analysis.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "loggers": {
                "app": {
                    "level": "DEBUG",
                    "handlers": ["console", "file"],
                    "propagate": False
                },
                "celery": {
                    "level": "INFO",
                    "handlers": ["console", "file"],
                    "propagate": False
                },
                "sqlalchemy": {
                    "level": "WARNING",
                    "handlers": ["file"],
                    "propagate": False
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console"]
            }
        }
        
        # Merge with custom config if provided
        if config:
            default_config.update(config)
        
        logging.config.dictConfig(default_config)


def get_logger(name: str) -> logging.Logger:
    """Get a structured logger"""
    return StockAnalysisLogger.get_logger(name)


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    """Log with additional context fields"""
    extra_fields = {
        "context": context,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Create a new record with extra fields
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    record.extra_fields = extra_fields
    
    logger.handle(record)


# Initialize logging
StockAnalysisLogger.setup_logging()

# Create module loggers
app_logger = get_logger("app")
celery_logger = get_logger("celery")
database_logger = get_logger("database")
api_logger = get_logger("api")
agent_logger = get_logger("agent")
task_logger = get_logger("task")











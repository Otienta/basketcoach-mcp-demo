# basketcoach-mcp/utils/logger.py
#!/usr/bin/env python3
"""
Système de logging centralisé pour BasketCoach MCP
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional

from .config import get_config

def setup_logging():
    """Configure le système de logging"""
    config = get_config()
    
    # Configuration de base
    log_level = getattr(logging, config.get('logging.level', 'INFO'))
    log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = config.get('logging.file', 'logs/basketcoach.log')
    
    # Création du répertoire de logs
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configuration root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            # Handler fichier avec rotation
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            # Handler console
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Réduction du verbosity pour certaines librairies
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger configuré
    """
    logger = logging.getLogger(name)
    
    # Si le logging n'est pas configuré, le configurer
    if not logger.handlers:
        setup_logging()
    
    return logger

class ColorFormatter(logging.Formatter):
    """Formateur de logs avec couleurs"""
    
    COLORS = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green  
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            return f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
        return log_message

def get_colored_logger(name: str) -> logging.Logger:
    """
    Retourne un logger avec coloration pour la console
    """
    logger = get_logger(name)
    
    # Ajout du formateur couleur seulement pour la console
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setFormatter(ColorFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
    
    return logger
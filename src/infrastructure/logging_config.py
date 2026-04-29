# src/infrastructure/logging_config.py
import logging
from pathlib import Path

def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler("logs/gamelauncher.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
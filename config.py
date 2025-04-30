"""
Configuration settings for the Threads scraper.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True)

# Database settings
DB_PATH = DATA_DIR / "threads.db"

# Browser settings
BROWSER_SETTINGS = {
    "headless": False,  # Set to True for headless mode
    "user_data_dir": DATA_DIR / "user_data",
    "timeout": 30000,  # 30 seconds
    "viewport": {"width": 1280, "height": 720},
    "args": [
        '--disable-blink-features=AutomationControlled',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--window-size=1280,720'
    ]
}

# Scraping settings
SCRAPING_SETTINGS = {
    "username": "antoniwan777",  # Default username to scrape
    "max_retries": 3,  # Maximum number of retry attempts
    "retry_delay": 5,  # Delay between retries in seconds
    "scroll_attempts": 3,  # Number of times to scroll for more content
    "scroll_delay": 2,  # Delay between scrolls in seconds
    "wait_timeout": 10,  # Timeout for waiting for elements in seconds
}

# Export settings
EXPORT_SETTINGS = {
    "csv_encoding": "utf-8-sig",  # Encoding for CSV files
    "date_format": "%Y%m%d_%H%M%S",  # Format for timestamps in filenames
    "include_media": True,  # Whether to include media URLs in exports
    "include_hashtags": True,  # Whether to include hashtags in exports
    "include_mentions": True,  # Whether to include mentions in exports
}

# Logging settings
LOGGING_SETTINGS = {
    "level": "INFO",  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "log_file": LOG_DIR / "threads_scraper.log",
}

def get_settings() -> Dict[str, Any]:
    """Get all settings as a dictionary."""
    return {
        "base_dir": BASE_DIR,
        "data_dir": DATA_DIR,
        "output_dir": OUTPUT_DIR,
        "log_dir": LOG_DIR,
        "db_path": DB_PATH,
        "browser_settings": BROWSER_SETTINGS,
        "scraping_settings": SCRAPING_SETTINGS,
        "export_settings": EXPORT_SETTINGS,
        "logging_settings": LOGGING_SETTINGS,
    } 
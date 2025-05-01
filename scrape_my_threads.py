import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from threads_playwright import ThreadsScraper
from config import get_settings

# Get settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings["logging_settings"]["level"]),
    format=settings["logging_settings"]["format"],
    handlers=[
        logging.FileHandler(settings["logging_settings"]["log_file"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def scrape_with_retry(
    username: str = settings["scraping_settings"]["username"],
    max_retries: int = settings["scraping_settings"]["max_retries"],
    retry_delay: int = settings["scraping_settings"]["retry_delay"]
) -> Optional[dict]:
    """
    Scrape Threads data with retry mechanism.
    
    Args:
        username: Threads username to scrape
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Scraped feed data or None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            
            # Initialize scraper with settings
            logger.info("Initializing Threads scraper...")
            async with ThreadsScraper(
                headless=settings["browser_settings"]["headless"],
                db_path=str(settings["db_path"])
            ) as scraper:
                # Get user feed
                feed = await scraper.get_user_feed(username)
                return feed
                
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Failed to scrape feed after all retries")
                return None

async def main():
    """Main function to scrape Threads data."""
    try:
        # Get user feed with retries
        username = settings["scraping_settings"]["username"]
        feed_data = await scrape_with_retry(username)
        
        if not feed_data:
            logger.error("Failed to scrape feed after all retries")
            return
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime(settings["export_settings"]["date_format"])
        
        # Export to CSV
        csv_path = settings["output_dir"] / f"threads_feed_{timestamp}.csv"
        logger.info(f"Exporting feed to CSV: {csv_path}")
        scraper.db.export_to_csv(username, str(csv_path))
        
        # Export to Markdown
        md_path = settings["output_dir"] / f"threads_feed_{timestamp}.md"
        logger.info(f"Exporting feed to Markdown: {md_path}")
        scraper.db.export_to_markdown(username, str(md_path))
        
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
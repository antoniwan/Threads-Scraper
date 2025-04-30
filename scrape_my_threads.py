import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from threads_playwright import ThreadsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('threads_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to scrape Threads data."""
    scraper = None
    try:
        # Initialize scraper
        logger.info("Initializing Threads scraper...")
        scraper = ThreadsScraper()
        
        # Check login status
        logger.info("Checking login status...")
        is_logged_in = await scraper.ensure_logged_in()
        if not is_logged_in:
            logger.error("Login failed. Please try again.")
            return
        
        # Get user feed
        username = "antoniwan777"  # Your Threads username
        logger.info(f"Fetching feed for user: {username}")
        feed_data = await scraper.get_user_feed(username)
        
        if not feed_data or not feed_data.get('data', {}).get('feedData', {}).get('posts'):
            logger.warning("No feed data found")
            return
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export to CSV
        csv_path = output_dir / f"threads_feed_{timestamp}.csv"
        logger.info(f"Exporting feed to CSV: {csv_path}")
        scraper.db.export_to_csv(username, str(csv_path))
        
        # Export to Markdown
        md_path = output_dir / f"threads_feed_{timestamp}.md"
        logger.info(f"Exporting feed to Markdown: {md_path}")
        scraper.db.export_to_markdown(username, str(md_path))
        
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise
        
    finally:
        # Cleanup
        if scraper:
            try:
                await scraper.close()
                logger.info("Scraper closed successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
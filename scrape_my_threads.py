import asyncio
import logging
from threads_playwright import ThreadsScraper

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Example usage of the ThreadsScraper."""
    try:
        # Initialize the scraper with visible browser
        logger.info("Initializing Threads scraper")
        async with ThreadsScraper(headless=False) as scraper:
            # Check login status and wait for manual login if needed
            is_logged_in = await scraper.ensure_logged_in()
            if not is_logged_in:
                logger.info("Please log in to Threads in the browser window")
                input("Press Enter after you've logged in...")
                
                # Verify login again
                is_logged_in = await scraper.ensure_logged_in()
                if not is_logged_in:
                    logger.error("Still not logged in. Please try again.")
                    return
            
            # Get profile data for a user
            username = "zuck"  # Example username
            logger.info(f"Fetching profile for @{username}")
            profile = await scraper.get_user_profile(username)
            print(f"Profile data: {profile}")
            
            # Get threads for the same user
            logger.info(f"Fetching threads for @{username}")
            threads = await scraper.get_user_threads(username)
            print(f"Threads data: {threads}")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == '__main__':
    asyncio.run(main())
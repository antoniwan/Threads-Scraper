"""
Threads scraper using Playwright for Python.
"""
import asyncio
import logging
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, Page, TimeoutError
from database import ThreadsDatabase
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ThreadsScraper:
    """A scraper for Threads using Playwright."""
    
    def __init__(self, headless: bool = True, db_path: str = "threads.db"):
        """
        Initialize the scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            db_path (str): Path to SQLite database file
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.db = ThreadsDatabase(db_path)
        self.storage_state_path = "storage_state.json"
        
    async def __aenter__(self):
        """Context manager entry."""
        logger.info("Starting Playwright browser")
        playwright = await async_playwright().start()
        
        # Create a new context with persistent storage
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir="./user_data",
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.browser = context.browser
        self.page = context.pages[0]
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            await self.browser.close()
        self.db.close()

    async def ensure_logged_in(self) -> bool:
        """
        Ensure we are logged in to Threads.
        Returns True if logged in successfully.
        """
        logger.info("Checking login status...")
        
        # Go to Threads homepage first
        await self.page.goto('https://www.threads.net', wait_until='networkidle')
        
        # Check if we're redirected to login
        current_url = self.page.url
        if 'instagram.com' in current_url or 'login' in current_url:
            logger.info("Not logged in. Please log in manually.")
            return False
            
        logger.info("Successfully logged in")
        return True
            
    async def get_user_profile(self, username: str) -> Dict:
        """
        Get a user's profile information.
        
        Args:
            username (str): Threads username
            
        Returns:
            Dict: User profile data
        """
        logger.info(f"Getting profile for user: {username}")
        try:
            # First ensure we're logged in
            is_logged_in = await self.ensure_logged_in()
            if not is_logged_in:
                raise Exception("Please log in first")
                
            await self.page.goto(f'https://www.threads.net/@{username}', wait_until='networkidle')
            logger.info("Page loaded, waiting for profile data")
            
            # Wait for main content
            await self.page.wait_for_selector('main', timeout=5000)
            logger.info("Main content loaded")
            
            # Extract profile data from the page
            profile_data = await self.page.evaluate("""() => {
                const data = {};
                const bio = document.querySelector('h1')?.nextElementSibling?.textContent;
                const followers = document.querySelector('a[href*="/followers"]')?.textContent;
                const following = document.querySelector('a[href*="/following"]')?.textContent;
                
                data['bio'] = bio;
                data['followers'] = followers;
                data['following'] = following;
                return data;
            }""")
            
            # Save to database
            self.db.save_user_profile(username, profile_data)
            
            logger.info(f"Profile data extracted and saved: {profile_data}")
            return {
                "data": {
                    "userData": profile_data
                },
                "extensions": {
                    "is_final": True
                }
            }
        except TimeoutError:
            logger.error("Timeout waiting for profile data")
            raise
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            raise
        
    async def get_user_threads(self, username: str) -> Dict:
        """
        Get a user's threads.
        
        Args:
            username (str): Threads username
            
        Returns:
            Dict: List of user's threads
        """
        logger.info(f"Getting threads for user: {username}")
        try:
            # First ensure we're logged in
            is_logged_in = await self.ensure_logged_in()
            if not is_logged_in:
                raise Exception("Please log in first")
                
            await self.page.goto(f'https://www.threads.net/@{username}', wait_until='networkidle')
            logger.info("Page loaded, waiting for threads")
            
            # Wait for threads
            await self.page.wait_for_selector('article', timeout=5000)
            logger.info("Threads loaded")
            
            # Scroll to load more threads
            await self.page.evaluate("""() => {
                window.scrollTo(0, document.body.scrollHeight);
            }""")
            await asyncio.sleep(2)  # Wait for scroll to complete
            
            # Extract thread data
            threads = await self.page.evaluate("""() => {
                const threads = [];
                document.querySelectorAll('article').forEach(article => {
                    const text = article.querySelector('div[dir="auto"]')?.textContent;
                    const likes = article.querySelector('span[class*="like"]')?.textContent;
                    const replies = article.querySelector('span[class*="reply"]')?.textContent;
                    const time = article.querySelector('time')?.dateTime;
                    
                    threads.push({
                        text,
                        likes,
                        replies,
                        time
                    });
                });
                return threads;
            }""")
            
            # Save to database
            self.db.save_user_threads(username, threads)
            
            logger.info(f"Found and saved {len(threads)} threads")
            
            # Log the most recent post
            if threads:
                last_post = threads[0]  # First post is the most recent
                logger.info(f"Most recent post by @{username}:")
                logger.info(f"Text: {last_post['text']}")
                logger.info(f"Likes: {last_post['likes']}")
                logger.info(f"Replies: {last_post['replies']}")
                logger.info(f"Time: {last_post['time']}")
            else:
                logger.info(f"No posts found for @{username}")
            
            return {
                "data": {
                    "mediaData": {
                        "threads": threads
                    }
                },
                "extensions": {
                    "is_final": True
                }
            }
        except TimeoutError:
            logger.error("Timeout waiting for threads")
            raise
        except Exception as e:
            logger.error(f"Error getting threads: {str(e)}")
            raise

async def main():
    """Example usage of the ThreadsScraper."""
    async with ThreadsScraper(headless=False) as scraper:
        # Login (optional, only needed for private profiles)
        # await scraper.login('your_username', 'your_password')
        
        # Get profile data
        profile = await scraper.get_user_profile('username')
        
        # Get threads
        threads = await scraper.get_user_threads('username')

if __name__ == '__main__':
    asyncio.run(main()) 
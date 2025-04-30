"""
Threads scraper using Playwright for Python.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, Page

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ThreadsScraper:
    """A scraper for Threads using Playwright."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        """Context manager entry."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            await self.browser.close()
            
    async def login(self, username: str, password: str) -> None:
        """
        Log in to Threads.
        
        Args:
            username (str): Instagram/Threads username
            password (str): Instagram/Threads password
        """
        logger.info("Logging in to Threads")
        await self.page.goto('https://www.threads.net/login')
        
        # Wait for and fill in login form
        await self.page.wait_for_selector('input[name="username"]')
        await self.page.fill('input[name="username"]', username)
        await self.page.fill('input[name="password"]', password)
        
        # Click login button
        await self.page.click('button[type="submit"]')
        
        # Wait for login to complete
        await self.page.wait_for_url('https://www.threads.net/**')
        logger.info("Successfully logged in")
        
    async def get_user_profile(self, username: str) -> Dict:
        """
        Get a user's profile information.
        
        Args:
            username (str): Threads username
            
        Returns:
            Dict: User profile data
        """
        logger.info(f"Getting profile for user: {username}")
        await self.page.goto(f'https://www.threads.net/@{username}')
        
        # Wait for profile data to load
        await self.page.wait_for_selector('main')
        
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
        
        return {
            "data": {
                "userData": profile_data
            },
            "extensions": {
                "is_final": True
            }
        }
        
    async def get_user_threads(self, username: str) -> Dict:
        """
        Get a user's threads.
        
        Args:
            username (str): Threads username
            
        Returns:
            Dict: List of user's threads
        """
        logger.info(f"Getting threads for user: {username}")
        await self.page.goto(f'https://www.threads.net/@{username}')
        
        # Wait for threads to load
        await self.page.wait_for_selector('article')
        
        # Scroll to load more threads
        await self.page.evaluate("""() => {
            window.scrollTo(0, document.body.scrollHeight);
        }""")
        
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
        
    def save_to_json(self, data: Dict, filename: str) -> None:
        """
        Save data to a JSON file.
        
        Args:
            data (Dict): Data to save
            filename (str): Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def save_to_csv(self, data: Dict, filename: str) -> None:
        """
        Save data to a CSV file.
        
        Args:
            data (Dict): Data to save
            filename (str): Output filename
        """
        import pandas as pd
        
        # Convert the data to match the existing CSV format
        csv_data = {
            'data': [str(data['data'])],
            'extensions': [data['extensions']['is_final']]
        }
        
        df = pd.DataFrame(csv_data)
        df.to_csv(filename, index=False)

async def main():
    """Example usage of the ThreadsScraper."""
    async with ThreadsScraper(headless=True) as scraper:
        # Login (optional, only needed for private profiles)
        # await scraper.login('your_username', 'your_password')
        
        # Get profile data
        profile = await scraper.get_user_profile('username')
        scraper.save_to_json(profile, 'my_profile.json')
        
        # Get threads
        threads = await scraper.get_user_threads('username')
        scraper.save_to_json(threads, 'my_threads.json')
        scraper.save_to_csv(threads, 'my_threads.csv')

if __name__ == '__main__':
    asyncio.run(main()) 
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
        try:
            self.playwright = await async_playwright().start()
            
            # Create a new context with persistent storage
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir="./user_data",
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            self.browser = self.context.browser
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            
            return self
        except Exception as e:
            logger.error(f"Error during browser initialization: {str(e)}")
            await self.cleanup()
            raise
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup()
        
    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if hasattr(self, 'page') and self.page and not self.page.is_closed():
                await self.page.close()
            if hasattr(self, 'context') and self.context:
                await self.context.close()
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            if hasattr(self, 'db'):
                self.db.close()
                
    async def ensure_logged_in(self) -> bool:
        """
        Ensure we are logged in to Threads.
        Returns True if logged in successfully.
        """
        logger.info("Checking login status...")
        
        try:
            # Go to Threads homepage with a more lenient wait condition
            await self.page.goto('https://www.threads.net', wait_until='domcontentloaded')
            
            # Check if we're redirected to login
            current_url = self.page.url
            if 'instagram.com' in current_url or 'login' in current_url:
                logger.info("Not logged in. Please log in manually.")
                return False
                
            logger.info("Successfully logged in")
            return True
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False
            
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
                
            # Navigate to profile with a more lenient wait condition
            await self.page.goto(f'https://www.threads.net/@{username}', wait_until='domcontentloaded')
            logger.info("Page loaded, waiting for profile data")
            
            # Wait for either main content or a reasonable timeout
            try:
                await self.page.wait_for_selector('main', timeout=10000)
                logger.info("Main content loaded")
            except TimeoutError:
                logger.warning("Timeout waiting for main content, proceeding anyway")
            
            # Extract profile data from the page
            profile_data = await self.page.evaluate("""() => {
                const data = {};
                
                // Try different selectors for bio
                const bio = document.querySelector('h1')?.nextElementSibling?.textContent || 
                           document.querySelector('div[dir="auto"]')?.textContent;
                
                // Try different selectors for followers/following
                const followers = document.querySelector('a[href*="/followers"]')?.textContent ||
                                document.querySelector('span[class*="followers"]')?.textContent ||
                                document.querySelector('span[class*="follower"]')?.textContent;
                
                const following = document.querySelector('a[href*="/following"]')?.textContent ||
                                document.querySelector('span[class*="following"]')?.textContent ||
                                document.querySelector('span[class*="follow"]')?.textContent;
                
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
                
            # Navigate to profile with a more lenient wait condition
            await self.page.goto(f'https://www.threads.net/@{username}', wait_until='domcontentloaded')
            logger.info("Page loaded, waiting for threads")
            
            # Wait for threads with a longer timeout
            try:
                await self.page.wait_for_selector('article', timeout=10000)
                logger.info("Threads loaded")
            except TimeoutError:
                logger.warning("Timeout waiting for threads, proceeding anyway")
            
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
                    const reposts = article.querySelector('span[class*="repost"]')?.textContent;
                    const time = article.querySelector('time')?.dateTime;
                    const url = article.querySelector('a[href*="/post/"]')?.href;
                    
                    // Extract media URLs
                    const mediaUrls = [];
                    article.querySelectorAll('img').forEach(img => {
                        if (img.src && !img.src.includes('data:')) {
                            mediaUrls.push(img.src);
                        }
                    });
                    
                    // Extract hashtags and mentions
                    const hashtags = [];
                    const mentions = [];
                    if (text) {
                        text.split(' ').forEach(word => {
                            if (word.startsWith('#')) {
                                hashtags.push(word.slice(1));
                            } else if (word.startsWith('@')) {
                                mentions.push(word.slice(1));
                            }
                        });
                    }
                    
                    // Extract thread ID from URL
                    const threadId = url ? url.split('/').pop() : '';
                    
                    threads.push({
                        id: threadId,
                        text,
                        likes,
                        replies,
                        reposts,
                        time,
                        url,
                        media_urls: mediaUrls,
                        hashtags,
                        mentions
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
        except Exception as e:
            logger.error(f"Error getting threads: {str(e)}")
            raise

    async def get_user_feed(self, username: str, max_retries: int = 3) -> Dict:
        """
        Get a user's feed (their posts and posts they've interacted with).
        
        Args:
            username (str): Threads username
            max_retries (int): Maximum number of retries for failed operations
            
        Returns:
            Dict: List of feed posts
        """
        logger.info(f"Getting feed for user: {username}")
        
        for attempt in range(max_retries):
            try:
                # First ensure we're logged in
                is_logged_in = await self.ensure_logged_in()
                if not is_logged_in:
                    raise Exception("Please log in first")
                    
                # Navigate to user's feed with retry
                try:
                    await self.page.goto(f'https://www.threads.net/@{username}', wait_until='domcontentloaded')
                    logger.info("Page loaded, checking for feed content")
                except Exception as e:
                    logger.warning(f"Navigation failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
                        continue
                    raise
                
                # Check if we are on the correct URL
                current_url = self.page.url
                expected_url = f"https://www.threads.net/@{username}"
                if not current_url.startswith(expected_url):
                    logger.warning(f"Unexpected URL after navigation: {current_url}")

                # Immediately check for posts
                articles_present = await self.page.evaluate("""() => !!document.querySelector('article')""")
                if not articles_present:
                    logger.info("No posts found immediately, waiting for feed content")
                    try:
                        await self.page.wait_for_selector('article', timeout=20000)
                        logger.info("Feed content loaded after wait")
                    except TimeoutError:
                        logger.warning("Timeout waiting for feed content, proceeding anyway")
                else:
                    logger.info("Feed content found immediately, proceeding to scrape")
                
                # Scroll multiple times to load more content
                for scroll_attempt in range(5):  # Increased scroll attempts
                    logger.info(f"Scroll attempt {scroll_attempt + 1}/5")
                    await self.page.evaluate("""() => {
                        window.scrollTo(0, document.body.scrollHeight);
                    }""")
                    await asyncio.sleep(3)  # Increased wait time between scrolls
                    
                    # Check if we have content after each scroll
                    content = await self.page.evaluate("""() => {
                        const articles = document.querySelectorAll('article');
                        return articles.length > 0;
                    }""")
                    
                    if content:
                        logger.info("Found content after scroll")
                        break
                
                # Extract feed data with more robust selectors
                feed = await self.page.evaluate("""() => {
                    const feed = [];
                    document.querySelectorAll('article').forEach(article => {
                        try {
                            // Get text content with fallbacks
                            const textElement = article.querySelector('div[dir="auto"]') || 
                                              article.querySelector('div[class*="text"]') ||
                                              article.querySelector('div[class*="content"]');
                            const text = textElement?.textContent?.trim() || '';
                            
                            // Get author with fallbacks
                            const authorElement = article.querySelector('a[href*="/@"]') ||
                                                article.querySelector('span[class*="username"]') ||
                                                article.querySelector('span[class*="author"]');
                            const author = authorElement?.textContent?.trim() || '';
                            
                            // Get engagement metrics with fallbacks
                            const likes = article.querySelector('span[class*="like"]')?.textContent?.trim() || '0';
                            const replies = article.querySelector('span[class*="reply"]')?.textContent?.trim() || '0';
                            const reposts = article.querySelector('span[class*="repost"]')?.textContent?.trim() || '0';
                            
                            // Get time with fallbacks
                            const timeElement = article.querySelector('time') ||
                                              article.querySelector('span[class*="time"]') ||
                                              article.querySelector('span[class*="date"]');
                            const time = timeElement?.dateTime || timeElement?.textContent?.trim() || '';
                            
                            // Get URL with fallbacks
                            const urlElement = article.querySelector('a[href*="/post/"]') ||
                                             article.querySelector('a[href*="/thread/"]');
                            const url = urlElement?.href || '';
                            
                            // Extract media URLs with better filtering
                            const mediaUrls = [];
                            article.querySelectorAll('img').forEach(img => {
                                if (img.src && 
                                    !img.src.includes('data:') && 
                                    !img.src.includes('avatar') && 
                                    !img.src.includes('profile')) {
                                    mediaUrls.push(img.src);
                                }
                            });
                            
                            // Extract hashtags and mentions with better parsing
                            const hashtags = [];
                            const mentions = [];
                            if (text) {
                                const words = text.split(/\\s+/);
                                words.forEach(word => {
                                    if (word.startsWith('#')) {
                                        hashtags.push(word.slice(1).replace(/[^\\w\\d]/g, ''));
                                    } else if (word.startsWith('@')) {
                                        mentions.push(word.slice(1).replace(/[^\\w\\d]/g, ''));
                                    }
                                });
                            }
                            
                            // Extract thread ID from URL
                            const threadId = url ? url.split('/').pop().split('?')[0] : '';
                            
                            if (text || mediaUrls.length > 0) {  // Only add if there's content
                                feed.push({
                                    id: threadId,
                                    author,
                                    text,
                                    likes,
                                    replies,
                                    reposts,
                                    time,
                                    url,
                                    media_urls: mediaUrls,
                                    hashtags,
                                    mentions
                                });
                            }
                        } catch (e) {
                            console.error('Error processing article:', e);
                        }
                    });
                    return feed;
                }""")
                
                if not feed:
                    logger.warning(f"No posts found in feed (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                
                # Save to database
                self.db.save_user_threads(username, feed)
                
                logger.info(f"Found and saved {len(feed)} feed items")
                
                # Log the most recent post
                if feed:
                    last_post = feed[0]  # First post is the most recent
                    logger.info(f"Most recent post in feed:")
                    logger.info(f"Author: @{last_post['author']}")
                    logger.info(f"Text: {last_post['text']}")
                    logger.info(f"Likes: {last_post['likes']}")
                    logger.info(f"Replies: {last_post['replies']}")
                    logger.info(f"Time: {last_post['time']}")
                else:
                    logger.info(f"No posts found in feed")
                
                return {
                    "data": {
                        "feedData": {
                            "posts": feed
                        }
                    },
                    "extensions": {
                        "is_final": True
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting feed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                raise

async def main():
    """Example usage of the ThreadsScraper."""
    async with ThreadsScraper(headless=False) as scraper:
        # Login (optional, only needed for private profiles)
        # await scraper.login('your_username', 'your_password')
        
        # Get feed for antoniwan777
        username = "antoniwan777"
        feed = await scraper.get_user_feed(username)
        
        # Export to CSV
        scraper.db.export_to_csv(username, f"{username}_feed.csv")
        
        # Export to Markdown
        scraper.db.export_to_markdown(username, f"{username}_feed.md")

if __name__ == '__main__':
    asyncio.run(main()) 
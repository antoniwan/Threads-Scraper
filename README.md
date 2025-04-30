## Features 🚀

A Software that scrapes the following sections from threads:

- Fetch user's profile information including bio, followers, and following counts
- Retrieve user's threads with content, likes, replies, and timestamps
- Save the fetched data into CSV and JSON files

## :file_folder: File Structure

- `threads_playwright.py`: Main scraper implementation using Playwright
- `requirements.txt`: Project dependencies

## :rocket: How to Use

### Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:

```bash
playwright install
```

### Usage

Example:

```python
from threads_playwright import ThreadsScraper
import asyncio

async def main():
    async with ThreadsScraper(headless=True) as scraper:
        # Optional: Login for private profiles
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
```

## Output

1. **Profile Data**

   - Input: `username`
   - Output: JSON file with profile information
   - Example:
     ```json
     {
       "bio": "Software Developer",
       "followers": "1.2K",
       "following": "500"
     }
     ```

2. **Threads Data**

   - Input: `username`
   - Output: JSON and CSV files with thread information
   - Example:
     ```json
     [
       {
         "text": "Hello, world!",
         "likes": "42",
         "replies": "5",
         "time": "2024-01-01T12:00:00Z"
       }
     ]
     ```

## Advantages of the New Implementation

- More reliable scraping by simulating real user interactions
- Better handling of dynamic content
- No dependency on internal API endpoints
- Automatic handling of rate limiting and anti-bot measures
- Support for both public and private profiles (with login)

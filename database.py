import sqlite3
from typing import Dict, List
import json
from pathlib import Path
import csv
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ThreadsDatabase:
    def __init__(self, db_path: str = "threads.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row  # Enable row factory for better column access
            self.update_schema()
            self.create_tables()
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
        
    def update_schema(self):
        """Update the database schema if needed."""
        cursor = self.conn.cursor()
        
        try:
            # Check if threads table exists
            cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='threads'
            """)
            
            if cursor.fetchone():
                # Table exists, check for new columns
                cursor.execute("PRAGMA table_info(threads)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Add missing columns with proper types and constraints
                if 'thread_id' not in columns:
                    cursor.execute("ALTER TABLE threads ADD COLUMN thread_id TEXT UNIQUE")
                if 'reposts' not in columns:
                    cursor.execute("ALTER TABLE threads ADD COLUMN reposts TEXT DEFAULT '0'")
                if 'url' not in columns:
                    cursor.execute("ALTER TABLE threads ADD COLUMN url TEXT")
                if 'media_urls' not in columns:
                    cursor.execute("ALTER TABLE threads ADD COLUMN media_urls TEXT DEFAULT '[]'")
                if 'hashtags' not in columns:
                    cursor.execute("ALTER TABLE threads ADD COLUMN hashtags TEXT DEFAULT '[]'")
                if 'mentions' not in columns:
                    cursor.execute("ALTER TABLE threads ADD COLUMN mentions TEXT DEFAULT '[]'")
                
                self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Schema update error: {str(e)}")
            self.conn.rollback()
            raise
        
    def create_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        try:
            # Create users table with proper constraints
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                bio TEXT,
                followers TEXT,
                following TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create threads table with more comprehensive fields and constraints
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                thread_id TEXT UNIQUE,
                text TEXT,
                likes TEXT DEFAULT '0',
                replies TEXT DEFAULT '0',
                reposts TEXT DEFAULT '0',
                time TEXT,
                url TEXT,
                media_urls TEXT DEFAULT '[]',
                hashtags TEXT DEFAULT '[]',
                mentions TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_threads_username ON threads(username)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_threads_thread_id ON threads(thread_id)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_threads_created_at ON threads(created_at)
            """)
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Table creation error: {str(e)}")
            self.conn.rollback()
            raise
        
    def save_user_profile(self, username: str, profile_data: Dict):
        """Save or update a user's profile data."""
        if not username or not isinstance(username, str):
            raise ValueError("Invalid username")
            
        cursor = self.conn.cursor()
        
        try:
            # Convert profile data to strings with validation
            bio = str(profile_data.get('bio', '')).strip()
            followers = str(profile_data.get('followers', '')).strip()
            following = str(profile_data.get('following', '')).strip()
            
            cursor.execute("""
            INSERT OR REPLACE INTO users (username, bio, followers, following, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (username, bio, followers, following))
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving user profile: {str(e)}")
            self.conn.rollback()
            raise
        
    def save_user_threads(self, username: str, threads: List[Dict]):
        """Save a user's threads."""
        if not username or not isinstance(username, str):
            raise ValueError("Invalid username")
        if not isinstance(threads, list):
            raise ValueError("Threads must be a list")
            
        cursor = self.conn.cursor()
        
        try:
            for thread in threads:
                # Extract and validate data
                thread_id = str(thread.get('id', '')).strip()
                text = str(thread.get('text', '')).strip()
                likes = str(thread.get('likes', '0')).strip()
                replies = str(thread.get('replies', '0')).strip()
                reposts = str(thread.get('reposts', '0')).strip()
                time = str(thread.get('time', '')).strip()
                url = str(thread.get('url', '')).strip()
                
                # Convert lists to JSON strings
                media_urls = json.dumps(thread.get('media_urls', []))
                hashtags = json.dumps(thread.get('hashtags', []))
                mentions = json.dumps(thread.get('mentions', []))
                
                cursor.execute("""
                INSERT OR REPLACE INTO threads (
                    username, thread_id, text, likes, replies, reposts, 
                    time, url, media_urls, hashtags, mentions, last_updated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    username,
                    thread_id,
                    text,
                    likes,
                    replies,
                    reposts,
                    time,
                    url,
                    media_urls,
                    hashtags,
                    mentions
                ))
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving user threads: {str(e)}")
            self.conn.rollback()
            raise
        
    def get_user_profile(self, username: str) -> Dict:
        """Get a user's profile data."""
        if not username or not isinstance(username, str):
            raise ValueError("Invalid username")
            
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
            SELECT bio, followers, following, last_updated 
            FROM users 
            WHERE username = ?
            """, (username,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'bio': row['bio'],
                    'followers': row['followers'],
                    'following': row['following'],
                    'last_updated': row['last_updated']
                }
            return {}
        except sqlite3.Error as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise
        
    def get_user_threads(self, username: str) -> List[Dict]:
        """Get a user's threads."""
        if not username or not isinstance(username, str):
            raise ValueError("Invalid username")
            
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
            SELECT thread_id, text, likes, replies, reposts, time, url, 
                   media_urls, hashtags, mentions, created_at, last_updated
            FROM threads 
            WHERE username = ? 
            ORDER BY created_at DESC
            """, (username,))
            
            threads = []
            for row in cursor.fetchall():
                threads.append({
                    'id': row['thread_id'],
                    'text': row['text'],
                    'likes': row['likes'],
                    'replies': row['replies'],
                    'reposts': row['reposts'],
                    'time': row['time'],
                    'url': row['url'],
                    'media_urls': json.loads(row['media_urls']) if row['media_urls'] else [],
                    'hashtags': json.loads(row['hashtags']) if row['hashtags'] else [],
                    'mentions': json.loads(row['mentions']) if row['mentions'] else [],
                    'created_at': row['created_at'],
                    'last_updated': row['last_updated']
                })
                
            return threads
        except sqlite3.Error as e:
            logger.error(f"Error getting user threads: {str(e)}")
            raise
        
    def export_to_csv(self, username: str, output_path: str):
        """Export user's threads to CSV."""
        if not username or not isinstance(username, str):
            raise ValueError("Invalid username")
        if not output_path or not isinstance(output_path, str):
            raise ValueError("Invalid output path")
            
        threads = self.get_user_threads(username)
        if not threads:
            logger.warning(f"No threads found for user {username}")
            return
            
        try:
            # Convert to DataFrame with proper data types
            df = pd.DataFrame(threads)
            
            # Convert JSON strings to lists for better readability
            df['media_urls'] = df['media_urls'].apply(lambda x: ', '.join(x) if x else '')
            df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x) if x else '')
            df['mentions'] = df['mentions'].apply(lambda x: ', '.join(x) if x else '')
            
            # Save to CSV with proper encoding
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"Exported {len(threads)} threads to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
        
    def export_to_markdown(self, username: str, output_path: str):
        """Export user's threads to Markdown."""
        if not username or not isinstance(username, str):
            raise ValueError("Invalid username")
        if not output_path or not isinstance(output_path, str):
            raise ValueError("Invalid output path")
            
        threads = self.get_user_threads(username)
        if not threads:
            logger.warning(f"No threads found for user {username}")
            return
            
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Threads by @{username}\n\n")
                
                for thread in threads:
                    f.write(f"## Thread from {thread['time']}\n\n")
                    
                    # Escape special characters in text
                    text = thread['text'].replace('\\', '\\\\').replace('`', '\\`')
                    f.write(f"{text}\n\n")
                    
                    if thread['media_urls']:
                        f.write("### Media\n")
                        for url in thread['media_urls']:
                            f.write(f"![Media]({url})\n\n")
                    
                    if thread['hashtags']:
                        f.write("### Hashtags\n")
                        f.write(" ".join(f"#{tag}" for tag in thread['hashtags']) + "\n\n")
                    
                    if thread['mentions']:
                        f.write("### Mentions\n")
                        f.write(" ".join(f"@{mention}" for mention in thread['mentions']) + "\n\n")
                    
                    f.write(f"**Stats:** {thread['likes']} likes, {thread['replies']} replies, {thread['reposts']} reposts\n\n")
                    f.write(f"[Original Thread]({thread['url']})\n\n")
                    f.write("---\n\n")
                    
            logger.info(f"Exported {len(threads)} threads to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {str(e)}")
            raise
        
    def close(self):
        """Close the database connection."""
        try:
            if self.conn:
                self.conn.close()
        except Exception as e:
            logger.error(f"Error closing database: {str(e)}")
            raise 
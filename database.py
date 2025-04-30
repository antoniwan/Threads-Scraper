import sqlite3
from typing import Dict, List
import json
from pathlib import Path

class ThreadsDatabase:
    def __init__(self, db_path: str = "threads.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        
    def create_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            bio TEXT,
            followers TEXT,
            following TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create threads table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            text TEXT,
            likes TEXT,
            replies TEXT,
            time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
        """)
        
        self.conn.commit()
        
    def save_user_profile(self, username: str, profile_data: Dict):
        """Save or update a user's profile data."""
        cursor = self.conn.cursor()
        
        # Convert profile data to strings
        bio = profile_data.get('bio', '')
        followers = profile_data.get('followers', '')
        following = profile_data.get('following', '')
        
        cursor.execute("""
        INSERT OR REPLACE INTO users (username, bio, followers, following)
        VALUES (?, ?, ?, ?)
        """, (username, bio, followers, following))
        
        self.conn.commit()
        
    def save_user_threads(self, username: str, threads: List[Dict]):
        """Save a user's threads."""
        cursor = self.conn.cursor()
        
        for thread in threads:
            cursor.execute("""
            INSERT INTO threads (username, text, likes, replies, time)
            VALUES (?, ?, ?, ?, ?)
            """, (
                username,
                thread.get('text', ''),
                thread.get('likes', ''),
                thread.get('replies', ''),
                thread.get('time', '')
            ))
        
        self.conn.commit()
        
    def get_user_profile(self, username: str) -> Dict:
        """Get a user's profile data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT bio, followers, following FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row:
            return {
                'bio': row[0],
                'followers': row[1],
                'following': row[2]
            }
        return {}
        
    def get_user_threads(self, username: str) -> List[Dict]:
        """Get a user's threads."""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT text, likes, replies, time 
        FROM threads 
        WHERE username = ? 
        ORDER BY created_at DESC
        """, (username,))
        
        threads = []
        for row in cursor.fetchall():
            threads.append({
                'text': row[0],
                'likes': row[1],
                'replies': row[2],
                'time': row[3]
            })
            
        return threads
        
    def close(self):
        """Close the database connection."""
        self.conn.close() 
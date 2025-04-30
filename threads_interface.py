"""
Provide a public interface for the Threads.
"""
import json
import re
import requests
import logging
from base_interface import BaseThreadsInterface

import csv
import os
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ThreadsInterface(BaseThreadsInterface):
    """
    A public interface for interacting with Threads.

    Each unique endpoint requires a unique document ID, predefined by the developers.
    """
    THREADS_API_URL = 'https://www.threads.net/api/graphql'

    def __init__(self):
        """
        Initialize the object.
        """
        super().__init__()

        self.api_token = self._generate_api_token()
        self.default_headers = {
            'Authority': 'www.threads.net',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.threads.net',
            'Pragma': 'no-cache',
            'Sec-Fetch-Site': 'same-origin',
            'X-ASBD-ID': '129477',
            'X-FB-LSD': self.api_token,
            'X-IG-App-ID': '238260118697367',
        }

    def _make_request(self, headers, data, endpoint_name):
        """
        Make an API request with proper error handling.
        
        Args:
            headers (dict): Request headers
            data (dict): Request data
            endpoint_name (str): Name of the endpoint for logging
            
        Returns:
            dict: Response JSON data
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            ValueError: If the response is not valid JSON or contains errors
        """
        try:
            logger.info(f"Making request to {endpoint_name}")
            response = requests.post(
                url=self.THREADS_API_URL,
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if 'errors' in data:
                error_msg = data['errors'][0]['message'] if data['errors'] else 'Unknown error'
                logger.error(f"API returned error for {endpoint_name}: {error_msg}")
                raise ValueError(f"API Error: {error_msg}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint_name}: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response for {endpoint_name}: {str(e)}")
            raise ValueError(f"Invalid JSON response: {str(e)}")

    def retrieve_user(self, user_id: int) -> dict:
        """
        Retrieve a user.

        Args:
            user_id (int): The user's unique identifier.

        Returns:
            dict: User information
        """
        logger.info(f"Retrieving user data for user_id: {user_id}")
        headers = self.default_headers.copy()
        headers['X-FB-Friendly-Name'] = 'BarcelonaProfileRootQuery'

        data = {
            'lsd': self.api_token,
            'variables': json.dumps({'userID': user_id}),
            'doc_id': '23996318473300828',
        }

        response = self._make_request(headers, data, 'retrieve_user')
        logger.debug(f"User data response: {response}")
        return response

    def retrieve_user_threads(self, user_id: int) -> dict:
        """
        Retrieve a user's threads.

        Args:
            user_id (int): The user's unique identifier.

        Returns:
            dict: List of user's threads
        """
        logger.info(f"Retrieving threads for user_id: {user_id}")
        headers = self.default_headers.copy()
        headers['X-FB-Friendly-Name'] = 'BarcelonaProfileThreadsTabQuery'

        data = {
            'lsd': self.api_token,
            'variables': json.dumps({'userID': user_id}),
            'doc_id': '6232751443445612',
        }

        response = self._make_request(headers, data, 'retrieve_user_threads')
        logger.debug(f"User threads response: {response}")
        return response

    def retrieve_user_replies(self, user_id: int) -> dict:
        """
        Retrieve a user's replies.

        Args:
            user_id (int): The user's unique identifier.

        Returns:
            dict: List of user's replies
        """
        logger.info(f"Retrieving replies for user_id: {user_id}")
        headers = self.default_headers.copy()
        headers['X-FB-Friendly-Name'] = 'BarcelonaProfileRepliesTabQuery'

        data = {
            'lsd': self.api_token,
            'variables': json.dumps({'userID': user_id}),
            'doc_id': '6307072669391286',
        }

        response = self._make_request(headers, data, 'retrieve_user_replies')
        logger.debug(f"User replies response: {response}")
        return response

    def retrieve_thread(self, thread_id: int) -> dict:
        """
        Retrieve a thread.

        Args:
            thread_id (int): The thread's unique identifier.

        Returns:
            dict: Thread information
        """
        logger.info(f"Retrieving thread data for thread_id: {thread_id}")
        headers = self.default_headers.copy()
        headers['X-FB-Friendly-Name'] = 'BarcelonaPostPageQuery'

        data = {
            'lsd': self.api_token,
            'variables': json.dumps({'postID': thread_id}),
            'doc_id': '5587632691339264',
        }

        response = self._make_request(headers, data, 'retrieve_thread')
        logger.debug(f"Thread data response: {response}")
        return response

    def retrieve_thread_likers(self, thread_id: int) -> dict:
        """
        Retrieve the likers of a thread.

        Args:
            thread_id (int): The thread's unique identifier.

        Returns:
            dict: List of thread likers
        """
        logger.info(f"Retrieving likers for thread_id: {thread_id}")
        data = {
            'lsd': self.api_token,
            'variables': json.dumps({'mediaID': thread_id}),
            'doc_id': '9360915773983802',
        }

        response = self._make_request(self.default_headers, data, 'retrieve_thread_likers')
        logger.debug(f"Thread likers response: {response}")
        return response

    def _generate_api_token(self) -> str:
        """
        Generate a token for the Threads.

        Returns:
            str: The token for the Threads
        """
        try:
            logger.info("Generating API token")
            response = requests.get(
                url='https://www.instagram.com/instagram',
                headers=self.headers_for_html_fetching,
                timeout=30
            )
            response.raise_for_status()

            token_key_value = re.search(
                'LSD",\\[\\],{"token":"(.*?)"},\\d+\\]', response.text)
            if not token_key_value:
                raise ValueError("Could not find token in response")
                
            token_key_value = token_key_value.group()
            token_key_value = token_key_value.replace('LSD",[],{"token":"', '')
            token = token_key_value.split('"')[0]
            
            logger.info("Successfully generated API token")
            return token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate API token: {str(e)}")
            raise
        except (AttributeError, IndexError) as e:
            logger.error(f"Failed to parse token from response: {str(e)}")
            raise ValueError("Failed to parse token from response")

    def save_data_to_csv(self, data: dict, filename: str):
        """
        Save the provided data into a CSV file.

        Args:
            data (dict): The data to be saved
            filename (str): The filename of the CSV file
        """
        try:
            logger.info(f"Attempting to save data to {filename}")
            logger.debug(f"Data to be saved: {data}")
            
            if not data:
                logger.warning(f"No data provided to save to {filename}")
                return
                
            if not isinstance(data, dict):
                logger.error(f"Invalid data type provided. Expected dict, got {type(data)}")
                return
                
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            logger.info(f"DataFrame created with shape: {df.shape}")
            
            # Save to CSV
            df.to_csv(filename, index=False)
            logger.info(f"Successfully saved data to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save data to {filename}: {str(e)}")
            raise

    def save_data_to_json(self, data: dict, filename: str):
        """
        Save the provided data into a JSON file.

        Args:
            data (dict): The data to be saved
            filename (str): The filename of the JSON file
        """
        try:
            logger.info(f"Saving data to JSON file: {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved data to {filename}")
        except Exception as e:
            logger.error(f"Failed to save data to JSON: {str(e)}")
            raise

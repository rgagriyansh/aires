import requests
from typing import Literal, Optional, Dict, List
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

@dataclass
class HumanizerResponse:
    humanized_text: str
    word_count: int

class AIHumanizer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HUMANIZER_API_KEY")
        if not self.api_key:
            raise ValueError("HUMANIZER_API_KEY environment variable is required")
        self.base_url = "https://v1-humanizer.rephrasy.ai/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum seconds between requests

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_api_request(self, payload: Dict) -> Dict:
        """Make API request with retry logic"""
        self._wait_for_rate_limit()
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def humanize(
        self,
        text: str
    ) -> HumanizerResponse:
        """
        Humanize the given text using the Rephrasy API.

        Args:
            text (str): The text to humanize

        Returns:
            HumanizerResponse: Object containing the humanized text and word count

        Raises:
            ValueError: If the API request fails
        """
        payload = {
            "text": text,
            "model": "undetectable",
            "words": True
        }

        try:
            data = self._make_api_request(payload)
            
            # Extract the humanized text from the response
            humanized_text = data.get("result", data.get("output", data.get("content", "")))
            if not humanized_text:
                raise ValueError("Could not find humanized text in API response")
                
            return HumanizerResponse(
                humanized_text=humanized_text,
                word_count=len(humanized_text.split())
            )
            
        except requests.exceptions.RequestException as e:
            error_message = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get("error", error_message)
                except:
                    pass
            raise ValueError(error_message) 
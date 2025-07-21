import requests
import logging
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
import time
import asyncio
from urllib.parse import urljoin
import json

from config import TLDV_CONFIG
from models.meeting import Meeting, MeetingResponse, MeetingFilters, MeetingImportRequest
from models.transcript import Transcript, TranscriptSegment
from models.highlights import Highlights, Highlight, HighlightSource, Topic

logger = logging.getLogger(__name__)

class TLDVAPIError(Exception):
    """Custom exception for tl;dv API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"tl;dv API Error {self.status_code}: {self.message}"
        return f"tl;dv API Error: {self.message}"

class TLDVRateLimiter:
    """Rate limiter for tl;dv API requests"""
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times = []

    def wait_if_needed(self):
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 60]
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0]) + 1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
        self.request_times.append(now)

class TLDVService:
    """Enhanced service class for tl;dv API integration"""
    def __init__(self):
        self.base_url = TLDV_CONFIG.full_base_url
        self.api_key = TLDV_CONFIG.api_key
        self.timeout = TLDV_CONFIG.timeout
        self.max_retries = TLDV_CONFIG.max_retries
        self.rate_limiter = TLDVRateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'User-Agent': 'Complaion-TLDV-Integration/1.0'
        })
        logger.info(f"Initialized tl;dv service with base URL: {self.base_url}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        for attempt in range(self.max_retries + 1):
            try:
                self.rate_limiter.wait_if_needed()
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
                logger.debug(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, retrying...")
                    if attempt == self.max_retries:
                        self._raise_api_error(response)
                    time.sleep(2 ** attempt)
                    continue
                else:
                    self._raise_api_error(response)
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt == self.max_retries:
                    raise TLDVAPIError("Request timeout after all retries")
                time.sleep(2 ** attempt)
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}")
                if attempt == self.max_retries:
                    raise TLDVAPIError("Connection error after all retries")
                time.sleep(2 ** attempt)
            except TLDVAPIError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    raise TLDVAPIError(f"Unexpected error: {str(e)}")
                time.sleep(2 ** attempt)
        raise TLDVAPIError("All retry attempts failed")

    def _raise_api_error(self, response: requests.Response):
        try:
            error_data = response.json()
            message = error_data.get('message', f'HTTP {response.status_code}')
        except (ValueError, json.JSONDecodeError):
            message = f'HTTP {response.status_code}: {response.text[:200]}'
            error_data = {}
        raise TLDVAPIError(message, response.status_code, error_data)

    # restul metodelor (get_meetings, get_meeting, get_transcript, get_highlights, import_meeting, etc.) raman la fel ca in fisierul tau original, cu tiparile Optional/Dicte deja corecte.
    # IMPORTANT: acum Optional si Dict sunt importate corect la inceputul fisierului.

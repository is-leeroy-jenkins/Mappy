'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                maps.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="maps.py" company="Terry D. Eppler">

	     Mappy is a python framework encapsulating the Google Maps functionality.
	     Copyright ©  2022  Terry Eppler

     Permission is hereby granted, free of charge, to any person obtaining a copy
     of this software and associated documentation files (the “Software”),
     to deal in the Software without restriction,
     including without limitation the rights to use,
     copy, modify, merge, publish, distribute, sublicense,
     and/or sell copies of the Software,
     and to permit persons to whom the Software is furnished to do so,
     subject to the following conditions:

     The above copyright notice and this permission notice shall be included in all
     copies or substantial portions of the Software.

     THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
     INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
     FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.
     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
     DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
     ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
     DEALINGS IN THE SOFTWARE.

     You can contact me at:  terryeppler@gmail.com or eppler.terry@epa.gov

  </copyright>
  <summary>
    maps.py
  </summary>
  ******************************************************************************************
  '''
"""
Purpose:
    Provide the low-level HTTP gateway for Google Maps Web Service calls with
    optional rate limiting and exponential backoff.

Parameters:
    api_key (str):
        Google Maps Platform API key with necessary APIs enabled.
    qps (Optional[float]):
        Queries-per-second cap. None or <=0 disables throttling.
    max_retries (int):
        Number of retry attempts on transient errors (HTTP 429/5xx, timeouts).
    backoff_min (float):
        Initial backoff in seconds for retries (exponential).
    backoff_max (float):
        Maximum backoff in seconds for retries.

Returns:
    Maps instance exposing .request(endpoint, params) for JSON APIs.
"""

import time
from typing import Dict, Optional

import requests

from .exceptions import GatewayError
from .rate import RateLimiter

class Maps:
	"""
    Purpose:
        Centralized HTTP gateway for Google Maps Web Services. Handles rate
        limiting, retry-with-backoff, and error normalization.

    Parameters:
        api_key (str):
            Google Maps Platform API key.
        qps (Optional[float]):
            Max queries per second (None disables).
        max_retries (int):
            Maximum number of retries for transient failures.
        backoff_min (float):
            Initial backoff seconds.
        backoff_max (float):
            Maximum backoff seconds.

    Returns:
        Ready-to-use gateway. Use .request("geocode/json", {...}) etc.
    """

	BASE = "https://maps.googleapis.com/maps/api"

	def __init__(
			self,
			api_key: str,
			qps: Optional[ float ] = 5.0,
			max_retries: int = 5,
			backoff_min: float = 1.0,
			backoff_max: float = 30.0,
			timeout_sec: float = 15.0,
	) -> None:
		self._key = api_key
		self._limiter = RateLimiter( qps )
		self._max_retries = max_retries
		self._backoff_min = backoff_min
		self._backoff_max = backoff_max
		self._timeout = timeout_sec
		self._session = requests.Session( )

	def request( self, endpoint: str, params: Dict[ str, str ] ) -> Dict:
		"""
        Purpose:
            Execute a GET request to the given Google Maps endpoint with query
            params and robust retry/backoff for transient errors.

        Parameters:
            endpoint (str):
                Endpoint path, e.g., "geocode/json", "distancematrix/json".
            params (Dict[str, str]):
                Query parameters for the request. "key" is injected.

        Returns:
            Parsed JSON (dict) on success.

        Raises:
            GatewayError for non-recoverable HTTP issues or malformed responses.
        """
		url = f"{self.BASE}/{endpoint}"
		attempt = 0
		backoff = self._backoff_min

		while True:
			self._limiter.wait( )
			try:
				q = dict( params or { } )
				q[ "key" ] = self._key
				resp = self._session.get( url, params = q, timeout = self._timeout )
				status = resp.status_code

				if status == 200:
					return resp.json( )

				if status in (408, 429, 500, 502, 503, 504):
					# Transient; fall through to retry path below.
					raise GatewayError( f"Transient HTTP {status}: {resp.text[ :200 ]}" )

				# Non-retryable HTTP errors.
				raise GatewayError( f"HTTP {status}: {resp.text[ :200 ]}" )
			except (requests.Timeout, requests.ConnectionError, GatewayError) as ex:
				attempt += 1
				if attempt > self._max_retries:
					raise GatewayError( f"Exceeded retries: {ex}" ) from ex
				time.sleep( backoff )
				backoff = min( backoff * 2, self._backoff_max )
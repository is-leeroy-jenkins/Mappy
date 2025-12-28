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
import time
from typing import Dict, Optional
import requests
from exceptions import GatewayError
from rates import RateLimiter
from boogr import Error, ErrorDialog

def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )

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
	base_url: Optional[ str ]
	endpoint: Optional[ str ]
	params: Optional[ Dict[ str, str ] ]
	api_key: str
	query_per_second: Optional[ float ]
	retries: Optional[ int ]
	min: Optional[ float ]
	max: Optional[ float ]
	timeout: Optional[ float ]
	url: Optional[ str ]
	session: Optional[ requests.Session ]
	limiter: Optional[ RateLimiter ]
	query: Optional[ Dict[ str, str ] ]

	BASE = 'https://maps.googleapis.com/maps/api'

	def __init__( self, api_key: str, qps: Optional[ float ]=5.0, retries: int=5,
			min: float=1.0, max: float=30.0, timeout: float=15.0 ) -> None:
		self.api_key = api_key
		self.limiter = RateLimiter( qps )
		self.retries = retries
		self.min = min
		self.max = max
		self.timeout = timeout
		self.session = requests.Session( )
		self.base_url = 'https://maps.googleapis.com/maps/api'


	def request( self, endpoint: str, params: Dict[ str, str ] ) -> Dict | None:
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

        """
		try:
			throw_if( 'endpoint', endpoint )
			throw_if( 'params', params )
			self.endpoint = endpoint
			self.params = params
			self.url = f'{self.base_url}/{self.endpoint}'
			attempt = 0
			backoff = self.min
			while True:
				self.limiter.wait( )
				try:
					self.query = dict( self.params or { } )
					self.query[ 'api_key' ] = self.api_key
					resp = self.session.get( self.url, params=self.query, timeout=self.timeout )
					status = resp.status_code
					if status == 200:
						return resp.json( )

					if status in (408, 429, 500, 502, 503, 504):
						raise GatewayError( f'Transient HTTP {status}: {resp.text[ :200 ]}' )
					raise GatewayError( f'HTTP {status}: {resp.text[ :200 ]}' )
				except (requests.Timeout, requests.ConnectionError, GatewayError) as ex:
					attempt += 1
					if attempt > self.retries:
						raise GatewayError( f'Exceeded retries: {ex}' ) from ex
					time.sleep( backoff )
					backoff = min( backoff * 2, self.max )
		except Exception as e:
			raise
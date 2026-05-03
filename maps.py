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
from boogr import Error
import config as cfg

def throw_if( name: str, value: object ) -> None:
	"""
	
		Purpose:
		--------
		Validate that a required value is not empty.
		
		Parameters:
		-----------
		name (str): Name of the argument being validated.
		value (object): Value to validate.
		
		Returns:
		--------
		None
		
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be None.' )
	
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty.' )

class Maps( ):
	"""

	    Purpose:
	        Centralized HTTP gateway for Google Maps Web Services. Handles rate
	        limiting, retry-with-backoff, API-key injection, response diagnostics,
	        and Google payload-status normalization.

	    Parameters:
	        api_key (str):
	            Google Maps Platform API key.
	        qps (Optional[float]):
	            Max queries per second. None or <= 0 disables throttling.
	        retries (int):
	            Maximum number of retry attempts for transient failures.
	        min (float):
	            Initial backoff seconds.
	        max (float):
	            Maximum backoff seconds.
	        timeout (float):
	            Request timeout in seconds.

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
	response: Optional[ requests.Response ]
	last_url: Optional[ str ]
	last_query: Optional[ Dict[ str, str ] ]
	last_status: Optional[ int ]
	last_elapsed_ms: Optional[ float ]
	last_payload_status: Optional[ str ]
	last_payload_error: Optional[ str ]
	
	BASE = 'https://maps.googleapis.com/maps/api'
	
	def __init__( self, qps: Optional[ float ] = 5.0, retries: int = 5,
			min: float = 1.0, max: float = 30.0, timeout: float = 15.0 ) -> None:
		self.api_key = cfg.GOOGLEMAPS_API_KEY
		self.limiter = RateLimiter( qps )
		self.retries = retries
		self.min = min
		self.max = max
		self.timeout = timeout
		self.session = requests.Session( )
		self.base_url = self.BASE
		self.endpoint = None
		self.params = None
		self.url = None
		self.query = None
		self.response = None
		self.last_url = None
		self.last_query = None
		self.last_status = None
		self.last_elapsed_ms = None
		self.last_payload_status = None
		self.last_payload_error = None
	
	def request( self, endpoint: str, params: Dict[ str, str ] ) -> Dict | None:
		"""

	        Purpose:
	            Execute a GET request to the given Google Maps endpoint with query
	            params and robust retry/backoff for transient errors. The Google
	            Maps API key is injected as the "key" query parameter.

	        Parameters:
	            endpoint (str):
	                Endpoint path, e.g., "geocode/json", "distancematrix/json".
	            params (Dict[str, str]):
	                Query parameters for the request. "key" is injected.

	        Returns:
	            Parsed JSON dictionary on success.

        """
		try:
			throw_if( 'endpoint', endpoint )
			throw_if( 'params', params )
			self.endpoint = endpoint
			self.params = params
			self.url = f'{self.base_url}/{self.endpoint}'
			self.last_url = self.url
			attempt = 0
			backoff = self.min
			while True:
				self.limiter.wait( )
				try:
					self.query = dict( self.params or { } )
					self.query[ 'key' ] = self.api_key
					self.last_query = dict( self.query )
					start = time.perf_counter( )
					self.response = self.session.get( self.url, params=self.query,
						timeout=self.timeout )
					elapsed = time.perf_counter( ) - start
					self.last_elapsed_ms = round( elapsed * 1000.0, 3 )
					self.last_status = self.response.status_code
					if self.last_status != 200:
						if self.last_status in (408, 429, 500, 502, 503, 504):
							raise GatewayError( f'Transient HTTP {self.last_status}: '
							                    f'{self.response.text[ :200 ]}' )
						
						raise GatewayError(
							f'HTTP {self.last_status}: {self.response.text[ :200 ]}' )
					
					payload = self.response.json( )
					self.last_payload_status = None
					self.last_payload_error = None
					if isinstance( payload, dict ):
						payload_status = str( payload.get( 'status', '' ) or '' ).strip( )
						payload_error = str( payload.get( 'error_message', '' ) or '' ).strip( )
						self.last_payload_status = payload_status
						self.last_payload_error = payload_error
						hard_failures = {
								'REQUEST_DENIED',
								'OVER_DAILY_LIMIT',
								'OVER_QUERY_LIMIT',
								'INVALID_REQUEST',
								'MAX_ELEMENTS_EXCEEDED',
								'MAX_DIMENSIONS_EXCEEDED',
								'UNKNOWN_ERROR'
						}
						if payload_status in hard_failures:
							message = payload_error or f'Google API status: {payload_status}'
							if payload_status in ('OVER_QUERY_LIMIT', 'UNKNOWN_ERROR'):
								raise GatewayError(
									f'Transient Google API status {payload_status}: {message}' )
							
							raise GatewayError( f'Google API status {payload_status}: {message}' )
					
					return payload
				except (requests.Timeout, requests.ConnectionError, GatewayError) as ex:
					attempt += 1
					if attempt > self.retries:
						raise GatewayError( f'Exceeded retries: {ex}' ) from ex
					
					time.sleep( backoff )
					backoff = min( backoff * 2, self.max )
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Maps'
			exception.method = 'request( self, endpoint: str, params: Dict[ str, str ] )'
			raise exception
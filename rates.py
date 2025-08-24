'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                rates.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="rates.py" company="Terry D. Eppler">

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
    rates.py
  </summary>
  ******************************************************************************************
  '''
import time
from typing import Optional
from boogr import Error, ErrorDialog


def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


class RateLimiter:
	"""

		Purpose:
		Enforce a rough max-queries-per-second ceiling by sleeping between
		calls. This is lightweight and process-local.

		Parameters:
		query_per_second (Optional[float]):
		Max queries per second. If None or <= 0, no throttling occurs.

		Returns:
		Instance exposing .wait() to call right before an outbound request.

	"""
	query_per_second: Optional[ float ]
	interval: Optional[ float ]
	last: Optional[ float ]
	now: Optional[ time ]
	delta: Optional[ float ]

	def __init__( self, max: Optional[ float ] ) -> None:
		self.query_per_second = max
		self.interval = 1.0 / max if max and max > 0 else 0.0
		self.last = 0.0

	def wait( self ) -> None:
		"""

			Purpose:
				Sleep just enough so successive calls keep under the configured QPS.

			Parameters:
				None.

			Returns:
				None.

		"""
		try:
			if self.interval <= 0:
				return
			now = time.time( )
			delta = now - self.last
			if delta < self.interval:
				time.sleep( self.interval - delta )
			self.last = time.time( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'RateLimiter'
			exception.method = 'wait( self ) -> None'
			error = ErrorDialog( exception )
			error.show( )

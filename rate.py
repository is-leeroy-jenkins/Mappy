'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                rate.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="rate.py" company="Terry D. Eppler">

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
    rate.py
  </summary>
  ******************************************************************************************
  '''
"""
Purpose:
    Provide a minimal, dependency-free rate limiter to constrain outbound QPS.

Parameters:
    None.

Returns:
    RateLimiter class that sleeps between calls to maintain an average rate.
"""
import time
from typing import Optional


def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


class RateLimiter:
	"""

		Purpose:
			Enforce a rough max-queries-per-second ceiling by sleeping between
			calls. This is lightweight and process-local.

		Parameters:
			qps (Optional[float]):
				Max queries per second. If None or <= 0, no throttling occurs.

		Returns:
			Instance exposing .wait() to call right before an outbound request.

	"""

	def __init__( self, qps: Optional[ float ] ) -> None:
		self._qps = qps
		self._interval = 1.0 / qps if qps and qps > 0 else 0.0
		self._last = 0.0

	def wait( self ) -> None:
		"""

			Purpose:
				Sleep just enough so successive calls keep under the configured QPS.

			Parameters:
				None.

			Returns:
				None.

		"""
		if self._interval <= 0:
			return
		now = time.time( )
		delta = now - self._last
		if delta < self._interval:
			time.sleep( self._interval - delta )
		self._last = time.time( )

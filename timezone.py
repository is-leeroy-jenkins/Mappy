'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                timezone.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="timezone.py" company="Terry D. Eppler">

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
    timezone.py
  </summary>
  ******************************************************************************************
'''
import time
from typing import Optional
from .maps import Maps


def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


class Timezone:
	"""
	
		Purpose:
			Wrap Google Time Zone API for simple coordinate lookups.

		Parameters:
			maps (Maps):
				Maps gateway instance.

		Returns:
			Timezone with .get_id(...).
			
	"""

	def __init__( self, maps: Maps ) -> None:
		self._maps = maps

	def get_id( self, lat: float, lng: float ) -> Optional[ str ]:
		"""
		
			Purpose:
				Fetch the IANA time zone id (e.g., "Europe/Paris") for a coordinate.

			Parameters:
				lat (float):
					Latitude.
				lng (float):
					Longitude.

			Returns:
				Time zone id string or None if unavailable.
				
		"""
		ts = int( time.time( ) )
		data = self._maps.request( 'timezone/json',
			{ 'location': f'{lat},{lng}', 'timestamp': str( ts ) } )
		return data.get( 'timeZoneId' )

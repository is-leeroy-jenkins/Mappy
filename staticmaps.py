'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                staticmaps.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="staticmaps.py" company="Terry D. Eppler">

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
    staticmaps.py
  </summary>
  ******************************************************************************************
  '''
from urllib.parse import urlencode


def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


class StaticMapURL( ):
	"""
		
		Purpose:
			Generate Google Static Maps URLs for quick preview images.
	
		Parameters:
			api_key (str):
				Google Maps Platform API key.
	
		Returns:
			Instance with simple URL-building helpers.
		
	"""

	BASE = 'https://maps.googleapis.com/maps/api/staticmap'

	def __init__( self, api_key: str ) -> None:
		self._key = api_key

	def pin( self, lat: float, lng: float, zoom: int = 12, size: str = '400x300' ) -> str:
		"""

			Purpose:
				Build a GET URL for a static map centered on a coordinate with a
				single marker.

			Parameters:
				lat (float):
					Latitude for the pin.
				lng (float):
					Longitude for the pin.
				zoom (int):
					Zoom level, 1..20 (higher is closer).
				size (str):
					Image dimensions 'WxH' in pixels.

			Returns:
				Fully-qualified URL string suitable for embedding.

		"""
		params = {
				'center': f'{lat},{lng}',
				'zoom': str( zoom ),
				'size': size,
				'markers': f'{lat},{lng}',
				'key': self._key,
		}
		return f'{self.BASE}?{urlencode( params )}'

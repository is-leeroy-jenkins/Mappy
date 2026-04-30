'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                distances.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="distances.py" company="Terry D. Eppler">

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
    distances.py
  </summary>
  ******************************************************************************************
'''
from typing import Dict, Tuple, Union
from maps import Maps
from boogr import Error

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

Coord = Tuple[ float, float ]
AddressOrCoord = Union[ str, Coord ]


def fmt( o: AddressOrCoord ) -> str:
	"""
	
		Purpose:
			Normalize an origin/destination input to the API's expected string.
	
		Parameters:
			o (AddressOrCoord):
				Either "lat,lng" as tuple or a free-form string address.
	
		Returns:
			String representation for the API, "lat,lng" or the original string.
			
	"""
	if isinstance( o, tuple ) and len( o ) == 2:
		return f"{o[ 0 ]},{o[ 1 ]}"
	return str( o )


class DistanceMatrix():
	"""
	
		Purpose:
			Provide a thin wrapper for Google Distance Matrix API.
	
		Parameters:
			maps (Maps):
				Maps gateway instance.
	
		Returns:
			DistanceMatrix with .summary(...).
			
	"""

	def __init__( self, maps: Maps ) -> None:
		self._maps = maps

	def summary( self, origin: AddressOrCoord, destination: AddressOrCoord,
	             mode: str='driving' ) -> Dict:
		"""
		
			Purpose:
			Return a compact dict with meters/seconds and human text fields.
	
			Parameters:
			origin (AddressOrCoord):
				Origin address string or (lat, lng) tuple.
				
			destination (AddressOrCoord):
				Destination address string or (lat, lng) tuple.
				
			mode (str):
				Travel mode: 'driving', 'walking', 'bicycling', 'transit'.
	
			Returns:
			Dict with distance_text, distance_meters, duration_text, duration_seconds.
				
		"""
		try:
			data = self._maps.request( 'distancematrix/json',
				{ 'origins': fmt( origin ), 'destinations': fmt( destination ), 'mode': mode }, )
			row = ((data.get( 'rows' ) or [ { } ])[ 0 ].get( 'elements' ) or [ { } ])[ 0 ]
			dist = row.get( 'distance' ) or { }
			dur = row.get( 'duration' ) or { }
			return {
					'distance_text': dist.get( 'text' ),
					'distance_meters': dist.get( 'value' ),
					'duration_text': dur.get( 'text' ),
					'duration_seconds': dur.get( 'value' ),
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'summary( self, **kwargs )'
			raise exception

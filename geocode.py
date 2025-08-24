'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                geocode.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file='geocode.py' company='Terry D. Eppler'>

	     Mappy is a python framework encapsulating the Google Maps functionality.
	     Copyright ©  2022  Terry Eppler

	     Purpose:
		    High-level Geocoding service that resolves addresses or city/state/country
		    triples into canonical address data and coordinates.


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
    geocode.py
  </summary>
  ******************************************************************************************
'''
from typing import Any, Dict, Optional, List, Tuple
from .caches import BaseCache
from .exceptions import NotFound
from .maps import Maps
from boogr import Error, ErrorDialog

def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )

def _flatten_geocode( result: Dict[ str, Any ] ) -> Dict[ str, Any ]:
	"""

		Purpose:
			Reduce a geocode result into a compact, row-friendly dict.

		Parameters:
			result (Dict[str, Any]):
				One element from 'results' in Geocoding API response.

		Returns:
			Dict with formatted_address, lat, lng, place_id, types, and components.

	"""
	geometry = result.get( 'geometry', { } ) or { }
	loc = geometry.get( 'location', { } ) or { }
	comps = result.get( 'address_components', [ ] ) or [ ]

	def comp( kind: str, want_long: bool = False ) -> Optional[ str ]:
		for c in comps:
			if kind in (c.get( 'types' ) or [ ]):
				return (c.get( 'long_name' ) if want_long else c.get( 'short_name' )) or None
		return None

	return {
			'formatted_address': result.get( 'formatted_address' ),
			'lat': loc.get( 'lat' ),
			'lng': loc.get( 'lng' ),
			'place_id': result.get( 'place_id' ),
			'types': ','.join( result.get( 'types', [ ] ) ) if result.get( 'types' ) else None,
			'country_code': comp( 'country' ),
			'country_name': comp( 'country', want_long = True ),
			'admin_level_1': comp( 'administrative_area_level_1' ),
			'admin_level_2': comp( 'administrative_area_level_2' ),
			'locality': comp( 'locality' ) or comp( 'postal_town' ),
			'postal_code': comp( 'postal_code' ),
	}

class Geocoder:
	"""

		Purpose:
		Provide address and city/state/country geocoding with optional caching.

		Parameters:
		maps (Maps): Maps gateway instance.
		cache (Optional[BaseCache]): Pluggable cache for memoization.

		Returns:
		Geocoder instance with clear methods and consistent output shape.

	"""
	maps: Optional[ Maps ]
	cache: Optional[ BaseCache ]
	prefix: Optional[ str ]
	data: Optional[ Dict ]
	output: Optional[ Dict ]
	parts: Optional[ Tuple ]
	city: Optional[ str ]
	address: Optional[ str ]
	state: Optional[ str ]
	country: Optional[ str ]
	comps: Optional[ Dict[ str, str ] ]
	key: Optional[ str ]
	query: Optional[ str ]

	def __init__( self, maps: Maps, cache: Optional[ BaseCache ] = None ) -> None:
		self._maps = maps
		self._cache = cache

	def key_for( self, prefix: str, *parts: str ) -> str | None:
		try:
			self.prefix = prefix
			self.parts = parts
			joined = ' '.join( p.strip( ) for p in parts if p and str( p ).strip( ) )
			return f'{prefix}::{joined}'
		except Exception as e:
			exception = Error( e )
			exception.module = ''
			exception.cause = ''
			exception.method = ''
			error = ErrorDialog( exception )
			error.show( )


	def freeform( self, address: str, country: Optional[ str ] = None ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Geocode a free-form address string. Optionally bias by country code.

			Parameters:
				address (str):
					Any human-entered address string.
				country (Optional[str]):
					ISO-3166 alpha-2 country code to bias results (e.g., 'US', 'FR').

			Returns:
				Flattened dict as from _flatten_geocode(...).

			Raises:
				NotFound when no results are returned.

		"""
		try:
			self.address = address
			self.country = country
			self.key = self.key_for( 'geocode', address, country or "" )
			if self._cache:
				_hit = self._cache.get( self.key )
				if _hit:
					return _hit

			self.comps = { 'country': self.country.upper( ) } if self.country else None
			self.data = self._maps.request( 'geocode/json',
				{ 'address': self.address, **(self.comps or { }) } )
			if self.data.get( 'status' ) != 'OK' or not self.data.get( 'results' ):
				raise NotFound( f'No geocode for "{self.address}" ' )

			self.output = _flatten_geocode( self.data[ 'results' ][ 0 ] )
			if self.cache:
				self.cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = ''
			exception.cause = ''
			exception.method = ''
			error = ErrorDialog( exception )
			error.show( )


	def city_state_country( self, city: str, state: Optional[ str ], ctry: str ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
			Geocode a structured triple: (city, optional state/region, country).

			Parameters:
			city (str):
			City or locality.

			state (Optional[str]):
			State or region (may be None or empty).

			ctry (str):
			Country name or ISO-2 code.

			Returns:
			Flattened dict like freeform().

			Raises:
			NotFound when no result is available.

		"""
		try:
			self.city = city
			self.state = state
			self.country = ctry
			self.parts = tuple( [ p for p in [ self.city, self.state, self.country ] if p ] )
			self.query = ', '.join( self.parts )
			_hint = self.country.strip( ).upper( ) if self.country and len(
				self.country.strip( ) ) <= 3 else None
			return self.freeform( self.query, _hint, )
		except Exception as e:
			exception = Error( e )
			exception.module = ''
			exception.cause = ''
			exception.method = ''
			error = ErrorDialog( exception )
			error.show( )

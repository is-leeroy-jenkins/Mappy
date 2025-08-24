'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                places.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="places.py" company="Terry D. Eppler">

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
    places.py
  </summary>
  ******************************************************************************************
  '''
"""
Purpose:
    Provide a Places Text Search fallback and detail fetch that can be promoted
    into a geocode-like shape (address, lat/lng, components).

Parameters:
    maps (Maps):
        Maps gateway instance.
    cache (Optional[BaseCache]):
        Pluggable cache to memoize the text queries.

Returns:
    Places with .text_to_location(query, country=None).
"""
from typing import Any, Dict, Optional, List
from .caches import BaseCache
from .exceptions import NotFound
from .maps import Maps
from boogr import Error, ErrorDialog


def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


class Places:
	"""

		Purpose:
		Use Places Text Search to recover locations that Geocoding may miss.
		Top result is promoted via Place Details to a geocode-like dict.

		Parameters:
		maps (Maps):
			Maps gateway instance.
		cache (Optional[BaseCache]):
			Optional cache for query results.

		Returns:
		Places instance with .text_to_location(...).

	"""
	map: Optional[ Maps ]
	cache: Optional[ BaseCache ]
	country: Optional[ str ]
	query: Optional[ str ]
	hit: Optional[ Dict[ str, Any ] ]
	params: Optional[ Dict[ str, str ] ]
	request: Optional[ Dict[ str, str ] ]
	search: Optional[ Dict ]
	results: Optional[ List ]
	details: Optional[ Dict ]
	geometry: Optional[ Dict ]
	key: Optional[ str ]
	output: Optional[ Dict ]


	def __init__( self, maps: Maps, cache: Optional[ BaseCache ] = None ) -> None:
		self.maps = maps
		self.cache = cache

	def text_to_location( self, query: str, country: Optional[ str ]=None ) -> Dict[ str, Any ] | None:
		"""
			Purpose:
				Resolve a free-text query into address and coordinates via Places.

			Parameters:
				query (str):
					Arbitrary human-entered text (e.g., "Newcastle, NSW, AU").
				country (Optional[str]):
					ISO-2 region bias (e.g., "AU", "US").

			Returns:
				Dict with formatted_address, lat, lng, place_id, types, components.

			Raises:
				NotFound if no candidate is returned.
		"""
		try:
			throw_if( 'query', query )
			throw_if( 'country', country )
			self.query = query
			self.country = country
			self.key = f"places::{self.query}::{(self.country or '').upper( )}"
			if self.cache:
				self.hit = self.cache.get( self.key )
				if self.hit:
					return self.hit
			self.params: Dict[ str, str ] = { 'query': self.query }
			if self.country:
				self.params[ 'region' ] = self.country.upper( )
			self.search = self.maps.request( 'place/textsearch/json', self.params )
			self.results = self.search.get( 'results' )
			if not self.results:
				raise NotFound( f'No places match for "{self.query}" ' )
			_top = self.results[ 0 ]
			_pid = _top.get( 'place_id' )
			if not _pid:
				raise NotFound( 'Top place had no place_id' )
			self.details = self.maps.request( 'place/details/json',
				{ 'place_id': _pid,
				  'fields': 'formatted_address,geometry,address_component,place_id,type' },
			).get( 'result', { } )
			self.geometry = (self.details.get( 'geometry' ) or { }).get( 'location' ) or { }
			self.output = \
			{
				'formatted_address': self.details.get( 'formatted_address' ),
				'lat': self.geometry.get( 'lat' ),
				'lng': self.geometry.get( 'lng' ),
				'place_id': self.details.get( 'place_id' ),
				'types': ','.join( self.details.get( 'types', [ ] ) ),
				'address_components': self.details.get( 'address_components', [ ] ),
			}
			if self.cache:
				self.cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Places'
			exception.method = 'text_to_location( self, query: str, country: Optional[ str ]=None ) -> Dict'
			error = ErrorDialog( exception )
			error.show( )

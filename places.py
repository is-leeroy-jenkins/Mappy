'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                places.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file='places.py' company='Terry D. Eppler'>

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
from typing import Any, Dict, Optional, List
from caches import BaseCache
from exceptions import NotFound
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

class Place( ):
	"""

		Purpose:
		Use Places Text Search and Place Details to recover locations that
		Geocoding may miss. Results are returned in the same canonical shape
		used by Geocoder so both services can be used interchangeably.

		Parameters:
		maps (Maps):
			Maps gateway instance.
		cache (Optional[BaseCache]):
			Optional cache for query results.

		Returns:
		Places instance with text search and place-details helpers.

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
		self.country = None
		self.query = None
		self.hit = None
		self.params = None
		self.request = None
		self.search = None
		self.results = None
		self.details = None
		self.geometry = None
		self.key = None
		self.output = None
	
	def key_for( self, prefix: str, *parts: str ) -> str | None:
		"""

			Purpose:
				Create a stable cache key from a namespace prefix and one or more
				string parts.

			Parameters:
				prefix (str):
					Cache namespace or operation prefix.
				*parts (str):
					Values that uniquely identify the request.

			Returns:
				str | None:
					Normalized cache key.

		"""
		try:
			throw_if( 'prefix', prefix )
			throw_if( 'parts', parts )
			joined = ' '.join( str( p ).strip( ) for p in parts if p and str( p ).strip( ) )
			return f'{prefix}::{joined}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Places'
			exception.method = 'key_for( self, *args )'
			raise exception
	
	def component_value( self, components: List[ Dict[ str, Any ] ], kind: str,
			want_long: bool = False ) -> Optional[ str ]:
		"""

			Purpose:
				Extract a single address component value from a Google Places or
				Geocoding address_components collection.

			Parameters:
				components (List[Dict[str, Any]]):
					Google address component dictionaries.
				kind (str):
					Component type to extract, such as country or locality.
				want_long (bool):
					When True, return long_name instead of short_name.

			Returns:
				Optional[str]:
					Component value when present; otherwise None.

		"""
		try:
			for component in components or [ ]:
				if kind in (component.get( 'types' ) or [ ]):
					if want_long:
						return component.get( 'long_name' ) or None
					
					return component.get( 'short_name' ) or None
			
			return None
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Places'
			exception.method = 'component_value( self, *args )'
			raise exception
	
	def flatten_place_details( self, details: Dict[ str, Any ], query: str = '' ) -> Dict[
		str, Any ]:
		"""

			Purpose:
				Convert a Place Details result into the same flattened output shape
				used by Geocoder.flatten_geocode(...).

			Parameters:
				details (Dict[str, Any]):
					Google Place Details result dictionary.
				query (str):
					Original query text, when available.

			Returns:
				Dict[str, Any]:
					Canonical location dictionary.

		"""
		try:
			throw_if( 'details', details )
			geometry = (details.get( 'geometry' ) or { }).get( 'location' ) or { }
			components = details.get( 'address_components', [ ] ) or [ ]
			return {
					'formatted_address': details.get( 'formatted_address' ),
					'lat': geometry.get( 'lat' ),
					'lng': geometry.get( 'lng' ),
					'place_id': details.get( 'place_id' ),
					'types': ','.join( details.get( 'types', [ ] ) )
					if details.get( 'types' ) else None,
					'country_code': self.component_value( components, 'country' ),
					'country_name': self.component_value( components, 'country', want_long=True ),
					'admin_level_1': self.component_value( components,
						'administrative_area_level_1' ),
					'admin_level_2': self.component_value( components,
						'administrative_area_level_2' ),
					'locality': (
							self.component_value( components, 'locality' )
							or self.component_value( components, 'postal_town' )
					),
					'postal_code': self.component_value( components, 'postal_code' ),
					'name': details.get( 'name' ),
					'business_status': details.get( 'business_status' ),
					'rating': details.get( 'rating' ),
					'user_ratings_total': details.get( 'user_ratings_total' ),
					'website': details.get( 'website' ),
					'formatted_phone_number': details.get( 'formatted_phone_number' ),
					'source': 'places',
					'query': query
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Places'
			exception.method = 'flatten_place_details( self, *args )'
			raise exception
	
	def place_details( self, place_id: str ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Fetch and flatten details for a known Google place_id.

			Parameters:
				place_id (str):
					Google Places place identifier.

			Returns:
				Dict[str, Any] | None:
					Canonical flattened place details.

		"""
		try:
			throw_if( 'place_id', place_id )
			self.key = self.key_for( 'place_details', place_id )
			if self.cache:
				self.hit = self.cache.get( self.key )
				if self.hit:
					return self.hit
			
			fields = ('formatted_address,geometry,address_component,place_id,type,'
			          'name,business_status,rating,user_ratings_total,website,'
			          'formatted_phone_number')
			self.details = self.maps.request( 'place/details/json', {
					'place_id': place_id,
					'fields': fields
			} ).get( 'result', { } )
			if not self.details:
				raise NotFound( f'No place details found for "{place_id}" ' )
			self.output = self.flatten_place_details( self.details, query=place_id )
			if self.cache:
				self.cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Places'
			exception.method = 'place_details( self, *args )'
			raise exception
	
	def text_to_location( self, query: str, country: str = 'US' ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Resolve a free-text query into a canonical address and coordinate
				record via Google Places Text Search and Place Details.

			Parameters:
				query (str):
					Arbitrary human-entered text such as "Newcastle, NSW, AU".
				country (str):
					ISO-2 region bias such as "AU" or "US".

			Returns:
				Dict[str, Any] | None:
					Canonical location dictionary compatible with Geocoder output.

			Raises:
				NotFound:
					Raised when no candidate is returned.

		"""
		try:
			throw_if( 'query', query )
			self.query = query.strip( )
			self.country = str( country or '' ).strip( )
			self.key = self.key_for( 'places', self.query, self.country.upper( ) )
			if self.cache:
				self.hit = self.cache.get( self.key )
				if self.hit:
					return self.hit
			self.params = { 'query': self.query }
			if self.country:
				self.params[ 'region' ] = self.country.upper( )
			self.search = self.maps.request( 'place/textsearch/json', self.params )
			self.results = self.search.get( 'results' ) or [ ]
			if not self.results:
				raise NotFound( f'No places match for "{self.query}" ' )
			top = self.results[ 0 ]
			place_id = top.get( 'place_id' )
			if not place_id:
				raise NotFound( 'Top place had no place_id' )
			fields = ('formatted_address,geometry,address_component,place_id,type,'
			          'name,business_status,rating,user_ratings_total,website,'
			          'formatted_phone_number')
			self.details = self.maps.request( 'place/details/json', {
					'place_id': place_id,
					'fields': fields
			} ).get( 'result', { } )
			if not self.details:
				raise NotFound( f'No place details found for "{self.query}" ' )
			self.output = self.flatten_place_details( self.details, query=self.query )
			if self.cache:
				self.cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Places'
			exception.method = 'text_to_location( self, *args )'
			raise exception
	
	def search_candidates( self, query: str, country: str = 'US', lmt: int = 5 ) -> List[
		Dict[ str, Any ] ]:
		"""

			Purpose:
				Return multiple Places Text Search candidates for a query. This is
				intended for future UI candidate-selection workflows.

			Parameters:
				query (str):
					Free-text search query.
				country (str):
					ISO-2 region bias.
				limit (int):
					Maximum candidates to return.

			Returns:
				List[Dict[str, Any]]:
					Raw candidate dictionaries returned by Text Search.

		"""
		try:
			throw_if( 'query', query )
			self.query = query.strip( )
			self.country = str( country or '' ).strip( )
			self.params = { 'query': self.query }
			if self.country:
				self.params[ 'region' ] = self.country.upper( )
			self.search = self.maps.request( 'place/textsearch/json', self.params )
			self.results = self.search.get( 'results' ) or [ ]
			if not self.results:
				raise NotFound( f'No places match for "{self.query}" ' )
			return self.results[ :max( 1, int( lmt ) ) ]
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Places'
			exception.method = 'search_candidates( self, *args )'
			raise exception

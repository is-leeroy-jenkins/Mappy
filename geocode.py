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
		    triples into canonical address stores and coordinates.


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

def flatten_geocode( result: Dict[ str, Any ] ) -> Dict[ str, Any ]:
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
			'country_name': comp( 'country', want_long=True ),
			'admin_level_1': comp( 'administrative_area_level_1' ),
			'admin_level_2': comp( 'administrative_area_level_2' ),
			'locality': comp( 'locality' ) or comp( 'postal_town' ),
			'postal_code': comp( 'postal_code' ),
	}

class Geocoder( ):
	"""

		Purpose:
		Provide address, city/state/country, reverse, and batch geocoding with
		optional caching and a consistent flattened output shape.

		Parameters:
		maps (Maps): Maps gateway instance.
		cache (Optional[BaseCache]): Pluggable cache for memoization.

		Returns:
		Geocoder instance with forward, reverse, and batch geocoding methods.

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
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	
	def __init__( self, maps: Maps, cache: Optional[ BaseCache ] = None ) -> None:
		self._maps = maps
		self._cache = cache
		self.maps = maps
		self.cache = cache
		self.prefix = None
		self.data = None
		self.output = None
		self.parts = None
		self.city = None
		self.address = None
		self.state = None
		self.country = None
		self.comps = None
		self.key = None
		self.query = None
		self.latitude = None
		self.longitude = None
	
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
			self.prefix = prefix
			self.parts = parts
			joined = ' '.join( str( p ).strip( ) for p in parts if p and str( p ).strip( ) )
			return f'{prefix}::{joined}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Geocoder'
			exception.method = 'key_for( self, *kwargs )'
			raise exception
	
	def validate_coordinates( self, latitude: float, longitude: float ) -> Tuple[ float, float ]:
		"""

			Purpose:
				Validate and normalize a latitude/longitude coordinate pair.

			Parameters:
				latitude (float):
					Latitude in decimal degrees.
				longitude (float):
					Longitude in decimal degrees.

			Returns:
				Tuple[float, float]:
					Validated latitude and longitude.

		"""
		try:
			throw_if( 'latitude', latitude )
			throw_if( 'longitude', longitude )
			lat = float( latitude )
			lng = float( longitude )
			if lat < -90.0 or lat > 90.0:
				raise ValueError( 'Latitude must be between -90 and 90.' )
			if lng < -180.0 or lng > 180.0:
				raise ValueError( 'Longitude must be between -180 and 180.' )
			return lat, lng
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Geocoder'
			exception.method = 'validate_coordinates( self, latitude: float, longitude: float )'
			raise exception
	
	def freeform( self, address: str, country: str = 'US' ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Geocode a free-form address string. Optionally bias by country code.

			Parameters:
				address (str):
					Any human-entered address string.
				country (str):
					ISO-3166 alpha-2 country code to bias results, such as 'US'
					or 'FR'. Pass an empty string to disable country bias.

			Returns:
				Dict[str, Any] | None:
					Flattened geocode result.

			Raises:
				NotFound:
					Raised when no results are returned.

		"""
		try:
			throw_if( 'address', address )
			self.address = address.strip( )
			self.country = str( country or '' ).strip( )
			self.key = self.key_for( 'geocode', self.address, self.country )
			if self._cache:
				hit = self._cache.get( self.key )
				if hit:
					return hit
			self.comps = { 'country': self.country.upper( ) } if self.country else None
			self.data = self._maps.request( 'geocode/json',
				{ 'address': self.address, **(self.comps or { }) } )
			
			if self.data.get( 'status' ) != 'OK' or not self.data.get( 'results' ):
				raise NotFound( f'No geocode for "{self.address}" ' )
			self.output = flatten_geocode( self.data[ 'results' ][ 0 ] )
			self.output[ 'source' ] = 'geocode'
			self.output[ 'query' ] = self.address
			if self._cache:
				self._cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Geocoder'
			exception.method = 'freeform( self, address: str, country: str=US )'
			raise exception
	
	def reverse( self, latitude: float, longitude: float ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Reverse geocode a latitude/longitude pair into a canonical address.

			Parameters:
				latitude (float):
					Latitude in decimal degrees.
				longitude (float):
					Longitude in decimal degrees.

			Returns:
				Dict[str, Any] | None:
					Flattened geocode result.

			Raises:
				NotFound:
					Raised when no reverse-geocode result is returned.

		"""
		try:
			self.latitude, self.longitude = self.validate_coordinates( latitude, longitude )
			self.key = self.key_for( 'reverse_geocode', str( self.latitude ),
				str( self.longitude ) )
			if self._cache:
				hit = self._cache.get( self.key )
				if hit:
					return hit
			self.data = self._maps.request( 'geocode/json',
				{ 'latlng': f'{self.latitude},{self.longitude}' } )
			
			if self.data.get( 'status' ) != 'OK' or not self.data.get( 'results' ):
				raise NotFound( f'No reverse geocode for "{self.latitude},{self.longitude}" ' )
			self.output = flatten_geocode( self.data[ 'results' ][ 0 ] )
			self.output[ 'source' ] = 'reverse_geocode'
			self.output[ 'query' ] = f'{self.latitude},{self.longitude}'
			if self._cache:
				self._cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Geocoder'
			exception.method = 'reverse( self, latitude: float, longitude: float )'
			raise exception
	
	def city_state_country( self, city: str, state: str, country: str ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Geocode a structured city/state/country triple.

			Parameters:
				city (str):
					City or locality.
				state (str):
					State, province, territory, or region. May be empty.
				country (str):
					Country name or ISO-2 country code.

			Returns:
				Dict[str, Any] | None:
					Flattened geocode result.

			Raises:
				NotFound:
					Raised when no result is available.

		"""
		try:
			throw_if( 'city', city )
			throw_if( 'country', country )
			self.city = city
			self.state = state
			self.country = country
			self.parts = tuple( [ p for p in [ self.city, self.state, self.country ] if p ] )
			self.query = ', '.join( self.parts )
			hint = (self.country.strip( ).upper( )
			        if self.country and len( self.country.strip( ) ) <= 3
			        else '')
			return self.freeform( self.query, hint )
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Geocoder'
			exception.method = 'city_state_country( self, city: str, state: str, country: str )'
			raise exception
	
	def batch_freeform( self, addresses: List[ str ], country: str = 'US' ) -> List[
		Dict[ str, Any ] ]:
		"""

			Purpose:
				Geocode a list of free-form addresses while preserving row-level
				success and failure status.

			Parameters:
				addresses (List[str]):
					Address strings to geocode.
				country (str):
					ISO-3166 alpha-2 country code used as a default country bias.

			Returns:
				List[Dict[str, Any]]:
					List of flattened geocode results. Failed rows include
					geocode_status='error' and geocode_error.

		"""
		try:
			throw_if( 'addresses', addresses )
			if not isinstance( addresses, list ):
				raise ValueError( 'addresses must be a list of strings.' )
			results: List[ Dict[ str, Any ] ] = [ ]
			for address in addresses:
				value = str( address or '' ).strip( )
				if not value:
					results.append( {
							'formatted_address': None,
							'lat': None,
							'lng': None,
							'place_id': None,
							'types': None,
							'country_code': None,
							'country_name': None,
							'admin_level_1': None,
							'admin_level_2': None,
							'locality': None,
							'postal_code': None,
							'source': 'geocode',
							'query': value,
							'geocode_status': 'skipped_empty',
							'geocode_error': None
					} )
					continue
				try:
					item = self.freeform( value, country=country ) or { }
					item[ 'geocode_status' ] = 'ok'
					item[ 'geocode_error' ] = None
					results.append( item )
				except Exception as row_error:
					results.append( {
							'formatted_address': None,
							'lat': None,
							'lng': None,
							'place_id': None,
							'types': None,
							'country_code': None,
							'country_name': None,
							'admin_level_1': None,
							'admin_level_2': None,
							'locality': None,
							'postal_code': None,
							'source': 'geocode',
							'query': value,
							'geocode_status': 'error',
							'geocode_error': str( row_error )
					} )
			return results
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Geocoder'
			exception.method = 'batch_freeform( self, *kwargs )'
			raise exception

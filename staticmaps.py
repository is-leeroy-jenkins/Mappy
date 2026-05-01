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
from typing import Optional, Dict
from urllib.parse import urlencode
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

class StaticMapURL( ):
	"""
		
		Purpose:
			Generate Google Static Maps URLs for single-point previews, multi-point
			previews, paths, and bounding-box previews.
	
		Parameters:
			api_key (str):
				Google Maps Platform API key.
	
		Returns:
			StaticMapURL instance with URL-building helpers.
		
	"""
	api_key: Optional[ str ]
	zoom: Optional[ int ]
	size: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	params: Optional[ Dict ]
	markers: Optional[ str ]
	base_url: Optional[ str ]
	points: Optional[ list ]
	maptype: Optional[ str ]
	color: Optional[ str ]
	weight: Optional[ int ]
	west: Optional[ float ]
	south: Optional[ float ]
	east: Optional[ float ]
	north: Optional[ float ]
	
	def __init__( self, api_key: str ) -> None:
		self.api_key = api_key
		self.zoom = None
		self.size = None
		self.latitude = None
		self.longitude = None
		self.params = None
		self.markers = None
		self.base_url = 'https://maps.googleapis.com/maps/api/staticmap'
		self.points = None
		self.maptype = None
		self.color = None
		self.weight = None
		self.west = None
		self.south = None
		self.east = None
		self.north = None
	
	def validate_coordinate( self, lat: float, lng: float ) -> tuple:
		"""

			Purpose:
				Validate and normalize a latitude and longitude pair.

			Parameters:
				lat (float):
					Latitude in decimal degrees.

				lng (float):
					Longitude in decimal degrees.

			Returns:
				tuple:
					Validated latitude and longitude.

		"""
		try:
			throw_if( 'lat', lat )
			throw_if( 'lng', lng )
			
			latitude = float( lat )
			longitude = float( lng )
			
			if latitude < -90.0 or latitude > 90.0:
				raise ValueError( 'Latitude must be between -90 and 90.' )
			
			if longitude < -180.0 or longitude > 180.0:
				raise ValueError( 'Longitude must be between -180 and 180.' )
			
			self.latitude = latitude
			self.longitude = longitude
			
			return self.latitude, self.longitude
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMapURL'
			exception.method = 'validate_coordinate( self, lat: float, lng: float )'
			raise exception
	
	def normalize_points( self, points: list ) -> list:
		"""

			Purpose:
				Normalize coordinate tuples, coordinate lists, or dictionaries with
				lat/lng fields into validated coordinate tuples.

			Parameters:
				points (list):
					List of coordinates. Supported item shapes include:
					(lat, lng), [lat, lng], {'lat': value, 'lng': value}, and
					{'latitude': value, 'longitude': value}.

			Returns:
				list:
					List of validated coordinate tuples.

		"""
		try:
			throw_if( 'points', points )
			
			if not isinstance( points, list ):
				raise ValueError( 'points must be a list.' )
			
			output = [ ]
			
			for point in points:
				if isinstance( point, dict ):
					lat_value = point.get( 'lat', point.get( 'latitude' ) )
					lng_value = point.get( 'lng', point.get( 'longitude' ) )
					output.append( self.validate_coordinate( lat_value, lng_value ) )
				
				elif isinstance( point, tuple ) and len( point ) == 2:
					output.append( self.validate_coordinate( point[ 0 ], point[ 1 ] ) )
				
				elif isinstance( point, list ) and len( point ) == 2:
					output.append( self.validate_coordinate( point[ 0 ], point[ 1 ] ) )
				
				else:
					raise ValueError( f'Unsupported point format: {point}' )
			
			if not output:
				raise ValueError( 'At least one coordinate is required.' )
			
			self.points = output
			
			return self.points
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMapURL'
			exception.method = 'normalize_points( self, points: list )'
			raise exception
	
	def build_url( self, params: Dict ) -> str | None:
		"""

			Purpose:
				Build a Google Static Maps URL from a parameter dictionary.

			Parameters:
				params (Dict):
					Google Static Maps query parameters.

			Returns:
				str | None:
					Fully-qualified Google Static Maps URL.

		"""
		try:
			throw_if( 'params', params )
			
			params_value = dict( params or { } )
			params_value[ 'key' ] = self.api_key
			self.params = params_value
			
			return f'{self.base_url}?{urlencode( self.params, doseq=True )}'
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMapURL'
			exception.method = 'build_url( self, params: Dict )'
			raise exception
	
	def pin( self, lat: float, lng: float, zoom: int = 12, size: str = '400x300' ) -> str | None:
		"""

			Purpose:
				Build a static map URL centered on a coordinate with a single marker.

			Parameters:
				lat (float):
					Latitude for the pin.

				lng (float):
					Longitude for the pin.

				zoom (int):
					Zoom level from 1 through 20.

				size (str):
					Image dimensions in WxH format.

			Returns:
				str | None:
					Fully-qualified URL string suitable for embedding.

		"""
		try:
			latitude, longitude = self.validate_coordinate( lat, lng )
			zoom_value = max( 1, min( int( zoom or 12 ), 20 ) )
			size_value = size or '400x300'
			marker_value = f'{latitude},{longitude}'
			
			self.latitude = latitude
			self.longitude = longitude
			self.zoom = zoom_value
			self.size = size_value
			self.markers = marker_value
			
			self.params = {
					'center': f'{self.latitude},{self.longitude}',
					'zoom': str( self.zoom ),
					'size': self.size,
					'markers': self.markers
			}
			
			return self.build_url( self.params )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMapURL'
			exception.method = 'pin( self, lat: float, lng: float, zoom: int=12, size: str=400x300 )'
			raise exception
	
	def pins( self, points: list, zoom: int = 0, size: str = '600x400',
			maptype: str = 'roadmap', color: str = 'red' ) -> str | None:
		"""

			Purpose:
				Build a static map URL with multiple markers. If zoom is zero,
				Google is allowed to fit the visible area to the supplied points.

			Parameters:
				points (list):
					List of coordinate tuples, coordinate lists, or dictionaries
					containing lat/lng fields.

				zoom (int):
					Zoom level. Use zero to omit explicit zoom.

				size (str):
					Image dimensions in WxH format.

				maptype (str):
					Map type: roadmap, satellite, terrain, or hybrid.

				color (str):
					Marker color.

			Returns:
				str | None:
					Fully-qualified URL string suitable for embedding.

		"""
		try:
			coordinates = self.normalize_points( points )
			zoom_value = int( zoom or 0 )
			size_value = size or '600x400'
			maptype_value = str( maptype or 'roadmap' ).strip( ).lower( )
			color_value = color or 'red'
			
			if maptype_value not in [ 'roadmap', 'satellite', 'terrain', 'hybrid' ]:
				raise ValueError( 'maptype must be roadmap, satellite, terrain, or hybrid.' )
			
			self.points = coordinates
			self.zoom = zoom_value
			self.size = size_value
			self.maptype = maptype_value
			self.color = color_value
			
			marker_values = [ ]
			
			for lat_value, lng_value in self.points:
				marker_values.append( f'color:{self.color}|{lat_value},{lng_value}' )
			
			self.params = {
					'size': self.size,
					'maptype': self.maptype,
					'markers': marker_values
			}
			
			if self.zoom > 0:
				center_lat = sum( p[ 0 ] for p in self.points ) / len( self.points )
				center_lng = sum( p[ 1 ] for p in self.points ) / len( self.points )
				self.params[ 'center' ] = f'{center_lat},{center_lng}'
				self.params[ 'zoom' ] = str( max( 1, min( self.zoom, 20 ) ) )
			
			else:
				self.params[ 'visible' ] = [ f'{lat},{lng}' for lat, lng in self.points ]
			
			return self.build_url( self.params )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMapURL'
			exception.method = 'pins( self, points: list, zoom: int=0, size: str=600x400 )'
			raise exception
	
	def path( self, points: list, size: str = '600x400', maptype: str = 'roadmap',
			color: str = '0x0000ff', weight: int = 5 ) -> str | None:
		"""

			Purpose:
				Build a static map URL showing a path through two or more points.

			Parameters:
				points (list):
					List of coordinate tuples, coordinate lists, or dictionaries
					containing lat/lng fields.

				size (str):
					Image dimensions in WxH format.

				maptype (str):
					Map type: roadmap, satellite, terrain, or hybrid.

				color (str):
					Path color.

				weight (int):
					Path stroke weight.

			Returns:
				str | None:
					Fully-qualified URL string suitable for embedding.

		"""
		try:
			coordinates = self.normalize_points( points )
			size_value = size or '600x400'
			maptype_value = str( maptype or 'roadmap' ).strip( ).lower( )
			color_value = color or '0x0000ff'
			weight_value = max( 1, int( weight or 5 ) )
			
			if len( coordinates ) < 2:
				raise ValueError( 'At least two coordinates are required for a path.' )
			
			if maptype_value not in [ 'roadmap', 'satellite', 'terrain', 'hybrid' ]:
				raise ValueError( 'maptype must be roadmap, satellite, terrain, or hybrid.' )
			
			self.points = coordinates
			self.size = size_value
			self.maptype = maptype_value
			self.color = color_value
			self.weight = weight_value
			
			path_points = [ f'{lat},{lng}' for lat, lng in self.points ]
			path_parts = [ f'color:{self.color}', f'weight:{self.weight}' ] + path_points
			path_value = '|'.join( path_parts )
			
			self.params = {
					'size': self.size,
					'maptype': self.maptype,
					'path': path_value,
					'markers': [
							f'color:green|{self.points[ 0 ][ 0 ]},{self.points[ 0 ][ 1 ]}',
							f'color:red|{self.points[ -1 ][ 0 ]},{self.points[ -1 ][ 1 ]}'
					],
					'visible': path_points
			}
			
			return self.build_url( self.params )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMapURL'
			exception.method = 'path( self, points: list, size: str=600x400 )'
			raise exception
	
	def bbox( self, west: float, south: float, east: float, north: float,
			size: str = '600x400', maptype: str = 'roadmap' ) -> str | None:
		"""

			Purpose:
				Build a static map URL showing a rectangular bounding box.

			Parameters:
				west (float):
					Western longitude.

				south (float):
					Southern latitude.

				east (float):
					Eastern longitude.

				north (float):
					Northern latitude.

				size (str):
					Image dimensions in WxH format.

				maptype (str):
					Map type: roadmap, satellite, terrain, or hybrid.

			Returns:
				str | None:
					Fully-qualified URL string suitable for embedding.

		"""
		try:
			throw_if( 'west', west )
			throw_if( 'south', south )
			throw_if( 'east', east )
			throw_if( 'north', north )
			
			west_value = float( west )
			south_value = float( south )
			east_value = float( east )
			north_value = float( north )
			size_value = size or '600x400'
			maptype_value = maptype or 'roadmap'
			
			southwest = self.validate_coordinate( south_value, west_value )
			northwest = self.validate_coordinate( north_value, west_value )
			northeast = self.validate_coordinate( north_value, east_value )
			southeast = self.validate_coordinate( south_value, east_value )
			
			self.west = west_value
			self.south = south_value
			self.east = east_value
			self.north = north_value
			self.size = size_value
			self.maptype = maptype_value
			self.points = [ southwest, northwest, northeast, southeast, southwest ]
			
			return self.path(
				points=self.points,
				size=self.size,
				maptype=self.maptype,
				color='0xff0000',
				weight=3 )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMapURL'
			exception.method = 'bbox( self, west: float, south: float, east: float, north: float )'
			raise exception
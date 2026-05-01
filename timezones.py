'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                timezones.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="timezones.py" company="Terry D. Eppler">

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
    timezones.py
  </summary>
  ******************************************************************************************
'''
import time
import datetime as dt
from typing import Optional, Dict
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

class Timezone:
	"""
	
		Purpose:
			Wrap Google Time Zone API for coordinate lookups, full payload retrieval,
			UTC offset extraction, local-time conversion, and batch enrichment.

		Parameters:
			maps (Maps):
				Maps gateway instance.

		Returns:
			Timezone with get_id, lookup, offset_hours, local_time, and batch_lookup.
			
	"""
	timestamp: Optional[ int ]
	maps: Optional[ Maps ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	data: Optional[ Dict ]
	offset: Optional[ float ]
	local: Optional[ str ]
	rows: Optional[ list ]
	lat_field: Optional[ str ]
	lng_field: Optional[ str ]
	utc_datetime: Optional[ dt.datetime ]
	
	def __init__( self, maps: Maps ) -> None:
		self.maps = maps
		self.timestamp = None
		self.latitude = None
		self.longitude = None
		self.data = None
		self.offset = None
		self.local = None
		self.rows = None
		self.lat_field = None
		self.lng_field = None
		self.utc_datetime = None
	
	def validate_coordinates( self, lat: float, lng: float ) -> tuple:
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
			exception.module = 'Mappy'
			exception.cause = 'Timezone'
			exception.method = 'validate_coordinates( self, lat: float, lng: float )'
			raise exception
	
	def lookup( self, lat: float, lng: float ) -> Dict | None:
		"""

			Purpose:
				Fetch the full Google Time Zone API response for a coordinate.

			Parameters:
				lat (float):
					Latitude.

				lng (float):
					Longitude.

			Returns:
				Dict | None:
					Full time zone response payload, including timeZoneId, timeZoneName,
					rawOffset, dstOffset, and status when available.

		"""
		try:
			latitude, longitude = self.validate_coordinates( lat, lng )
			timestamp_value = int( time.time( ) )
			
			self.latitude = latitude
			self.longitude = longitude
			self.timestamp = timestamp_value
			
			self.data = self.maps.request(
				'timezone/json',
				{
						'location': f'{self.latitude},{self.longitude}',
						'timestamp': str( self.timestamp )
				} )
			
			return self.data
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Timezone'
			exception.method = 'lookup( self, lat: float, lng: float )'
			raise exception
	
	def get_id( self, lat: float, lng: float ) -> Optional[ str ]:
		"""
		
			Purpose:
				Fetch the IANA time zone id for a coordinate.

			Parameters:
				lat (float):
					Latitude.

				lng (float):
					Longitude.

			Returns:
				Optional[str]:
					Time zone id string or None if unavailable.
				
		"""
		try:
			self.data = self.lookup( lat, lng )
			
			if not isinstance( self.data, dict ):
				return None
			
			return self.data.get( 'timeZoneId' )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Timezone'
			exception.method = 'get_id( self, lat: float, lng: float )'
			raise exception
	
	def offset_hours( self, lat: float, lng: float ) -> Optional[ float ]:
		"""
		
			Purpose:
				Fetch the total UTC offset in hours for a coordinate.

			Parameters:
				lat (float):
					Latitude.

				lng (float):
					Longitude.

			Returns:
				Optional[float]:
					Total UTC offset in hours, including daylight-saving offset
					when returned by the API.
				
		"""
		try:
			self.data = self.lookup( lat, lng )
			
			if not isinstance( self.data, dict ):
				return None
			
			raw_offset = self.data.get( 'rawOffset', 0 ) or 0
			dst_offset = self.data.get( 'dstOffset', 0 ) or 0
			offset_value = round( (float( raw_offset ) + float( dst_offset )) / 3600.0, 3 )
			
			self.offset = offset_value
			
			return self.offset
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Timezone'
			exception.method = 'offset_hours( self, lat: float, lng: float )'
			raise exception
	
	def local_time( self, lat: float, lng: float,
			utc_datetime: Optional[ dt.datetime ] = None ) -> Dict | None:
		"""
		
			Purpose:
				Convert a UTC datetime into local time at a coordinate using the
				Google Time Zone API rawOffset and dstOffset fields.

			Parameters:
				lat (float):
					Latitude.

				lng (float):
					Longitude.

				utc_datetime (Optional[dt.datetime]):
					Optional UTC datetime. If None, the current UTC time is used.

			Returns:
				Dict | None:
					Dictionary containing timezone metadata, UTC time, local time,
					and total offset hours.
				
		"""
		try:
			self.data = self.lookup( lat, lng )
			if not isinstance( self.data, dict ):
				return None
			
			if utc_datetime is None:
				utc_value = dt.datetime.now( dt.timezone.utc )
			else:
				utc_value = utc_datetime
				
				if utc_value.tzinfo is None:
					utc_value = utc_value.replace( tzinfo=dt.timezone.utc )
				else:
					utc_value = utc_value.astimezone( dt.timezone.utc )
			
			raw_offset = self.data.get( 'rawOffset', 0 ) or 0
			dst_offset = self.data.get( 'dstOffset', 0 ) or 0
			total_seconds = float( raw_offset ) + float( dst_offset )
			local_value = utc_value + dt.timedelta( seconds=total_seconds )
			offset_value = round( total_seconds / 3600.0, 3 )
			self.utc_datetime = utc_value
			self.offset = offset_value
			self.local = local_value.isoformat( )
			
			return {
					'timeZoneId': self.data.get( 'timeZoneId' ),
					'timeZoneName': self.data.get( 'timeZoneName' ),
					'status': self.data.get( 'status' ),
					'rawOffset': raw_offset,
					'dstOffset': dst_offset,
					'offset_hours': self.offset,
					'utc_time': self.utc_datetime.isoformat( ),
					'local_time': self.local,
					'lat': self.latitude,
					'lng': self.longitude
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Timezone'
			exception.method = 'local_time( self, lat: float, lng: float, utc_datetime: Optional[ dt.datetime ]=None )'
			raise exception
	
	def batch_lookup( self, rows: list, lat_field: str = 'lat', lng_field: str = 'lng' ) -> list:
		"""
		
			Purpose:
				Enrich a list of row dictionaries with Google Time Zone API fields.

			Parameters:
				rows (list):
					List of dictionaries containing latitude and longitude fields.

				lat_field (str):
					Latitude field name.

				lng_field (str):
					Longitude field name.

			Returns:
				list:
					List of copied row dictionaries with timezone fields appended.
				
		"""
		try:
			throw_if( 'rows', rows )
			if not isinstance( rows, list ):
				raise ValueError( 'rows must be a list of dictionaries.' )
			lat_field_value = lat_field or 'lat'
			lng_field_value = lng_field or 'lng'
			self.rows = rows
			self.lat_field = lat_field_value
			self.lng_field = lng_field_value
			output = [ ]
			for row in self.rows:
				item = dict( row or { } )
				
				try:
					lat_value = item.get( self.lat_field )
					lng_value = item.get( self.lng_field )
					data = self.lookup( lat_value, lng_value )
					
					if not isinstance( data, dict ):
						item[ 'timeZoneId' ] = None
						item[ 'timeZoneName' ] = None
						item[ 'rawOffset' ] = None
						item[ 'dstOffset' ] = None
						item[ 'offset_hours' ] = None
						item[ 'timezone_status' ] = 'not_found'
						item[ 'timezone_error' ] = 'No timezone response returned.'
					
					else:
						raw_offset = data.get( 'rawOffset', 0 ) or 0
						dst_offset = data.get( 'dstOffset', 0 ) or 0
						offset_value = round(
							(float( raw_offset ) + float( dst_offset )) / 3600.0,
							3 )
						
						self.offset = offset_value
						
						item[ 'timeZoneId' ] = data.get( 'timeZoneId' )
						item[ 'timeZoneName' ] = data.get( 'timeZoneName' )
						item[ 'rawOffset' ] = raw_offset
						item[ 'dstOffset' ] = dst_offset
						item[ 'offset_hours' ] = self.offset
						item[ 'timezone_status' ] = data.get( 'status', 'OK' )
						item[ 'timezone_error' ] = None
				
				except Exception as row_error:
					item[ 'timeZoneId' ] = None
					item[ 'timeZoneName' ] = None
					item[ 'rawOffset' ] = None
					item[ 'dstOffset' ] = None
					item[ 'offset_hours' ] = None
					item[ 'timezone_status' ] = 'error'
					item[ 'timezone_error' ] = str( row_error )
				
				output.append( item )
			
			return output
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Timezone'
			exception.method = 'batch_lookup( self, rows: list, lat_field: str=lat, lng_field: str=lng )'
			raise exception
'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                excel.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="excel.py" company="Terry D. Eppler">

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
    excel.py
  </summary>
  ******************************************************************************************
  '''
from typing import Optional, Dict, List
import pandas as pd
from caches import BaseCache
from geocode import Geocoder
from maps import Maps
from places import Place
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

class Excel:
	"""
	
        Purpose:
        Read and write spreadsheets while enriching location rows using Google
        Maps APIs. Keeps original columns; appends geocode outputs, row-level
        status, row-level errors, and summary metrics.

        Parameters:
        api_key (str): Google Maps Platform API key.
        cache (Optional[BaseCache]): Optional cache for memoization.

        Returns:
        Excel helper with file-based and DataFrame-first enrichment entry points.
        
    """
	api_key: str
	maps: Optional[ Maps ]
	geocoder: Optional[ Geocoder ]
	places: Optional[ Place ]
	input_path: Optional[ str ]
	output_path: Optional[ str ]
	dataframe: Optional[ pd.DataFrame ]
	worksheet: Optional[ str ]
	output: Optional[ Dict[ str, List ] ]
	address: Optional[ str ]
	cache: Optional[ BaseCache ]
	file_path: Optional[ str ]
	last_summary: Optional[ Dict ]
	city: Optional[ str ]
	state: Optional[ str ]
	country: Optional[ str ]
	
	def __init__( self, api: str, cache: Optional[ BaseCache ] = None ) -> None:
		throw_if( 'api', api )
		self.api_key = api
		self.cache = cache
		self.maps = Maps( api_key=self.api_key )
		self.geocoder = Geocoder( self.maps, cache=self.cache )
		self.places = Place( self.maps, cache=self.cache )
		self.input_path = None
		self.output_path = None
		self.dataframe = None
		self.worksheet = None
		self.output = None
		self.address = None
		self.file_path = None
		self.last_summary = None
		self.city = None
		self.state = None
		self.country = None
	
	def read( self, path: str, sheet: Optional[ str ] ) -> pd.DataFrame:
		"""

            Purpose:
            Robustly read CSV/XLSX and preserve strings, including leading zeros.

            Parameters:
            path (str): Input file path, either .csv or .xlsx.
            sheet (Optional[str]): Optional sheet name for Excel.

            Returns:
            pd.DataFrame: DataFrame with dtype=str for string-like columns.

        """
		try:
			throw_if( 'path', path )
			
			path_value = path
			sheet_value = sheet
			
			self.file_path = path_value
			self.worksheet = sheet_value
			
			if self.file_path.lower( ).endswith( '.csv' ):
				self.dataframe = pd.read_csv( self.file_path, dtype=str )
			else:
				self.dataframe = pd.read_excel(
					self.file_path,
					sheet_name=self.worksheet or 0,
					dtype=str )
			
			for column in self.dataframe.columns:
				if self.dataframe[ column ].dtype == object:
					self.dataframe[ column ] = (
							self.dataframe[ column ]
							.fillna( '' )
							.astype( str )
							.str.strip( )
					)
			
			return self.dataframe
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'read( self, path: str, sheet: Optional[ str ] )'
			raise exception
	
	def write( self, df: pd.DataFrame, path: str, sheet: Optional[ str ] ) -> None:
		"""

	        Purpose:
	            Write CSV/XLSX with index suppressed.

	        Parameters:
	            df (pd.DataFrame):
	                Data to persist.
	            path (str):
	                Output path, either .csv or .xlsx.
	            sheet (Optional[str]):
	                Optional Excel sheet name.

	        Returns:
	            None.

        """
		try:
			throw_if( 'df', df )
			throw_if( 'path', path )
			
			path_value = path
			sheet_value = sheet or 'Sheet1'
			dataframe_value = df.copy( )
			
			self.file_path = path_value
			self.dataframe = dataframe_value
			self.worksheet = sheet_value
			
			if self.file_path.lower( ).endswith( '.csv' ):
				self.dataframe.to_csv( self.file_path, index=False )
			else:
				self.dataframe.to_excel(
					self.file_path,
					index=False,
					sheet_name=self.worksheet )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'write( self, df: pd.DataFrame, path: str, sheet: Optional[ str ] )'
			raise exception
	
	def create_outputs( self ) -> Dict[ str, List ]:
		"""

			Purpose:
				Create the standard geocode enrichment output-column container.

			Parameters:
				None.

			Returns:
				Dict[str, List]:
					Dictionary of output column names and empty value lists.

		"""
		try:
			return {
					'formatted_address': [ ],
					'lat': [ ],
					'lng': [ ],
					'place_id': [ ],
					'types': [ ],
					'country_code': [ ],
					'country_name': [ ],
					'admin_level_1': [ ],
					'admin_level_2': [ ],
					'locality': [ ],
					'postal_code': [ ],
					'geocode_status': [ ],
					'geocode_error': [ ],
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'create_outputs( self )'
			raise exception
	
	def append_empty( self, outputs: Dict[ str, List ], status: str = 'skipped_empty',
			error: Optional[ str ] = None ) -> None:
		"""

			Purpose:
				Append an empty geocode result to the output container.

			Parameters:
				outputs (Dict[str, List]):
					Output column container.
				status (str):
					Row-level geocode status.
				error (Optional[str]):
					Optional row-level error message.

			Returns:
				None.

		"""
		try:
			throw_if( 'outputs', outputs )
			
			outputs[ 'formatted_address' ].append( None )
			outputs[ 'lat' ].append( None )
			outputs[ 'lng' ].append( None )
			outputs[ 'place_id' ].append( None )
			outputs[ 'types' ].append( None )
			outputs[ 'country_code' ].append( None )
			outputs[ 'country_name' ].append( None )
			outputs[ 'admin_level_1' ].append( None )
			outputs[ 'admin_level_2' ].append( None )
			outputs[ 'locality' ].append( None )
			outputs[ 'postal_code' ].append( None )
			outputs[ 'geocode_status' ].append( status or 'skipped_empty' )
			outputs[ 'geocode_error' ].append( error )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'append_empty( self, outputs: Dict[ str, List ], status: str=skipped_empty )'
			raise exception
	
	def append_result( self, outputs: Dict[ str, List ], result: Dict,
			status: str, error: Optional[ str ] = None ) -> None:
		"""

			Purpose:
				Append a geocode result dictionary to the output container.

			Parameters:
				outputs (Dict[str, List]):
					Output column container.
				result (Dict):
					Flattened geocode or Places result.
				status (str):
					Row-level status.
				error (Optional[str]):
					Optional row-level error message.

			Returns:
				None.

		"""
		try:
			throw_if( 'outputs', outputs )
			
			result_value = result or { }
			status_value = status or 'not_found'
			
			outputs[ 'formatted_address' ].append( result_value.get( 'formatted_address' ) )
			outputs[ 'lat' ].append( result_value.get( 'lat' ) )
			outputs[ 'lng' ].append( result_value.get( 'lng' ) )
			outputs[ 'place_id' ].append( result_value.get( 'place_id' ) )
			outputs[ 'types' ].append( result_value.get( 'types' ) )
			outputs[ 'country_code' ].append( result_value.get( 'country_code' ) )
			outputs[ 'country_name' ].append( result_value.get( 'country_name' ) )
			outputs[ 'admin_level_1' ].append( result_value.get( 'admin_level_1' ) )
			outputs[ 'admin_level_2' ].append( result_value.get( 'admin_level_2' ) )
			outputs[ 'locality' ].append( result_value.get( 'locality' ) )
			outputs[ 'postal_code' ].append( result_value.get( 'postal_code' ) )
			outputs[ 'geocode_status' ].append( status_value )
			outputs[ 'geocode_error' ].append( error )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'append_result( self, outputs: Dict[ str, List ], result: Dict, status: str )'
			raise exception
	
	def summarize( self, df: pd.DataFrame ) -> Dict:
		"""

			Purpose:
				Build summary metrics for the most recent enrichment result.

			Parameters:
				df (pd.DataFrame):
					Enriched DataFrame.

			Returns:
				Dict:
					Summary metrics.

		"""
		try:
			throw_if( 'df', df )
			
			status_counts = { }
			
			if 'geocode_status' in df.columns:
				status_counts = df[ 'geocode_status' ].value_counts( dropna=False ).to_dict( )
			
			summary = {
					'rows_total': int( len( df ) ),
					'rows_ok': int( status_counts.get( 'ok', 0 ) ),
					'rows_ok_places': int( status_counts.get( 'ok_places', 0 ) ),
					'rows_not_found': int( status_counts.get( 'not_found', 0 ) ),
					'rows_skipped_empty': int( status_counts.get( 'skipped_empty', 0 ) ),
					'rows_error': int( status_counts.get( 'error', 0 ) ),
					'status_counts': status_counts,
			}
			
			self.last_summary = summary
			
			return self.last_summary
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'summarize( self, df: pd.DataFrame )'
			raise exception
	
	def detect_columns( self, df: pd.DataFrame ) -> Dict:
		"""

			Purpose:
				Suggest likely address, city, state, and country columns from a
				DataFrame's column names.

			Parameters:
				df (pd.DataFrame):
					DataFrame to inspect.

			Returns:
				Dict:
					Suggested column names.

		"""
		try:
			throw_if( 'df', df )
			
			columns = list( df.columns )
			lower_map = { str( column ).strip( ).lower( ): column for column in columns }
			
			def find_first( names: List[ str ] ) -> Optional[ str ]:
				for name in names:
					if name in lower_map:
						return lower_map[ name ]
				return None
			
			return {
					'address': find_first(
						[
								'address',
								'street address',
								'full address',
								'location',
								'mailing address'
						] ),
					'city': find_first(
						[
								'city',
								'town',
								'locality',
								'municipality'
						] ),
					'state': find_first(
						[
								'state',
								'st',
								'province',
								'region',
								'admin_level_1'
						] ),
					'country': find_first(
						[
								'country',
								'country_code',
								'cntry',
								'nation'
						] )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'detect_columns( self, df: pd.DataFrame )'
			raise exception
	
	def resolve_address( self, address: str, country: Optional[ str ] = None ) -> Dict:
		"""

			Purpose:
				Resolve one free-form address using Geocoder first and Places fallback.

			Parameters:
				address (str):
					Free-form address text.
				country (Optional[str]):
					Optional ISO-2 country bias.

			Returns:
				Dict:
					Dictionary with result, status, and error fields.

		"""
		try:
			throw_if( 'address', address )
			
			address_value = str( address ).strip( )
			country_value = str( country or 'US' ).strip( ).upper( )
			
			self.address = address_value
			self.country = country_value
			
			try:
				result = self.geocoder.freeform( self.address, country=self.country )
				return {
						'result': result or { },
						'status': 'ok',
						'error': None
				}
			
			except Exception as geocode_error:
				try:
					result = self.places.text_to_location( self.address, country=self.country )
					return {
							'result': result or { },
							'status': 'ok_places',
							'error': None
					}
				
				except Exception as places_error:
					return {
							'result': { },
							'status': 'not_found',
							'error': f'{geocode_error}; {places_error}'
					}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'resolve_address( self, address: str, country: Optional[ str ]=None )'
			raise exception
	
	def resolve_city_state_country( self, city: str, state: Optional[ str ],
			country: str ) -> Dict:
		"""

			Purpose:
				Resolve one city/state/country row using Geocoder first and Places
				fallback.

			Parameters:
				city (str):
					City or locality value.
				state (Optional[str]):
					State, province, region, or territory value.
				country (str):
					Country name or ISO-2 country code.

			Returns:
				Dict:
					Dictionary with result, status, and error fields.

		"""
		try:
			city_value = str( city or '' ).strip( )
			state_value = str( state or '' ).strip( )
			country_value = str( country or '' ).strip( )
			
			if not any( [ city_value, state_value, country_value ] ):
				return {
						'result': { },
						'status': 'skipped_empty',
						'error': None
				}
			
			self.city = city_value
			self.state = state_value
			self.country = country_value
			
			try:
				result = self.geocoder.city_state_country(
					self.city,
					self.state,
					self.country )
				return {
						'result': result or { },
						'status': 'ok',
						'error': None
				}
			
			except Exception as geocode_error:
				query = ', '.join(
					[ value for value in [ self.city, self.state, self.country ] if value ] )
				
				try:
					result = self.places.text_to_location( query, country=self.country )
					return {
							'result': result or { },
							'status': 'ok_places',
							'error': None
					}
				
				except Exception as places_error:
					return {
							'result': { },
							'status': 'not_found',
							'error': f'{geocode_error}; {places_error}'
					}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'resolve_city_state_country( self, city: str, state: Optional[ str ], country: str )'
			raise exception
	
	def enrich_from_address( self, inpath: str, outpath: str, address: str, sheet: Optional[ str ],
			cntry: Optional[ str ] ) -> pd.DataFrame:
		"""
            Purpose:
                Enrich a file containing a single free-form address column, adding
                lat/lng, place_id, canonical components, status, and error fields.

            Parameters:
                inpath (str):
                    Path to input CSV/XLSX with an address column.
                outpath (str):
                    Output path to write enriched file.
                address (str):
                    Column name containing free-form addresses.
                sheet (Optional[str]):
                    Excel sheet name if .xlsx.
                cntry (Optional[str]):
                    Optional column containing ISO-2 country bias codes.

            Returns:
                pd.DataFrame:
                    Enriched DataFrame. The output file is still written.
        """
		try:
			throw_if( 'inpath', inpath )
			throw_if( 'outpath', outpath )
			throw_if( 'address', address )
			
			self.input_path = inpath
			self.output_path = outpath
			self.address = address
			self.worksheet = sheet
			self.country = cntry
			
			df = self.read( self.input_path, self.worksheet )
			
			if self.address not in df.columns:
				raise ValueError( f'Address column "{self.address}" was not found.' )
			
			outputs = self.create_outputs( )
			resolved = { }
			
			for _, row in df.iterrows( ):
				addr = str( row.get( self.address ) or '' ).strip( )
				
				if not addr:
					self.append_empty( outputs )
					continue
				
				hint = (
						str( row.get( self.country ) or '' ).strip( ).upper( )
						if (self.country and self.country in df.columns)
						else 'US'
				)
				cache_key = f'{addr}::{hint}'
				
				if cache_key not in resolved:
					resolved[ cache_key ] = self.resolve_address( addr, country=hint )
				
				item = resolved[ cache_key ]
				self.append_result(
					outputs,
					item.get( 'result', { } ),
					item.get( 'status', 'not_found' ),
					item.get( 'error' ) )
			
			for key, values in outputs.items( ):
				df[ key ] = values
			
			self.dataframe = df
			self.output = outputs
			self.summarize( self.dataframe )
			self.write( self.dataframe, self.output_path, self.worksheet )
			
			return self.dataframe
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'enrich_from_address( self, **kwargs )'
			raise exception
	
	def enrich( self, inpath: str, outpath: str, city: str, state: Optional[ str ], cntry: str,
			sheet: Optional[ str ] = None, ) -> pd.DataFrame:
		"""

			Purpose:
			Enrich a file with City, State/Region, and Country columns by appending
			lat/lng, place_id, canonical components, status, and error fields.
	
			Parameters:
			inpath (str): Input CSV/XLSX path containing location columns.
			outpath (str): Output CSV/XLSX path to write enriched results.
			city (str): Column for city/locality.
			state (Optional[str]): Column for state/region.
			cntry (str): Column for country name or ISO-2 code.
			sheet (Optional[str]): Excel sheet name if .xlsx.
	
			Returns:
			pd.DataFrame: Enriched DataFrame. The output file is still written.

		"""
		try:
			throw_if( 'inpath', inpath )
			throw_if( 'outpath', outpath )
			throw_if( 'city', city )
			throw_if( 'cntry', cntry )
			
			self.input_path = inpath
			self.output_path = outpath
			self.city = city
			self.state = state
			self.country = cntry
			self.worksheet = sheet
			
			df = self.read( self.input_path, self.worksheet )
			
			if self.city not in df.columns:
				raise ValueError( f'City column "{self.city}" was not found.' )
			
			if self.country not in df.columns:
				raise ValueError( f'Country column "{self.country}" was not found.' )
			
			if self.state and self.state not in df.columns:
				raise ValueError( f'State column "{self.state}" was not found.' )
			
			outputs = self.create_outputs( )
			resolved = { }
			
			for _, row in df.iterrows( ):
				city_value = str( row.get( self.city ) or '' ).strip( )
				state_value = (
						str( row.get( self.state ) or '' ).strip( )
						if (self.state and self.state in df.columns)
						else ''
				)
				country_value = str( row.get( self.country ) or '' ).strip( )
				
				if not any( [ city_value, state_value, country_value ] ):
					self.append_empty( outputs )
					continue
				
				cache_key = f'{city_value}::{state_value}::{country_value}'
				
				if cache_key not in resolved:
					resolved[ cache_key ] = self.resolve_city_state_country(
						city_value,
						state_value,
						country_value )
				
				item = resolved[ cache_key ]
				self.append_result(
					outputs,
					item.get( 'result', { } ),
					item.get( 'status', 'not_found' ),
					item.get( 'error' ) )
			
			for key, values in outputs.items( ):
				df[ key ] = values
			
			self.dataframe = df
			self.output = outputs
			self.summarize( self.dataframe )
			self.write( self.dataframe, self.output_path, self.worksheet )
			
			return self.dataframe
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'Excel'
			exception.method = 'enrich( self, **kwargs)'
			raise exception
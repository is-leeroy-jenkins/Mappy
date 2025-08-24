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
"""
Purpose:
    Spreadsheet helper that enriches a sheet of locations with coordinates and
    canonical addresses using the Geocoding API.

Parameters:
    api_key (str):
        Google Maps Platform API key for constructing services internally.
    cache (Optional[BaseCache]):
        Optional cache to cut repeat lookups across runs.

Returns:
    Excel with enrichment methods for either full-address or city/state/country.
"""
from typing import Optional, Dict, List
import pandas as pd
from .caches import BaseCache
from .geocode import Geocoder
from .maps import Maps
from .places import Places
from boogr import Error, ErrorDialog


def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )



class Excel:
	"""
	
        Purpose:
        Read and write spreadsheets while enriching location rows using Google
        Maps APIs. Keeps original columns; appends geocode outputs.

        Parameters:
        api_key (str): Google Maps Platform API key.
        cache (Optional[BaseCache]): Optional cache for memoization.

        Returns: Excel helper with two enrichment entry points.
        
    """
	api_key: str
	maps: Optional[ Maps ]
	geocoder: Optional[ Geocoder ]
	places: Optional[ Places ]
	input_path: Optional[ str ]
	output_path: Optional[ str ]
	dataframe: Optional[ pd.DataFrame ]
	worksheet: Optional[ str ]
	output: Optional[ Dict[ str, List ] ]
	address: Optional[ str ]
	cache: Optional[ BaseCache ]
	file_path: Optional[ str ]
	

	def __init__( self, api: str, cache: Optional[ BaseCache ] = None ) -> None:
		self.api_key = api
		self.cache = cache
		self.maps = Maps( api_key=self.api_key )
		self.geocoder = Geocoder( self.maps, cache=self.cache )
		self.places = Places( self.maps, cache=self.cache )


	def read( self, path: str, sheet: Optional[ str ] ) -> pd.DataFrame:
		"""

            Purpose:
            Robustly read CSV/XLSX and preserve strings (e.g., leading zeros).

            Parameters:
            path (str): Input file path (.csv or .xlsx).
            sheet (Optional[str]): Optional sheet name for Excel.

            Returns: DataFrame with dtype=str for string-like columns.

        """
		if path.lower( ).endswith( '.csv' ):
			self.dataframe = pd.read_csv( path, dtype = str )
		else:
			self.dataframe = pd.read_excel( path, sheet_name=sheet, dtype=str )

		for c in self.dataframe.columns:
			if self.dataframe[ c ].dtype == object:
				self.dataframe[ c ] = self.dataframe[ c ].fillna( "" ).astype( str ).str.strip( )

		return self.dataframe


	def write( self, df: pd.DataFrame, path: str, sheet: Optional[ str ] ) -> None:
		"""

	        Purpose:
	            Write CSV/XLSX with index suppressed.

	        Parameters:
	            df (pd.DataFrame):
	                Data to persist.
	            path (str):
	                Output path (.csv or .xlsx).
	            sheet (Optional[str]):
	                Optional Excel sheet name.

	        Returns:
	            None.

        """
		self.file_path = path
		self.dataframe = df.copy( )
		if self.file_path.lower( ).endswith( '.csv' ):
			self.dataframe.to_csv( self.file_path, index=False )
		else:
			self.dataframe.to_excel( self.file_path, index=False, sheet_name=sheet )


	def enrich_from_address( self, inpath: str, outpath: str, address: str, sheet: Optional[ str ],
	                         cntry: Optional[ str ] ) -> None:
		"""
            Purpose:
                Enrich a file containing a single free-form address column, adding
                lat/lng, place_id, and canonical components.

            Parameters:
                inpath (str):
                    Path to input CSV/XLSX with an address column.
                outpath (str):
                    Output path to write enriched file.
                address (str):
                    Column name containing free-form addresses.
                sheet (Optional[str]):
                    Excel sheet name (if .xlsx).
                cntry (Optional[str]):
                    Optional column containing ISO-2 country bias codes.

            Returns:
                None. Writes the enriched file.
        """
		df = self.read( inpath, sheet )
		outputs = \
		{
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
		}

		for _, row in df.iterrows( ):
			addr = (row.get( address ) or "").strip( )
			hint = (
					((row.get( cntry ) or "").strip( ).upper( ))
					if (cntry and cntry in df.columns)
					else None
			)
			if not addr:
				for k in outputs:
					outputs[ k ].append( None if k != 'geocode_status' else 'skipped_empty' )
				continue

			try:
				g = self.geocoder.freeform( addr, country = hint )
				status = 'ok'
			except Exception:
				# Fallback via Places for stubborn inputs
				try:
					g = self.places.text_to_location( addr, country = hint )
					status = "ok_places"
				except Exception:
					g = { }
					status = "not_found"

			outputs[ 'formatted_address' ].append( g.get( 'formatted_address' ) )
			outputs[ 'lat' ].append( g.get( 'lat' ) )
			outputs[ 'lng' ].append( g.get( 'lng' ) )
			outputs[ 'place_id' ].append( g.get( 'place_id' ) )
			outputs[ 'types' ].append( g.get( 'types' ) )
			outputs[ 'country_code' ].append( g.get( 'country_code' ) )
			outputs[ 'country_name' ].append( g.get( 'country_name' ) )
			outputs[ 'admin_level_1' ].append( g.get( 'admin_level_1' ) )
			outputs[ 'admin_level_2' ].append( g.get( 'admin_level_2' ) )
			outputs[ 'locality' ].append( g.get( 'locality' ) )
			outputs[ 'postal_code' ].append( g.get( 'postal_code' ) )
			outputs[ 'geocode_status' ].append( status )

		for k, v in outputs.items( ):
			df[ k ] = v

		self.write( df, outpath, sheet )

	def enrich( self, inpath: str, outpath: str, city: str, state: Optional[ str ], cntry: str,
	            sheet: Optional[ str ]=None, ) -> None:
		"""

	            Purpose:
                Enrich a file with (City, State/Region, Country) columns by appending
                lat/lng, place_id, and standardized components.

	            Parameters:
                inpath (str): Input CSV/XLSX path containing location columns.
                outpath (str): Output CSV/XLSX path to write enriched results.
                city (str): Column for city/locality.
                state (Optional[str]): Column for state/region (optional/not required).
                cntry (str): Column for country (name or ISO-2 code).
                sheet (Optional[str]): Excel sheet name (if .xlsx).

	            Returns:
                None. Writes the enriched file.

            """
		try:
			throw_if( 'inpath', inpath )
			df = self.read( inpath, sheet )
			outputs = \
			{
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
			}

			for _, row in df.iterrows( ):
				city = (row.get( city ) ).strip( )
				state = (row.get( state ) ).strip( ) if (
						state and state in df.columns) else ""
				country = (row.get( cntry ) ).strip( )

				if not any( [ city, state, country ] ):
					for k in outputs:
						outputs[ k ].append( None if k != 'geocode_status' else 'skipped_empty' )
					continue

				try:
					g = self._geocoder.city_state_country( city, state, country )
					status = 'ok'
				except Exception:
					query = ', '.join( [ p for p in [ city, state, country ] if p ] )
					try:
						g = self._places.text_to_location( query, country = country )
						status = 'ok_places'
					except Exception:
						g = { }
						status = 'not_found'

				outputs[ 'formatted_address' ].append( g.get( 'formatted_address' ) )
				outputs[ 'lat' ].append( g.get( 'lat' ) )
				outputs[ 'lng' ].append( g.get( 'lng' ) )
				outputs[ 'place_id' ].append( g.get( 'place_id' ) )
				outputs[ 'types' ].append( g.get( 'types' ) )
				outputs[ 'country_code' ].append( g.get( 'country_code' ) )
				outputs[ 'country_name' ].append( g.get( 'country_name' ) )
				outputs[ 'admin_level_1' ].append( g.get( 'admin_level_1' ) )
				outputs[ 'admin_level_2' ].append( g.get( 'admin_level_2' ) )
				outputs[ 'locality' ].append( g.get( 'locality' ) )
				outputs[ 'postal_code' ].append( g.get( 'postal_code' ) )
				outputs[ 'geocode_status' ].append( status )

			for k, v in outputs.items( ):
				df[ k ] = v

			self._write( df, outpath, sheet )
		except Exception as e:
			exception = Error( e )
			exception.module = ''
			exception.cause = ''
			exception.method = ''
			error = ErrorDialog( exception )
			error.show( )

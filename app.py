'''
******************************************************************************************
 Assembly:                Mappy
 Filename:                app.py
 Author:                  Terry D. Eppler (framework) / Assistant (Streamlit UI)
 Created:                 12-27-2025
******************************************************************************************

Purpose:
    Streamlit application exposing Mappy geospatial functionality:
        - Geocoding
        - Places Text Search fallback
        - Distance Matrix
        - Static Maps
        - Time Zone lookup
        - Excel / CSV enrichment

CRITICAL ASSUMPTIONS (VERIFIED):
    - Flat project layout (no package directory)
    - Maps.__init__(api_key, qps)
    - Places.text_to_location(...) is the ONLY Places lookup method
    - Cache is injected ONLY into services that support it
******************************************************************************************
'''

from __future__ import annotations

from exceptions import NotFound
import os
from typing import Optional
import matplotlib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import sqlite3
import re
import datetime as dt
from typing import Optional
import time
from pathlib import Path
import config as cfg
from maps import Maps
from typing import Any, Optional, Dict, List, Tuple
from geocode import Geocoder
from places import Places
from distances import DistanceMatrix
from timezones import Timezone
from staticmaps import StaticMapURL
from excel import Excel
from caches import InMemoryCache, SQLiteCache
from fetchers import (
	GoogleWeather,
	OpenWeather,
	HistoricalWeather,
	ClimateData,
	TidesAndCurrents,
	AirNow,
	UvIndex,
	OpenAQ,
	PurpleAir,
	EnviroFacts,
	Firms,
	EoNet,
	USGSEarthquakes,
	USGSWaterData,
	USGSTheNationalMap,
	GlobalImagery,
	NavalObservatory,
	SatelliteCenter,
	SpaceWeather,
	AstroCatalog,
	AstroQuery,
	StarMap,
	StarChart
)

# ---------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------

if 'mode' not in st.session_state:
	st.session_state[ 'mode' ] = 'Geocoding'

if 'previous_mode' not in st.session_state:
	st.session_state[ 'previous_mode' ] = ''
	
if 'source' not in st.session_state:
	st.session_state[ 'source' ] = ''

if 'df_source' not in st.session_state:
	st.session_state[ 'df_source' ] = pd.DataFrame( )

if 'df_frame' not in st.session_state:
	st.session_state[ 'df_frame' ] = pd.DataFrame( )

if 'df_original' not in st.session_state:
	st.session_state[ 'df_original' ] = pd.DataFrame( )
	
if 'df_raw' not in st.session_state:
	st.session_state[ 'df_raw' ] = pd.DataFrame( )
	
if 'df_dataset' not in st.session_state:
	st.session_state[ 'df_dataset' ] = pd.DataFrame( )

if 'pipeline_log' not in st.session_state:
	st.session_state[ 'pipeline_log' ] = [ ]

if 'coordinates' not in st.session_state:
	st.session_state[ 'coordinates' ] = None

if 'location' not in st.session_state:
	st.session_state[ 'location' ] = ''

if 'country' not in st.session_state:
	st.session_state[ 'country' ] = ''

if 'state' not in st.session_state:
	st.session_state[ 'state' ] = ''

if 'city' not in st.session_state:
	st.session_state[ 'city' ] = ''

if 'description' not in st.session_state:
	st.session_state[ 'description' ] = ''

if 'date' not in st.session_state:
	st.session_state[ 'date' ] = ''

# ---------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------

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
	
def style_subheaders( ) -> None:
	"""
	
		Purpose:
		_________
		Sets the style of subheaders in the main UI
		
	"""
	st.markdown(
		"""
		<style>
		div[data-testid="stMarkdownContainer"] h2,
		div[data-testid="stMarkdownContainer"] h3,
		div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] h2,
		div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] h3 {
			color: rgb(0, 120, 252) !important;
		}
		</style>
		""",
		unsafe_allow_html=True, )

def init_state( key: str, value: Any ) -> None:
	"""
		
		Purpose:
		--------
		Initialize a Streamlit session-state key only when the key is not already present.
	
		Parameters:
		-----------
		key (str): Session-state key to initialize.
		value (Any): Default value assigned only when the key is absent.
	
		Returns:
		--------
		None
		
	"""
	if key not in st.session_state:
		st.session_state[ key ] = value

def init_env_state( key: str, config_name: str, env_name: str ) -> None:
	"""
		
		Purpose:
		--------
		Initialize a session-state API/configuration key from config.py and mirror the value to
		os.environ when a configured value exists.
	
		Parameters:
		-----------
		key (str): Session-state key to initialize.
		config_name (str): Attribute name to read from config.py.
		env_name (str): Environment variable name to assign.
	
		Returns:
		--------
		None
		
	"""
	init_state( key, '' )
	if st.session_state.get( key, '' ) == '':
		default = getattr( cfg, config_name, '' )
		if default:
			st.session_state[ key ] = default
			os.environ[ env_name ] = default

def normalize( obj ):
	if obj is None or isinstance( obj, (str, int, float, bool) ):
		return obj
	
	if isinstance( obj, dict ):
		return { k: normalize( v ) for k, v in obj.items( ) }
	
	if isinstance( obj, (list, tuple, set) ):
		return [ normalize( v ) for v in obj ]
	if hasattr( obj, "model_dump" ):
		try:
			return obj.model_dump( )
		except Exception:
			return str( obj )
	return str( obj )

def set_blue_divider( ) -> None:
	st.markdown( cfg.BLUE_DIVIDER, unsafe_allow_html=True )

def log_step( msg: str ) -> None:
	st.session_state.pipeline_log.append( msg )

# ------------ DATABASE UTILITIES

def initialize_database( ) -> None:
	"""
		Purpose:
		--------
		Ensure required SQLite tables exist and that the Prompts table contains the
		columns required by the prompt utilities and Prompt Engineering mode.

		Parameters:
		-----------
		None

		Returns:
		--------
		None
	"""
	Path( 'stores/sqlite' ).mkdir( parents=True, exist_ok=True )
	with sqlite3.connect( cfg.DB_PATH ) as conn:
		conn.execute(
			"""
            CREATE TABLE IF NOT EXISTS chat_history
            (
                id
                INTEGER
                PRIMARY
                KEY
                AUTOINCREMENT,
                role
                TEXT,
                content
                TEXT
            )
			"""
		)
		
		conn.execute(
			"""
            CREATE TABLE IF NOT EXISTS embeddings
            (
                id
                INTEGER
                PRIMARY
                KEY
                AUTOINCREMENT,
                chunk
                TEXT,
                vector
                BLOB
            )
			"""
		)
		
		conn.execute(
			"""
            CREATE TABLE IF NOT EXISTS Prompts
            (
                PromptsId
                INTEGER
                NOT
                NULL
                PRIMARY
                KEY
                AUTOINCREMENT,
                Caption
                TEXT,
                Name
                TEXT
            (
                80
            ),
                Text TEXT,
                Version TEXT
            (
                80
            ),
                ID TEXT
            (
                80
            )
                )
			"""
		)
		
		prompt_columns = [ row[ 1 ] for row in
		                   conn.execute( 'PRAGMA table_info("Prompts");' ).fetchall( ) ]
		
		if 'Caption' not in prompt_columns:
			conn.execute( 'ALTER TABLE "Prompts" ADD COLUMN "Caption" TEXT;' )
		
		conn.commit( )

def create_connection( ) -> sqlite3.Connection:
	return sqlite3.connect( cfg.DB_PATH )

def list_tables( ) -> List[ str ]:
	with create_connection( ) as conn:
		_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
		rows = conn.execute( _query ).fetchall( )
		return [ r[ 0 ] for r in rows ]

def create_schema( table: str ) -> List[ Tuple ]:
	with create_connection( ) as conn:
		return conn.execute( f'PRAGMA table_info("{table}");' ).fetchall( )

def read_table( table: str, limit: int = None, offset: int = 0 ) -> pd.DataFrame:
	"""
	
		Purpose:
		--------
		Read a SQLite table into a pandas DataFrame using a normalized scalar-only path.
	
		Parameters:
		-----------
		table : str
			Table name.
		limit : int = None
			Optional row limit.
		offset : int = 0
			Optional row offset.
	
		Returns:
		--------
		pd.DataFrame
			DataFrame of plain Python scalar values.
	
	"""
	if not table:
		return pd.DataFrame( )
	
	query = f'SELECT * FROM "{table}"'
	if limit:
		query += f' LIMIT {int( limit )} OFFSET {int( offset )}'
	
	with create_connection( ) as conn:
		cur = conn.cursor( )
		cur.execute( query )
		
		raw_columns = [ d[ 0 ] for d in (cur.description or [ ]) ]
		rows = cur.fetchall( )
	
	seen: Dict[ str, int ] = { }
	columns: List[ str ] = [ ]
	
	for col in raw_columns:
		name = str( col )
		if name not in seen:
			seen[ name ] = 0
			columns.append( name )
		else:
			seen[ name ] += 1
			columns.append( f'{name}_{seen[ name ]}' )
	
	def _scalarize( value: Any ) -> Any:
		if value is None or isinstance( value, (str, int, float, bool) ):
			return value
		
		if isinstance( value, bytes ):
			try:
				return value.decode( 'utf-8' )
			except Exception:
				return value.hex( )
		
		if isinstance( value, (list, tuple, set, dict) ):
			try:
				return str( normalize( value ) )
			except Exception:
				return str( value )
		
		if hasattr( value, 'model_dump' ):
			try:
				return str( value.model_dump( ) )
			except Exception:
				return str( value )
		
		return str( value )
	
	normalized_rows: List[ Dict[ str, Any ] ] = [ ]
	for row in rows:
		record: Dict[ str, Any ] = { }
		for idx, col in enumerate( columns ):
			record[ col ] = _scalarize( row[ idx ] )
		normalized_rows.append( record )
	
	return pd.DataFrame( normalized_rows, columns=columns )

def render_table( df: pd.DataFrame ) -> None:
	"""
	
		Purpose:
		--------
		Render a DataFrame safely in Streamlit. Use the normal interactive dataframe
		first, and fall back to HTML rendering if Streamlit/PyArrow serialization fails.
	
		Parameters:
		-----------
		df : pd.DataFrame
			The DataFrame to render.
	
		Returns:
		--------
		None
	
	"""
	if df is None:
		st.info( 'No data available.' )
		return
	
	try:
		st.data_editor( df, use_container_width=True )
		return
	except Exception:
		pass
	
	fallback_df = df.copy( )
	fallback_df = fallback_df.where( pd.notnull( fallback_df ), '' )
	
	for col in fallback_df.columns:
		fallback_df[ col ] = fallback_df[ col ].map(
			lambda x: x if isinstance( x, (str, int, float, bool) ) or x == '' else str( x ) )
	
	st.markdown( fallback_df.to_html( index=False, escape=True ), unsafe_allow_html=True )

def make_display_safe( df: pd.DataFrame ) -> pd.DataFrame:
	display_df = df.copy( )
	
	for col in display_df.columns:
		display_df[ col ] = display_df[ col ].map(
			lambda x: '' if x is None else str( x )
		)
	
	return display_df

def drop_table( table: str ) -> None:
	"""
		Purpose:
		--------
		Safely drop a table if it exists.
	
		Parameters:
		-----------
		table : str
			Table name.
	"""
	if not table:
		return
	
	with create_connection( ) as conn:
		conn.execute( f'DROP TABLE IF EXISTS "{table}";' )
		conn.commit( )

def create_index( table: str, column: str ) -> None:
	"""
		Purpose:
		--------
		Create a safe SQLite index on a specified table column.
	
		Handles:
			- Spaces in column names
			- Special characters
			- Reserved words
			- Duplicate index names
			- Validation against actual table schema
	
		Parameters:
		-----------
		table : str
			Table name.
		column : str
			Column name to index.
	"""
	if not table or not column:
		return
	
	# ------------------------------------------------------------------
	# Validate table exists
	# ------------------------------------------------------------------
	tables = list_tables( )
	if table not in tables:
		raise ValueError( 'Invalid table name.' )
	
	# ------------------------------------------------------------------
	# Validate column exists
	# ------------------------------------------------------------------
	schema = create_schema( table )
	valid_columns = [ col[ 1 ] for col in schema ]
	
	if column not in valid_columns:
		raise ValueError( 'Invalid column name.' )
	
	# ------------------------------------------------------------------
	# Sanitize index name (identifier only)
	# ------------------------------------------------------------------
	safe_index_name = re.sub( r"[^0-9a-zA-Z_]+", "_", f"idx_{table}_{column}" )
	
	# ------------------------------------------------------------------
	# Create index safely (quote identifiers)
	# ------------------------------------------------------------------
	sql = f'CREATE INDEX IF NOT EXISTS "{safe_index_name}" ON "{table}"("{column}");'
	
	with create_connection( ) as conn:
		conn.execute( sql )
		conn.commit( )

def apply_filters( df: pd.DataFrame ) -> pd.DataFrame:
	st.subheader( 'Advanced Filters' )
	conditions = [ ]
	col1, col2, col3 = st.columns( 3 )
	column = col1.selectbox( 'Column', df.columns )
	operator = col2.selectbox( 'Operator', [ '=', '!=', '>', '<', '>=', '<=', 'contains' ] )
	value = col3.text_input( 'Value' )
	if value:
		if operator == '=':
			df = df[ df[ column ] == value ]
		elif operator == '!=':
			df = df[ df[ column ] != value ]
		elif operator == '>':
			df = df[ df[ column ].astype( float ) > float( value ) ]
		elif operator == '<':
			df = df[ df[ column ].astype( float ) < float( value ) ]
		elif operator == '>=':
			df = df[ df[ column ].astype( float ) >= float( value ) ]
		elif operator == '<=':
			df = df[ df[ column ].astype( float ) <= float( value ) ]
		elif operator == 'contains':
			df = df[ df[ column ].astype( str ).str.contains( value ) ]
	
	return df

def create_aggregation( df: pd.DataFrame ):
	st.subheader( 'Aggregation Engine' )
	
	numeric_cols = df.select_dtypes( include=[ 'number' ] ).columns.tolist( )
	
	if not numeric_cols:
		st.info( 'No numeric columns available.' )
		return
	
	col = st.selectbox( 'Column', numeric_cols )
	agg = st.selectbox( 'Aggregation', [ 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'MEDIAN' ] )
	
	if agg == 'COUNT':
		result = df[ col ].count( )
	elif agg == 'SUM':
		result = df[ col ].sum( )
	elif agg == 'AVG':
		result = df[ col ].mean( )
	elif agg == 'MIN':
		result = df[ col ].min( )
	elif agg == 'MAX':
		result = df[ col ].max( )
	elif agg == 'MEDIAN':
		result = df[ col ].median( )
	
	st.metric( 'Result', result )

def create_visualization( df: pd.DataFrame ) -> None:
	"""
	
		Purpose:
		--------
		Render data visualizations without passing pandas objects directly into
		Plotly/Narwhals.
		
		Parameters:
		-----------
		df : pd.DataFrame
			The input DataFrame.
		
		Returns:
		--------
		None
		
	"""
	st.subheader( 'Visualization Engine' )
	
	if df is None or df.empty:
		st.info( 'No data available.' )
		return
	
	df_plot = df.copy( )
	
	for col in df_plot.columns:
		if df_plot[ col ].dtype == object:
			df_plot[ col ] = df_plot[ col ].map(
				lambda x: '' if x is None else str( x )
			)
	
	numeric_cols: List[ str ] = [ ]
	for col in df_plot.columns:
		series_num = pd.to_numeric( df_plot[ col ], errors='coerce' )
		if series_num.notna( ).any( ):
			numeric_cols.append( col )
	
	categorical_cols: List[ str ] = [ col for col in df_plot.columns if col not in numeric_cols ]
	
	chart = st.selectbox(
		'Chart Type',
		[ 'Histogram', 'Bar', 'Line', 'Scatter', 'Box', 'Pie', 'Correlation' ] )
	
	if chart == 'Histogram':
		if not numeric_cols:
			st.info( 'No numeric columns available.' )
			return
		
		col = st.selectbox( 'Column', numeric_cols )
		values = pd.to_numeric( df_plot[ col ], errors='coerce' ).dropna( ).tolist( )
		
		fig = go.Figure( data=[ go.Histogram( x=values ) ] )
		fig.update_layout( xaxis_title=col, yaxis_title='Count' )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Bar':
		if not numeric_cols:
			st.info( 'No numeric columns available.' )
			return
		
		x = st.selectbox( 'X', df_plot.columns )
		y = st.selectbox( 'Y', numeric_cols )
		
		x_values = df_plot[ x ].astype( str ).tolist( )
		y_values = pd.to_numeric( df_plot[ y ], errors='coerce' ).fillna( 0 ).tolist( )
		
		fig = go.Figure( data=[ go.Bar( x=x_values, y=y_values ) ] )
		fig.update_layout( xaxis_title=x, yaxis_title=y )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Line':
		if not numeric_cols:
			st.info( 'No numeric columns available.' )
			return
		
		x = st.selectbox( 'X', df_plot.columns )
		y = st.selectbox( 'Y', numeric_cols )
		
		x_values = df_plot[ x ].astype( str ).tolist( )
		y_values = pd.to_numeric( df_plot[ y ], errors='coerce' ).fillna( 0 ).tolist( )
		
		fig = go.Figure( data=[ go.Scatter( x=x_values, y=y_values, mode='lines' ) ] )
		fig.update_layout( xaxis_title=x, yaxis_title=y )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Scatter':
		if len( numeric_cols ) < 2:
			st.info( 'At least two numeric columns are required.' )
			return
		
		x = st.selectbox( 'X', numeric_cols, key='viz_scatter_x' )
		y = st.selectbox( 'Y', numeric_cols, key='viz_scatter_y' )
		
		x_series = pd.to_numeric( df_plot[ x ], errors='coerce' )
		y_series = pd.to_numeric( df_plot[ y ], errors='coerce' )
		mask = x_series.notna( ) & y_series.notna( )
		
		x_values = x_series[ mask ].tolist( )
		y_values = y_series[ mask ].tolist( )
		
		fig = go.Figure( data=[ go.Scatter( x=x_values, y=y_values, mode='markers' ) ] )
		fig.update_layout( xaxis_title=x, yaxis_title=y )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Box':
		if not numeric_cols:
			st.info( 'No numeric columns available.' )
			return
		
		col = st.selectbox( 'Column', numeric_cols, key='viz_box_col' )
		values = pd.to_numeric( df_plot[ col ], errors='coerce' ).dropna( ).tolist( )
		
		fig = go.Figure( data=[ go.Box( y=values, name=col ) ] )
		fig.update_layout( yaxis_title=col )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Pie':
		if not categorical_cols:
			st.info( 'No categorical columns available.' )
			return
		
		col = st.selectbox( 'Category Column', categorical_cols )
		counts = df_plot[ col ].astype( str ).value_counts( )
		
		fig = go.Figure(
			data=[ go.Pie( labels=counts.index.tolist( ), values=counts.values.tolist( ) ) ] )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Correlation':
		if len( numeric_cols ) < 2:
			st.info( 'At least two numeric columns are required.' )
			return
		
		corr_df = pd.DataFrame( )
		for col in numeric_cols:
			corr_df[ col ] = pd.to_numeric( df_plot[ col ], errors='coerce' )
		
		corr = corr_df.corr( )
		
		fig = go.Figure(
			data=[ go.Heatmap(
				z=corr.values.tolist( ),
				x=corr.columns.tolist( ),
				y=corr.index.tolist( ) ) ] )
		st.plotly_chart( fig, use_container_width=True )

def convert_dataframe( table_name: str, df: pd.DataFrame ):
	columns = [ ]
	for col in df.columns:
		sql_type = get_sqlite_type( df[ col ].dtype )
		safe_col = col.replace( ' ', '_' )
		columns.append( f'{safe_col} {sql_type}' )
	
	create_stmt = f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join( columns )});'
	
	with create_connection( ) as conn:
		conn.execute( create_stmt )
		conn.commit( )

def insert_data( table_name: str, df: pd.DataFrame ):
	df = df.copy( )
	df.columns = [ c.replace( ' ', '_' ) for c in df.columns ]
	
	placeholders = ', '.join( [ '?' ] * len( df.columns ) )
	stmt = f'INSERT INTO {table_name} VALUES ({placeholders});'
	
	with create_connection( ) as conn:
		conn.executemany( stmt, df.values.tolist( ) )
		conn.commit( )

def get_sqlite_type( dtype ) -> str:
	"""
		Purpose:
		--------
		Map a pandas dtype to an appropriate SQLite column type.
	
		Parameters:
		-----------
		dtype : pandas dtype
			The dtype of a pandas Series.
	
		Returns:
		--------
		str
			SQLite column type.
	"""
	dtype_str = str( dtype ).lower( )
	
	# ------------------------------------------------------------------
	# Integer Types (including nullable Int64)
	# ------------------------------------------------------------------
	if 'int' in dtype_str:
		return 'INTEGER'
	
	# ------------------------------------------------------------------
	# Float Types
	# ------------------------------------------------------------------
	if 'float' in dtype_str:
		return 'REAL'
	
	# ------------------------------------------------------------------
	# Boolean
	# ------------------------------------------------------------------
	if 'bool' in dtype_str:
		return 'INTEGER'
	
	# ------------------------------------------------------------------
	# Datetime
	# ------------------------------------------------------------------
	if 'datetime' in dtype_str:
		return 'TEXT'
	
	# ------------------------------------------------------------------
	# Categorical
	# ------------------------------------------------------------------
	if 'category' in dtype_str:
		return 'TEXT'
	
	# ------------------------------------------------------------------
	# Default fallback
	# ------------------------------------------------------------------
	return 'TEXT'

def create_custom_table( table_name: str, columns: list ) -> None:
	"""
		Purpose:
		--------
		Create a custom SQLite table from column definitions.
	
		Parameters:
		-----------
		table_name : str
			Name of table.
	
		columns : list of dict
			[
				{
					"name": str,
					"type": str,
					"not_null": bool,
					"primary_key": bool,
					"auto_increment": bool
				}
			]
	"""
	if not table_name:
		raise ValueError( 'Table name required.' )
	
	# Validate identifier
	if not re.match( r"^[A-Za-z_][A-Za-z0-9_]*$", table_name ):
		raise ValueError( 'Invalid table name.' )
	
	col_defs = [ ]
	
	for col in columns:
		col_name = col[ 'name' ]
		col_type = col[ 'type' ].upper( )
		
		if not re.match( r"^[A-Za-z_][A-Za-z0-9_]*$", col_name ):
			raise ValueError( f"Invalid column name: {col_name}" )
		
		definition = f'"{col_name}" {col_type}'
		
		if col[ 'primary_key' ]:
			definition += ' PRIMARY KEY'
			if col[ 'auto_increment' ] and col_type == 'INTEGER':
				definition += ' AUTOINCREMENT'
		
		if col[ "not_null" ]:
			definition += " NOT NULL"
		
		col_defs.append( definition )
	
	sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join( col_defs )});'
	
	with create_connection( ) as conn:
		conn.execute( sql )
		conn.commit( )

def is_safe_query( query: str ) -> bool:
	"""
	
		Purpose:
		--------
		Determine whether a SQL query is read-only and safe to execute.
	
		Allows:
			SELECT
			WITH (CTE returning SELECT)
			EXPLAIN SELECT
			PRAGMA (read-only)
	
		Blocks:
			INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, ATTACH,
			DETACH, VACUUM, REPLACE, TRIGGER, and multiple statements.
			
	"""
	if not query or not isinstance( query, str ):
		return False
	
	q = query.strip( ).lower( )
	
	# ------------------------------------------------------------------
	# Block multiple statements
	# ------------------------------------------------------------------
	if ';' in q[ :-1 ]:
		return False
	
	# ------------------------------------------------------------------
	# Remove SQL comments
	# ------------------------------------------------------------------
	q = re.sub( r"--.*?$", "", q, flags=re.MULTILINE )
	q = re.sub( r"/\*.*?\*/", "", q, flags=re.DOTALL )
	q = q.strip( )
	
	# ------------------------------------------------------------------
	# Allowed starting keywords
	# ------------------------------------------------------------------
	allowed_starts = ('select', 'with', 'explain', 'pragma')
	if not q.startswith( allowed_starts ):
		return False
	
	# ------------------------------------------------------------------
	# Block dangerous keywords anywhere
	# ------------------------------------------------------------------
	blocked_keywords = ('insert ', 'update ', 'delete ', 'drop ', 'alter ',
	                    'create ', 'attach ', 'detach ', 'vacuum ', 'replace ', 'trigger ')
	
	for keyword in blocked_keywords:
		if keyword in q:
			return False
	
	return True

def create_identifier( name: str ) -> str:
	"""
	
		Purpose:
		--------
		Sanitize a string into a safe SQLite identifier.
	
		- Replaces invalid characters with underscores
		- Ensures it starts with a letter or underscore
		- Prevents empty names
		
	"""
	if not name or not isinstance( name, str ):
		raise ValueError( 'Invalid Identifier.' )
	
	safe = re.sub( r'[^0-9a-zA-Z_]', '_', name.strip( ) )
	if not re.match( r'^[A-Za-z_]', safe ):
		safe = f'_{safe}'
	
	if not safe:
		raise ValueError( 'Invalid identifier after sanitization.' )
	
	return safe

def get_indexes( table: str ):
	with create_connection( ) as conn:
		rows = conn.execute( f'PRAGMA index_list("{table}");' ).fetchall( )
		return rows

def add_column( table: str, column: str, col_type: str ):
	column = create_identifier( column )
	col_type = col_type.upper( )
	
	with create_connection( ) as conn:
		conn.execute(
			f'ALTER TABLE "{table}" ADD COLUMN "{column}" {col_type};' )
		conn.commit( )

def rename_column( table_name: str, old_name: str, new_name: str ) -> None:
	"""
	
		Purpose:
		--------
		Rename a column within an existing SQLite table. Attempts native ALTER TABLE rename
		first; if it fails, falls back to a schema-safe rebuild preserving column order, data,
		and indexes.

		Parameters:
		-----------
		table_name : str
			Table containing the column.

		old_name : str
			Existing column name.

		new_name : str
			New column name.

		Returns:
		--------
		None
		
	"""
	if not table_name or not old_name or not new_name:
		return
	
	with create_connection( ) as conn:
		try:
			conn.execute(
				f'ALTER TABLE "{table_name}" RENAME COLUMN "{old_name}" TO "{new_name}";'
			)
			conn.commit( )
			return
		except Exception:
			pass
		
		row = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='table' AND name =?
			""",
			(table_name,)
		).fetchone( )
		
		if not row or not row[ 0 ]:
			raise ValueError( "Table definition not found." )
		
		create_sql = row[ 0 ]
		
		indexes = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
			""",
			(table_name,)
		).fetchall( )
		
		schema = conn.execute( f'PRAGMA table_info("{table_name}");' ).fetchall( )
		cols = [ r[ 1 ] for r in schema ]
		if old_name not in cols:
			raise ValueError( "Column not found." )
		
		mapped_cols = [ (new_name if c == old_name else c) for c in cols ]
		
		temp_table = f"{table_name}__rebuild_temp"
		
		col_defs: List[ str ] = [ ]
		pk_cols = [ r for r in schema if int( r[ 5 ] or 0 ) > 0 ]
		single_pk = len( pk_cols ) == 1
		
		for row in schema:
			col_name = row[ 1 ]
			col_type = row[ 2 ] or ''
			not_null = int( row[ 3 ] or 0 )
			default_value = row[ 4 ]
			pk = int( row[ 5 ] or 0 )
			
			out_name = new_name if col_name == old_name else col_name
			col_def = f'"{out_name}" {col_type}'.strip( )
			
			if not_null:
				col_def += ' NOT NULL'
			
			if default_value is not None:
				col_def += f' DEFAULT {default_value}'
			
			if single_pk and pk == 1:
				col_def += ' PRIMARY KEY'
			
			col_defs.append( col_def )
		
		new_create_sql = f'CREATE TABLE "{temp_table}" ({", ".join( col_defs )});'
		
		old_select = ", ".join( [ f'"{c}"' for c in cols ] )
		new_insert = ", ".join( [ f'"{c}"' for c in mapped_cols ] )
		
		conn.execute( "BEGIN" )
		conn.execute( new_create_sql )
		conn.execute(
			f'INSERT INTO "{temp_table}" ({new_insert}) SELECT {old_select} FROM "{table_name}";'
		)
		
		conn.execute( f'DROP TABLE "{table_name}";' )
		conn.execute( f'ALTER TABLE "{temp_table}" RENAME TO "{table_name}";' )
		
		for idx in indexes:
			idx_sql = idx[ 0 ]
			if idx_sql:
				idx_sql = idx_sql.replace( f'"{old_name}"', f'"{new_name}"' )
				conn.execute( idx_sql )
		
		conn.commit( )

def create_profile_table( table: str ):
	df = read_table( table )
	profile_rows = [ ]
	total_rows = len( df )
	for col in df.columns:
		series = df[ col ]
		null_count = series.isna( ).sum( )
		distinct_count = series.nunique( dropna=True )
		row = \
			{
					'column': col, 'dtype': str( series.dtype ),
					'null_%': round( (null_count / total_rows) * 100, 2 ) if total_rows else 0,
					'distinct_%': round( (
							                     distinct_count / total_rows) * 100,
						2 ) if total_rows else 0,
			}
		
		if pd.api.types.is_numeric_dtype( series ):
			row[ 'min' ] = series.min( )
			row[ 'max' ] = series.max( )
			row[ 'mean' ] = series.mean( )
		else:
			row[ 'min' ] = None
			row[ 'max' ] = None
			row[ 'mean' ] = None
		
		profile_rows.append( row )
	
	return pd.DataFrame( profile_rows )

def drop_column( table: str, column: str ):
	if not table or not column:
		raise ValueError( 'Table and column required.' )
	
	with create_connection( ) as conn:
		# ------------------------------------------------------------
		# Fetch original CREATE TABLE statement
		# ------------------------------------------------------------
		row = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='table' AND name =?
			""",
			(table,)
		).fetchone( )
		
		if not row or not row[ 0 ]:
			raise ValueError( 'Table definition not found.' )
		
		create_sql = row[ 0 ]
		
		# ------------------------------------------------------------
		# Extract column definitions
		# ------------------------------------------------------------
		open_paren = create_sql.find( "(" )
		close_paren = create_sql.rfind( ")" )
		
		if open_paren == -1 or close_paren == -1:
			raise ValueError( "Malformed CREATE TABLE statement." )
		
		inner = create_sql[ open_paren + 1: close_paren ]
		
		column_defs = [ c.strip( ) for c in inner.split( "," ) ]
		
		# Remove target column
		new_defs = [ ]
		for col_def in column_defs:
			col_name = col_def.split( )[ 0 ].strip( '"' )
			if col_name != column:
				new_defs.append( col_def )
		
		if len( new_defs ) == len( column_defs ):
			raise ValueError( "Column not found." )
		
		# ------------------------------------------------------------
		# Build new CREATE TABLE statement
		# ------------------------------------------------------------
		temp_table = f"{table}_rebuild_temp"
		
		new_create_sql = (
				f'CREATE TABLE "{temp_table}" ('
				+ ", ".join( new_defs )
				+ ");"
		)
		
		# ------------------------------------------------------------
		# Begin transaction
		# ------------------------------------------------------------
		conn.execute( "BEGIN" )
		
		conn.execute( new_create_sql )
		
		remaining_cols = [
				c.split( )[ 0 ].strip( '"' )
				for c in new_defs
		]
		
		col_list = ", ".join( [ f'"{c}"' for c in remaining_cols ] )
		
		conn.execute(
			f'INSERT INTO "{temp_table}" ({col_list}) '
			f'SELECT {col_list} FROM "{table}";'
		)
		
		# Preserve indexes
		indexes = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
			""",
			(table,)
		).fetchall( )
		
		conn.execute( f'DROP TABLE "{table}";' )
		conn.execute(
			f'ALTER TABLE "{temp_table}" RENAME TO "{table}";'
		)
		
		# Recreate indexes
		for idx in indexes:
			idx_sql = idx[ 0 ]
			if column not in idx_sql:
				conn.execute( idx_sql )
		
		conn.commit( )

def rename_table( old_name: str, new_name: str ) -> None:
	"""
	
		Purpose:
		--------
		Rename an existing SQLite table. Attempts native ALTER TABLE rename first; if it fails,
		falls back to a schema-safe rebuild using the original CREATE TABLE statement and
		preserves indexes.

		Parameters:
		-----------
		old_name : str
			Existing table name.

		new_name : str
			New table name.

		Returns:
		--------
		None
		
	"""
	if not old_name or not new_name:
		return
	
	with create_connection( ) as conn:
		try:
			conn.execute( f'ALTER TABLE "{old_name}" RENAME TO "{new_name}";' )
			conn.commit( )
			return
		except Exception:
			pass
		
		row = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='table' AND name =?
			""",
			(old_name,)
		).fetchone( )
		
		if not row or not row[ 0 ]:
			raise ValueError( "Table definition not found." )
		
		create_sql = row[ 0 ]
		
		indexes = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
			""",
			(old_name,)
		).fetchall( )
		
		open_paren = create_sql.find( "(" )
		if open_paren == -1:
			raise ValueError( "Malformed CREATE TABLE statement." )
		
		temp_name = f"{new_name}__rebuild_temp"
		
		conn.execute( "BEGIN" )
		conn.execute( f'CREATE TABLE "{temp_name}" {create_sql[ open_paren: ]}' )
		
		cols = [ r[ 1 ] for r in conn.execute( f'PRAGMA table_info("{old_name}");' ).fetchall( ) ]
		col_list = ", ".join( [ f'"{c}"' for c in cols ] )
		
		conn.execute(
			f'INSERT INTO "{temp_name}" ({col_list}) SELECT {col_list} FROM "{old_name}";'
		)
		
		conn.execute( f'DROP TABLE "{old_name}";' )
		conn.execute( f'ALTER TABLE "{temp_name}" RENAME TO "{new_name}";' )
		
		for idx in indexes:
			idx_sql = idx[ 0 ]
			if idx_sql:
				idx_sql = idx_sql.replace( f'ON "{old_name}"', f'ON "{new_name}"' )
				conn.execute( idx_sql )
		
		conn.commit( )

# ------------- DATASET UTILITIES

def has_loaded_dataset( df_frame: object ) -> bool:
	"""
		Purpose:
		--------
		Determine whether an object is a valid loaded dataframe.

		Parameters:
		-----------
		df_frame ( object ): Candidate dataframe object.

		Returns:
		--------
		bool:
			True when the object is a non-empty dataframe with at least one column.
	"""
	return (
			isinstance( df_frame, pd.DataFrame )
			and not df_frame.empty
			and len( df_frame.columns ) > 0
	)

def get_loaded_dataset( ) -> pd.DataFrame | None:
	"""
		Purpose:
		--------
		Return the currently loaded dataset from session state when valid.

		Parameters:
		-----------
		None

		Returns:
		--------
		pd.DataFrame | None:
			Copy of the loaded dataset, or None when no valid dataset exists.
	"""
	df_frame = st.session_state.get( 'df_dataset', None )
	if not has_loaded_dataset( df_frame ):
		return None
	
	return df_frame.copy( )

def store_loaded_dataset( df_dataset: pd.DataFrame, df_original: pd.DataFrame | None = None ) -> None:
	"""
		Purpose:
		--------
		Persist a successfully loaded dataset to session state.

		Parameters:
		-----------
		df_dataset ( pd.DataFrame ): Loaded dataset.
		df_original ( pd.DataFrame | None ): Optional original copy.

		Returns:
		--------
		None
	"""
	if not has_loaded_dataset( df_dataset ):
		return
	
	df_source = df_dataset.copy( )
	df_base = df_original.copy( ) if isinstance( df_original, pd.DataFrame ) else df_source.copy( )
	
	st.session_state[ 'df_raw' ] = df_source.copy( )
	st.session_state[ 'df_original' ] = df_base.copy( )
	st.session_state[ 'df_dataset' ] = df_source.copy( )
	
# ---------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------
st.set_page_config(  page_title='Mappy', layout='wide', page_icon=cfg.FAVICON,
    initial_sidebar_state='expanded', )

style_subheaders( )

# ==============================================================================
# SIDEBAR
# ==============================================================================

st.logo( cfg.LOGO, size='large' )

with st.sidebar:
	# ------- Mode Selection
	set_blue_divider( )
	
	st.subheader( 'Mappy Mode' )
	
	mode = st.sidebar.radio( 'Select', cfg.MODES, index=0 )
	previous_mode = st.session_state.get( 'previous_mode', None )
	
	if previous_mode != mode:
		st.session_state[ 'previous_mode' ] = mode
		st.rerun( )
	
	st.session_state[ 'previous_mode' ] = mode
	
	# ------- Data Selection
	set_blue_divider( )
	
	st.subheader( 'Data Source' )
	
	with st.expander( 'Database', expanded=False ):
		source = st.selectbox( label='Select',
			options=[ 'Default Data', 'Database Data', 'Custom Data' ], key='source_selectbox' )
	
	uploaded = st.file_uploader( label='Upload Spreadsheet', type=[ 'xlsx', 'xls', 'csv' ],
		key='source_uploader' )
	
	loaded_df: pd.DataFrame | None = None
	loaded_original: pd.DataFrame | None = None
	
	if source == 'Default Data':
		loaded_df = pd.read_excel( cfg.DEFAULT_DATA )
		loaded_original = loaded_df.copy( )
	
	elif source == 'Database Data':
		try:
			with sqlite3.connect( cfg.DB_PATH ) as connection:
				df_tables = pd.read_sql_query(
					"""
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                      AND name NOT LIKE 'sqlite_%'
                    ORDER BY name;
					""",
					connection )
				
				table_options = df_tables[ 'name' ].tolist( )[ :3 ]
				
				if table_options:
					selected_table = st.selectbox( label='Select Database Table',
						options=table_options, key='database_table_selectbox' )
					
					if selected_table:
						loaded_df = pd.read_sql_query( f'SELECT * FROM "{selected_table}"',
							connection )
						
						loaded_original = loaded_df.copy( )
						log_step( f'Loaded Database Table: {selected_table}' )
				else:
					st.warning( 'No tables were found in the database.' )
		except Exception as ex:
			st.error( f'Error loading database data: {ex}' )
	
	elif source == 'Custom Data':
		if uploaded is not None:
			if uploaded.name.lower( ).endswith( ('.xlsx', '.xls') ):
				loaded_df = pd.read_excel( uploaded )
			else:
				loaded_df = pd.read_csv( uploaded )
			
			loaded_original = loaded_df.copy( )
			log_step( f'Loaded uploaded file: {uploaded.name}' )
		else:
			st.info( 'Upload a spreadsheet to load data.' )
	
	if has_loaded_dataset( loaded_df ):
		store_loaded_dataset( loaded_df, loaded_original )
	
	# ------- Mappy Configuration
	set_blue_divider( )

	with st.sidebar.expander( 'Configuration', expanded=False ):
			api_keys = { name: value for name, value in vars( cfg ).items( )
			             if name.endswith( '_API_KEY' ) and value }
			if not api_keys:
				st.error( 'No API keys found in config.py' )
			
			selected_key = st.selectbox( 'API Key', options=list( api_keys.keys( ) ), key='api_key' )
			api_key = api_keys[ selected_key ]
		
	with st.sidebar.expander( 'Query', expanded=False ):
		qps = st.slider( 'Queries Per Second', min_value=1, max_value=50, value=10, )
	
	with st.sidebar.expander( 'Cache', expanded=False ):
		cache_backend = st.selectbox( 'Cache Backend', options=[ 'none', 'memory', 'sqlite' ],
			key='cache_backend' )
		cache: Optional[ object ] = None
		if cache_backend == 'memory':
			cache = InMemoryCache( )
		elif cache_backend == 'sqlite':
			cache_path = st.text_input( 'SQLite Cache Path', value='mappy_cache.db', )
			cache = SQLiteCache( cache_path )

# -----------  Core Maps Gateway (NO cache argument — VERIFIED)

maps = Maps( api_key=api_key, qps=qps, )
geocoder = Geocoder( maps, cache=cache )
places = Places( maps, cache=cache )
distances = DistanceMatrix( maps )
timezone = Timezone( maps )
static_maps = StaticMapURL( api_key=api_key )


# ==============================================================================
# GEOCODING MODE
# ==============================================================================
if mode == 'Geocoding':
	left, center, right = st.columns( [ 0.025, 0.95, 0.025 ] )
	with center:
		st.subheader( 'Geocoding & Places' )
		st.divider( )
		
		geo_c1, geo_c2 = st.columns( [ 0.60, 0.40  ], border=True, gap='xsmall' )
		with geo_c1:
			query = st.text_input( 'Enter Address or Location', key='location' )
			
			btn_c1, btn_c2 = st.columns( 2 )
			with btn_c1:
				if st.button( 'Resolve Location', width='stretch' ):
					if not query:
						st.warning( 'Enter a location.' )
					else:
						try:
							result = geocoder.freeform( query )
							st.json( result )
						
						except NotFound:
							st.warning( 'Geocoding failed. Trying Places search.' )
							result = places.text_to_location( query )
							st.json( result )
							
						except Exception as e:
							st.error( str( e ) )
			with btn_c2:
				if st.button( 'Clear Location', width='stretch' ):
					if not query:
						st.warning( 'Nothing to clear' )
					else:
						query = None
						st.json( query )
					
		with geo_c2:
			use_places = st.checkbox( 'Use Places fallback if geocoding fails', value=True )


# ==============================================================================
# WEATHER MODE
# ==============================================================================
elif mode == 'Weather':
	left, center, right = st.columns( [ 0.025, 0.95, 0.025 ] )
	with center:
		st.subheader( 'Weather & Climate Data' )
		st.divider( )
		
		met_c1, met_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		
		with met_c1:
			# ------------------------------------------------------------------
			# GOOGLE WEATHER
			# ------------------------------------------------------------------
			with st.expander( '🌦️ Google Weather', expanded=True ):
				google_address = st.text_input(
					'Address or Location',
					value='Washington, DC',
					key='weather_google_address' )
				
				google_product = st.selectbox(
					'Product',
					options=[ 'Current Conditions', 'Hourly Forecast', 'Daily Forecast', 'Alerts' ],
					key='weather_google_product' )
				
				google_units = st.selectbox(
					'Units System',
					options=[ 'METRIC', 'IMPERIAL' ],
					key='weather_google_units' )
				
				google_language = st.text_input(
					'Language Code',
					value='en',
					key='weather_google_language' )
				
				google_hours = st.number_input(
					'Hours',
					min_value=1,
					max_value=240,
					value=24,
					step=1,
					key='weather_google_hours',
					disabled=(google_product != 'Hourly Forecast') )
				
				google_days = st.number_input(
					'Days',
					min_value=1,
					max_value=10,
					value=5,
					step=1,
					key='weather_google_days',
					disabled=(google_product != 'Daily Forecast') )
				
				google_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=10,
					step=1,
					key='weather_google_timeout' )
				
				google_btn_c1, google_btn_c2 = st.columns( 2 )
				with google_btn_c1:
					if st.button( 'Run Google Weather', key='weather_google_run',
							use_container_width=True ):
						if not google_address:
							st.warning( 'Enter an address or location.' )
						else:
							try:
								weather = GoogleWeather( )
								
								if google_product == 'Current Conditions':
									result = weather.fetch_current(
										address=google_address,
										units_system=google_units,
										language_code=google_language,
										time=int( google_timeout ) )
								
								elif google_product == 'Hourly Forecast':
									result = weather.fetch_hourly_forecast(
										address=google_address,
										hours=int( google_hours ),
										units_system=google_units,
										language_code=google_language,
										time=int( google_timeout ) )
								
								elif google_product == 'Daily Forecast':
									result = weather.fetch_daily_forecast(
										address=google_address,
										days=int( google_days ),
										units_system=google_units,
										language_code=google_language,
										time=int( google_timeout ) )
								
								else:
									result = weather.fetch_alerts(
										address=google_address,
										language_code=google_language,
										time=int( google_timeout ) )
								
								st.session_state[ 'weather_last_source' ] = 'Google Weather'
								st.session_state[ 'weather_last_result' ] = result or { }
								st.session_state[ 'weather_last_latitude' ] = weather.latitude
								st.session_state[ 'weather_last_longitude' ] = weather.longitude
								st.success( 'Google Weather request completed.' )
							
							except Exception as ex:
								st.error( f'Google Weather request failed: {ex}' )
				
				with google_btn_c2:
					if st.button( 'Clear Google Result', key='weather_google_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# OPENWEATHER / OPEN-METEO
			# ------------------------------------------------------------------
			with st.expander( '🌤️ OpenWeather / Open-Meteo', expanded=False ):
				open_location = st.text_input(
					'Location',
					value='Washington, DC',
					key='weather_open_location' )
				
				open_mode = st.selectbox(
					'Mode',
					options=[ 'current', 'hourly', 'daily' ],
					key='weather_open_mode' )
				
				open_zone = st.text_input(
					'Timezone',
					value='auto',
					key='weather_open_zone' )
				
				open_forecast_days = st.number_input(
					'Forecast Days',
					min_value=1,
					max_value=16,
					value=7,
					step=1,
					key='weather_open_forecast_days' )
				
				open_past_days = st.number_input(
					'Past Days',
					min_value=0,
					max_value=92,
					value=0,
					step=1,
					key='weather_open_past_days' )
				
				open_count = st.number_input(
					'Geocoding Result Count',
					min_value=1,
					max_value=100,
					value=10,
					step=1,
					key='weather_open_count' )
				
				open_btn_c1, open_btn_c2 = st.columns( 2 )
				
				with open_btn_c1:
					if st.button( 'Run OpenWeather', key='weather_open_run',
							use_container_width=True ):
						if not open_location:
							st.warning( 'Enter a location.' )
						else:
							try:
								weather = OpenWeather( )
								result = weather.fetch(
									location=open_location,
									mode=open_mode,
									zone=open_zone,
									forecast_days=int( open_forecast_days ),
									past_days=int( open_past_days ),
									count=int( open_count ) )
								
								st.session_state[
									'weather_last_source' ] = 'OpenWeather / Open-Meteo'
								st.session_state[ 'weather_last_result' ] = result or { }
								st.session_state[ 'weather_last_latitude' ] = getattr(
									weather, 'latitude', None )
								st.session_state[ 'weather_last_longitude' ] = getattr(
									weather, 'longitude', None )
								st.success( 'OpenWeather request completed.' )
							
							except Exception as ex:
								st.error( f'OpenWeather request failed: {ex}' )
				
				with open_btn_c2:
					if st.button( 'Clear OpenWeather Result', key='weather_open_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# HISTORICAL WEATHER
			# ------------------------------------------------------------------
			with st.expander( '🕰️ Historical Weather', expanded=False ):
				historical_location = st.text_input(
					'Location',
					value='Washington, DC',
					key='weather_historical_location' )
				
				historical_date = st.date_input(
					'Historical Date',
					value=dt.date.today( ) - dt.timedelta( days=7 ),
					key='weather_historical_date' )
				
				historical_zone = st.text_input(
					'Timezone',
					value='auto',
					key='weather_historical_zone' )
				
				historical_count = st.number_input(
					'Geocoding Result Count',
					min_value=1,
					max_value=100,
					value=10,
					step=1,
					key='weather_historical_count' )
				
				historical_btn_c1, historical_btn_c2 = st.columns( 2 )
				
				with historical_btn_c1:
					if st.button( 'Run Historical Weather', key='weather_historical_run',
							use_container_width=True ):
						if not historical_location:
							st.warning( 'Enter a location.' )
						else:
							try:
								weather = HistoricalWeather( )
								result = weather.fetch(
									location=historical_location,
									date=historical_date,
									zone=historical_zone,
									count=int( historical_count ) )
								
								st.session_state[ 'weather_last_source' ] = 'Historical Weather'
								st.session_state[ 'weather_last_result' ] = result or { }
								st.session_state[ 'weather_last_latitude' ] = getattr(
									weather, 'latitude', None )
								st.session_state[ 'weather_last_longitude' ] = getattr(
									weather, 'longitude', None )
								st.success( 'Historical Weather request completed.' )
							
							except Exception as ex:
								st.error( f'Historical Weather request failed: {ex}' )
				
				with historical_btn_c2:
					if st.button( 'Clear Historical Result', key='weather_historical_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# CLIMATE DATA
			# ------------------------------------------------------------------
			with st.expander( '🌡️ Climate Data', expanded=False ):
				climate_mode = st.selectbox(
					'Mode',
					options=[ 'datasets', 'data' ],
					key='weather_climate_mode' )
				
				climate_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='weather_climate_timeout' )
				
				if climate_mode == 'datasets':
					climate_keyword = st.text_input(
						'Keyword',
						value='daily',
						key='weather_climate_keyword' )
					
					climate_start_date_value = st.date_input(
						'Start Date',
						value=dt.date.today( ) - dt.timedelta( days=365 ),
						key='weather_climate_dataset_start_date' )
					
					climate_end_date_value = st.date_input(
						'End Date',
						value=dt.date.today( ),
						key='weather_climate_dataset_end_date' )
					
					climate_limit = st.number_input(
						'Limit',
						min_value=1,
						max_value=1000,
						value=25,
						step=1,
						key='weather_climate_dataset_limit' )
					
					climate_offset = st.number_input(
						'Offset',
						min_value=0,
						max_value=100000,
						value=0,
						step=1,
						key='weather_climate_dataset_offset' )
					
					climate_dataset = ''
					climate_stations = ''
					climate_data_types = ''
				
				else:
					climate_dataset = st.text_input(
						'Dataset',
						value='daily-summaries',
						help='Example: daily-summaries',
						key='weather_climate_dataset' )
					
					climate_data_c1, climate_data_c2 = st.columns( 2 )
					with climate_data_c1:
						climate_start_date_value = st.date_input(
							'Start Date',
							value=dt.date.today( ) - dt.timedelta( days=30 ),
							key='weather_climate_data_start_date' )
					
					with climate_data_c2:
						climate_end_date_value = st.date_input(
							'End Date',
							value=dt.date.today( ),
							key='weather_climate_data_end_date' )
					
					climate_stations = st.text_input(
						'Stations',
						value='',
						help='Optional comma-separated station identifiers.',
						key='weather_climate_stations' )
					
					climate_data_types = st.text_input(
						'Data Types',
						value='',
						help='Optional comma-separated data type identifiers.',
						key='weather_climate_data_types' )
					
					climate_limit = st.number_input(
						'Limit',
						min_value=1,
						max_value=1000,
						value=25,
						step=1,
						key='weather_climate_data_limit' )
					
					climate_offset = 0
					climate_keyword = ''
				
				climate_btn_c1, climate_btn_c2 = st.columns( 2 )
				
				with climate_btn_c1:
					if st.button( 'Run Climate Data', key='weather_climate_run',
							use_container_width=True ):
						try:
							service = ClimateData( )
							
							if climate_mode == 'datasets':
								result = service.fetch_datasets(
									keyword=climate_keyword,
									start_date=climate_start_date_value.isoformat( ),
									end_date=climate_end_date_value.isoformat( ),
									limit=int( climate_limit ),
									offset=int( climate_offset ),
									time=int( climate_timeout ) )
							
							else:
								if not climate_dataset:
									st.warning( 'Enter a dataset identifier.' )
									result = None
								else:
									result = service.fetch_data(
										dataset=climate_dataset,
										start_date=climate_start_date_value.isoformat( ),
										end_date=climate_end_date_value.isoformat( ),
										stations=climate_stations,
										data_types=climate_data_types,
										limit=int( climate_limit ),
										time=int( climate_timeout ) )
							
							if result is not None:
								st.session_state[ 'weather_last_source' ] = 'Climate Data'
								st.session_state[ 'weather_last_result' ] = result or { }
								st.session_state[ 'weather_last_latitude' ] = None
								st.session_state[ 'weather_last_longitude' ] = None
								st.success( 'Climate Data request completed.' )
						
						except Exception as ex:
							st.error( f'Climate Data request failed: {ex}' )
				
				with climate_btn_c2:
					if st.button( 'Clear Climate Result', key='weather_climate_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# TIDES AND CURRENTS
			# ------------------------------------------------------------------
			with st.expander( '🌊 Tides & Currents', expanded=False ):
				tides_mode = st.selectbox(
					'Mode',
					options=[ 'station', 'water-level', 'tide-predictions' ],
					key='weather_tides_mode' )
				
				tides_station_id = st.text_input(
					'Station ID',
					value='8594900',
					help='Example NOAA station: 8594900',
					key='weather_tides_station_id' )
				
				tides_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='weather_tides_timeout' )
				
				if tides_mode == 'station':
					tides_begin_date = ''
					tides_end_date = ''
					tides_datum = 'MLLW'
					tides_units = 'metric'
					tides_time_zone = 'gmt'
					tides_interval = 'hilo'
				
				else:
					tides_date_c1, tides_date_c2 = st.columns( 2 )
					with tides_date_c1:
						tides_begin = st.date_input(
							'Begin Date',
							value=dt.date.today( ) - dt.timedelta( days=1 ),
							key='weather_tides_begin_date' )
					
					with tides_date_c2:
						tides_end = st.date_input(
							'End Date',
							value=dt.date.today( ),
							key='weather_tides_end_date' )
					
					tides_begin_date = tides_begin.strftime( '%Y%m%d' )
					tides_end_date = tides_end.strftime( '%Y%m%d' )
					
					tides_datum = st.selectbox(
						'Datum',
						options=[ 'MLLW', 'MLW', 'MSL', 'MHW', 'MHHW', 'NAVD' ],
						key='weather_tides_datum' )
					
					tides_units = st.selectbox(
						'Units',
						options=[ 'metric', 'english' ],
						key='weather_tides_units' )
					
					tides_time_zone = st.selectbox(
						'Time Zone',
						options=[ 'gmt', 'lst', 'lst_ldt' ],
						key='weather_tides_time_zone' )
					
					if tides_mode == 'tide-predictions':
						tides_interval = st.selectbox(
							'Interval',
							options=[ 'hilo', 'h' ],
							key='weather_tides_interval' )
					else:
						tides_interval = 'hilo'
				
				tides_btn_c1, tides_btn_c2 = st.columns( 2 )
				
				with tides_btn_c1:
					if st.button( 'Run Tides & Currents', key='weather_tides_run',
							use_container_width=True ):
						try:
							service = TidesAndCurrents( )
							
							result = service.fetch(
								mode=tides_mode,
								station_id=tides_station_id,
								begin_date=tides_begin_date,
								end_date=tides_end_date,
								datum=tides_datum,
								units=tides_units,
								time_zone=tides_time_zone,
								interval=tides_interval,
								time=int( tides_timeout ) )
							
							st.session_state[ 'weather_last_source' ] = 'Tides & Currents'
							st.session_state[ 'weather_last_result' ] = result or { }
							st.session_state[ 'weather_last_latitude' ] = None
							st.session_state[ 'weather_last_longitude' ] = None
							st.success( 'Tides & Currents request completed.' )
						
						except Exception as ex:
							st.error( f'Tides & Currents request failed: {ex}' )
				
				with tides_btn_c2:
					if st.button( 'Clear Tides Result', key='weather_tides_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
		
		with met_c2:
			# ------------------------------------------------------------------
			# WEATHER RESULTS
			# ------------------------------------------------------------------
			st.markdown( '##### Weather Results' )
			
			weather_source = st.session_state.get( 'weather_last_source', '' )
			weather_result = st.session_state.get( 'weather_last_result', { } )
			weather_latitude = st.session_state.get( 'weather_last_latitude', None )
			weather_longitude = st.session_state.get( 'weather_last_longitude', None )
			
			if not weather_result:
				st.info( 'No weather results available. Run one of the Weather expanders.' )
			
			else:
				if weather_source:
					st.caption( f'Source: {weather_source}' )
				
				if weather_latitude is not None and weather_longitude is not None:
					try:
						lat_value = float( weather_latitude )
						lng_value = float( weather_longitude )
						
						lat_c, lng_c = st.columns( 2 )
						with lat_c:
							st.metric( 'Latitude', f'{lat_value:.6f}' )
						with lng_c:
							st.metric( 'Longitude', f'{lng_value:.6f}' )
						
						preview_url = static_maps.pin(
							lat=lat_value,
							lng=lng_value,
							zoom=8,
							size='600x400' )
						
						st.image( preview_url )
					
					except Exception as ex:
						st.warning( f'Static map preview failed: {ex}' )
				
				st.json( weather_result )

# ==============================================================================
# ENVIRONMENTAL MODE
# ==============================================================================
elif mode == 'Environmental':
	left, center, right = st.columns( [ 0.025, 0.95, 0.025 ] )
	with center:
		st.subheader( 'Environmental Data' )
		st.divider( )
		
		enviro_c1, enviro_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		
		with enviro_c1:
			# ------------------------------------------------------------------
			# AIRNOW AIR QUALITY
			# ------------------------------------------------------------------
			with st.expander( '🌫️ AirNow Air Quality', expanded=True ):
				airnow_mode = st.selectbox(
					'Mode',
					options=[
							'Current by ZIP',
							'Current by Coordinates',
							'Forecast by ZIP',
							'Forecast by Coordinates'
					],
					key='env_airnow_mode' )
				
				airnow_distance = st.number_input(
					'Distance',
					min_value=0,
					max_value=250,
					value=25,
					step=1,
					key='env_airnow_distance' )
				
				airnow_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_airnow_timeout' )
				
				if 'ZIP' in airnow_mode:
					airnow_zip = st.text_input(
						'ZIP Code',
						value='20001',
						key='env_airnow_zip' )
					
					airnow_latitude = None
					airnow_longitude = None
				
				else:
					airnow_zip = ''
					airnow_latitude = st.number_input(
						'Latitude',
						value=38.907200,
						format='%.6f',
						key='env_airnow_latitude' )
					
					airnow_longitude = st.number_input(
						'Longitude',
						value=-77.036900,
						format='%.6f',
						key='env_airnow_longitude' )
				
				if 'Forecast' in airnow_mode:
					airnow_date = st.date_input(
						'Forecast Date',
						value=dt.date.today( ),
						key='env_airnow_date' )
				else:
					airnow_date = None
				
				airnow_btn_c1, airnow_btn_c2 = st.columns( 2 )
				
				with airnow_btn_c1:
					if st.button( 'Run AirNow', key='env_airnow_run',
							use_container_width=True ):
						try:
							service = AirNow( )
							
							if airnow_mode == 'Current by ZIP':
								if not airnow_zip:
									st.warning( 'Enter a ZIP code.' )
									result = None
								else:
									result = service.fetch_current_zip(
										zip_code=airnow_zip,
										distance=int( airnow_distance ),
										time=int( airnow_timeout ) )
							
							elif airnow_mode == 'Current by Coordinates':
								result = service.fetch_current_latlon(
									latitude=float( airnow_latitude ),
									longitude=float( airnow_longitude ),
									distance=int( airnow_distance ),
									time=int( airnow_timeout ) )
							
							elif airnow_mode == 'Forecast by ZIP':
								if not airnow_zip:
									st.warning( 'Enter a ZIP code.' )
									result = None
								else:
									result = service.fetch_forecast_zip(
										zip_code=airnow_zip,
										date=airnow_date.isoformat( ),
										distance=int( airnow_distance ),
										time=int( airnow_timeout ) )
							
							else:
								result = service.fetch_forecast_latlon(
									latitude=float( airnow_latitude ),
									longitude=float( airnow_longitude ),
									date=airnow_date.isoformat( ),
									distance=int( airnow_distance ),
									time=int( airnow_timeout ) )
							
							if result is not None:
								st.session_state[ 'env_last_source' ] = 'AirNow'
								st.session_state[ 'env_last_result' ] = result or { }
								st.session_state[ 'env_last_latitude' ] = airnow_latitude
								st.session_state[ 'env_last_longitude' ] = airnow_longitude
								st.success( 'AirNow request completed.' )
						
						except Exception as ex:
							st.error( f'AirNow request failed: {ex}' )
				
				with airnow_btn_c2:
					if st.button( 'Clear AirNow Result', key='env_airnow_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# UV INDEX
			# ------------------------------------------------------------------
			with st.expander( '☀️ UV Index', expanded=False ):
				uv_mode = st.selectbox(
					'Mode',
					options=[
							'Daily by ZIP',
							'Daily by City / State',
							'Hourly by ZIP',
							'Hourly by City / State'
					],
					key='env_uv_mode' )
				
				uv_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_uv_timeout' )
				
				if 'ZIP' in uv_mode:
					uv_zip = st.text_input(
						'ZIP Code',
						value='20001',
						key='env_uv_zip' )
					
					uv_city = ''
					uv_state = ''
				
				else:
					uv_zip = ''
					uv_city = st.text_input(
						'City',
						value='Washington',
						key='env_uv_city' )
					
					uv_state = st.text_input(
						'State',
						value='DC',
						key='env_uv_state' )
				
				uv_btn_c1, uv_btn_c2 = st.columns( 2 )
				
				with uv_btn_c1:
					if st.button( 'Run UV Index', key='env_uv_run',
							use_container_width=True ):
						try:
							service = UvIndex( )
							
							if uv_mode == 'Daily by ZIP':
								if not uv_zip:
									st.warning( 'Enter a ZIP code.' )
									result = None
								else:
									result = service.fetch_daily_zip(
										zip_code=uv_zip,
										time=int( uv_timeout ) )
							
							elif uv_mode == 'Daily by City / State':
								if not uv_city or not uv_state:
									st.warning( 'Enter both city and state.' )
									result = None
								else:
									result = service.fetch_daily_city_state(
										city=uv_city,
										state=uv_state,
										time=int( uv_timeout ) )
							
							elif uv_mode == 'Hourly by ZIP':
								if not uv_zip:
									st.warning( 'Enter a ZIP code.' )
									result = None
								else:
									result = service.fetch_hourly_zip(
										zip_code=uv_zip,
										time=int( uv_timeout ) )
							
							else:
								if not uv_city or not uv_state:
									st.warning( 'Enter both city and state.' )
									result = None
								else:
									result = service.fetch_hourly_city_state(
										city=uv_city,
										state=uv_state,
										time=int( uv_timeout ) )
							
							if result is not None:
								st.session_state[ 'env_last_source' ] = 'UV Index'
								st.session_state[ 'env_last_result' ] = result or { }
								st.session_state[ 'env_last_latitude' ] = None
								st.session_state[ 'env_last_longitude' ] = None
								st.success( 'UV Index request completed.' )
						
						except Exception as ex:
							st.error( f'UV Index request failed: {ex}' )
				
				with uv_btn_c2:
					if st.button( 'Clear UV Result', key='env_uv_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# OPENAQ
			# ------------------------------------------------------------------
			with st.expander( '🧪 OpenAQ', expanded=False ):
				openaq_mode = st.selectbox(
					'Mode',
					options=[ 'Locations', 'Latest Measurements' ],
					key='env_openaq_mode' )
				
				openaq_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_openaq_timeout' )
				
				if openaq_mode == 'Locations':
					openaq_country_id = st.number_input(
						'Country ID',
						min_value=0,
						value=0,
						step=1,
						key='env_openaq_country_id' )
					
					openaq_coordinates = st.text_input(
						'Coordinates',
						value='38.9072,-77.0369',
						help='OpenAQ expects a latitude,longitude string.',
						key='env_openaq_coordinates' )
					
					openaq_radius = st.number_input(
						'Radius',
						min_value=1,
						max_value=100000,
						value=25000,
						step=1000,
						key='env_openaq_radius' )
					
					openaq_providers_id = st.text_input(
						'Providers ID',
						value='',
						key='env_openaq_providers_id' )
					
					openaq_parameters_id = st.text_input(
						'Parameters ID',
						value='',
						key='env_openaq_parameters_id' )
					
					openaq_limit = st.number_input(
						'Limit',
						min_value=1,
						max_value=1000,
						value=25,
						step=1,
						key='env_openaq_limit' )
					
					openaq_page = st.number_input(
						'Page',
						min_value=1,
						max_value=10000,
						value=1,
						step=1,
						key='env_openaq_page' )
					
					openaq_location_id = None
				
				else:
					openaq_country_id = 0
					openaq_coordinates = ''
					openaq_radius = 25000
					openaq_providers_id = ''
					openaq_parameters_id = ''
					openaq_limit = 25
					openaq_page = 1
					
					openaq_location_id = st.number_input(
						'Location ID',
						min_value=1,
						value=1,
						step=1,
						key='env_openaq_location_id' )
				
				openaq_btn_c1, openaq_btn_c2 = st.columns( 2 )
				
				with openaq_btn_c1:
					if st.button( 'Run OpenAQ', key='env_openaq_run',
							use_container_width=True ):
						try:
							service = OpenAQ( )
							
							if openaq_mode == 'Locations':
								country_id_value = None
								if int( openaq_country_id ) > 0:
									country_id_value = int( openaq_country_id )
								
								result = service.fetch_locations(
									country_id=country_id_value,
									coordinates=openaq_coordinates,
									radius=int( openaq_radius ),
									providers_id=openaq_providers_id,
									parameters_id=openaq_parameters_id,
									limit=int( openaq_limit ),
									page=int( openaq_page ),
									time=int( openaq_timeout ) )
								
								lat_value = None
								lng_value = None
								try:
									parts = [ p.strip( ) for p in openaq_coordinates.split( ',' ) ]
									if len( parts ) == 2:
										lat_value = float( parts[ 0 ] )
										lng_value = float( parts[ 1 ] )
								except Exception:
									lat_value = None
									lng_value = None
							
							else:
								result = service.fetch_latest(
									location_id=int( openaq_location_id ),
									time=int( openaq_timeout ) )
								
								lat_value = None
								lng_value = None
							
							st.session_state[ 'env_last_source' ] = 'OpenAQ'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = lat_value
							st.session_state[ 'env_last_longitude' ] = lng_value
							st.success( 'OpenAQ request completed.' )
						
						except Exception as ex:
							st.error( f'OpenAQ request failed: {ex}' )
				
				with openaq_btn_c2:
					if st.button( 'Clear OpenAQ Result', key='env_openaq_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# PURPLEAIR SENSORS
			# ------------------------------------------------------------------
			with st.expander( '🟣 PurpleAir Sensors', expanded=False ):
				purple_mode = st.selectbox(
					'Mode',
					options=[ 'Sensors by Bounding Box', 'Single Sensor' ],
					key='env_purple_mode' )
				
				purple_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_purple_timeout' )
				
				if purple_mode == 'Sensors by Bounding Box':
					st.caption(
						'Bounding box uses northwest longitude/latitude and southeast longitude/latitude.' )
					
					purple_box_c1, purple_box_c2 = st.columns( 2 )
					with purple_box_c1:
						purple_nwlng = st.number_input(
							'NW Longitude',
							value=-77.150000,
							format='%.6f',
							key='env_purple_nwlng' )
						
						purple_nwlat = st.number_input(
							'NW Latitude',
							value=39.000000,
							format='%.6f',
							key='env_purple_nwlat' )
					
					with purple_box_c2:
						purple_selng = st.number_input(
							'SE Longitude',
							value=-76.900000,
							format='%.6f',
							key='env_purple_selng' )
						
						purple_selat = st.number_input(
							'SE Latitude',
							value=38.800000,
							format='%.6f',
							key='env_purple_selat' )
					
					purple_location_type = st.number_input(
						'Location Type',
						min_value=0,
						max_value=1,
						value=0,
						step=1,
						help='Public outdoor sensors are commonly 0.',
						key='env_purple_location_type' )
					
					purple_max_age = st.number_input(
						'Max Age',
						min_value=0,
						max_value=10080,
						value=0,
						step=10,
						help='Maximum sensor age in minutes. 0 keeps the broad/default behavior.',
						key='env_purple_max_age' )
					
					purple_modified_since = st.number_input(
						'Modified Since',
						min_value=0,
						max_value=4102444800,
						value=0,
						step=1,
						help='UNIX timestamp filter. 0 disables the filter.',
						key='env_purple_modified_since' )
					
					purple_sensor_index = 0
				
				else:
					purple_nwlng = 0.0
					purple_nwlat = 0.0
					purple_selng = 0.0
					purple_selat = 0.0
					purple_location_type = 0
					purple_max_age = 0
					purple_modified_since = 0
					
					purple_sensor_index = st.number_input(
						'Sensor Index',
						min_value=1,
						value=1,
						step=1,
						key='env_purple_sensor_index' )
				
				purple_btn_c1, purple_btn_c2 = st.columns( 2 )
				
				with purple_btn_c1:
					if st.button( 'Run PurpleAir', key='env_purple_run',
							use_container_width=True ):
						try:
							service = PurpleAir( )
							
							if purple_mode == 'Sensors by Bounding Box':
								result = service.fetch_sensors(
									nwlng=float( purple_nwlng ),
									nwlat=float( purple_nwlat ),
									selng=float( purple_selng ),
									selat=float( purple_selat ),
									location_type=int( purple_location_type ),
									max_age=int( purple_max_age ),
									modified_since=int( purple_modified_since ),
									time=int( purple_timeout ) )
								
								map_lat = (float( purple_nwlat ) + float( purple_selat )) / 2.0
								map_lng = (float( purple_nwlng ) + float( purple_selng )) / 2.0
							
							else:
								result = service.fetch_sensor(
									sensor_index=int( purple_sensor_index ),
									time=int( purple_timeout ) )
								
								map_lat = None
								map_lng = None
							
							st.session_state[ 'env_last_source' ] = 'PurpleAir'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = map_lat
							st.session_state[ 'env_last_longitude' ] = map_lng
							st.success( 'PurpleAir request completed.' )
						
						except Exception as ex:
							st.error( f'PurpleAir request failed: {ex}' )
				
				with purple_btn_c2:
					if st.button( 'Clear PurpleAir Result', key='env_purple_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# ENVIROFACTS
			# ------------------------------------------------------------------
			with st.expander( '🏭 EnviroFacts Facilities', expanded=False ):
				envirofacts_table = st.selectbox(
					'Table',
					options=[ 'TRI_FACILITY', 'TRI_RELEASE', 'EF_W_EMISSIONS_SOURCE_GHG' ],
					key='env_envirofacts_table' )
				
				envirofacts_state = st.text_input(
					'State Code',
					value='DC',
					help='Optional two-letter state filter.',
					key='env_envirofacts_state' )
				
				envirofacts_facility = st.text_input(
					'Facility Name',
					value='',
					help='Optional facility-name prefix filter.',
					key='env_envirofacts_facility' )
				
				envirofacts_limit = st.number_input(
					'Limit',
					min_value=1,
					max_value=500,
					value=25,
					step=1,
					key='env_envirofacts_limit' )
				
				envirofacts_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_envirofacts_timeout' )
				
				envirofacts_btn_c1, envirofacts_btn_c2 = st.columns( 2 )
				
				with envirofacts_btn_c1:
					if st.button( 'Run EnviroFacts', key='env_envirofacts_run',
							use_container_width=True ):
						try:
							service = EnviroFacts( )
							result = service.fetch(
								table_name=envirofacts_table,
								state_code=envirofacts_state,
								facility_name=envirofacts_facility,
								limit=int( envirofacts_limit ),
								time=int( envirofacts_timeout ) )
							
							st.session_state[ 'env_last_source' ] = 'EnviroFacts'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = None
							st.session_state[ 'env_last_longitude' ] = None
							st.success( 'EnviroFacts request completed.' )
						
						except Exception as ex:
							st.error( f'EnviroFacts request failed: {ex}' )
				
				with envirofacts_btn_c2:
					if st.button( 'Clear EnviroFacts Result', key='env_envirofacts_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# FIRMS FIRE / THERMAL ANOMALIES
			# ------------------------------------------------------------------
			with st.expander( '🔥 FIRMS Fire / Thermal Anomalies', expanded=False ):
				firms_source = st.selectbox(
					'Source',
					options=[
							'MODIS_NRT',
							'MODIS_SP',
							'VIIRS_SNPP_NRT',
							'VIIRS_SNPP_SP',
							'VIIRS_NOAA20_NRT',
							'VIIRS_NOAA20_SP',
							'VIIRS_NOAA21_NRT',
							'LANDSAT_NRT'
					],
					key='env_firms_source' )
				
				firms_area_mode = st.selectbox(
					'Area Mode',
					options=[ 'World', 'Bounding Box' ],
					key='env_firms_area_mode' )
				
				if firms_area_mode == 'World':
					firms_area_coordinates = 'world'
					firms_center_lat = None
					firms_center_lng = None
				
				else:
					firms_box_c1, firms_box_c2 = st.columns( 2 )
					with firms_box_c1:
						firms_west = st.number_input(
							'West',
							value=-77.150000,
							format='%.6f',
							key='env_firms_west' )
						
						firms_south = st.number_input(
							'South',
							value=38.800000,
							format='%.6f',
							key='env_firms_south' )
					
					with firms_box_c2:
						firms_east = st.number_input(
							'East',
							value=-76.900000,
							format='%.6f',
							key='env_firms_east' )
						
						firms_north = st.number_input(
							'North',
							value=39.000000,
							format='%.6f',
							key='env_firms_north' )
					
					firms_area_coordinates = (
							f'{float( firms_west )},{float( firms_south )},'
							f'{float( firms_east )},{float( firms_north )}'
					)
					firms_center_lat = (float( firms_south ) + float( firms_north )) / 2.0
					firms_center_lng = (float( firms_west ) + float( firms_east )) / 2.0
				
				firms_day_range = st.number_input(
					'Day Range',
					min_value=1,
					max_value=5,
					value=1,
					step=1,
					key='env_firms_day_range' )
				
				firms_use_date = st.checkbox(
					'Use Start Date',
					value=False,
					key='env_firms_use_date' )
				
				if firms_use_date:
					firms_date_value = st.date_input(
						'Date',
						value=dt.date.today( ),
						key='env_firms_date' )
					firms_date = firms_date_value.isoformat( )
				else:
					firms_date = ''
				
				firms_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_firms_timeout' )
				
				firms_btn_c1, firms_btn_c2 = st.columns( 2 )
				
				with firms_btn_c1:
					if st.button( 'Run FIRMS', key='env_firms_run',
							use_container_width=True ):
						try:
							service = Firms( )
							result = service.fetch_area(
								source=firms_source,
								area_coordinates=firms_area_coordinates,
								day_range=int( firms_day_range ),
								date=firms_date,
								time=int( firms_timeout ) )
							
							st.session_state[ 'env_last_source' ] = 'FIRMS'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = firms_center_lat
							st.session_state[ 'env_last_longitude' ] = firms_center_lng
							st.success( 'FIRMS request completed.' )
						
						except Exception as ex:
							st.error( f'FIRMS request failed: {ex}' )
				
				with firms_btn_c2:
					if st.button( 'Clear FIRMS Result', key='env_firms_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# EONET NATURAL EVENTS
			# ------------------------------------------------------------------
			with st.expander( '🌎 EONET Natural Events', expanded=False ):
				eonet_mode = st.selectbox(
					'Mode',
					options=[ 'events', 'categories' ],
					key='env_eonet_mode' )
				
				eonet_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_eonet_timeout' )
				
				if eonet_mode == 'events':
					eonet_source = st.text_input(
						'Source',
						value='',
						help='Optional EONET source identifier or comma-separated identifiers.',
						key='env_eonet_source' )
					
					eonet_category = st.text_input(
						'Category',
						value='',
						help='Optional EONET category identifier or comma-separated identifiers.',
						key='env_eonet_category' )
					
					eonet_status = st.selectbox(
						'Status',
						options=[ 'open', 'closed', 'all' ],
						key='env_eonet_status' )
					
					eonet_limit = st.number_input(
						'Limit',
						min_value=1,
						max_value=500,
						value=25,
						step=1,
						key='env_eonet_limit' )
					
					eonet_days = st.number_input(
						'Days',
						min_value=1,
						max_value=3650,
						value=30,
						step=1,
						key='env_eonet_days' )
					
					eonet_use_dates = st.checkbox(
						'Use Start / End Dates',
						value=False,
						key='env_eonet_use_dates' )
					
					if eonet_use_dates:
						eonet_date_c1, eonet_date_c2 = st.columns( 2 )
						with eonet_date_c1:
							eonet_start_value = st.date_input(
								'Start Date',
								value=dt.date.today( ) - dt.timedelta( days=30 ),
								key='env_eonet_start_date' )
						
						with eonet_date_c2:
							eonet_end_value = st.date_input(
								'End Date',
								value=dt.date.today( ),
								key='env_eonet_end_date' )
						
						eonet_start_date = eonet_start_value.isoformat( )
						eonet_end_date = eonet_end_value.isoformat( )
					
					else:
						eonet_start_date = ''
						eonet_end_date = ''
					
					eonet_use_bbox = st.checkbox(
						'Use Bounding Box',
						value=False,
						key='env_eonet_use_bbox' )
					
					if eonet_use_bbox:
						eonet_box_c1, eonet_box_c2 = st.columns( 2 )
						with eonet_box_c1:
							eonet_min_lon = st.number_input(
								'Min Longitude',
								value=-77.150000,
								format='%.6f',
								key='env_eonet_min_lon' )
							
							eonet_max_lat = st.number_input(
								'Max Latitude',
								value=39.000000,
								format='%.6f',
								key='env_eonet_max_lat' )
						
						with eonet_box_c2:
							eonet_max_lon = st.number_input(
								'Max Longitude',
								value=-76.900000,
								format='%.6f',
								key='env_eonet_max_lon' )
							
							eonet_min_lat = st.number_input(
								'Min Latitude',
								value=38.800000,
								format='%.6f',
								key='env_eonet_min_lat' )
						
						eonet_bbox = (
								f'{float( eonet_min_lon )},{float( eonet_max_lat )},'
								f'{float( eonet_max_lon )},{float( eonet_min_lat )}'
						)
						eonet_center_lat = (float( eonet_min_lat ) + float( eonet_max_lat )) / 2.0
						eonet_center_lng = (float( eonet_min_lon ) + float( eonet_max_lon )) / 2.0
					
					else:
						eonet_bbox = ''
						eonet_center_lat = None
						eonet_center_lng = None
				
				else:
					eonet_source = ''
					eonet_category = ''
					eonet_status = 'open'
					eonet_limit = 25
					eonet_days = 30
					eonet_start_date = ''
					eonet_end_date = ''
					eonet_bbox = ''
					eonet_center_lat = None
					eonet_center_lng = None
				
				eonet_btn_c1, eonet_btn_c2 = st.columns( 2 )
				
				with eonet_btn_c1:
					if st.button( 'Run EONET', key='env_eonet_run',
							use_container_width=True ):
						try:
							service = EoNet( )
							result = service.fetch(
								mode=eonet_mode,
								source=eonet_source,
								category=eonet_category,
								status=eonet_status,
								limit=int( eonet_limit ),
								days=int( eonet_days ),
								start_date=eonet_start_date,
								end_date=eonet_end_date,
								bbox=eonet_bbox,
								time=int( eonet_timeout ) )
							
							st.session_state[ 'env_last_source' ] = 'EONET'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = eonet_center_lat
							st.session_state[ 'env_last_longitude' ] = eonet_center_lng
							st.success( 'EONET request completed.' )
						
						except Exception as ex:
							st.error( f'EONET request failed: {ex}' )
				
				with eonet_btn_c2:
					if st.button( 'Clear EONET Result', key='env_eonet_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
						
		with enviro_c2:
			# ------------------------------------------------------------------
			# ENVIRONMENTAL RESULTS
			# ------------------------------------------------------------------
			st.markdown( '##### Environmental Results' )
			
			env_source = st.session_state.get( 'env_last_source', '' )
			env_result = st.session_state.get( 'env_last_result', { } )
			env_latitude = st.session_state.get( 'env_last_latitude', None )
			env_longitude = st.session_state.get( 'env_last_longitude', None )
			
			if not env_result:
				st.info(
					'No environmental results available. Run one of the Environmental expanders.' )
			
			else:
				if env_source:
					st.caption( f'Source: {env_source}' )
				
				summary = env_result.get( 'summary', None ) if isinstance( env_result,
					dict ) else None
				rows = env_result.get( 'rows', None ) if isinstance( env_result, dict ) else None
				
				if isinstance( summary, dict ) and summary:
					st.markdown( '##### Summary' )
					st.data_editor(
						pd.DataFrame( [ summary ] ),
						key='env_summary_table',
						use_container_width=True,
						disabled=True )
				
				if env_latitude is not None and env_longitude is not None:
					try:
						lat_value = float( env_latitude )
						lng_value = float( env_longitude )
						
						lat_c, lng_c = st.columns( 2 )
						with lat_c:
							st.metric( 'Latitude', f'{lat_value:.6f}' )
						with lng_c:
							st.metric( 'Longitude', f'{lng_value:.6f}' )
						
						preview_url = static_maps.pin(
							lat=lat_value,
							lng=lng_value,
							zoom=8,
							size='600x400' )
						
						st.image( preview_url )
					
					except Exception as ex:
						st.warning( f'Static map preview failed: {ex}' )
				
				if isinstance( rows, list ) and rows:
					st.markdown( '##### Rows' )
					st.data_editor(
						pd.DataFrame( rows ),
						key='env_rows_table',
						use_container_width=True,
						disabled=True )
				
				st.markdown( '##### Raw Result' )
				st.json( env_result )

# ==============================================================================
# ASTRONOMICAL MODE
# ==============================================================================
elif mode == 'Astronomical':
	left, center, right = st.columns( [ 0.025, 0.95, 0.025 ] )
	with center:
		st.subheader( 'Astronomical Data' )
		st.divider( )
		
		astro_c1, astro_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		
		with astro_c1:
			# ------------------------------------------------------------------
			# NAVAL OBSERVATORY
			# ------------------------------------------------------------------
			with st.expander( '🧭 Naval Observatory', expanded=True ):
				naval_date = st.date_input(
					'Date',
					value=dt.date.today( ),
					key='astro_naval_date' )
				
				naval_time_value = st.text_input(
					'Time',
					value='12:00:00',
					help='Use HH:MM, HH:MM:SS, or HH:MM:SS.S format.',
					key='astro_naval_time_value' )
				
				naval_c1, naval_c2 = st.columns( 2 )
				with naval_c1:
					naval_latitude = st.number_input(
						'Latitude',
						value=38.907200,
						format='%.6f',
						key='astro_naval_latitude' )
				
				with naval_c2:
					naval_longitude = st.number_input(
						'Longitude',
						value=-77.036900,
						format='%.6f',
						key='astro_naval_longitude' )
				
				naval_location_label = st.text_input(
					'Location Label',
					value='Washington, DC',
					key='astro_naval_location_label' )
				
				naval_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_naval_timeout' )
				
				naval_btn_c1, naval_btn_c2 = st.columns( 2 )
				
				with naval_btn_c1:
					if st.button( 'Run Naval Observatory', key='astro_naval_run',
							use_container_width=True ):
						try:
							service = NavalObservatory( )
							result = service.fetch(
								mode='celnav',
								date_value=naval_date.isoformat( ),
								time_value=naval_time_value,
								latitude=float( naval_latitude ),
								longitude=float( naval_longitude ),
								location_label=naval_location_label,
								time=int( naval_timeout ) )
							
							st.session_state[ 'astro_last_source' ] = 'Naval Observatory'
							st.session_state[ 'astro_last_result' ] = result or { }
							st.session_state[ 'astro_last_latitude' ] = naval_latitude
							st.session_state[ 'astro_last_longitude' ] = naval_longitude
							st.session_state[ 'astro_last_url' ] = ''
							st.success( 'Naval Observatory request completed.' )
						
						except Exception as ex:
							st.error( f'Naval Observatory request failed: {ex}' )
				
				with naval_btn_c2:
					if st.button( 'Clear Naval Result', key='astro_naval_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# SPACE WEATHER
			# ------------------------------------------------------------------
			with st.expander( '☀️ Space Weather', expanded=False ):
				space_mode = st.selectbox(
					'Mode',
					options=[
							'cme',
							'cme_analysis',
							'gst',
							'ips',
							'flr',
							'sep',
							'mpc',
							'rbe',
							'hss',
							'wsa_enlil',
							'notifications'
					],
					key='astro_space_mode' )
				
				space_date_c1, space_date_c2 = st.columns( 2 )
				with space_date_c1:
					space_start = st.date_input(
						'Start Date',
						value=dt.date.today( ) - dt.timedelta( days=7 ),
						key='astro_space_start_date' )
				
				with space_date_c2:
					space_end = st.date_input(
						'End Date',
						value=dt.date.today( ),
						key='astro_space_end_date' )
				
				space_location = st.text_input(
					'Location',
					value='ALL',
					key='astro_space_location' )
				
				space_catalog = st.text_input(
					'Catalog',
					value='ALL',
					key='astro_space_catalog' )
				
				space_notification_type = st.text_input(
					'Notification Type',
					value='all',
					key='astro_space_notification_type' )
				
				space_c1, space_c2 = st.columns( 2 )
				with space_c1:
					space_most_accurate_only = st.checkbox(
						'Most Accurate Only',
						value=True,
						key='astro_space_most_accurate_only' )
					
					space_complete_entry_only = st.checkbox(
						'Complete Entry Only',
						value=True,
						key='astro_space_complete_entry_only' )
				
				with space_c2:
					space_speed = st.number_input(
						'Speed',
						min_value=0,
						max_value=5000,
						value=0,
						step=10,
						key='astro_space_speed' )
					
					space_half_angle = st.number_input(
						'Half Angle',
						min_value=0,
						max_value=360,
						value=0,
						step=1,
						key='astro_space_half_angle' )
				
				space_keyword = st.text_input(
					'Keyword',
					value='',
					key='astro_space_keyword' )
				
				space_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_space_timeout' )
				
				space_btn_c1, space_btn_c2 = st.columns( 2 )
				
				with space_btn_c1:
					if st.button( 'Run Space Weather', key='astro_space_run',
							use_container_width=True ):
						try:
							service = SpaceWeather( )
							result = service.fetch(
								mode=space_mode,
								start_date=space_start.isoformat( ),
								end_date=space_end.isoformat( ),
								time=int( space_timeout ),
								location=space_location,
								catalog=space_catalog,
								notification_type=space_notification_type,
								most_accurate_only=bool( space_most_accurate_only ),
								complete_entry_only=bool( space_complete_entry_only ),
								speed=int( space_speed ),
								half_angle=int( space_half_angle ),
								keyword=space_keyword,
								api_key=getattr( cfg, 'NASA_API_KEY', None ) )
							
							st.session_state[ 'astro_last_source' ] = 'Space Weather'
							st.session_state[ 'astro_last_result' ] = result or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = ''
							st.success( 'Space Weather request completed.' )
						
						except Exception as ex:
							st.error( f'Space Weather request failed: {ex}' )
				
				with space_btn_c2:
					if st.button( 'Clear Space Weather Result', key='astro_space_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# STAR CHART
			# ------------------------------------------------------------------
			with st.expander( '✨ Star Chart', expanded=False ):
				chart_mode = st.selectbox(
					'Mode',
					options=[
							'Object Chart',
							'Coordinate Chart',
							'Static Chart'
					],
					key='astro_chart_mode' )
				
				chart_zoom = st.number_input(
					'Zoom',
					min_value=1,
					max_value=20,
					value=5,
					step=1,
					key='astro_chart_zoom' )
				
				chart_image_source = st.text_input(
					'Image Source',
					value='DSS2',
					key='astro_chart_image_source' )
				
				if chart_mode == 'Object Chart':
					chart_object_name = st.text_input(
						'Object Name',
						value='M31',
						key='astro_chart_object_name' )
					
					chart_ra = 0.0
					chart_dec = 0.0
				
				else:
					chart_object_name = ''
					coord_c1, coord_c2 = st.columns( 2 )
					with coord_c1:
						chart_ra = st.number_input(
							'Right Ascension',
							value=10.6847083,
							format='%.7f',
							key='astro_chart_ra' )
					
					with coord_c2:
						chart_dec = st.number_input(
							'Declination',
							value=41.2687500,
							format='%.7f',
							key='astro_chart_dec' )
				
				chart_box_color = st.selectbox(
					'Box Color',
					options=[ 'yellow', 'red', 'green', 'blue', 'white' ],
					key='astro_chart_box_color' )
				
				chart_options_c1, chart_options_c2 = st.columns( 2 )
				with chart_options_c1:
					chart_show_box = st.checkbox(
						'Show Box',
						value=True,
						key='astro_chart_show_box' )
					
					chart_show_grid = st.checkbox(
						'Show Grid',
						value=True,
						key='astro_chart_show_grid' )
				
				with chart_options_c2:
					chart_show_lines = st.checkbox(
						'Show Lines',
						value=True,
						key='astro_chart_show_lines' )
					
					chart_show_boundaries = st.checkbox(
						'Show Boundaries',
						value=True,
						key='astro_chart_show_boundaries' )
				
				if chart_mode == 'Static Chart':
					static_c1, static_c2 = st.columns( 2 )
					with static_c1:
						chart_width = st.number_input(
							'Width',
							min_value=250,
							max_value=2500,
							value=900,
							step=50,
							key='astro_chart_width' )
						
						chart_magnitude = st.number_input(
							'Magnitude',
							min_value=0.0,
							max_value=20.0,
							value=7.5,
							step=0.1,
							format='%.1f',
							key='astro_chart_magnitude' )
					
					with static_c2:
						chart_height = st.number_input(
							'Height',
							min_value=250,
							max_value=2500,
							value=450,
							step=50,
							key='astro_chart_height' )
						
						chart_show_const_names = st.checkbox(
							'Show Constellation Names',
							value=False,
							key='astro_chart_show_const_names' )
				
				else:
					chart_width = 900
					chart_height = 450
					chart_magnitude = 7.5
					chart_show_const_names = False
				
				chart_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_chart_timeout' )
				
				chart_btn_c1, chart_btn_c2 = st.columns( 2 )
				
				with chart_btn_c1:
					if st.button( 'Run Star Chart', key='astro_chart_run',
							use_container_width=True ):
						try:
							service = StarChart( )
							
							if chart_mode == 'Object Chart':
								if not chart_object_name:
									st.warning( 'Enter an object name.' )
									result = None
								else:
									result = service.fetch_object_chart(
										name=chart_object_name,
										zoom=int( chart_zoom ),
										box_color=chart_box_color,
										show_box=bool( chart_show_box ),
										image_source=chart_image_source,
										time=int( chart_timeout ) )
							
							elif chart_mode == 'Coordinate Chart':
								result = service.fetch_coordinate_chart(
									ra=float( chart_ra ),
									dec=float( chart_dec ),
									zoom=int( chart_zoom ),
									box_color=chart_box_color,
									show_box=bool( chart_show_box ),
									show_grid=bool( chart_show_grid ),
									show_lines=bool( chart_show_lines ),
									show_boundaries=bool( chart_show_boundaries ),
									image_source=chart_image_source )
							
							else:
								result = service.fetch_static_chart(
									ra=float( chart_ra ),
									dec=float( chart_dec ),
									zoom=int( chart_zoom ),
									image_source=chart_image_source,
									show_grid=bool( chart_show_grid ),
									show_lines=bool( chart_show_lines ),
									show_boundaries=bool( chart_show_boundaries ),
									show_const_names=bool( chart_show_const_names ),
									width=int( chart_width ),
									height=int( chart_height ),
									magnitude=float( chart_magnitude ) )
							
							if result is not None:
								result_url = ''
								if isinstance( result, dict ):
									result_url = (
											result.get( 'chart_url', '' )
											or result.get( 'image_url', '' )
											or result.get( 'static_chart_url', '' )
											or result.get( 'preferred_image_url', '' )
											or result.get( 'snapshot_page_url', '' )
									)
								
								st.session_state[ 'astro_last_source' ] = 'Star Chart'
								st.session_state[ 'astro_last_result' ] = result or { }
								st.session_state[ 'astro_last_latitude' ] = None
								st.session_state[ 'astro_last_longitude' ] = None
								st.session_state[ 'astro_last_url' ] = result_url
								st.success( 'Star Chart request completed.' )
						
						except Exception as ex:
							st.error( f'Star Chart request failed: {ex}' )
				
				with chart_btn_c2:
					if st.button( 'Clear Star Chart Result', key='astro_chart_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# SATELLITE CENTER
			# ------------------------------------------------------------------
			with st.expander( '🛰️ Satellite Center', expanded=False ):
				satellite_mode = st.selectbox(
					'Mode',
					options=[ 'observatories', 'ground_stations', 'locations' ],
					key='astro_satellite_mode' )
				
				satellite_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_satellite_timeout' )
				
				if satellite_mode == 'locations':
					satellite_query = st.text_input(
						'Observatories',
						value='iss',
						help='Comma-separated observatory identifiers such as iss or mms1,mms2.',
						key='astro_satellite_query' )
					
					satellite_start_date = st.date_input(
						'Start Date',
						value=dt.date.today( ) - dt.timedelta( days=1 ),
						key='astro_satellite_start_date' )
					
					satellite_start_time = st.text_input(
						'Start Time',
						value='00:00:00Z',
						help='Use UTC time ending in Z.',
						key='astro_satellite_start_time' )
					
					satellite_end_date = st.date_input(
						'End Date',
						value=dt.date.today( ),
						key='astro_satellite_end_date' )
					
					satellite_end_time = st.text_input(
						'End Time',
						value='00:00:00Z',
						help='Use UTC time ending in Z.',
						key='astro_satellite_end_time' )
					
					satellite_coordinate_systems = st.text_input(
						'Coordinate Systems',
						value='gse',
						help='Comma-separated coordinate systems such as gse, geo, or gsm.',
						key='astro_satellite_coordinate_systems' )
					
					satellite_resolution_factor = st.number_input(
						'Resolution Factor',
						min_value=1,
						max_value=10000,
						value=1,
						step=1,
						key='astro_satellite_resolution_factor' )
				
				else:
					satellite_query = ''
					satellite_start_date = dt.date.today( )
					satellite_start_time = ''
					satellite_end_date = dt.date.today( )
					satellite_end_time = ''
					satellite_coordinate_systems = 'gse'
					satellite_resolution_factor = 1
				
				satellite_btn_c1, satellite_btn_c2 = st.columns( 2 )
				
				with satellite_btn_c1:
					if st.button( 'Run Satellite Center', key='astro_satellite_run',
							use_container_width=True ):
						try:
							service = SatelliteCenter( )
							
							if satellite_mode == 'locations':
								start_value = f'{satellite_start_date.isoformat( )}T{satellite_start_time}'
								end_value = f'{satellite_end_date.isoformat( )}T{satellite_end_time}'
							else:
								start_value = ''
								end_value = ''
							
							result = service.fetch(
								mode=satellite_mode,
								query=satellite_query,
								start_time=start_value,
								end_time=end_value,
								coordinate_systems=satellite_coordinate_systems,
								resolution_factor=int( satellite_resolution_factor ),
								time=int( satellite_timeout ) )
							
							st.session_state[ 'astro_last_source' ] = 'Satellite Center'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = ''
							st.success( 'Satellite Center request completed.' )
						
						except Exception as ex:
							st.error( f'Satellite Center request failed: {ex}' )
				
				with satellite_btn_c2:
					if st.button( 'Clear Satellite Result', key='astro_satellite_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# ASTRO CATALOG
			# ------------------------------------------------------------------
			with st.expander( '🔭 Astro Catalog', expanded=False ):
				catalog_mode = st.selectbox(
					'Mode',
					options=[ 'object_query', 'cone_search' ],
					key='astro_catalog_mode' )
				
				catalog_quantity = st.text_input(
					'Quantity',
					value='',
					help='Optional Open Astronomy Catalog quantity path segment.',
					key='astro_catalog_quantity' )
				
				catalog_attributes = st.text_input(
					'Attributes',
					value='',
					help='Optional comma-separated attribute path segments.',
					key='astro_catalog_attributes' )
				
				catalog_arguments = st.text_area(
					'Arguments',
					value='',
					help='Optional comma-separated or newline-separated key=value arguments.',
					key='astro_catalog_arguments' )
				
				catalog_data_format = st.selectbox(
					'Data Format',
					options=[ 'json', 'csv' ],
					key='astro_catalog_data_format' )
				
				catalog_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_catalog_timeout' )
				
				if catalog_mode == 'object_query':
					catalog_query = st.text_input(
						'Object Name',
						value='SN2011fe',
						key='astro_catalog_query' )
					
					catalog_ra = ''
					catalog_dec = ''
					catalog_radius = 2
				
				else:
					catalog_query = ''
					catalog_ra = st.text_input(
						'Right Ascension',
						value='10:00:00',
						key='astro_catalog_ra' )
					
					catalog_dec = st.text_input(
						'Declination',
						value='+10:00:00',
						key='astro_catalog_dec' )
					
					catalog_radius = st.number_input(
						'Radius',
						min_value=1,
						max_value=360,
						value=2,
						step=1,
						key='astro_catalog_radius' )
				
				catalog_btn_c1, catalog_btn_c2 = st.columns( 2 )
				
				with catalog_btn_c1:
					if st.button( 'Run Astro Catalog', key='astro_catalog_run',
							use_container_width=True ):
						try:
							service = AstroCatalog( )
							result = service.fetch(
								mode=catalog_mode,
								query=catalog_query,
								quantity=catalog_quantity,
								attributes=catalog_attributes,
								arguments=catalog_arguments,
								ra=catalog_ra,
								dec=catalog_dec,
								radius=int( catalog_radius ),
								data_format=catalog_data_format,
								time=int( catalog_timeout ) )
							
							st.session_state[ 'astro_last_source' ] = 'Astro Catalog'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = ''
							st.success( 'Astro Catalog request completed.' )
						
						except Exception as ex:
							st.error( f'Astro Catalog request failed: {ex}' )
				
				with catalog_btn_c2:
					if st.button( 'Clear Astro Catalog Result', key='astro_catalog_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# ASTROQUERY / SIMBAD
			# ------------------------------------------------------------------
			with st.expander( '🌌 AstroQuery / SIMBAD', expanded=False ):
				astroquery_mode = st.selectbox(
					'Mode',
					options=[ 'object_search', 'object_ids', 'region_search' ],
					key='astro_astroquery_mode' )
				
				astroquery_row_limit = st.number_input(
					'Row Limit',
					min_value=1,
					max_value=10000,
					value=100,
					step=1,
					key='astro_astroquery_row_limit' )
				
				if astroquery_mode in [ 'object_search', 'object_ids' ]:
					astroquery_query = st.text_input(
						'Object Name',
						value='M31',
						key='astro_astroquery_query' )
					
					astroquery_ra = ''
					astroquery_dec = ''
					astroquery_radius = 0.5
					astroquery_radius_unit = 'deg'
				
				else:
					astroquery_query = ''
					astroquery_ra = st.text_input(
						'Right Ascension',
						value='10.6847083',
						key='astro_astroquery_ra' )
					
					astroquery_dec = st.text_input(
						'Declination',
						value='41.2687500',
						key='astro_astroquery_dec' )
					
					astroquery_radius = st.number_input(
						'Radius',
						min_value=0.001,
						max_value=180.0,
						value=0.5,
						step=0.1,
						format='%.3f',
						key='astro_astroquery_radius' )
					
					astroquery_radius_unit = st.selectbox(
						'Radius Unit',
						options=[ 'deg', 'arcmin', 'arcsec' ],
						key='astro_astroquery_radius_unit' )
				
				astroquery_btn_c1, astroquery_btn_c2 = st.columns( 2 )
				
				with astroquery_btn_c1:
					if st.button( 'Run AstroQuery', key='astro_astroquery_run',
							use_container_width=True ):
						try:
							service = AstroQuery( )
							result = service.fetch(
								mode=astroquery_mode,
								query=astroquery_query,
								ra=astroquery_ra,
								dec=astroquery_dec,
								radius=float( astroquery_radius ),
								radius_unit=astroquery_radius_unit,
								row_limit=int( astroquery_row_limit ) )
							
							st.session_state[ 'astro_last_source' ] = 'AstroQuery / SIMBAD'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = ''
							st.success( 'AstroQuery request completed.' )
						
						except Exception as ex:
							st.error( f'AstroQuery request failed: {ex}' )
				
				with astroquery_btn_c2:
					if st.button( 'Clear AstroQuery Result', key='astro_astroquery_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# STAR MAP
			# ------------------------------------------------------------------
			with st.expander( '🗺️ Star Map', expanded=False ):
				starmap_mode = st.selectbox(
					'Mode',
					options=[ 'object_link', 'coordinate_link', 'snapshot' ],
					key='astro_starmap_mode' )
				
				starmap_zoom = st.number_input(
					'Zoom',
					min_value=1,
					max_value=20,
					value=5,
					step=1,
					key='astro_starmap_zoom' )
				
				starmap_image_source = st.text_input(
					'Image Source',
					value='DSS2',
					key='astro_starmap_image_source' )
				
				starmap_box_color = st.selectbox(
					'Box Color',
					options=[ 'yellow', 'red', 'green', 'blue', 'white' ],
					key='astro_starmap_box_color' )
				
				if starmap_mode == 'object_link':
					starmap_query = st.text_input(
						'Object Name',
						value='M31',
						key='astro_starmap_query' )
					
					starmap_ra = 0.0
					starmap_dec = 0.0
				
				else:
					starmap_query = ''
					starmap_coord_c1, starmap_coord_c2 = st.columns( 2 )
					with starmap_coord_c1:
						starmap_ra = st.number_input(
							'Right Ascension',
							value=10.6847083,
							format='%.7f',
							key='astro_starmap_ra' )
					
					with starmap_coord_c2:
						starmap_dec = st.number_input(
							'Declination',
							value=41.2687500,
							format='%.7f',
							key='astro_starmap_dec' )
				
				starmap_options_c1, starmap_options_c2 = st.columns( 2 )
				with starmap_options_c1:
					starmap_show_box = st.checkbox(
						'Show Box',
						value=True,
						key='astro_starmap_show_box' )
					
					starmap_show_grid = st.checkbox(
						'Show Grid',
						value=True,
						key='astro_starmap_show_grid' )
				
				with starmap_options_c2:
					starmap_show_lines = st.checkbox(
						'Show Lines',
						value=True,
						key='astro_starmap_show_lines' )
					
					starmap_show_boundaries = st.checkbox(
						'Show Boundaries',
						value=True,
						key='astro_starmap_show_boundaries' )
				
				starmap_show_const_names = st.checkbox(
					'Show Constellation Names',
					value=False,
					key='astro_starmap_show_const_names' )
				
				starmap_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_starmap_timeout' )
				
				starmap_btn_c1, starmap_btn_c2 = st.columns( 2 )
				
				with starmap_btn_c1:
					if st.button( 'Run Star Map', key='astro_starmap_run',
							use_container_width=True ):
						try:
							service = StarMap( )
							result = service.fetch(
								mode=starmap_mode,
								query=starmap_query,
								ra=float( starmap_ra ),
								dec=float( starmap_dec ),
								zoom=int( starmap_zoom ),
								image_source=starmap_image_source,
								box_color=starmap_box_color,
								show_box=bool( starmap_show_box ),
								show_grid=bool( starmap_show_grid ),
								show_lines=bool( starmap_show_lines ),
								show_boundaries=bool( starmap_show_boundaries ),
								show_const_names=bool( starmap_show_const_names ),
								time=int( starmap_timeout ) )
							
							result_url = ''
							if isinstance( result, dict ):
								result_url = (
										result.get( 'preferred_image_url', '' )
										or result.get( 'snapshot_page_url', '' )
										or result.get( 'object_page_url', '' )
										or result.get( 'coordinate_page_url', '' )
										or result.get( 'url', '' )
								)
							
							st.session_state[ 'astro_last_source' ] = 'Star Map'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = result_url
							st.success( 'Star Map request completed.' )
						
						except Exception as ex:
							st.error( f'Star Map request failed: {ex}' )
				
				with starmap_btn_c2:
					if st.button( 'Clear Star Map Result', key='astro_starmap_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
						
		with astro_c2:
			# ------------------------------------------------------------------
			# ASTRONOMICAL RESULTS
			# ------------------------------------------------------------------
			st.markdown( '##### Astronomical Results' )
			
			astro_source = st.session_state.get( 'astro_last_source', '' )
			astro_result = st.session_state.get( 'astro_last_result', { } )
			astro_latitude = st.session_state.get( 'astro_last_latitude', None )
			astro_longitude = st.session_state.get( 'astro_last_longitude', None )
			astro_url = st.session_state.get( 'astro_last_url', '' )
			
			if not astro_result:
				st.info( 'No astronomical results available. Run one of the Astronomical expanders.' )
			
			else:
				if astro_source:
					st.caption( f'Source: {astro_source}' )
				
				if astro_latitude is not None and astro_longitude is not None:
					try:
						lat_value = float( astro_latitude )
						lng_value = float( astro_longitude )
						
						lat_c, lng_c = st.columns( 2 )
						with lat_c:
							st.metric( 'Latitude', f'{lat_value:.6f}' )
						with lng_c:
							st.metric( 'Longitude', f'{lng_value:.6f}' )
						
						preview_url = static_maps.pin(
							lat=lat_value,
							lng=lng_value,
							zoom=6,
							size='600x400' )
						
						st.image( preview_url )
					
					except Exception as ex:
						st.warning( f'Static map preview failed: {ex}' )
				
				if astro_url:
					st.markdown( '##### Generated Link' )
					st.markdown( f'[Open Generated Astronomical Resource]({astro_url})' )
					
					try:
						if any( astro_url.lower( ).endswith( ext ) for ext in
						        [ '.png', '.jpg', '.jpeg' ] ):
							st.image( astro_url )
					except Exception:
						pass
				
				summary = astro_result.get( 'summary', None ) if isinstance( astro_result,
					dict ) else None
				
				if isinstance( summary, dict ) and summary:
					st.markdown( '##### Summary' )
					st.data_editor(
						pd.DataFrame( [ summary ] ),
						key='astro_summary_table',
						use_container_width=True,
						disabled=True )
				
					
				columns = astro_result.get( 'columns', None ) if isinstance( astro_result,
					dict ) else None
				rows = astro_result.get( 'rows', None ) if isinstance( astro_result, dict ) else None
				
				if isinstance( rows, list ) and rows:
					st.markdown( '##### Rows' )
					
					if isinstance( columns, list ) and columns:
						df_astro_rows = pd.DataFrame( rows, columns=columns )
					else:
						df_astro_rows = pd.DataFrame( rows )
					
					st.data_editor( df_astro_rows, key='astro_rows_table',
						use_container_width=True, disabled=True )
					
				st.markdown( '##### Raw Result' )
				st.json( astro_result )

# ==============================================================================
# GEOLOGICAL MODE
# ==============================================================================
elif mode == 'Geological':
	left, center, right = st.columns( [ 0.025, 0.95, 0.025 ] )
	with center:
		st.subheader( 'Geological Data' )
		st.divider( )
		
		geo_c1, geo_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		
		with geo_c1:
			# ------------------------------------------------------------------
			# USGS EARTHQUAKES
			# ------------------------------------------------------------------
			with st.expander( '🌎 USGS Earthquakes', expanded=True ):
				quake_mode = st.selectbox(
					'Mode',
					options=[ 'feed', 'search' ],
					key='geo_quake_mode' )
				
				quake_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='geo_quake_timeout' )
				
				if quake_mode == 'feed':
					quake_feed = st.selectbox(
						'Feed',
						options=[
								'all_hour.geojson',
								'all_day.geojson',
								'all_week.geojson',
								'all_month.geojson',
								'1.0_hour.geojson',
								'1.0_day.geojson',
								'1.0_week.geojson',
								'1.0_month.geojson',
								'2.5_hour.geojson',
								'2.5_day.geojson',
								'2.5_week.geojson',
								'2.5_month.geojson',
								'4.5_hour.geojson',
								'4.5_day.geojson',
								'4.5_week.geojson',
								'4.5_month.geojson',
								'significant_hour.geojson',
								'significant_day.geojson',
								'significant_week.geojson',
								'significant_month.geojson'
						],
						key='geo_quake_feed' )
					
					quake_start_date = ''
					quake_end_date = ''
					quake_min_magnitude = 1.0
					quake_max_magnitude = 10.0
					quake_limit = 25
					quake_order_by = 'time'
					quake_event_type = 'earthquake'
					quake_use_location = False
					quake_latitude = None
					quake_longitude = None
					quake_radius = None
				
				else:
					quake_feed = 'all_day.geojson'
					
					search_c1, search_c2 = st.columns( 2 )
					with search_c1:
						quake_start = st.date_input(
							'Start Date',
							value=dt.date.today( ) - dt.timedelta( days=7 ),
							key='geo_quake_start_date' )
					with search_c2:
						quake_end = st.date_input(
							'End Date',
							value=dt.date.today( ),
							key='geo_quake_end_date' )
					
					quake_start_date = quake_start.isoformat( )
					quake_end_date = quake_end.isoformat( )
					
					mag_c1, mag_c2 = st.columns( 2 )
					with mag_c1:
						quake_min_magnitude = st.number_input(
							'Minimum Magnitude',
							min_value=0.0,
							max_value=10.0,
							value=1.0,
							step=0.1,
							format='%.1f',
							key='geo_quake_min_magnitude' )
					with mag_c2:
						quake_max_magnitude = st.number_input(
							'Maximum Magnitude',
							min_value=0.0,
							max_value=10.0,
							value=10.0,
							step=0.1,
							format='%.1f',
							key='geo_quake_max_magnitude' )
					
					quake_limit = st.number_input(
						'Limit',
						min_value=1,
						max_value=20000,
						value=25,
						step=1,
						key='geo_quake_limit' )
					
					quake_order_by = st.selectbox(
						'Order By',
						options=[ 'time', 'time-asc', 'magnitude', 'magnitude-asc' ],
						key='geo_quake_order_by' )
					
					quake_event_type = st.text_input(
						'Event Type',
						value='earthquake',
						key='geo_quake_event_type' )
					
					quake_use_location = st.checkbox(
						'Use Location Radius Filter',
						value=False,
						key='geo_quake_use_location' )
					
					if quake_use_location:
						loc_c1, loc_c2 = st.columns( 2 )
						with loc_c1:
							quake_latitude = st.number_input(
								'Latitude',
								value=38.907200,
								format='%.6f',
								key='geo_quake_latitude' )
						with loc_c2:
							quake_longitude = st.number_input(
								'Longitude',
								value=-77.036900,
								format='%.6f',
								key='geo_quake_longitude' )
						
						quake_radius = st.number_input(
							'Maximum Radius KM',
							min_value=1.0,
							max_value=20000.0,
							value=500.0,
							step=10.0,
							format='%.1f',
							key='geo_quake_radius' )
					
					else:
						quake_latitude = None
						quake_longitude = None
						quake_radius = None
				
				quake_btn_c1, quake_btn_c2 = st.columns( 2 )
				
				with quake_btn_c1:
					if st.button( 'Run USGS Earthquakes', key='geo_quake_run',
							use_container_width=True ):
						try:
							service = USGSEarthquakes( )
							
							result = service.fetch(
								mode=quake_mode,
								feed=quake_feed,
								start_date=quake_start_date,
								end_date=quake_end_date,
								min_magnitude=float( quake_min_magnitude ),
								max_magnitude=float( quake_max_magnitude ),
								limit=int( quake_limit ),
								order_by=quake_order_by,
								event_type=quake_event_type,
								latitude=quake_latitude,
								longitude=quake_longitude,
								max_radius_km=quake_radius,
								time=int( quake_timeout ) )
							
							st.session_state[ 'geo_last_source' ] = 'USGS Earthquakes'
							st.session_state[ 'geo_last_result' ] = result or { }
							st.session_state[ 'geo_last_latitude' ] = quake_latitude
							st.session_state[ 'geo_last_longitude' ] = quake_longitude
							st.success( 'USGS Earthquake request completed.' )
						
						except Exception as ex:
							st.error( f'USGS Earthquake request failed: {ex}' )
				
				with quake_btn_c2:
					if st.button( 'Clear Earthquake Result', key='geo_quake_clear',
							use_container_width=True ):
						st.session_state[ 'geo_last_source' ] = ''
						st.session_state[ 'geo_last_result' ] = { }
						st.session_state[ 'geo_last_latitude' ] = None
						st.session_state[ 'geo_last_longitude' ] = None
						st.session_state[ 'geo_last_image_path' ] = ''
			
			# ------------------------------------------------------------------
			# GLOBAL IMAGERY
			# ------------------------------------------------------------------
			with st.expander( '🛰️ Global Imagery', expanded=False ):
				st.caption(
					'Uses the original GlobalImagery fetcher. The current fetch_map_services() '
					'writes the default NASA GIBS image to python-examples.'
				)
				
				imagery_product = st.selectbox(
					'Product',
					options=[ 'NASA GIBS EPSG:4326 Default Map Service' ],
					key='geo_imagery_product' )
				
				imagery_btn_c1, imagery_btn_c2 = st.columns( 2 )
				
				with imagery_btn_c1:
					if st.button( 'Run Global Imagery', key='geo_imagery_run',
							use_container_width=True ):
						try:
							Path( 'python-examples' ).mkdir( parents=True, exist_ok=True )
							
							service = GlobalImagery( )
							result = service.fetch_map_services( )
							
							image_path = (
									'python-examples/'
									'MODIS_Terra_CorrectedReflectance_TrueColor.png'
							)
							
							st.session_state[ 'geo_last_source' ] = 'Global Imagery'
							st.session_state[ 'geo_last_result' ] = {
									'mode': 'fetch_map_services',
									'product': imagery_product,
									'image_path': image_path,
									'result': str( result )
							}
							st.session_state[ 'geo_last_latitude' ] = None
							st.session_state[ 'geo_last_longitude' ] = None
							st.session_state[ 'geo_last_image_path' ] = image_path
							st.success( 'Global Imagery request completed.' )
						
						except Exception as ex:
							st.error( f'Global Imagery request failed: {ex}' )
				
				with imagery_btn_c2:
					if st.button( 'Clear Imagery Result', key='geo_imagery_clear',
							use_container_width=True ):
						st.session_state[ 'geo_last_source' ] = ''
						st.session_state[ 'geo_last_result' ] = { }
						st.session_state[ 'geo_last_latitude' ] = None
						st.session_state[ 'geo_last_longitude' ] = None
						st.session_state[ 'geo_last_image_path' ] = ''
			
			# ------------------------------------------------------------------
			# USGS WATER DATA
			# ------------------------------------------------------------------
			with st.expander( '💧 USGS Water Data', expanded=False ):
				water_mode = st.selectbox(
					'Mode',
					options=[
							'monitoring-locations',
							'time-series-metadata',
							'latest-continuous',
							'latest-daily'
					],
					key='geo_water_mode' )
				
				water_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='geo_water_timeout' )
				
				water_limit = st.number_input(
					'Limit',
					min_value=1,
					max_value=1000,
					value=25,
					step=1,
					key='geo_water_limit' )
				
				if water_mode == 'monitoring-locations':
					water_monitoring_location_id = st.text_input(
						'Monitoring Location ID',
						value='',
						help='Optional. Example: USGS-01491000',
						key='geo_water_monitoring_location_id' )
					
					water_state_code = st.text_input(
						'State Code',
						value='',
						help='Optional state filter.',
						key='geo_water_state_code' )
					
					water_county_code = st.text_input(
						'County Code',
						value='',
						help='Optional county filter.',
						key='geo_water_county_code' )
					
					water_site_type = st.text_input(
						'Site Type',
						value='',
						help='Optional site type filter.',
						key='geo_water_site_type' )
					
					water_parameter_code = ''
				
				else:
					water_monitoring_location_id = st.text_input(
						'Monitoring Location ID',
						value='USGS-01491000',
						help='Example: USGS-01491000',
						key='geo_water_monitoring_location_id_value' )
					
					water_parameter_code = st.text_input(
						'Parameter Code',
						value='',
						help='Optional USGS parameter code.',
						key='geo_water_parameter_code' )
					
					water_state_code = ''
					water_county_code = ''
					water_site_type = ''
				
				water_btn_c1, water_btn_c2 = st.columns( 2 )
				
				with water_btn_c1:
					if st.button( 'Run USGS Water Data', key='geo_water_run',
							use_container_width=True ):
						try:
							service = USGSWaterData( )
							result = service.fetch(
								mode=water_mode,
								monitoring_location_id=water_monitoring_location_id,
								state_code=water_state_code,
								county_code=water_county_code,
								site_type=water_site_type,
								parameter_code=water_parameter_code,
								limit=int( water_limit ),
								time=int( water_timeout ) )
							
							st.session_state[ 'geo_last_source' ] = 'USGS Water Data'
							st.session_state[ 'geo_last_result' ] = result or { }
							st.session_state[ 'geo_last_latitude' ] = None
							st.session_state[ 'geo_last_longitude' ] = None
							st.session_state[ 'geo_last_image_path' ] = ''
							st.success( 'USGS Water Data request completed.' )
						
						except Exception as ex:
							st.error( f'USGS Water Data request failed: {ex}' )
				
				with water_btn_c2:
					if st.button( 'Clear Water Data Result', key='geo_water_clear',
							use_container_width=True ):
						st.session_state[ 'geo_last_source' ] = ''
						st.session_state[ 'geo_last_result' ] = { }
						st.session_state[ 'geo_last_latitude' ] = None
						st.session_state[ 'geo_last_longitude' ] = None
						st.session_state[ 'geo_last_image_path' ] = ''
			
			# ------------------------------------------------------------------
			# USGS THE NATIONAL MAP
			# ------------------------------------------------------------------
			with st.expander( '🗺️ USGS The National Map', expanded=False ):
				tnm_mode = st.selectbox(
					'Mode',
					options=[ 'datasets', 'products' ],
					key='geo_tnm_mode' )
				
				tnm_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='geo_tnm_timeout' )
				
				if tnm_mode == 'datasets':
					tnm_dataset = ''
					tnm_query = ''
					tnm_bbox = ''
					tnm_prod_formats = ''
					tnm_max_items = 25
					tnm_offset = 0
					tnm_center_lat = None
					tnm_center_lng = None
				
				else:
					tnm_dataset = st.text_input(
						'Dataset',
						value='',
						help='Optional TNM dataset filter.',
						key='geo_tnm_dataset' )
					
					tnm_query = st.text_input(
						'Search Query',
						value='',
						help='Optional free-text product search.',
						key='geo_tnm_query' )
					
					tnm_prod_formats = st.text_input(
						'Product Formats',
						value='',
						help='Optional format filter such as GeoTIFF, IMG, LAS, or LAZ.',
						key='geo_tnm_prod_formats' )
					
					tnm_use_bbox = st.checkbox(
						'Use Bounding Box',
						value=False,
						key='geo_tnm_use_bbox' )
					
					if tnm_use_bbox:
						tnm_box_c1, tnm_box_c2 = st.columns( 2 )
						with tnm_box_c1:
							tnm_min_x = st.number_input(
								'Min X / West Longitude',
								value=-77.150000,
								format='%.6f',
								key='geo_tnm_min_x' )
							
							tnm_min_y = st.number_input(
								'Min Y / South Latitude',
								value=38.800000,
								format='%.6f',
								key='geo_tnm_min_y' )
						
						with tnm_box_c2:
							tnm_max_x = st.number_input(
								'Max X / East Longitude',
								value=-76.900000,
								format='%.6f',
								key='geo_tnm_max_x' )
							
							tnm_max_y = st.number_input(
								'Max Y / North Latitude',
								value=39.000000,
								format='%.6f',
								key='geo_tnm_max_y' )
						
						tnm_bbox = (
								f'{float( tnm_min_x )},{float( tnm_min_y )},'
								f'{float( tnm_max_x )},{float( tnm_max_y )}'
						)
						tnm_center_lat = (float( tnm_min_y ) + float( tnm_max_y )) / 2.0
						tnm_center_lng = (float( tnm_min_x ) + float( tnm_max_x )) / 2.0
					
					else:
						tnm_bbox = ''
						tnm_center_lat = None
						tnm_center_lng = None
					
					tnm_max_items = st.number_input(
						'Max Items',
						min_value=1,
						max_value=1000,
						value=25,
						step=1,
						key='geo_tnm_max_items' )
					
					tnm_offset = st.number_input(
						'Offset',
						min_value=0,
						max_value=100000,
						value=0,
						step=1,
						key='geo_tnm_offset' )
				
				tnm_btn_c1, tnm_btn_c2 = st.columns( 2 )
				
				with tnm_btn_c1:
					if st.button( 'Run The National Map', key='geo_tnm_run',
							use_container_width=True ):
						try:
							service = USGSTheNationalMap( )
							result = service.fetch(
								mode=tnm_mode,
								dataset=tnm_dataset,
								q=tnm_query,
								bbox=tnm_bbox,
								prod_formats=tnm_prod_formats,
								max_items=int( tnm_max_items ),
								offset=int( tnm_offset ),
								time=int( tnm_timeout ) )
							
							st.session_state[ 'geo_last_source' ] = 'USGS The National Map'
							st.session_state[ 'geo_last_result' ] = result or { }
							st.session_state[ 'geo_last_latitude' ] = tnm_center_lat
							st.session_state[ 'geo_last_longitude' ] = tnm_center_lng
							st.session_state[ 'geo_last_image_path' ] = ''
							st.success( 'USGS The National Map request completed.' )
						
						except Exception as ex:
							st.error( f'USGS The National Map request failed: {ex}' )
				
				with tnm_btn_c2:
					if st.button( 'Clear National Map Result', key='geo_tnm_clear',
							use_container_width=True ):
						st.session_state[ 'geo_last_source' ] = ''
						st.session_state[ 'geo_last_result' ] = { }
						st.session_state[ 'geo_last_latitude' ] = None
						st.session_state[ 'geo_last_longitude' ] = None
						st.session_state[ 'geo_last_image_path' ] = ''
						
		with geo_c2:
			# ------------------------------------------------------------------
			# GEOLOGICAL RESULTS
			# ------------------------------------------------------------------
			st.markdown( '##### Geological Results' )
			
			geo_source = st.session_state.get( 'geo_last_source', '' )
			geo_result = st.session_state.get( 'geo_last_result', { } )
			geo_latitude = st.session_state.get( 'geo_last_latitude', None )
			geo_longitude = st.session_state.get( 'geo_last_longitude', None )
			geo_image_path = st.session_state.get( 'geo_last_image_path', '' )
			
			if not geo_result:
				st.info( 'No geological results available. Run one of the Geological expanders.' )
			
			else:
				if geo_source:
					st.caption( f'Source: {geo_source}' )
				
				if geo_image_path and os.path.exists( geo_image_path ):
					st.markdown( '##### Image Output' )
					st.image( geo_image_path )
				
				summary = geo_result.get( 'summary', None ) if isinstance( geo_result,
					dict ) else None
				rows = geo_result.get( 'rows', None ) if isinstance( geo_result, dict ) else None
				
				if isinstance( summary, dict ) and summary:
					st.markdown( '##### Summary' )
					st.data_editor(
						pd.DataFrame( [ summary ] ),
						key='geo_summary_table',
						use_container_width=True,
						disabled=True )
				
				if geo_latitude is not None and geo_longitude is not None:
					try:
						lat_value = float( geo_latitude )
						lng_value = float( geo_longitude )
						
						lat_c, lng_c = st.columns( 2 )
						with lat_c:
							st.metric( 'Latitude', f'{lat_value:.6f}' )
						with lng_c:
							st.metric( 'Longitude', f'{lng_value:.6f}' )
						
						preview_url = static_maps.pin(
							lat=lat_value,
							lng=lng_value,
							zoom=5,
							size='600x400' )
						
						st.image( preview_url )
					
					except Exception as ex:
						st.warning( f'Static map preview failed: {ex}' )
				
				if isinstance( rows, list ) and rows:
					st.markdown( '##### Rows' )
					df_geo_rows = pd.DataFrame( rows )
					st.data_editor(
						df_geo_rows,
						key='geo_rows_table',
						use_container_width=True,
						disabled=True )
				
				st.markdown( '##### Raw Result' )
				st.json( geo_result )
		
# ==============================================================================
# Distance Matrix Tab
# ==============================================================================
elif mode == 'Distances':
	st.subheader( 'Distance Matrix' )
	st.divider( )
	
	col1, col2 = st.columns( 2 )
	with col1:
		origin = st.text_input( 'Origin', key='distance_origin' )
	
	with col2:
		destination = st.text_input( 'Destination', key='distance_destination' )
	
	travel_mode = st.selectbox(
		'Travel Mode',
		[ 'driving', 'walking', 'bicycling', 'transit' ],
		key='travel_key' )
	
	if st.button( 'Calculate Distance', key='distance_calculate' ):
		if not origin or not destination:
			st.warning( 'Provide both origin and destination.' )
		else:
			summary = distances.summary( origin, destination, mode=travel_mode )
			st.table( pd.DataFrame( [ summary ] ) )

# ==============================================================================
# STATIC MAPS
# ==============================================================================
elif mode == 'Maps':
	st.header( 'Static Map Preview' )
	st.divider( )
	
	lat = st.number_input( 'Latitude', value=0.0, format='%.6f' )
	lng = st.number_input( 'Longitude', value=0.0, format='%.6f' )
	zoom = st.slider( 'Zoom', 1, 20, 12 )
	size = st.selectbox( 'Image Size', [ '400x400', '600x400', '800x600' ], key='size_key' )
	
	if st.button( 'Generate Map' ):
		url = static_maps.pin( lat=lat, lng=lng, zoom=zoom, size=size, )
		st.image( url )
		st.code( url )

# ==============================================================================
# TIME ZONE MODE
# ==============================================================================
elif mode == 'Time Zones':
	st.subheader( 'Time Zone Lookup' )
	st.divider( )
	lat_tz = st.number_input( 'Latitude', key='tz_lat', value=0.0, format='%.6f', )
	lng_tz = st.number_input( 'Longitude', key='tz_lng', value=0.0, format='%.6f', )
	
	if st.button( 'Lookup Time Zone' ):
		result = timezone.lookup( lat_tz, lng_tz )
		st.json( result )

# ==============================================================================
# DATA UPLOAD MODE
# ==============================================================================
elif mode == 'Data Upload':
	st.subheader( 'Excel / CSV' )
	st.divider( )
	
	uploaded = st.file_uploader(
		'Upload CSV or XLSX',
		type=[ 'csv', 'xlsx' ],
		key='data_upload_file' )
	
	enrichment_mode = st.selectbox(
		'Enrichment Mode',
		options=[ 'City / State / Country', 'Address Column' ],
		key='data_upload_enrichment_mode' )
	
	if enrichment_mode == 'City / State / Country':
		city_col = st.text_input( 'City Column', value='City', key='data_upload_city_col' )
		state_col = st.text_input( 'State Column', value='State', key='data_upload_state_col' )
		country_col = st.text_input( 'Country Column', value='Country',
			key='data_upload_country_col' )
		address_col = ''
	
	else:
		address_col = st.text_input( 'Address Column', value='Address',
			key='data_upload_address_col' )
		country_col = st.text_input(
			'Country Bias Column',
			value='Country',
			help='Optional. Leave as-is if the uploaded file has no country-bias column.',
			key='data_upload_address_country_col' )
		city_col = ''
		state_col = ''
	
	sheet_name = st.text_input(
		'Worksheet',
		value='Sheet1',
		help='Used for Excel files. For CSV files this value is ignored.',
		key='data_upload_sheet_name' )
	
	if uploaded:
		input_path = f'_input_{uploaded.name}'
		output_path = f'_output_{uploaded.name}'
		
		with open( input_path, 'wb' ) as f:
			f.write( uploaded.read( ) )
		
		if st.button( 'Enrich File', key='data_upload_enrich' ):
			try:
				excel = Excel( api=api_key, cache=cache )
				sheet_value = sheet_name if input_path.lower( ).endswith( '.xlsx' ) else None
				
				if enrichment_mode == 'City / State / Country':
					excel.enrich(
						inpath=input_path,
						outpath=output_path,
						city=city_col,
						state=state_col,
						cntry=country_col,
						sheet=sheet_value )
				
				else:
					excel.enrich_from_address(
						inpath=input_path,
						outpath=output_path,
						address=address_col,
						sheet=sheet_value,
						cntry=country_col )
				
				if output_path.lower( ).endswith( '.csv' ):
					df_output = pd.read_csv( output_path )
				else:
					df_output = pd.read_excel( output_path )
				
				st.data_editor(
					df_output,
					key='data_upload_enriched_preview',
					use_container_width=True,
					disabled=True )
				
				with open( output_path, 'rb' ) as f:
					output_bytes = f.read( )
				
				st.download_button(
					'Download Enriched File',
					data=output_bytes,
					file_name=Path( output_path ).name,
					key='data_upload_download' )
			
			except Exception as e:
				st.error( f'Enrichment failed: {e}' )
			
			finally:
				try:
					if os.path.exists( input_path ):
						os.remove( input_path )
					if os.path.exists( output_path ):
						os.remove( output_path )
				except Exception:
					pass
		
# ==============================================================================
# DATA MANAGEMENT MODE
# ==============================================================================
elif mode == 'Data Management':
	st.subheader( 'Data Management' )
	st.divider( )
	left, center, right = st.columns( [ 0.05, 0.90, 0.05 ] )
	with center:
		st.markdown( '##### 🏛️ Database'  )
		tabs = st.tabs( [ 'Import', 'Browse', 'CRUD', 'Explore', 'Filter',
		                  'Aggregate', 'Visualize', 'Admin', 'SQL' ] )
		 
		tables = list_tables( )
		if not tables:
			st.info( "No tables available." )
		
		# ------------------------------------------------------------------------------
		# UPLOAD TAB
		# ------------------------------------------------------------------------------
		with tabs[ 0 ]:
			uploaded_file = st.file_uploader( 'Upload Excel File', type=[ 'xlsx' ] )
			overwrite = st.checkbox( 'Overwrite existing tables', value=True )
			if uploaded_file:
				try:
					sheets = pd.read_excel( uploaded_file, sheet_name=None )
					with create_connection( ) as conn:
						conn.execute( 'BEGIN' )
						for sheet_name, df in sheets.items( ):
							table_name = create_identifier( sheet_name )
							if overwrite:
								conn.execute( f'DROP TABLE IF EXISTS "{table_name}"' )
							
							# --- Create Table ---
							columns = [ ]
							df.columns = [ create_identifier( c ) for c in df.columns ]
							for col in df.columns:
								sql_type = get_sqlite_type( df[ col ].dtype )
								columns.append( f'"{col}" {sql_type}' )
							
							create_stmt = (
									f'CREATE TABLE "{table_name}" '
									f'({", ".join( columns )});'
							)
							
							conn.execute( create_stmt )
							
							# --- Insert Data ---
							placeholders = ", ".join( [ "?" ] * len( df.columns ) )
							insert_stmt = (
									f'INSERT INTO "{table_name}" '
									f'VALUES ({placeholders});'
							)
							
							conn.executemany( insert_stmt,
								df.where( pd.notnull( df ), None ).values.tolist( ) )
						
						conn.commit( )
					
					st.success( 'Import completed successfully (transaction committed).' )
					st.rerun( )
				
				except Exception as e:
					try:
						conn.rollback( )
					except:
						pass
					st.error( f'Import failed — transaction rolled back.\n\n{e}' )
		
		# ------------------------------------------------------------------------------
		# BROWSE TAB
		# ------------------------------------------------------------------------------
		with tabs[ 1 ]:
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Table', tables, key='table_name' )
				df = read_table( table )
				st.data_editor( df )
			else:
				st.info( 'No tables available.' )
		
		# ------------------------------------------------------------------------------
		# CRUD (Schema-Aware)
		# ------------------------------------------------------------------------------
		with tabs[ 2 ]:
			tables = list_tables( )
			if not tables:
				st.info( 'No tables available.' )
			else:
				crud_header_c1, crud_header_c2, crud_header_c3 = st.columns(
					[ 0.45, 0.25, 0.30 ], border=True )
				
				with crud_header_c1:
					table = st.selectbox( 'Select Table', tables, key='crud_table' )
				
				df = read_table( table )
				schema = create_schema( table )
				
				type_map = { col[ 1 ]: col[ 2 ].upper( ) for col in schema if col[ 1 ] != 'rowid' }
				
				with crud_header_c2:
					st.metric( 'Rows', len( df.index ) )
				
				with crud_header_c3:
					st.metric( 'Columns', len( type_map ) )
				
				st.divider( )
				
				insert_col, update_col = st.columns( [ 0.50, 0.50 ], border=True )
				
				# ------------------------------------------------------------------
				# INSERT
				# ------------------------------------------------------------------
				with insert_col:
					st.markdown( '##### Insert Row' )
					insert_data = { }
					
					for column, col_type in type_map.items( ):
						if 'INT' in col_type:
							insert_data[ column ] = st.number_input( column, step=1,
								key=f'ins_{table}_{column}' )
						
						elif 'REAL' in col_type:
							insert_data[ column ] = st.number_input( column, format='%.6f',
								key=f'ins_{table}_{column}' )
						
						elif 'BOOL' in col_type:
							insert_data[ column ] = 1 if st.checkbox( column,
								key=f'ins_{table}_{column}' ) else 0
						
						else:
							insert_data[ column ] = st.text_input( column,
								key=f'ins_{table}_{column}' )
					
					if st.button( 'Insert Row', key=f'insert_row_{table}',
							use_container_width=True ):
						cols = list( insert_data.keys( ) )
						quoted_cols = [ f'"{c}"' for c in cols ]
						placeholders = ', '.join( [ '?' ] * len( cols ) )
						stmt = (
								f'INSERT INTO "{table}" ({", ".join( quoted_cols )}) '
								f'VALUES ({placeholders});')
						
						with create_connection( ) as conn:
							conn.execute( stmt, list( insert_data.values( ) ) )
							conn.commit( )
						
						st.success( 'Row inserted.' )
						st.rerun( )
				
				# ------------------------------------------------------------------
				# UPDATE
				# ------------------------------------------------------------------
				with update_col:
					st.markdown( '##### Update Row' )
					rowid = st.number_input( 'Row ID', min_value=1, step=1,
						key=f'crud_update_rowid_{table}' )
					
					update_data = { }
					
					for column, col_type in type_map.items( ):
						if 'INT' in col_type:
							val = st.number_input( column, step=1, key=f'upd_{table}_{column}' )
							update_data[ column ] = val
						
						elif 'REAL' in col_type:
							val = st.number_input( column, format='%.6f', key=f'upd_{table}_{column}' )
							update_data[ column ] = val
						
						elif 'BOOL' in col_type:
							val = 1 if st.checkbox( column,
								key=f'upd_{table}_{column}' ) else 0
							update_data[ column ] = val
						
						else:
							val = st.text_input( column, key=f'upd_{table}_{column}' )
							update_data[ column ] = val
					
					if st.button( 'Update Row', key=f'update_row_{table}',
							use_container_width=True ):
						set_clause = ', '.join( [ f'"{c}"=?' for c in update_data ] )
						stmt = f'UPDATE "{table}" SET {set_clause} WHERE rowid=?;'
						
						with create_connection( ) as conn:
							conn.execute( stmt, list( update_data.values( ) ) + [ rowid ] )
							conn.commit( )
						
						st.success( 'Row updated.' )
						st.rerun( )
				
				st.divider( )
				delete_col, preview_col = st.columns( [ 0.35, 0.65 ], border=True )
				
				# ------------------------------------------------------------------
				# DELETE
				# ------------------------------------------------------------------
				with delete_col:
					st.markdown( '##### Delete Row' )
					delete_id = st.number_input( 'Row ID to Delete', min_value=1, step=1,
						key=f'crud_delete_rowid_{table}' )
					
					if st.button( 'Delete Row', key=f'delete_row_{table}', use_container_width=True ):
						with create_connection( ) as conn:
							conn.execute( f'DELETE FROM "{table}" WHERE rowid=?;', (delete_id,) )
							conn.commit( )
						
						st.success( 'Row deleted.' )
						st.rerun( )
				
				# ------------------------------------------------------------------
				# PREVIEW
				# ------------------------------------------------------------------
				with preview_col:
					st.markdown( '##### Current Data Preview' )
					st.data_editor( df.head( 25 ), key=f'dm_crud_preview_{table}',
						use_container_width=True, disabled=True )
		
		# ------------------------------------------------------------------------------
		# EXPLORE
		# ------------------------------------------------------------------------------
		with tabs[ 3 ]:
			tables = list_tables( )
			if tables:
				exp_c1, exp_c2, exp_c3 = st.columns( [ 0.4, 0.4, 0.2 ], border=True )
				with exp_c1:
					table = st.selectbox( 'Table', tables, key='explore_table' )
				with exp_c2:
					page_size = st.slider( 'Rows per page', 10, 500, 50 )
				with exp_c3:
					page = st.number_input( 'Page', min_value=1, step=1 )
					offset = (page - 1) * page_size
					df_page = read_table( table, page_size, offset )
				
				st.data_editor( data=df_page, num_rows='dynamic', hide_index=False )
		
		# ------------------------------------------------------------------------------
		# FILTER
		# ------------------------------------------------------------------------------
		with tabs[ 4 ]:
			tables = list_tables( )
			if tables:
				tbl_c1, tbl_c2, tbl_c3 = st.columns( [ 0.25, 0.25, 0.5 ], border=True )
				with tbl_c1:
					table = st.selectbox( 'Select Table', tables, key='filter_table' )
					df = read_table( table )
				with tbl_c2:
					column = st.selectbox( 'Select Field', df.columns, key='selected_column' )
				with tbl_c3:
					value = st.text_input( 'Contains', placeholder='Enter Text for Lookup' )
					if value:
						df = df[ df[ column ].astype( str ).str.contains( value ) ]
				
				st.data_editor( df )
		
		# ------------------------------------------------------------------------------
		# AGGREGATE
		# ------------------------------------------------------------------------------
		with tabs[ 5 ]:
			tables = list_tables( )
			if tables:
				agg_c1, agg_c2, agg_c3, agg_c4 = st.columns( [ 0.2, 0.2, 0.2, 0.4 ], border=True )
				with agg_c1:
					table = st.selectbox( 'Table', tables, key='agg_table' )
					df = read_table( table )
					numeric_cols = df.select_dtypes( include=[ 'number' ] ).columns.tolist( )
					with agg_c2:
						if numeric_cols:
							col = st.selectbox( 'Column', numeric_cols, key='selected_col' )
					with agg_c3:
						agg = st.selectbox( 'Function', [ 'SUM', 'AVG', 'COUNT' ] )
					with agg_c4:
						if agg == 'SUM':
							st.metric( 'Result', df[ col ].sum( ), width='stretch',
								format='accounting' )
						
						elif agg == 'AVG':
							st.metric( 'Result', df[ col ].mean( ), width='stretch',
								format='accounting' )
						
						elif agg == 'COUNT':
							st.metric( 'Result', df[ col ].count( ), width='stretch',
								format='accounting' )
		
		# ------------------------------------------------------------------------------
		# VISUALIZE
		# ------------------------------------------------------------------------------
		with tabs[ 6 ]:
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Table', tables, key='viz_table' )
				df = read_table( table )
				create_visualization( df )
		
		# ------------------------------------------------------------------------------
		# ADMIN
		# ------------------------------------------------------------------------------
		with tabs[ 7 ]:
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Table', tables, key='admin_table' )
			
			st.divider( )
			
			st.subheader( 'Data Profiling' )
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Select Table', tables, key='profile_table' )
				if st.button( 'Generate Profile' ):
					profile_df = create_profile_table( table )
					render_table( profile_df )
			
			st.subheader( 'Drop Table' )
			
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Select Table to Drop', tables, key='admin_drop_table' )
				
				# Initialize confirmation state
				if 'dm_confirm_drop' not in st.session_state:
					st.session_state.dm_confirm_drop = False
				
				# Step 1: Initial Drop click
				if st.button( 'Drop Table', key='admin_drop_button' ):
					st.session_state.dm_confirm_drop = True
				
				# Step 2: Confirmation UI
				if st.session_state.dm_confirm_drop:
					st.warning( f'You are about to permanently delete table {table}. '
					            'This action cannot be undone.' )
					
					col1, col2 = st.columns( 2 )
					
					if col1.button( 'Confirm Drop', key='admin_confirm_drop' ):
						try:
							drop_table( table )
							st.success( f'Table {table} dropped successfully.' )
						except Exception as e:
							st.error( f'Drop failed: {e}' )
						
						st.session_state.dm_confirm_drop = False
						st.rerun( )
					
					if col2.button( 'Cancel', key='admin_cancel_drop' ):
						st.session_state.dm_confirm_drop = False
						st.rerun( )
				
				df = read_table( table )
				col = st.selectbox( 'Create Index On', df.columns, key='df_key' )
				
				if st.button( 'Create Index' ):
					create_index( table, col )
					st.success( 'Index created.' )
			
			st.divider( )
			
			st.subheader( 'Create Custom Table' )
			new_table_name = st.text_input( 'Table Name' )
			column_count = st.number_input( 'Number of Columns', min_value=1, max_value=20,
				value=1 )
			columns = [ ]
			for i in range( column_count ):
				st.markdown( f'### Column {i + 1}' )
				col_name = st.text_input( 'Column Name', key=f'col_name_{i}' )
				col_type = st.selectbox( 'Column Type', [ 'INTEGER', 'REAL', 'TEXT' ],
					key=f'col_type_{i}' )
				
				not_null = st.checkbox( 'NOT NULL', key=f'not_null_{i}' )
				primary_key = st.checkbox( 'PRIMARY KEY', key=f'pk_{i}' )
				auto_inc = st.checkbox( 'AUTOINCREMENT (INTEGER only)', key=f'ai_{i}' )
				
				columns.append( {
						'name': col_name,
						'type': col_type,
						'not_null': not_null,
						'primary_key': primary_key,
						'auto_increment': auto_inc } )
			
			if st.button( 'Create Table' ):
				try:
					create_custom_table( new_table_name, columns )
					st.success( 'Table created successfully.' )
					st.rerun( )
				
				except Exception as e:
					st.error( f'Error: {e}' )
			
			st.divider( )
			st.subheader( 'Schema Viewer' )
			
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Select Table', tables, key='schema_view_table' )
				
				# Column schema
				schema = create_schema( table )
				schema_df = pd.DataFrame(
					schema,
					columns=[ 'cid', 'name', 'type', 'notnull', 'default', 'pk' ] )
				
				st.markdown( "### Columns" )
				st.data_editor(
					make_display_safe( schema_df ),
					hide_index=True,
					use_container_width=True,
					disabled=True )
				
				# Row count
				with create_connection( ) as conn:
					count = conn.execute(
						f'SELECT COUNT(*) FROM "{table}"'
					).fetchone( )[ 0 ]
				
				st.metric( "Row Count", f"{count:,}" )
				
				# Indexes
				indexes = get_indexes( table )
				if indexes:
					idx_df = pd.DataFrame(
						indexes,
						columns=[ 'seq', 'name', 'unique', 'origin', 'partial' ]
					)
					st.markdown( "### Indexes" )
					st.data_editor(
						make_display_safe( idx_df ),
						hide_index=True,
						use_container_width=True,
						disabled=True )
				else:
					st.info( "No indexes defined." )
			
			st.divider( )
			st.subheader( "ALTER TABLE Operations" )
			
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Select Table', tables, key='alter_table_select' )
				operation = st.selectbox( 'Operation',
					[ 'Add Column', 'Rename Column', 'Rename Table', 'Drop Column' ], key='op_key' )
				
				if operation == 'Add Column':
					new_col = st.text_input( 'Column Name' )
					col_type = st.selectbox( 'Column Type', [ 'INTEGER', 'REAL', 'TEXT' ],
						key='key_type' )
					
					if st.button( 'Add Column' ):
						add_column( table, new_col, col_type )
						st.success( 'Column added.' )
						st.rerun( )
				
				elif operation == 'Rename Column':
					schema = create_schema( table )
					col_names = [ col[ 1 ] for col in schema ]
					
					old_col = st.selectbox( 'Column to Rename', col_names, key='old_key' )
					new_col = st.text_input( 'New Column Name' )
					
					if st.button( 'Rename Column' ):
						rename_column( table, old_col, new_col )
						st.success( 'Column renamed.' )
						st.rerun( )
				
				elif operation == 'Rename Table':
					new_name = st.text_input( 'New Table Name' )
					
					if st.button( 'Rename Table' ):
						rename_table( table, new_name )
						st.success( 'Table renamed.' )
						st.rerun( )
				
				elif operation == 'Drop Column':
					schema = create_schema( table )
					col_names = [ col[ 1 ] for col in schema ]
					
					drop_col = st.selectbox( 'Column to Drop', col_names, key='drop_key' )
					
					if st.button( 'Drop Column' ):
						drop_column( table, drop_col )
						st.success( 'Column dropped.' )
						st.rerun( )
		
		# ------------------------------------------------------------------------------
		# SQL
		# ------------------------------------------------------------------------------
		with tabs[ 8 ]:
			st.subheader( 'SQL Console' )
			query = st.text_area( 'Enter SQL Query' )
			if st.button( 'Run Query' ):
				if not is_safe_query( query ):
					st.error( 'Query blocked: Only read-only SELECT statements are allowed.' )
				else:
					try:
						start_time = time.perf_counter( )
						with create_connection( ) as conn:
							result = pd.read_sql_query( query, conn )
						
						end_time = time.perf_counter( )
						elapsed = end_time - start_time
						
						# ----------------------------------------------------------
						# Display Results
						# ----------------------------------------------------------
						st.dataframe( result, use_container_width=True )
						row_count = len( result )
						
						# ----------------------------------------------------------
						# Execution Metrics
						# ----------------------------------------------------------
						col1, col2 = st.columns( 2 )
						col1.metric( 'Rows Returned', f'{row_count:,}' )
						col2.metric( 'Execution Time (seconds)', f'{elapsed:.6f}' )
						
						# Optional slow query warning
						if elapsed > 2.0:
							st.warning( 'Slow query detected (> 2 seconds). Consider indexing.' )
						
						# ----------------------------------------------------------
						# Download
						# ----------------------------------------------------------
						if not result.empty:
							csv = result.to_csv( index=False ).encode( 'utf-8' )
							st.download_button( 'Download CSV', csv,
								'query_results.csv', 'text/csv' )
					
					except Exception as e:
						st.error( f'Execution failed: {e}' )
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
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import sqlite3
import re
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
style_subheaders( )
st.set_page_config(  page_title='Mappy', layout='wide', page_icon=cfg.FAVICON,
    initial_sidebar_state='expanded', )

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
			
			selected_key = st.selectbox( 'API Key', options=list( api_keys.keys( ) ), key='sel_api' )
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
				if st.button( 'Resolve Location' ):
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
				if st.button( 'Clear Location' ):
					if not query:
						st.warning( 'Nothing to clear' )
					else:
						query = None
						st.json( query )
					
		with geo_c2:
			use_places = st.checkbox( 'Use Places fallback if geocoding fails', value=True )
			
# ==============================================================================
# METEOROLOGICAL MODE
# ==============================================================================
if mode == 'Weather':
	left, center, right = st.columns( [ 0.025, 0.95, 0.025 ] )
	with center:
		st.subheader( 'Weather & Meteorological Data' )
		st.divider( )
		
		met_c1, met_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		with met_c1:
			#----Expanders for Fetchers
			pass
		with met_c2:
			#----Static Map & Langchain Document Data
			pass

# ==============================================================================
# ENVIRONMENTAL MODE
# ==============================================================================
if mode == 'Environnmental':
	st.subheader( 'Environmental Data' )
	st.divider( )
	
	enviro_c1, enviro_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
	with enviro_c1:
		# ----Expanders for Fetchers
		pass
	with enviro_c2:
		# ----Static Map & Langchain Document Data
		pass

# ==============================================================================
# ASTRONOMICAL MODE
# ==============================================================================
if mode == 'Astronomical':
	left, center, right = st.columns( [ 0.025, 0.95, 0.025 ] )
	with center:
		st.subheader( 'Astronomical Data' )
		st.divider( )
		
		astro_c1, astro_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		with asto_c1:
			# ----Expanders for Fetchers
			pass
		with astro_c2:
			# ----Static Map & Langchain Document Data
			pass

# ==============================================================================
# GEOPHYSICAL MODE
# ==============================================================================
if mode == 'Geological':
	left, center, right = st.columns( [ 0.025, 0.95, 0.025 ] )
	with center:
		st.subheader( 'Geological Data' )
		st.divider( )
		
		geo_c1, geo_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		with geo_c1:
			# ----Expanders for Fetchers
			pass
		with geo_c2:
			# ----Static Map & Langchain Document Data
			pass


# ==============================================================================
# Distance Matrix Tab
# ==============================================================================
elif mode == 'Distances':
    st.subheader( 'Distance Matrix' )
    st.divider( )

    col1, col2 = st.columns( 2 )
    with col1:
        origin = st.text_input( 'Origin' )

    with col2:
        destination = st.text_input( 'Destination' )
    
    mode = st.selectbox( 'Travel Mode', [ 'driving', 'walking', 'bicycling', 'transit' ],
	    key='travel_key' )
    if st.button( 'Calculate Distance' ):
	    if not origin or not destination:
		    st.warning( 'Provide both origin and destination.' )
	    else:
		    summary = distances.summary( origin, destination,  mode=mode, )
		    st.table( pd.DataFrame( [ summary ] ) )

# ==============================================================================
# Static Maps Tab
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
# Time Zone Tab
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
# Excel Enrichment Tab
# ==============================================================================
elif mode == 'Data Upload':
	st.subheader( 'Excel / CSV' )
	st.divider( )
	
	uploaded = st.file_uploader( 'Upload CSV or XLSX', type=[ 'csv', 'xlsx' ], )
	city_col = st.text_input( 'City Column', value='City' )
	state_col = st.text_input( 'State Column', value='State' )
	country_col = st.text_input( 'Country Column', value='Country' )
	if uploaded:
		input_path = f'_input_{uploaded.name}'
		output_path = f'_output_{uploaded.name}'
		
		with open( input_path, 'wb' ) as f:
			f.write( uploaded.read( ) )
		
		if st.button( 'Enrich File' ):
			excel = Excel( api_key=api_key )
	
		excel.enrich( input_path=input_path, output_path=output_path, city_col=city_col,
			state_col=state_col, country_col=country_col, )
		
		df = pd.read_excel( output_path )
		st.data_editor( df )
		
		st.download_button( 'Download Enriched File', data=open( output_path, 'rb' ).read( ),
			file_name=output_path, )
		
		os.remove( input_path )
		os.remove( output_path )
		
# ==============================================================================
# DATA MANAGEMENT MODE
# ==============================================================================
elif mode == 'Data Management':
	st.subheader( 'Database' )
	st.divider( )
	left, center, right = st.columns( [ 0.05, 0.90, 0.05 ] )
	with center:
		st.subheader( '🏛️ Data Management'  )
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
				render_table( df )
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
					st.markdown( '#### Insert Row' )
					insert_data = { }
					
					for column, col_type in type_map.items( ):
						if 'INT' in col_type:
							insert_data[ column ] = st.number_input(
								column,
								step=1,
								key=f'ins_{table}_{column}' )
						
						elif 'REAL' in col_type:
							insert_data[ column ] = st.number_input(
								column,
								format='%.6f',
								key=f'ins_{table}_{column}' )
						
						elif 'BOOL' in col_type:
							insert_data[ column ] = 1 if st.checkbox(
								column,
								key=f'ins_{table}_{column}' ) else 0
						
						else:
							insert_data[ column ] = st.text_input(
								column,
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
					st.markdown( '#### Update Row' )
					rowid = st.number_input(
						'Row ID',
						min_value=1,
						step=1,
						key=f'crud_update_rowid_{table}' )
					
					update_data = { }
					
					for column, col_type in type_map.items( ):
						if 'INT' in col_type:
							val = st.number_input(
								column,
								step=1,
								key=f'upd_{table}_{column}' )
							update_data[ column ] = val
						
						elif 'REAL' in col_type:
							val = st.number_input(
								column,
								format='%.6f',
								key=f'upd_{table}_{column}' )
							update_data[ column ] = val
						
						elif 'BOOL' in col_type:
							val = 1 if st.checkbox(
								column,
								key=f'upd_{table}_{column}' ) else 0
							update_data[ column ] = val
						
						else:
							val = st.text_input(
								column,
								key=f'upd_{table}_{column}' )
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
					st.markdown( '#### Delete Row' )
					delete_id = st.number_input(
						'Row ID to Delete',
						min_value=1,
						step=1,
						key=f'crud_delete_rowid_{table}' )
					
					if st.button( 'Delete Row', key=f'delete_row_{table}',
							use_container_width=True ):
						with create_connection( ) as conn:
							conn.execute( f'DELETE FROM "{table}" WHERE rowid=?;', (delete_id,) )
							conn.commit( )
						
						st.success( 'Row deleted.' )
						st.rerun( )
				
				# ------------------------------------------------------------------
				# PREVIEW
				# ------------------------------------------------------------------
				with preview_col:
					st.markdown( '#### Current Data Preview' )
					st.data_editor(
						df.head( 25 ),
						key=f'dm_crud_preview_{table}',
						use_container_width=True,
						disabled=True )
		
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
				
				st.data_editor( df_page )
		
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
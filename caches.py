'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                caches.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="caches.py" company="Terry D. Eppler">

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
    caches.py
  </summary>
  ******************************************************************************************
  '''
import json
import os
import sqlite3
import time
from typing import Any, Dict, Optional
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

class BaseCache:
	"""
	
		Purpose:
			Minimal cache interface for mapping string keys to JSON-serializable
			dictionary values, with optional TTL and diagnostics support.

		Parameters:
			None.

		Returns:
			Subclasses implement get/set and may optionally implement delete,
			clear, contains, stats, and namespace_key.
			
	"""
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		raise NotImplementedError
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		raise NotImplementedError
	
	def delete( self, key: str ) -> None:
		raise NotImplementedError
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		raise NotImplementedError
	
	def contains( self, key: str ) -> bool:
		return self.get( key ) is not None
	
	def namespace_key( self, namespace: str, key: str ) -> str:
		"""

			Purpose:
				Create a cache key prefixed by a namespace.

			Parameters:
				namespace (str):
					Logical cache namespace, such as geocode, places, weather,
					distance, or fetcher.

				key (str):
					Raw cache key.

			Returns:
				str:
					Namespace-qualified cache key.

		"""
		throw_if( 'namespace', namespace )
		throw_if( 'key', key )
		return f'{namespace}::{key}'
	
	def stats( self ) -> Dict[ str, Any ]:
		raise NotImplementedError

class InMemoryCache( BaseCache ):
	"""

		Purpose:
			Provide a fast, process-local dictionary cache with optional TTL,
			hit/miss counters, deletion, clearing, and basic diagnostics.

		Parameters:
			None.

		Returns:
			O(1) get/set operations for this process lifetime.

	"""
	_store: Dict[ str, Dict[ str, Any ] ]
	_hits: int
	_misses: int
	_sets: int
	_deletes: int
	
	def __init__( self ) -> None:
		self._store = { }
		self._hits = 0
		self._misses = 0
		self._sets = 0
		self._deletes = 0
	
	def now( self ) -> float:
		"""

			Purpose:
				Return the current Unix timestamp.

			Parameters:
				None.

			Returns:
				float:
					Current Unix timestamp.

		"""
		try:
			return time.time( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'now( self )'
			raise exception
	
	def make_record( self, key: str, value: Dict[ str, Any ],
			ttl: Optional[ int ] = None ) -> Dict[ str, Any ]:
		"""

			Purpose:
				Create a cache metadata record for the supplied key and value.

			Parameters:
				key (str):
					Cache key.

				value (Dict[str, Any]):
					JSON-serializable cache value.

				ttl (Optional[int]):
					Optional time-to-live in seconds.

			Returns:
				Dict[str, Any]:
					Cache metadata record.

		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			
			now_value = self.now( )
			ttl_value = int( ttl ) if ttl is not None and int( ttl ) > 0 else None
			expires_value = now_value + ttl_value if ttl_value else None
			
			return {
					'key': key,
					'value': value,
					'created_at': now_value,
					'updated_at': now_value,
					'expires_at': expires_value,
					'hit_count': 0,
					'last_accessed': None
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'make_record( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ]=None )'
			raise exception
	
	def is_expired( self, record: Dict[ str, Any ] ) -> bool:
		"""

			Purpose:
				Determine whether an in-memory cache record has expired.

			Parameters:
				record (Dict[str, Any]):
					Cache metadata record.

			Returns:
				bool:
					True if expired; otherwise False.

		"""
		try:
			throw_if( 'record', record )
			expires_at = record.get( 'expires_at' )
			
			if expires_at is None:
				return False
			
			return float( expires_at ) <= self.now( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'is_expired( self, record: Dict[ str, Any ] )'
			raise exception
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		"""

			Purpose:
				Return a cached value by key when present and not expired.

			Parameters:
				key (str):
					Cache key.

			Returns:
				Optional[Dict[str, Any]]:
					Cached value or None.

		"""
		try:
			throw_if( 'key', key )
			
			record = self._store.get( key )
			
			if not record:
				self._misses += 1
				return None
			
			if self.is_expired( record ):
				self.delete( key )
				self._misses += 1
				return None
			
			record[ 'hit_count' ] = int( record.get( 'hit_count', 0 ) or 0 ) + 1
			record[ 'last_accessed' ] = self.now( )
			self._hits += 1
			
			return record.get( 'value' )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'get( self, key: str )'
			raise exception
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		"""

			Purpose:
				Set a cache value by key.

			Parameters:
				key (str):
					Cache key.

				value (Dict[str, Any]):
					JSON-serializable cache value.

				ttl (Optional[int]):
					Optional time-to-live in seconds.

			Returns:
				None.

		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			
			self._store[ key ] = self.make_record( key, value, ttl )
			self._sets += 1
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ]=None )'
			raise exception
	
	def delete( self, key: str ) -> None:
		"""

			Purpose:
				Delete a cache entry by key.

			Parameters:
				key (str):
					Cache key.

			Returns:
				None.

		"""
		try:
			throw_if( 'key', key )
			
			if key in self._store:
				del self._store[ key ]
				self._deletes += 1
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'delete( self, key: str )'
			raise exception
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		"""

			Purpose:
				Clear all cache entries or only entries under a namespace prefix.

			Parameters:
				namespace (Optional[str]):
					Optional namespace prefix.

			Returns:
				None.

		"""
		try:
			if namespace:
				prefix = f'{namespace}::'
				keys = [ key for key in self._store if key.startswith( prefix ) ]
				
				for key in keys:
					self.delete( key )
			else:
				deleted = len( self._store )
				self._store.clear( )
				self._deletes += deleted
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'clear( self, namespace: Optional[ str ]=None )'
			raise exception
	
	def contains( self, key: str ) -> bool:
		"""

			Purpose:
				Determine whether a cache key exists and is not expired.

			Parameters:
				key (str):
					Cache key.

			Returns:
				bool:
					True if the key exists and is not expired.

		"""
		try:
			return self.get( key ) is not None
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'contains( self, key: str )'
			raise exception
	
	def stats( self ) -> Dict[ str, Any ]:
		"""

			Purpose:
				Return cache diagnostics.

			Parameters:
				None.

			Returns:
				Dict[str, Any]:
					Cache diagnostics.

		"""
		try:
			expired = 0
			
			for record in self._store.values( ):
				if self.is_expired( record ):
					expired += 1
			
			return {
					'backend': 'memory',
					'entries': len( self._store ),
					'expired_entries': expired,
					'hits': self._hits,
					'misses': self._misses,
					'sets': self._sets,
					'deletes': self._deletes
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'stats( self )'
			raise exception

class SQLiteCache( BaseCache ):
	"""

		Purpose:
			Persist a small cache on disk via sqlite3. Keys are text; values are
			stored as JSON strings with optional TTL and metadata.

		Parameters:
			path (str):
				File path for the SQLite database. Directory is created if needed.

		Returns:
			Durable cache across runs with upsert semantics and diagnostics.

	"""
	path: Optional[ str ]
	_conn: sqlite3.Connection
	
	def __init__( self, path: str = 'mappy_cache.sqlite' ) -> None:
		self.path = path
		d = os.path.dirname( self.path )
		if d:
			os.makedirs( d, exist_ok=True )
		self._conn = sqlite3.connect( self.path )
		self.initialize( )
	
	def initialize( self ) -> None:
		"""

			Purpose:
				Create the SQLite cache table when it does not already exist.

			Parameters:
				None.

			Returns:
				None.

		"""
		try:
			self._conn.execute(
				'''
                CREATE TABLE IF NOT EXISTS kv
                (
                    k
                    TEXT
                    PRIMARY
                    KEY,
                    v
                    TEXT
                    NOT
                    NULL,
                    created_at
                    REAL,
                    updated_at
                    REAL,
                    expires_at
                    REAL,
                    hit_count
                    INTEGER
                    DEFAULT
                    0,
                    last_accessed
                    REAL
                )
				'''
			)
			
			self.migrate( )
			self._conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'initialize( self )'
			raise exception
	
	def migrate( self ) -> None:
		"""

			Purpose:
				Add metadata columns to older kv tables that only contain k and v.

			Parameters:
				None.

			Returns:
				None.

		"""
		try:
			cursor = self._conn.execute( 'PRAGMA table_info(kv)' )
			columns = { row[ 1 ] for row in cursor.fetchall( ) }
			
			additions = {
					'created_at': 'ALTER TABLE kv ADD COLUMN created_at REAL',
					'updated_at': 'ALTER TABLE kv ADD COLUMN updated_at REAL',
					'expires_at': 'ALTER TABLE kv ADD COLUMN expires_at REAL',
					'hit_count': 'ALTER TABLE kv ADD COLUMN hit_count INTEGER DEFAULT 0',
					'last_accessed': 'ALTER TABLE kv ADD COLUMN last_accessed REAL'
			}
			
			for column, sql in additions.items( ):
				if column not in columns:
					self._conn.execute( sql )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'migrate( self )'
			raise exception
	
	def now( self ) -> float:
		"""

			Purpose:
				Return the current Unix timestamp.

			Parameters:
				None.

			Returns:
				float:
					Current Unix timestamp.

		"""
		try:
			return time.time( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'now( self )'
			raise exception
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		"""

			Purpose:
				Return a cached value by key when present and not expired.

			Parameters:
				key (str):
					Cache key.

			Returns:
				Optional[Dict[str, Any]]:
					Cached value or None.

		"""
		try:
			throw_if( 'key', key )
			
			cursor = self._conn.execute(
				'SELECT v, expires_at, hit_count FROM kv WHERE k = ?',
				(key,) )
			row = cursor.fetchone( )
			
			if not row:
				return None
			
			payload = row[ 0 ]
			expires_at = row[ 1 ]
			hit_count = int( row[ 2 ] or 0 )
			
			if expires_at is not None and float( expires_at ) <= self.now( ):
				self.delete( key )
				return None
			
			self._conn.execute(
				'UPDATE kv SET hit_count = ?, last_accessed = ? WHERE k = ?',
				(hit_count + 1, self.now( ), key) )
			self._conn.commit( )
			
			return json.loads( payload )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'get( self, key: str )'
			raise exception
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		"""

			Purpose:
				Set a cache value by key.

			Parameters:
				key (str):
					Cache key.

				value (Dict[str, Any]):
					JSON-serializable cache value.

				ttl (Optional[int]):
					Optional time-to-live in seconds.

			Returns:
				None.

		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			
			now_value = self.now( )
			ttl_value = int( ttl ) if ttl is not None and int( ttl ) > 0 else None
			expires_value = now_value + ttl_value if ttl_value else None
			payload = json.dumps( value, ensure_ascii=False )
			
			self._conn.execute(
				'''
                INSERT INTO kv
                (k,
                 v,
                 created_at,
                 updated_at,
                 expires_at,
                 hit_count,
                 last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(k) DO
                UPDATE SET
                    v = excluded.v,
                    updated_at = excluded.updated_at,
                    expires_at = excluded.expires_at
				''',
				(key, payload, now_value, now_value, expires_value, 0, None) )
			self._conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ]=None )'
			raise exception
	
	def delete( self, key: str ) -> None:
		"""

			Purpose:
				Delete a cache entry by key.

			Parameters:
				key (str):
					Cache key.

			Returns:
				None.

		"""
		try:
			throw_if( 'key', key )
			self._conn.execute( 'DELETE FROM kv WHERE k = ?', (key,) )
			self._conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'delete( self, key: str )'
			raise exception
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		"""

			Purpose:
				Clear all cache entries or only entries under a namespace prefix.

			Parameters:
				namespace (Optional[str]):
					Optional namespace prefix.

			Returns:
				None.

		"""
		try:
			if namespace:
				prefix = f'{namespace}::%'
				self._conn.execute( 'DELETE FROM kv WHERE k LIKE ?', (prefix,) )
			else:
				self._conn.execute( 'DELETE FROM kv' )
			
			self._conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'clear( self, namespace: Optional[ str ]=None )'
			raise exception
	
	def contains( self, key: str ) -> bool:
		"""

			Purpose:
				Determine whether a cache key exists and is not expired.

			Parameters:
				key (str):
					Cache key.

			Returns:
				bool:
					True if the key exists and is not expired.

		"""
		try:
			return self.get( key ) is not None
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'contains( self, key: str )'
			raise exception
	
	def purge_expired( self ) -> int:
		"""

			Purpose:
				Delete expired cache entries.

			Parameters:
				None.

			Returns:
				int:
					Number of rows deleted.

		"""
		try:
			cursor = self._conn.execute(
				'SELECT COUNT(*) FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?',
				(self.now( ),) )
			count = int( cursor.fetchone( )[ 0 ] or 0 )
			self._conn.execute(
				'DELETE FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?',
				(self.now( ),) )
			self._conn.commit( )
			return count
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'purge_expired( self )'
			raise exception
	
	def stats( self ) -> Dict[ str, Any ]:
		"""

			Purpose:
				Return SQLite cache diagnostics.

			Parameters:
				None.

			Returns:
				Dict[str, Any]:
					Cache diagnostics.

		"""
		try:
			total = self._conn.execute( 'SELECT COUNT(*) FROM kv' ).fetchone( )[ 0 ]
			expired = self._conn.execute(
				'SELECT COUNT(*) FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?',
				(self.now( ),) ).fetchone( )[ 0 ]
			hits = self._conn.execute(
				'SELECT COALESCE(SUM(hit_count), 0) FROM kv' ).fetchone( )[ 0 ]
			
			return {
					'backend': 'sqlite',
					'path': self.path,
					'entries': int( total or 0 ),
					'expired_entries': int( expired or 0 ),
					'hits': int( hits or 0 )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'stats( self )'
			raise exception
	
	def close( self ) -> None:
		"""

			Purpose:
				Close the SQLite connection.

			Parameters:
				None.

			Returns:
				None.

		"""
		try:
			self._conn.close( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'Mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'close( self )'
			raise exception
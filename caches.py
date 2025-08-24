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
from typing import Any, Dict, Optional



def throw_if( name: str, value: object ):
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


class BaseCache:
	"""
	Purpose:
		Minimal cache interface for mapping string keys to JSON-serializable
		dict values.

	Parameters:
		None.

	Returns:
		Subclasses implement get/set.
	"""

	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		raise NotImplementedError

	def set( self, key: str, value: Dict[ str, Any ] ) -> None:
		raise NotImplementedError


class InMemoryCache( BaseCache ):
	"""

		Purpose:
			Provide a fast, process-local dictionary cache.

		Parameters:
			None.

		Returns:
			O(1) get/set operations for this process lifetime.

	"""

	def __init__( self ) -> None:
		self._store: Dict[ str, Dict[ str, Any ] ] = { }

	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		return self._store.get( key )

	def set( self, key: str, value: Dict[ str, Any ] ) -> None:
		self._store[ key ] = value


class SQLiteCache( BaseCache ):
	"""

		Purpose:
			Persist a small cache on disk via sqlite3. Keys are text; values are
			stored as JSON strings.

		Parameters:
			path (str):
				File path for the SQLite database. Directory is created if needed.

		Returns:
			Durable cache across runs with simple upsert semantics.

	"""

	def __init__( self, path: str='mappy_cache.sqlite' ) -> None:
		d = os.path.dirname( path )
		if d:
			os.makedirs( d, exist_ok = True )
		self._conn = sqlite3.connect( path )
		self._conn.execute(
			'CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL)'
		)
		self._conn.commit( )

	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		cur = self._conn.execute( 'SELECT v FROM kv WHERE k = ?', (key,) )
		row = cur.fetchone( )
		if not row:
			return None
		return json.loads( row[ 0 ] )

	def set( self, key: str, value: Dict[ str, Any ] ) -> None:
		payload = json.dumps( value, ensure_ascii=False )
		self._conn.execute(
			'INSERT OR REPLACE INTO kv (k, v) VALUES (?, ?)', (key, payload)
		)
		self._conn.commit( )

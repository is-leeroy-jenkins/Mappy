'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                places.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="places.py" company="Terry D. Eppler">

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
"""
Purpose:
    Provide a Places Text Search fallback and detail fetch that can be promoted
    into a geocode-like shape (address, lat/lng, components).

Parameters:
    maps (Maps):
        Maps gateway instance.
    cache (Optional[BaseCache]):
        Pluggable cache to memoize the text queries.

Returns:
    Places with .text_to_location(query, country_hint=None).
"""

from typing import Any, Dict, Optional

from .caching import BaseCache
from .exceptions import NotFound
from .maps import Maps

class Places:
	"""
	Purpose:
		Use Places Text Search to recover locations that Geocoding may miss.
		Top result is promoted via Place Details to a geocode-like dict.

	Parameters:
		maps (Maps):
			Maps gateway instance.
		cache (Optional[BaseCache]):
			Optional cache for query results.

	Returns:
		Places instance with .text_to_location(...).
	"""

	def __init__( self, maps: Maps, cache: Optional[ BaseCache ] = None ) -> None:
		self._maps = maps
		self._cache = cache

	def text_to_location( self, query: str, country_hint: Optional[ str ] = None ) -> Dict[
		str, Any ]:
		"""
			Purpose:
				Resolve a free-text query into address and coordinates via Places.

			Parameters:
				query (str):
					Arbitrary human-entered text (e.g., "Newcastle, NSW, AU").
				country_hint (Optional[str]):
					ISO-2 region bias (e.g., "AU", "US").

			Returns:
				Dict with formatted_address, lat, lng, place_id, types, components.

			Raises:
				NotFound if no candidate is returned.
		"""
		key = f"places::{query}::{(country_hint or '').upper( )}"
		if self._cache:
			hit = self._cache.get( key )
			if hit:
				return hit

		params: Dict[ str, str ] = { "query": query }
		if country_hint:
			params[ "region" ] = country_hint.upper( )

		search = self._maps.request( "place/textsearch/json", params )
		results = search.get( "results" ) or [ ]
		if not results:
			raise NotFound( f"No places match for '{query}'" )

		top = results[ 0 ]
		pid = top.get( "place_id" )
		if not pid:
			raise NotFound( "Top place had no place_id" )

		detail = self._maps.request(
			"place/details/json",
			{ "place_id": pid,
			  "fields": "formatted_address,geometry,address_component,place_id,type" },
		).get( "result", { } )

		geom = (detail.get( "geometry" ) or { }).get( "location" ) or { }
		out = {
				"formatted_address": detail.get( "formatted_address" ),
				"lat": geom.get( "lat" ),
				"lng": geom.get( "lng" ),
				"place_id": detail.get( "place_id" ),
				"types": ",".join( detail.get( "types", [ ] ) ) if detail.get( "types" ) else None,
				"address_components": detail.get( "address_components", [ ] ),
		}
		if self._cache:
			self._cache.set( key, out )
		return out

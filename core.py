'''
	******************************************************************************************
	  Assembly:                Mappy
	  Filename:                core.py
	  Author:                  Terry D. Eppler (adapted by Bro)
	  Created:                 05-31-2022
	  Last Modified By:        Terry D. Eppler
	  Last Modified On:        08-25-2025
	******************************************************************************************
	<copyright file="core.py" company="Terry D. Eppler">
	
	     Mappy is a GIS Toolkit written in python
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
	
	 THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	 FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.
	 IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
	 DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
	 ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
	 DEALINGS IN THE SOFTWARE.
	
	 You can contact me at:  terryeppler@gmail.com or eppler.terry@epa.gov
	
	</copyright>
	<summary>
	    core.py — lightweight immutable result container and small core helpers
	</summary>
	******************************************************************************************
'''
from __future__ import annotations
from typing import Dict, Optional, Any
from requests import Response

def throw_if( name: str, value: object ) -> None:
	"""

		Purpose:
		--------
		Lightweight guard used to validate required arguments. Treats None and
		empty/whitespace-only strings as invalid values and raises ValueError.
	
		Parameters:
		----------
		name (str): Human-friendly argument name used in the raised message.
		value (object): Value to validate.
	
		Returns:
		-------
		None

	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be None' )

class Result( ):
	"""

		Purpose:
		--------
		Immutable container that represents the outcome of fetching a single
		page. It stores the canonical URL, http status code, extracted plain
		text, optional raw HTML, and response headers.
	
		Parameters:
		----------
		url (str): Canonical URL that was fetched.
		status_code (int): HTTP status code (use 0 when not applicable).
		text (str): Extracted plain text content (may be empty).
		html (Optional[str]): Raw HTML from the response, if available.
		headers (Optional[Dict[str, str]]): Response headers, if available.
	
		Returns:
		-------
		None

	"""
	url: Optional[ str ]
	status_code: Optional[ int ]
	text: Optional[ str ]
	encoding: Optional[ str ]
	headers: Optional[ str ]
	response: Optional[ Response ]

	def __init__( self, response: Response ) -> None:
			self.response = response
			self.url = response.url
			self.status_code = response.status_code
			self.text = response.text
			self.encoding = response.encoding
			self.headers = response.headers

	def __dir__( self ) -> list[ str ]:
		"""

			Purpose:
			--------
			Provide a stable ordering of attributes used by GUIs or inspector tooling.
	
			Returns:
			-------
			list[str]: attribute names in a stable order.

		"""
		return [ 'url',
		         'status_code',
		         'text',
		         'encoding',
		         'headers',
		         'has_html',
		         'to_dict',
		         'from_response']

	def to_dict( self ) -> Dict[ str, Any ]:
		"""

			Purpose:
			--------
			Produce a plain dictionary representation of the Result for serialization
			or tests. This copies headers to avoid outside mutations.
	
			Parameters:
			----------
			None
	
			Returns:
			-------
			Dict[str, Any]: dictionary with keys url, status_code, text, html, headers

		"""
		return \
		{
			'url': self.url,
			'status_code': self.status_code,
			'text': self.text,
			'encoding': self.encoding,
			'headers': dict( self.headers ),
		}

	@property
	def has_html( self ) -> bool:
		"""

			Purpose:
			--------
			Indicate whether the Result includes non-empty HTML content.
	
			Parameters:
			----------
			None
	
			Returns:
			-------
			bool: True when html is a non-empty string; otherwise False.

		"""
		return isinstance( self.text, str )


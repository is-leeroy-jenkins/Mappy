'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                fetchers.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file='fetchers.py' company='Terry D. Eppler'>

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
    fetchers.py
  </summary>
  ******************************************************************************************
  '''
from __future__ import annotations

import base64
import datetime as dt
import io
import re
import os
import urllib.parse
from pathlib import Path
import pandas as pd
from typing import Any, Dict, Optional, Pattern, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import requests
from PIL.Image import Image
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy import units as u
from astroquery.simbad import Simbad
from bs4 import BeautifulSoup
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from google import genai
from grokipedia_api import GrokipediaClient
from langchain_community.retrievers import ArxivRetriever, WikipediaRetriever
from langchain_core.documents import Document
from langchain_core.tools import Tool
from langchain_googledrive.retrievers import GoogleDriveRetriever
from playwright.sync_api import sync_playwright
from owslib.wms import WebMapService
from requests import Response
from sscws.sscws import SscWs
import time
import config as cfg
from boogr import Error
from core import Result
import xml.etree.ElementTree as ET

def throw_if( name: str, value: Any ) -> None:
	'''
		
		Purpose:
		-----------
		Simple guard which raises ValueError when `value` is falsy (None, empty).
			
		Parameters:
		-----------
		name (str): Variable name used in the raised message.
		value (Any): Value to validate.
			
		Returns:
		-----------
		None: Raises ValueError when `value` is falsy.
			
	'''
	if value is None:
		raise ValueError( f"Argument '{name}' cannot be empty!" )

def encode_image( path: str ) -> str:
	'''
		
		Purpose:
		-----------
		Simple guard which raises ValueError when `path` is falsy (None, empty).
		
		Parameters:
		-----------
		path (str): the path to an image file.
		
		Returns:
		-----------
		str: string representing the bytes of the image
		
	'''
	if path is None:
		raise ValueError( f"Argument '{path}' cannot be empty!" )
	else:
		data = Path( path ).read_bytes( )
		return base64.b64encode( data ).decode( "utf-8" )

class Fetcher:
	'''

		Purpose:
		--------
		Base class for fetchers.

		Attribues:
		-----------
		timeout - int
		headers - Dict[ str, Any ]
		response - requests.Response
		url - str
		result - core.Result
		query - string

		Methods:
		-----------
		fetch( ) -> Dict[ str, Any ]


	'''
	timeout: Optional[ int ]
	headers: Optional[ Dict[ str, Any ] ]
	response: Optional[ Response ]
	url: Optional[ str ]
	result: Optional[ Result ]
	query: Optional[ str ]
	
	def __init__( self ) -> None:
		'''

			Purpose:
			-----------
			Base initializer. Subclasses should set defaults they require.

		'''
		self.timeout = None
		self.headers = None
		self.response = None
		self.url = None
		self.result = None
		self.query = None
	
	def __dir__( self ) -> list[ str ]:
		'''

			Purpose:
			-----------
			Control ordering for introspection.

			Parameters:
			-----------
			None

			Returns:
			-----------
			list[str]: Ordered attribute/method names.

		'''
		return [ 'timeout',
		         'headers',
		         'response',
		         'url',
		         'result',
		         'query',
		         'fetch' ]
	
	def fetch( self, query: str, url:str, time: int=10 ) -> Result | None:
		'''

			Purpose:
			--------
			Abstract fetch method to be implemented by subclasses.

			Parameters:
			-----------
			url (str): Resource URL to fetch.
			time (int): Timeout in seconds.
			query (str):  Text provided to Agent

			Returns:
			---------
			Optional[Result]: Should return Result on success or None on failure.

		'''
		raise NotImplementedError( 'Must be implemented by a subclass.' )

class WebFetcher( Fetcher ):
	'''

		Purpose:
		--------
		Fetches web pages with requests and extracts common HTML content structures.

		Attributes:
		-----------
		soup,
		agents,
		url,
		html,
		re_tag,
		re_ws,
		response,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		validate_required_string(...): Performs required string validation.
		validate_positive_integer(...): Performs positive integer validation.
		validate_non_negative_integer(...): Performs non-negative integer validation.
		validate_non_negative_float(...): Performs non-negative float validation.
		fetch(...): Performs the fetch operation for this fetcher.
		html_to_text(...): Performs the html_to_text operation for this fetcher.
		coerce_items(...): Performs the coerce_items operation for this fetcher.
		extract_title(...): Performs the extract_title operation for this fetcher.
		truncate_text(...): Performs the truncate_text operation for this fetcher.
		normalize_url(...): Performs the normalize_url operation for this fetcher.
		same_domain(...): Performs the same_domain operation for this fetcher.
		extract_links(...): Performs the extract_links operation for this fetcher.
		extract_structured_data(...): Performs structured extraction for this fetcher.
		scrape_paragraphs(...): Performs the scrape_paragraphs operation for this fetcher.
		scrape_lists(...): Performs the scrape_lists operation for this fetcher.
		scrape_tables(...): Performs the scrape_tables operation for this fetcher.
		scrape_articles(...): Performs the scrape_articles operation for this fetcher.
		scrape_headings(...): Performs the scrape_headings operation for this fetcher.
		scrape_divisions(...): Performs the scrape_divisions operation for this fetcher.
		scrape_sections(...): Performs the scrape_sections operation for this fetcher.
		scrape_blockquotes(...): Performs the scrape_blockquotes operation for this fetcher.
		scrape_hyperlinks(...): Performs the scrape_hyperlinks operation for this fetcher.
		scrape_images(...): Performs the scrape_images operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	soup: Optional[ BeautifulSoup ]
	agents: Optional[ str ]
	url: Optional[ str ]
	html: Optional[ str ]
	re_tag: Optional[ Pattern ]
	re_ws: Optional[ Pattern ]
	response: Optional[ Response ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize WebFetcher with request defaults, regular expressions, headers,
			and response state.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.timeout = 10
		self.re_tag = re.compile( r'<[^>]+>' )
		self.re_ws = re.compile( r'\s+' )
		self.url = None
		self.html = None
		self.response = None
		self.result = None
		self.soup = None
		self.headers = { }
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ] = self.agents
		
		if 'Accept' not in self.headers:
			self.headers[
				'Accept' ] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Return stable introspection names for the fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]: Ordered attribute and method names.
		'''
		return [
				'agents',
				'url',
				'html',
				'timeout',
				'headers',
				'response',
				'result',
				'soup',
				're_tag',
				're_ws',
				'validate_required_string',
				'validate_positive_integer',
				'validate_non_negative_integer',
				'validate_non_negative_float',
				'fetch',
				'html_to_text',
				'coerce_items',
				'extract_title',
				'truncate_text',
				'normalize_url',
				'same_domain',
				'extract_links',
				'extract_structured_data',
				'scrape_headings',
				'scrape_paragraphs',
				'scrape_lists',
				'scrape_tables',
				'scrape_articles',
				'scrape_sections',
				'scrape_divisions',
				'scrape_blockquotes',
				'scrape_hyperlinks',
				'scrape_images',
				'create_schema'
		]
	
	def validate_required_string( self, name: str, value: Any ) -> str:
		'''
			Purpose:
			--------
			Validate that a mandatory string argument is present and non-empty.

			Parameters:
			-----------
			name (str): Argument name used in the raised exception.
			value (Any): Argument value to validate.

			Returns:
			--------
			str: Stripped string value.
		'''
		try:
			throw_if( 'name', name )
			throw_if( name, value )
			
			if not isinstance( value, str ):
				raise TypeError( f'{name} must be a string.' )
			
			text = value.strip( )
			if not text:
				raise ValueError( f'{name} cannot be empty.' )
			
			return text
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'validate_required_string( self, name: str, value: Any ) -> str'
			raise exception
	
	def validate_positive_integer( self, name: str, value: Any ) -> int:
		'''
			Purpose:
			--------
			Validate and return an integer greater than or equal to one.

			Parameters:
			-----------
			name (str): Argument name used in the raised exception.
			value (Any): Argument value to validate.

			Returns:
			--------
			int: Validated integer value.
		'''
		try:
			throw_if( 'name', name )
			throw_if( name, value )
			number = int( value )
			
			if number < 1:
				raise ValueError( f'{name} must be greater than or equal to 1.' )
			
			return number
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = (
					'validate_positive_integer( self, name: str, value: Any ) -> int')
			raise exception
	
	def validate_non_negative_integer( self, name: str, value: Any ) -> int:
		'''
			Purpose:
			--------
			Validate and return an integer greater than or equal to zero.

			Parameters:
			-----------
			name (str): Argument name used in the raised exception.
			value (Any): Argument value to validate.

			Returns:
			--------
			int: Validated integer value.
		'''
		try:
			throw_if( 'name', name )
			
			if value is None:
				raise ValueError( f'{name} cannot be None.' )
			
			number = int( value )
			if number < 0:
				raise ValueError( f'{name} must be greater than or equal to 0.' )
			
			return number
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = (
					'validate_non_negative_integer( self, name: str, value: Any ) -> int')
			raise exception
	
	def validate_non_negative_float( self, name: str, value: Any ) -> float:
		'''
			Purpose:
			--------
			Validate and return a float greater than or equal to zero.

			Parameters:
			-----------
			name (str): Argument name used in the raised exception.
			value (Any): Argument value to validate.

			Returns:
			--------
			float: Validated float value.
		'''
		try:
			throw_if( 'name', name )
			
			if value is None:
				raise ValueError( f'{name} cannot be None.' )
			
			number = float( value )
			if number < 0:
				raise ValueError( f'{name} must be greater than or equal to 0.' )
			
			return number
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = (
					'validate_non_negative_float( self, name: str, value: Any ) -> float')
			raise exception
	
	def fetch( self, url: str, time: int = 10 ) -> Result | None:
		'''
			Purpose:
			--------
			Perform an HTTP GET request and store the response, HTML, URL, timeout,
			and canonical Result object.

			Parameters:
			-----------
			url (str): Absolute HTTP or HTTPS URL to fetch.
			time (int): Request timeout in seconds.

			Returns:
			--------
			Result | None: Result wrapping the HTTP response when successful.
		'''
		try:
			self.url = self.validate_required_string( 'url', url )
			self.timeout = self.validate_positive_integer( 'time', time )
			
			self.response = requests.get(
				url=self.url,
				headers=self.headers,
				timeout=self.timeout
			)
			self.response.raise_for_status( )
			self.html = self.response.text or ''
			self.soup = BeautifulSoup( self.html, 'html.parser' )
			self.result = Result( self.response )
			return self.result
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'fetch( self, url: str, time: int=10 ) -> Result | None'
			raise exception
	
	def html_to_text( self, html: str ) -> str:
		'''
			Purpose:
			--------
			Convert raw HTML to compact plain text.

			Parameters:
			-----------
			html (str): Raw HTML string.

			Returns:
			--------
			str: Plain-text content extracted from the HTML.
		'''
		try:
			source = self.validate_required_string( 'html', html )
			clean_html = re.sub( r'<script[\s\S]*?</script>', ' ', source, flags=re.IGNORECASE )
			clean_html = re.sub( r'<style[\s\S]*?</style>', ' ', clean_html, flags=re.IGNORECASE )
			clean_html = re.sub(
				r'</?(p|div|br|li|h[1-6]|section|article|blockquote)[^>]*>',
				'\n',
				clean_html,
				flags=re.IGNORECASE
			)
			text = re.sub( self.re_tag, ' ', clean_html )
			text = re.sub( self.re_ws, ' ', text ).strip( )
			return text
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'html_to_text( self, html: str ) -> str'
			raise exception
	
	def coerce_items( self, value: Any ) -> List[ str ]:
		'''
			Purpose:
			--------
			Normalize extracted values into a list of strings.

			Parameters:
			-----------
			value (Any): Value returned by a scraping or extraction operation.

			Returns:
			--------
			List[str]: Clean list of string values.
		'''
		if value is None:
			return [ ]
		
		if isinstance( value, list ):
			return [ str( item ) for item in value if item is not None ]
		
		return [ str( value ) ]
	
	def extract_title( self, html: str ) -> str:
		'''
			Purpose:
			--------
			Extract the title element from an HTML document.

			Parameters:
			-----------
			html (str): Raw HTML content.

			Returns:
			--------
			str: Decoded page title or an empty string.
		'''
		try:
			source = self.validate_required_string( 'html', html )
			soup = BeautifulSoup( source, 'html.parser' )
			
			if soup.title and soup.title.string:
				return re.sub( r'\s+', ' ', soup.title.string ).strip( )
			
			match = re.search(
				r'<title[^>]*>(.*?)</title>',
				source,
				flags=re.IGNORECASE | re.DOTALL
			)
			
			if not match:
				return ''
			
			return re.sub( r'\s+', ' ', match.group( 1 ) ).strip( )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'extract_title( self, html: str ) -> str'
			raise exception
	
	def truncate_text( self, text: str, limit: int = 12000 ) -> str:
		'''
			Purpose:
			--------
			Limit long text blocks for display or logging.

			Parameters:
			-----------
			text (str): Text to truncate.
			limit (int): Maximum visible character count.

			Returns:
			--------
			str: Truncated or original text.
		'''
		try:
			source = self.validate_required_string( 'text', text )
			maximum = self.validate_positive_integer( 'limit', limit )
			
			if len( source ) <= maximum:
				return source
			
			return source[ : maximum ] + '\n\n... [truncated]'
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'truncate_text( self, text: str, limit: int=12000 ) -> str'
			raise exception
	
	def normalize_url( self, base_url: str, href: str ) -> str:
		'''
			Purpose:
			--------
			Convert a possibly relative URL into a normalized HTTP or HTTPS URL.

			Parameters:
			-----------
			base_url (str): Base URL used for relative links.
			href (str): Raw href value or absolute URL.

			Returns:
			--------
			str: Normalized URL or an empty string.
		'''
		try:
			base = self.validate_required_string( 'base_url', base_url )
			raw_href = self.validate_required_string( 'href', href )
			
			if raw_href.startswith( ('mailto:', 'tel:', 'javascript:', '#') ):
				return ''
			
			absolute = urllib.parse.urljoin( base, raw_href )
			parsed = urllib.parse.urlparse( absolute )
			
			if parsed.scheme not in ('http', 'https'):
				return ''
			
			if not parsed.netloc:
				return ''
			
			path = parsed.path or '/'
			normalized = parsed._replace( path=path, fragment='' )
			return normalized.geturl( )
		
		except Exception:
			return ''
	
	def same_domain( self, left_url: str, right_url: str ) -> bool:
		'''
			Purpose:
			--------
			Determine whether two URLs share the same network location.

			Parameters:
			-----------
			left_url (str): First URL.
			right_url (str): Second URL.

			Returns:
			--------
			bool: True when the network locations match.
		'''
		try:
			left = self.validate_required_string( 'left_url', left_url )
			right = self.validate_required_string( 'right_url', right_url )
			left_host = (urllib.parse.urlparse( left ).netloc or '').lower( )
			right_host = (urllib.parse.urlparse( right ).netloc or '').lower( )
			return bool( left_host ) and left_host == right_host
		
		except Exception:
			return False
	
	def extract_links( self, base_url: str, html: str ) -> List[ str ]:
		'''
			Purpose:
			--------
			Extract normalized hyperlinks from an HTML document.

			Parameters:
			-----------
			base_url (str): Base page URL used to resolve relative links.
			html (str): Raw HTML content.

			Returns:
			--------
			List[str]: Unique normalized hyperlinks in document order.
		'''
		try:
			base = self.validate_required_string( 'base_url', base_url )
			source = self.validate_required_string( 'html', html )
			soup = BeautifulSoup( source, 'html.parser' )
			results: List[ str ] = [ ]
			seen: set[ str ] = set( )
			
			for tag in soup.find_all( 'a', href=True ):
				candidate = self.normalize_url( base, tag.get( 'href', '' ) )
				if candidate and candidate not in seen:
					seen.add( candidate )
					results.append( candidate )
			
			return results
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'extract_links( self, base_url: str, html: str ) -> List[ str ]'
			raise exception
	
	def extract_structured_data( self, url: str, html: str,
			selected_methods: Optional[ List[ str ] ]=None ) -> Dict[ str, List[ str ] ]:
		'''
			Purpose:
			--------
			Extract selected structured HTML elements from a fetched HTML document.

			Parameters:
			-----------
			url (str): Page URL used to resolve relative hyperlinks and image links.
			html (str): Raw HTML content.
			selected_methods (Optional[List[str]]): Selected extraction method names.

			Returns:
			--------
			Dict[str, List[str]]: Structured extraction results by display label.
		'''
		try:
			source_url = self.validate_required_string( 'url', url )
			source_html = self.validate_required_string( 'html', html )
			methods = selected_methods or [ ]
			
			if not isinstance( methods, list ):
				raise TypeError( 'selected_methods must be a list of strings or None.' )
			
			results: Dict[ str, List[ str ] ] = { }
			soup = BeautifulSoup( source_html, 'html.parser' )
			
			registry: Dict[ str, Tuple[ str, Any ] ] = \
				{
						'scrape_headings':
							(
									'Headings',
									lambda: [
											tag.get_text( ' ', strip=True )
											for tag in
											soup.find_all( [ 'h1', 'h2', 'h3', 'h4', 'h5', 'h6' ] )
											if tag.get_text( ' ', strip=True )
									]
							),
						'scrape_paragraphs':
							(
									'Paragraphs',
									lambda: [
											tag.get_text( ' ', strip=True )
											for tag in soup.find_all( 'p' )
											if tag.get_text( ' ', strip=True )
									]
							),
						'scrape_lists':
							(
									'Lists',
									lambda: [
											tag.get_text( ' ', strip=True )
											for tag in soup.find_all( 'li' )
											if tag.get_text( ' ', strip=True )
									]
							),
						'scrape_tables':
							(
									'Tables',
									lambda: [
											cell.get_text( ' ', strip=True )
											for table in soup.find_all( 'table' )
											for row in table.find_all( 'tr' )
											for cell in row.find_all( [ 'td', 'th' ] )
											if cell.get_text( ' ', strip=True )
									]
							),
						'scrape_articles':
							(
									'Articles',
									lambda: [
											tag.get_text( ' ', strip=True )
											for tag in soup.find_all( 'article' )
											if tag.get_text( ' ', strip=True )
									]
							),
						'scrape_sections':
							(
									'Sections',
									lambda: [
											tag.get_text( ' ', strip=True )
											for tag in soup.find_all( 'section' )
											if tag.get_text( ' ', strip=True )
									]
							),
						'scrape_divisions':
							(
									'Divisions',
									lambda: [
											tag.get_text( ' ', strip=True )
											for tag in soup.find_all( 'div' )
											if tag.get_text( ' ', strip=True )
									]
							),
						'scrape_blockquotes':
							(
									'Blockquotes',
									lambda: [
											tag.get_text( ' ', strip=True )
											for tag in soup.find_all( 'blockquote' )
											if tag.get_text( ' ', strip=True )
									]
							),
						'scrape_hyperlinks':
							(
									'Hyperlinks',
									lambda: [
											self.normalize_url( source_url, tag.get( 'href', '' ) )
											for tag in soup.find_all( 'a', href=True )
											if
											self.normalize_url( source_url, tag.get( 'href', '' ) )
									]
							),
						'scrape_images':
							(
									'Images',
									lambda: [
											self.normalize_url( source_url, tag.get( 'src', '' ) )
											for tag in soup.find_all( 'img', src=True )
											if
											self.normalize_url( source_url, tag.get( 'src', '' ) )
									]
							),
				}
			
			for method_name in methods:
				if method_name not in registry:
					continue
				
				label, extractor = registry[ method_name ]
				values = self.coerce_items( extractor( ) )
				deduped: List[ str ] = [ ]
				seen: set[ str ] = set( )
				
				for value in values:
					if value not in seen:
						seen.add( value )
						deduped.append( value )
				
				results[ label ] = deduped
			
			return results
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = (
					'extract_structured_data( self, url: str, html: str, '
					'selected_methods: Optional[ List[ str ] ]=None ) '
					'-> Dict[ str, List[ str ] ]'
			)
			raise exception
	
	def scrape_paragraphs( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract readable text from all paragraph elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Cleaned paragraph text entries.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_paragraphs' ] ).get( 'Paragraphs', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_paragraphs( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_lists( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract readable text from all list item elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Cleaned list item text entries.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_lists' ] ).get( 'Lists', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_lists( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_tables( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract flattened table cell text from all table elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Table cell values from td and th elements.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_tables' ] ).get( 'Tables', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_tables( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_articles( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract consolidated readable text from all article elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Article-level text blocks.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_articles' ] ).get( 'Articles', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_articles( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_headings( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract readable text from h1 through h6 heading elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Cleaned heading strings.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_headings' ] ).get( 'Headings', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_headings( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_divisions( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract readable text from all div elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Cleaned division text blocks.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_divisions' ] ).get( 'Divisions', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_divisions( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_sections( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract readable text from all section elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Cleaned section text blocks.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_sections' ] ).get( 'Sections', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_sections( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_blockquotes( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract readable text from all blockquote elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Cleaned blockquote text entries.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_blockquotes' ] ).get( 'Blockquotes', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_blockquotes( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_hyperlinks( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract hyperlink href values from all anchor elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Hyperlink href values.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_hyperlinks' ] ).get( 'Hyperlinks', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_hyperlinks( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def scrape_images( self, uri: str ) -> List[ str ] | None:
		'''
			Purpose:
			--------
			Extract image source values from all image elements.

			Parameters:
			-----------
			uri (str): Fully-qualified URI of the HTML document.

			Returns:
			--------
			List[str] | None: Image source values.
		'''
		try:
			url = self.validate_required_string( 'uri', uri )
			self.fetch( url, time=int( self.timeout or 10 ) )
			return self.extract_structured_data( url, self.html or '',
				[ 'scrape_images' ] ).get( 'Images', [ ] )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = 'scrape_images( self, uri: str ) -> List[ str ] | None'
			raise exception
	
	def create_schema( self, function: str, tool: str, description: str,
			parameters: dict, required: list[ str ] ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Construct and return a dynamic tool schema definition.

			Parameters:
			-----------
			function (str): Function name exposed to the model.
			tool (str): Underlying service or system name.
			description (str): Description of the exposed function.
			parameters (dict): JSON-schema-style parameter definitions.
			required (list[str]): Required parameter names.

			Returns:
			--------
			Dict[str, Any] | None: JSON-compatible tool schema dictionary.
		'''
		try:
			function_name = self.validate_required_string( 'function', function )
			tool_name = self.validate_required_string( 'tool', tool )
			schema_description = self.validate_required_string( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError( 'parameters must be a dict of parameter schema definitions.' )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			if not isinstance( required, list ):
				raise TypeError( 'required must be a list of strings or None.' )
			
			return {
					'name': function_name,
					'description': (
							f'{schema_description} This function uses the {tool_name} service.'
					),
					'parameters':
						{
								'type': 'object',
								'properties': parameters,
								'required': required
						}
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebFetcher'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, Any ] | None'
			)
			raise exception

class WebCrawler( WebFetcher ):
	'''

		Purpose:
		--------
		Extends WebFetcher with single-page scraping, optional Playwright rendering,
		and bounded recursive crawl orchestration.

		Attributes:
		-----------
		use_playwright,
		browser_context,
		raw_url,
		raw_html,
		pages,
		summary,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this crawler.
		__dir__(...): Performs the __dir__ operation for this crawler.
		fetch(...): Performs the fetch operation for this crawler.
		render_with_playwright(...): Performs the render_with_playwright operation.
		scrape_page(...): Performs the scrape_page operation for this crawler.
		crawl(...): Performs the crawl operation for this crawler.

	'''
	use_playwright: Optional[ bool ]
	browser_context: Optional[ Any ]
	raw_url: Optional[ str ]
	raw_html: Optional[ str ]
	pages: Optional[ List[ Dict[ str, Any ] ] ]
	summary: Optional[ Dict[ str, Any ] ]
	
	def __init__( self, headers: Optional[ Dict[ str, str ] ] = None,
			use_playwright: bool = False ) -> None:
		'''
			Purpose:
			--------
			Initialize WebCrawler with optional headers and optional Playwright rendering.

			Parameters:
			-----------
			headers (Optional[Dict[str, str]]): Optional request headers.
			use_playwright (bool): Whether to render pages through Playwright.

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.browser_context = None
		self.raw_url = None
		self.raw_html = None
		self.response = None
		self.pages = [ ]
		self.summary = { }
		self.use_playwright = bool( use_playwright )
		
		if headers is not None:
			self.headers = headers
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ] = cfg.AGENTS
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Return stable introspection names for the crawler.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]: Ordered attribute and method names.
		'''
		return [
				'use_playwright',
				'browser_context',
				'raw_url',
				'raw_html',
				'pages',
				'summary',
				'fetch',
				'html_to_text',
				'coerce_items',
				'extract_title',
				'truncate_text',
				'normalize_url',
				'same_domain',
				'extract_links',
				'extract_structured_data',
				'render_with_playwright',
				'scrape_page',
				'crawl'
		]
	
	def fetch( self, url: str, time: int = 10 ) -> Result | None:
		'''
			Purpose:
			--------
			Fetch a page using either Playwright rendering or the base WebFetcher
			requests-based fetch path.

			Parameters:
			-----------
			url (str): Absolute URL to fetch.
			time (int): Request timeout in seconds.

			Returns:
			--------
			Result | None: Result returned by the base fetch path, or None when
			Playwright rendering is used.
		'''
		try:
			throw_if( 'url', url )
			
			if self.use_playwright:
				self.url = str( url ).strip( )
				self.timeout = int( time )
				self.raw_url = self.url
				self.raw_html = self.render_with_playwright( self.url, timeout=self.timeout )
				self.html = self.raw_html or ''
				self.soup = BeautifulSoup( self.html, 'html.parser' )
				return None
			
			return super( ).fetch( url=url, time=time )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebCrawler'
			exception.method = 'fetch( self, url: str, time: int=10 ) -> Result | None'
			raise exception
	
	def render_with_playwright( self, url: str, timeout: int = 15 ) -> str:
		'''
			Purpose:
			--------
			Render a page with Playwright and return the rendered HTML.

			Parameters:
			-----------
			url (str): URL to render.
			timeout (int): Timeout seconds for page navigation and network idle.

			Returns:
			--------
			str: Rendered HTML for the page.
		'''
		try:
			throw_if( 'url', url )
			
			with sync_playwright( ) as p:
				browser = p.chromium.launch( )
				page = browser.new_page( )
				page.goto( url, timeout=int( timeout ) * 1000 )
				page.wait_for_load_state( 'networkidle', timeout=int( timeout ) * 1000 )
				html = page.content( )
				browser.close( )
				return html
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebCrawler'
			exception.method = 'render_with_playwright( self, url: str, timeout: int=15 ) -> str'
			raise exception
	
	def scrape_page( self, url: str, include_title: bool = True,
			include_basic_text: bool = True, include_raw_html: bool = False,
			selected_methods: Optional[ List[ str ] ] = None, request_timeout: int = 10,
			max_bytes: int = 1000000 ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Fetch and extract one web page using the currently configured fetch path.

			Parameters:
			-----------
			url (str): Page URL to fetch.
			include_title (bool): Include the page title.
			include_basic_text (bool): Include normalized page text.
			include_raw_html (bool): Include raw HTML.
			selected_methods (Optional[List[str]]): Structured extraction methods.
			request_timeout (int): Request timeout in seconds.
			max_bytes (int): Maximum accepted response size in bytes.

			Returns:
			--------
			Dict[str, Any]: Page scrape result.
		'''
		page_result: Dict[ str, Any ] = \
			{
					'url': url,
					'status_code': None,
					'encoding': None,
					'title': '',
					'plain_text': '',
					'raw_html': '',
					'links_discovered': [ ],
					'data': { },
					'errors': [ ],
					'content_bytes': 0,
					'truncated_by_max_bytes': False,
			}
		
		try:
			methods = selected_methods or [ ]
			self.fetch( url=url, time=int( request_timeout ) )
			
			raw_html = self.html or ''
			if self.response is not None:
				page_result[ 'status_code' ] = getattr( self.response, 'status_code', None )
				page_result[ 'encoding' ] = getattr( self.response, 'encoding', None )
			else:
				page_result[ 'status_code' ] = 200
				page_result[ 'encoding' ] = 'rendered'
			
			raw_bytes = raw_html.encode( 'utf-8', errors='ignore' )
			page_result[ 'content_bytes' ] = len( raw_bytes )
			
			if int( max_bytes ) > 0 and len( raw_bytes ) > int( max_bytes ):
				raw_html = raw_bytes[ : int( max_bytes ) ].decode( 'utf-8', errors='ignore' )
				page_result[ 'truncated_by_max_bytes' ] = True
				page_result[ 'errors' ].append(
					f'Response exceeded max bytes and was truncated to {int( max_bytes )} bytes.' )
			
			page_result[ 'links_discovered' ] = self.extract_links( url, raw_html )
			
			if include_title:
				page_result[ 'title' ] = self.extract_title( raw_html )
			
			if include_basic_text:
				try:
					page_result[ 'plain_text' ] = self.html_to_text( raw_html ) or ''
				except Exception as exc:
					page_result[ 'errors' ].append( f'Basic Text: {str( exc )}' )
			
			if include_raw_html:
				page_result[ 'raw_html' ] = raw_html
			
			page_result[ 'data' ] = self.extract_structured_data(
				url=url,
				html=raw_html,
				selected_methods=methods )
			
			return page_result
		
		except Exception as exc:
			page_result[ 'errors' ].append( f'Fetch: {str( exc )}' )
			return page_result
	
	def crawl( self, seed_url: str, include_title: bool = True,
			include_basic_text: bool = True, include_raw_html: bool = False,
			selected_methods: Optional[ List[ str ] ] = None, recursive: bool = False,
			max_depth: int = 1, max_pages: int = 10, same_domain_only: bool = True,
			request_timeout: int = 10, delay_seconds: float = 0.25,
			max_bytes: int = 1000000 ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Crawl one page or a bounded set of pages from a seed URL.

			Parameters:
			-----------
			seed_url (str): Initial URL.
			include_title (bool): Include page titles.
			include_basic_text (bool): Include normalized page text.
			include_raw_html (bool): Include raw HTML.
			selected_methods (Optional[List[str]]): Structured extraction method names.
			recursive (bool): Enable recursive crawling.
			max_depth (int): Maximum crawl depth.
			max_pages (int): Maximum number of pages to process.
			same_domain_only (bool): Restrict discovered URLs to the seed domain.
			request_timeout (int): Request timeout in seconds.
			delay_seconds (float): Delay between page requests.
			max_bytes (int): Maximum accepted response size in bytes.

			Returns:
			--------
			Dict[str, Any]: Crawl result containing pages and summary.
		'''
		try:
			throw_if( 'seed_url', seed_url )
			
			started_at = dt.datetime.now( )
			normalized_seed = self.normalize_url( seed_url, seed_url )
			if not normalized_seed:
				raise ValueError( 'A valid absolute URL is required.' )
			
			methods = selected_methods or [ ]
			queue: List[ Tuple[ str, int ] ] = [ (normalized_seed, 0) ]
			visited: set[ str ] = set( )
			enqueued: set[ str ] = { normalized_seed }
			skipped_urls: List[ str ] = [ ]
			pages: List[ Dict[ str, Any ] ] = [ ]
			
			index = 0
			while index < len( queue ) and len( pages ) < int( max_pages ):
				current_url, depth = queue[ index ]
				index += 1
				
				if current_url in visited:
					continue
				
				visited.add( current_url )
				
				page_result = self.scrape_page(
					url=current_url,
					include_title=include_title,
					include_basic_text=include_basic_text,
					include_raw_html=include_raw_html,
					selected_methods=methods,
					request_timeout=int( request_timeout ),
					max_bytes=int( max_bytes ) )
				
				page_result[ 'depth' ] = depth
				pages.append( page_result )
				
				if float( delay_seconds ) > 0 and index < len( queue ):
					time.sleep( float( delay_seconds ) )
				
				if not recursive:
					continue
				
				if depth >= int( max_depth ):
					continue
				
				discovered_links = page_result.get( 'links_discovered', [ ] ) or [ ]
				for next_url in discovered_links:
					if len( pages ) + (len( queue ) - index) >= int( max_pages ):
						break
					
					if not next_url or next_url in visited or next_url in enqueued:
						continue
					
					if same_domain_only and not self.same_domain( normalized_seed, next_url ):
						skipped_urls.append( next_url )
						continue
					
					queue.append( (next_url, depth + 1) )
					enqueued.add( next_url )
			
			finished_at = dt.datetime.now( )
			error_count = sum( len( page.get( 'errors', [ ] ) or [ ] ) for page in pages )
			total_bytes = sum( int( page.get( 'content_bytes', 0 ) or 0 ) for page in pages )
			
			self.pages = pages
			self.summary = {
					'mode': 'recursive' if recursive else 'single-page',
					'seed_url': normalized_seed,
					'pages_processed': len( pages ),
					'pages_visited': len( visited ),
					'pages_skipped': len( skipped_urls ),
					'pages_enqueued_remaining': max( 0, len( queue ) - index ),
					'errors': error_count,
					'total_content_bytes': total_bytes,
					'recursive_requested': bool( recursive ),
					'max_depth': int( max_depth ),
					'max_pages': int( max_pages ),
					'same_domain_only': bool( same_domain_only ),
					'request_timeout': int( request_timeout ),
					'delay_seconds': float( delay_seconds ),
					'max_bytes_per_page': int( max_bytes ),
					'use_playwright': bool( self.use_playwright ),
					'started_at': started_at.isoformat( ),
					'finished_at': finished_at.isoformat( ),
					'elapsed_seconds': round( (finished_at - started_at).total_seconds( ), 3 ),
					'visited_urls': list( visited ),
					'skipped_urls': skipped_urls,
			}
			
			return {
					'pages': self.pages,
					'summary': self.summary
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'WebCrawler'
			exception.method = (
					'crawl( self, seed_url: str, include_title: bool=True, '
					'include_basic_text: bool=True, include_raw_html: bool=False, '
					'selected_methods: Optional[ List[ str ] ]=None, recursive: bool=False, '
					'max_depth: int=1, max_pages: int=10, same_domain_only: bool=True, '
					'request_timeout: int=10, delay_seconds: float=0.25, '
					'max_bytes: int=1000000 ) -> Dict[ str, Any ]'
			)
			raise exception

class ArXiv( Fetcher ):
	'''

		Purpose:
		--------
		Fetches ArXiv documents through the LangChain ArxivRetriever.

		Attributes:
		-----------
		fetcher,
		documents,
		max_documents,
		full_documents,
		include_metadata,
		query,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.

	'''
	fetcher: Optional[ ArxivRetriever ]
	documents: Optional[ List[ Document ] ]
	max_documents: Optional[ int ]
	full_documents: Optional[ bool ]
	include_metadata: Optional[ bool ]
	query: Optional[ str ]
	
	def __init__( self, max_documents: int=5, full_documents: bool=False,
			include_metadata: bool=False ) -> None:
		super( ).__init__( )
		self.fetcher = None
		self.documents = None
		self.query = None
		self.max_documents = max( 1, min( int( max_documents ), 300 ) )
		self.full_documents = bool( full_documents )
		self.include_metadata = bool( include_metadata )
	
	def fetch( self, question: str, max_documents: int=None,
			full_documents: bool=None, include_metadata: bool=None ) -> List[ Document ] | None:
		'''

			Purpose:
			--------
			Query ArXiv through LangChain's ArxivRetriever and return LangChain
			Document objects.

			Parameters:
			-----------
			question: str
			Free-text search query or arXiv identifier.
			
			max_documents: int
			Optional override for maximum number of returned documents.
			
			full_documents:  bool
			Optional override indicating whether full document text should  be fetched instead of
			summary-oriented retrieval.
			
			include_metadata: bool
			Optional override indicating whether all available metadata should be included.

			Returns:
			--------
			List[Document] | None

		'''
		try:
			throw_if( 'question', question )
			self.query = question.strip( )
			max_docs = self.max_documents if max_documents is None else \
				max( 1, min( int( max_documents ), 300 ) )
			
			get_full = self.full_documents if full_documents is None else \
				bool( full_documents )
			
			load_meta = self.include_metadata if include_metadata is None else \
				bool( include_metadata )
			
			self.fetcher = ArxivRetriever( load_max_docs=max_docs, get_full_documents=get_full,
				load_all_available_meta=load_meta )
			
			self.documents = self.fetcher.invoke( self.query )
			return self.documents
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ArXiv'
			exception.method =  'fetch( self, *kwargs ) -> List[ Document ]'
			raise exception

class GoogleDrive( Fetcher ):
	'''

		Purpose:
		--------
		Fetches Google Drive documents through the LangChain GoogleDriveRetriever.

		Attributes:
		-----------
		fetcher,
		documents,
		num_results,
		folder_id,
		template,
		query,
		mime_type,
		mode,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		mime_options(...): Performs the mime_options operation for this fetcher.
		template_options(...): Performs the template_options operation for this fetcher.
		mode_options(...): Performs the mode_options operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.

	'''
	fetcher: Optional[ GoogleDriveRetriever ]
	documents: Optional[ List[ Document ] ]
	num_results: Optional[ int ]
	folder_id: Optional[ str ]
	template: Optional[ str ]
	query: Optional[ str ]
	mime_type: Optional[ str ]
	mode: Optional[ str ]
	
	def __init__( self ) -> None:
		super( ).__init__( )
		self.fetcher = None
		self.documents = None
		self.query = None
		self.template = 'gdrive-query'
		self.folder_id = 'root'
		self.num_results = 10
		self.mime_type = None
		self.mode = 'documents'
	
	@property
	def mime_options( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return supported MIME types aligned to the Google Drive retriever docs.
		
			Returns:
			--------
			List[str]
		
		'''
		return [ '', 'text/text', 'text/plain', 'text/html', 'text/csv', 'text/markdown',
				'image/png', 'image/jpeg', 'application/epub+zip', 'application/pdf',
				'application/rtf', 'application/vnd.google-apps.document',
				'application/vnd.google-apps.presentation', 'application/vnd.google-apps.spreadsheet',
				'application/vnd.google.colaboratory',
				'application/vnd.openxmlformats-officedocument.presentationml.presentation',
				'application/vnd.openxmlformats-officedocument.wordprocessingml.document', ]
	
	@property
	def template_options( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return predefined template options supported by GoogleDriveRetriever.
		
			Returns:
			--------
			List[str]
		
		'''
		return [ 'gdrive-all-in-folder', 'gdrive-query', 'gdrive-by-name', 'gdrive-query-in-folder',
				'gdrive-mime-type', 'gdrive-mime-type-in-folder', 'gdrive-query-with-mime-type',
				'gdrive-query-with-mime-type-and-folder', ]
	
	@property
	def mode_options( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return supported retrieval display modes.
		
			Returns:
			--------
			List[str]
		
		'''
		return [ 'documents', 'snippets' ]
	
	def fetch( self, question: str, folder_id: str='root', results: int=10, template: str='gdrive-query',
			mime_type: str=None, mode: str='documents' ) -> List[ Document ] | None:
		'''Query Google Drive through LangChain's GoogleDriveRetriever and return LangChain Document objects.
		
			Parameters:
			-----------
			question: str
				Free-text query used by the retriever. For templates that do not
				require a query, a placeholder value may still be passed.
				
			folder_id: str
				Google Drive folder id. Use 'root' for the user's root Drive.
				
			results: int
				Maximum number of returned documents.
				
			template: str
				Predefined GoogleDriveRetriever selection template.
				
			mime_type:
				Optional MIME type filter.
				
			mode: str
				Retrieval mode, typically 'documents' or 'snippets'.
		
			Returns:
			--------
			List[Document] | None
		
		'''
		try:
			throw_if( 'template', template )
			throw_if( 'folder_id', folder_id )
			
			self.query = (question or '').strip( )
			self.folder_id = folder_id.strip( ) if folder_id else 'root'
			self.num_results = max( 1, min( int( results ), 100 ) )
			self.template = template.strip( )
			self.mime_type = mime_type.strip( ) if isinstance( mime_type, str ) and mime_type.strip( ) else None
			self.mode = mode.strip( ) if mode else 'documents'
			
			retriever_kwargs: Dict[ str, Any ]={
					'folder_id': self.folder_id,
					'template': self.template,
					'num_results': self.num_results,
					'mode': self.mode,
			}
			
			if self.mime_type:
				retriever_kwargs[ 'mime_type' ]=self.mime_type
			
			if cfg.GOOGLE_ACCOUNT_FILE:
				retriever_kwargs[ 'credentials_path' ]=cfg.GOOGLE_ACCOUNT_FILE
			
			if cfg.GOOGLE_DRIVE_TOKEN_PATH:
				retriever_kwargs[ 'token_path' ]=cfg.GOOGLE_DRIVE_TOKEN_PATH
			
			self.fetcher = GoogleDriveRetriever( **retriever_kwargs )
			
			invoke_query = self.query
			if not invoke_query:
				if self.template in ('gdrive-all-in-folder', 'gdrive-mime-type',
				                     'gdrive-mime-type-in-folder'):
					invoke_query = '*'
				else:
					raise ValueError( 'A query is required for the selected Google Drive template.')
			
			self.documents = self.fetcher.invoke( invoke_query )
			return self.documents
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleDrive'
			exception.method = 'fetch( self, *kwargs ) -> List[ Document ]'
			raise exception

class Wikipedia( Fetcher ):
	'''

		Purpose:
		--------
		Fetches Wikipedia documents through the LangChain WikipediaRetriever.

		Attributes:
		-----------
		fetcher,
		documents,
		max_documents,
		include_metadata,
		language,
		query,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.

	'''
	fetcher: Optional[ WikipediaRetriever ]
	documents: Optional[ List[ Document ] ]
	max_documents: Optional[ int ]
	include_metadata: Optional[ bool ]
	language: Optional[ str ]
	query: Optional[ str ]
	
	def __init__( self, language: str='en', max_documents: int=5,
			include_metadata: bool=False ) -> None:
		super( ).__init__( )
		self.fetcher = None
		self.documents = None
		self.query = None
		self.language = (language or 'en').strip( ) or 'en'
		self.max_documents = max( 1, min( int( max_documents ), 300 ) )
		self.include_metadata = bool( include_metadata )
	
	def fetch( self, question: str, language: str=None, max_documents: int=None,
			include_metadata: bool=None ) -> List[ Document ] | None:
		'''
			Query Wikipedia through LangChain's WikipediaRetriever and return
			LangChain Document objects.

			Parameters:
			-----------
			question:
				Free-text Wikipedia query.
				
			language:
				Optional language code override, e.g. "en", "fr", "de", "ja".
				
			max_documents:
				Optional override for maximum number of returned documents.
				Hard-capped at 300.
				
			include_metadata:
				Optional override indicating whether all available metadata
				should be included.

			Returns:
			--------
			List[Document] | None

		'''
		try:
			throw_if( 'question', question )
			self.query = question.strip( )
			
			lang = self.language if language is None else \
				(language.strip( ) if language else 'en')
			
			max_docs = self.max_documents if max_documents is None else \
				max( 1, min( int( max_documents ), 300 ) )
			
			load_meta = self.include_metadata if include_metadata is None else \
				bool( include_metadata )
			
			self.fetcher = WikipediaRetriever( lang=lang, load_max_docs=max_docs,
				load_all_available_meta=load_meta )
			
			self.documents = self.fetcher.invoke( input=self.query )
			return self.documents
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Wikipedia'
			exception.method = 'fetch( self, question: str, **kwargs ) -> List[ Document ]'
			raise exception

class TheNews( Fetcher ):
	'''

		Purpose:
		--------
		Provides a structured wrapper around The News API endpoints.

	'''
	agents: Optional[ str ]
	url: Optional[ str ]
	response: Optional[ Response ]
	api_key: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	endpoint: Optional[ str ]
	limit: Optional[ int ]
	page: Optional[ int ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize The News API wrapper with sane defaults and environment-
			based authentication.
		'''
		super( ).__init__( )
		self.timeout = 10
		self.url = 'https://api.thenewsapi.com/v1/news'
		self.response = None
		self.result = None
		self.headers = { }
		self.params = { }
		self.endpoint = 'all'
		self.limit = 10
		self.page = 1
		self.api_key = cfg.THENEWS_API_KEY
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		if 'Accept' not in self.headers:
			self.headers[ 'Accept' ]='application/json'
	
	def __dir__( self ) -> List[ str ]:
		'''
			Return visible member ordering.
		'''
		return [ 'api_key', 'url', 'timeout', 'headers', 'endpoint',
		         'limit', 'page', 'params', 'fetch', ]
	
	def fetch( self, endpoint: str='all', query: str='', language: str='en', categories: str='',
			exclude_categories: str='', locale: str='', domains: str='', exclude_domains: str='',
			source_ids: str='', exclude_source_ids: str='', published_after: str='',
			published_before: str='', published_on: str='', sort: str='published_at',
			limit: int=10, page: int=1, include_similar: bool=True, headlines_per_category: int=6,
			time: int=10, api_key: str=None ) -> Dict[ str, Any ] | None:
		'''Send a request to The News API using one of the documented endpoints and return the parsed JSON response.

			Parameters:
			-----------
			endpoint:
				One of: all, top, headlines, sources
				
			query:
				Search query for endpoints that support search.
				
			language:
				Comma-separated language codes.
				
			categories:
				Comma-separated category filter.
				
			exclude_categories:
				Comma-separated excluded categories.
				
			locale:
				Comma-separated country codes where supported.
				
			domains:
				Comma-separated included domains.
				
			exclude_domains:
				Comma-separated excluded domains.
				
			source_ids:
				Comma-separated included source ids.
				
			exclude_source_ids:
				Comma-separated excluded source ids.
				
			published_after:
				Date/datetime filter when supported.
				
			published_before:
				Date/datetime filter when supported.
				
			published_on:
				Single publication date filter when supported.
				
			sort:
				Sort order for applicable endpoints.
				
			limit:
				Result size.
				
			page:
				Page number.
				
			include_similar:
				Headlines-only switch.
				
			headlines_per_category:
				Headlines-only per-category limit.
				
			time:
				Request timeout in seconds.
				
			api_key:
				Optional runtime override. Falls back to cfg.THENEWS_API_KEY.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.endpoint = (endpoint or 'all').strip( ).lower( )
			self.timeout = int( time )
			self.limit = max( 1, min( int( limit ), 50 ) )
			self.page = max( 1, int( page ) )
			active_key = (api_key or self.api_key or '').strip( )
			if not active_key:
				raise ValueError( 'The News API key is required.' )
			
			valid_endpoints = { 'all', 'top', 'headlines', 'sources' }
			if self.endpoint not in valid_endpoints:
				raise ValueError( f"Unsupported endpoint '{self.endpoint}'. "
					f"Supported endpoints: {', '.join( sorted( valid_endpoints ) )}." )
			
			self.params = { 'api_token': active_key }
			if self.endpoint in ('all', 'top'):
				if query and query.strip( ):
					self.params[ 'search' ]=query.strip( )
				
				if language and language.strip( ):
					self.params[ 'language' ]=language.strip( )
				
				if categories and categories.strip( ):
					self.params[ 'categories' ]=categories.strip( )
				
				if exclude_categories and exclude_categories.strip( ):
					self.params[ 'exclude_categories' ]=exclude_categories.strip( )
				
				if domains and domains.strip( ):
					self.params[ 'domains' ]=domains.strip( )
				
				if exclude_domains and exclude_domains.strip( ):
					self.params[ 'exclude_domains' ]=exclude_domains.strip( )
				
				if source_ids and source_ids.strip( ):
					self.params[ 'source_ids' ]=source_ids.strip( )
				
				if exclude_source_ids and exclude_source_ids.strip( ):
					self.params[ 'exclude_source_ids' ]=exclude_source_ids.strip( )
				
				if published_after and published_after.strip( ):
					self.params[ 'published_after' ]=published_after.strip( )
				
				if published_before and published_before.strip( ):
					self.params[ 'published_before' ]=published_before.strip( )
				
				if published_on and published_on.strip( ):
					self.params[ 'published_on' ]=published_on.strip( )
				
				if sort and sort.strip( ):
					self.params[ 'sort' ]=sort.strip( )
				
				self.params[ 'limit' ]=self.limit
				self.params[ 'page' ]=self.page
				if self.endpoint == 'top' and locale and locale.strip( ):
					self.params[ 'locale' ]=locale.strip( )
			
			elif self.endpoint == 'headlines':
				if locale and locale.strip( ):
					self.params[ 'locale' ]=locale.strip( )
				
				if domains and domains.strip( ):
					self.params[ 'domains' ]=domains.strip( )
				
				if exclude_domains and exclude_domains.strip( ):
					self.params[ 'exclude_domains' ]=exclude_domains.strip( )
				
				if source_ids and source_ids.strip( ):
					self.params[ 'source_ids' ]=source_ids.strip( )
				
				if exclude_source_ids and exclude_source_ids.strip( ):
					self.params[ 'exclude_source_ids' ]=exclude_source_ids.strip( )
				
				if language and language.strip( ):
					self.params[ 'language' ]=language.strip( )
				
				if published_on and published_on.strip( ):
					self.params[ 'published_on' ]=published_on.strip( )
				
				self.params[ 'headlines_per_category' ]=max( 1, min( int( headlines_per_category ), 10 ) )
				
				self.params[ 'include_similar' ]=\
					'true' if bool( include_similar ) else 'false'
			
			elif self.endpoint == 'sources':
				if categories and categories.strip( ):
					self.params[ 'categories' ]=categories.strip( )
				
				if exclude_categories and exclude_categories.strip( ):
					self.params[ 'exclude_categories' ]=exclude_categories.strip( )
				
				if language and language.strip( ):
					self.params[ 'language' ]=language.strip( )
				
				self.params[ 'page' ]=self.page
			
			request_url = f'{self.url}/{self.endpoint}'
			self.response = requests.get( url=request_url, params=self.params, headers=self.headers,
				timeout=self.timeout )
			
			self.response.raise_for_status( )
			return self.response.json( )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'TheNews'
			exception.method =  'fetch( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception

class GoogleSearch( Fetcher ):
	'''

		Purpose:
		--------
		Fetches Google Custom Search results.
	
		Attributes:
		-----------
		keywords,
		url,
		re_tag,
		re_ws,
		response,
		api_key,
		cse_id,
		params,
		results,
		start,
	
		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
	
	'''
	keywords: Optional[ str ]
	url: Optional[ str ]
	re_tag: Optional[ Pattern ]
	re_ws: Optional[ Pattern ]
	response: Optional[ Response ]
	api_key: Optional[ str ]
	cse_id: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	results: Optional[ int ]
	start: Optional[ int ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize GoogleSearch with environment-based credentials and sane defaults.

			Returns:
			-----------
			None
		'''
		super( ).__init__( )
		self.api_key = cfg.GOOGLE_API_KEY
		self.cse_id = cfg.GOOGLE_CSE_ID
		self.re_tag = re.compile( r'<[^>]+>' )
		self.re_ws = re.compile( r'\s+' )
		self.url = 'https://customsearch.googleapis.com/customsearch/v1'
		self.headers = { }
		self.timeout = 10
		self.keywords = None
		self.params = { }
		self.response = None
		self.results = 10
		self.start = 1
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		if 'Accept' not in self.headers:
			self.headers[ 'Accept' ]='application/json'
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			-----------
			Control visible ordering for GoogleSearch.
		'''
		return [ 'keywords', 'url', 'timeout', 'headers', 'fetch', 'api_key',
		         'response', 'cse_id', 'params', 'agents', 'results', 'start', ]
	
	def fetch( self, keywords: str, results: int=10,
			start: int=1, exact_terms: str='', exclude_terms: str='',
			file_type: str='', date_restrict: str='', gl: str='', lr: str='',
			safe: str='off', search_type: str='', site_search: str='', site_search_filter: str='',
			sort: str='', img_size: str='', img_type: str='', img_color_type: str='',
			img_dominant_color: str='', time: int=10, api_key: str=None,
			cse_id: str=None ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Send a request to the Google Custom Search JSON API and return the
			parsed JSON response.

			Parameters:
			-----------
			keywords:
				Search query string.
			results:
				Number of results per request. Google supports up to 10 per request.
			start:
				Index of the first result to return. Combined paging is limited to
				the first 100 results.
			exact_terms:
				Phrase that all documents must contain.
			exclude_terms:
				Words or phrases that must not appear.
			file_type:
				File extension filter, e.g. pdf, docx.
			date_restrict:
				Date restriction such as d7, w2, m1, y1.
			gl:
				Country boost code, e.g. us.
			lr:
				Language restrict code, e.g. lang_en.
			safe:
				Safe search value, typically active or off.
			search_type:
				Set to image for image search.
			site_search:
				Restrict to a site or domain.
			site_search_filter:
				i to include, e to exclude the specified site.
			sort:
				Sort expression when supported by the engine.
			img_size:
				Image size filter when search_type=image.
			img_type:
				Image type filter when search_type=image.
			img_color_type:
				Image color type filter when search_type=image.
			img_dominant_color:
				Image dominant color filter when search_type=image.
			time:
				Request timeout in seconds.
			api_key:
				Optional runtime override. Falls back to cfg.GOOGLE_API_KEY.
			cse_id:
				Optional runtime override. Falls back to cfg.GOOGLE_CSE_ID.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			throw_if( 'keywords', keywords )
			active_key = (api_key or self.api_key or '').strip( )
			active_cse = (cse_id or self.cse_id or '').strip( )
			if not active_key:
				raise ValueError( 'Google API key is required.' )
			
			if not active_cse:
				raise ValueError( 'Google CSE ID is required.' )
			
			self.timeout = int( time )
			self.keywords = keywords.strip( )
			self.results = max( 1, min( int( results ), 10 ) )
			self.start = max( 1, min( int( start ), 91 ) )
			self.params = {
					'q': self.keywords,
					'key': active_key,
					'cx': active_cse,
					'num': self.results,
					'start': self.start,
					'safe': (safe or 'off').strip( ),
			}
			
			if exact_terms and exact_terms.strip( ):
				self.params[ 'exactTerms' ]=exact_terms.strip( )
			
			if exclude_terms and exclude_terms.strip( ):
				self.params[ 'excludeTerms' ]=exclude_terms.strip( )
			
			if file_type and file_type.strip( ):
				self.params[ 'fileType' ]=file_type.strip( )
			
			if date_restrict and date_restrict.strip( ):
				self.params[ 'dateRestrict' ]=date_restrict.strip( )
			
			if gl and gl.strip( ):
				self.params[ 'gl' ]=gl.strip( )
			
			if lr and lr.strip( ):
				self.params[ 'lr' ]=lr.strip( )
			
			if search_type and search_type.strip( ):
				self.params[ 'searchType' ]=search_type.strip( )
			
			if site_search and site_search.strip( ):
				self.params[ 'siteSearch' ]=site_search.strip( )
			
			if site_search_filter and site_search_filter.strip( ):
				self.params[ 'siteSearchFilter' ]=site_search_filter.strip( )
			
			if sort and sort.strip( ):
				self.params[ 'sort' ]=sort.strip( )
			
			if search_type.strip( ).lower( ) == 'image':
				if img_size and img_size.strip( ):
					self.params[ 'imgSize' ]=img_size.strip( )
				
				if img_type and img_type.strip( ):
					self.params[ 'imgType' ]=img_type.strip( )
				
				if img_color_type and img_color_type.strip( ):
					self.params[ 'imgColorType' ]=img_color_type.strip( )
				
				if img_dominant_color and img_dominant_color.strip( ):
					self.params[ 'imgDominantColor' ]=img_dominant_color.strip( )
			
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=self.timeout )
			
			self.response.raise_for_status( )
			return self.response.json( )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GoogleSearch'
			exception.method = ( 'fetch( self, keywords: str, results: int=10 ) -> Dict[ str, Any ]')
			raise exception
			
class GoogleMaps( Fetcher ):
	'''

		Purpose:
		--------
		Provides Google Maps geocoding, validation, and directions requests.

		Attributes:
		-----------
		file_path,
		headers,
		num_results,
		api_key,
		mode,
		latitude,
		longitude,
		coordinates,
		address,
		directions,
		params,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		geocode_location(...): Performs the geocode_location operation for this fetcher.
		geocode_coordinates(...): Performs the geocode_coordinates operation for this fetcher.
		validate_address(...): Performs the validate_address operation for this fetcher.
		request_directions(...): Performs the request_directions operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	file_path: Optional[ str ]
	headers: Optional[ Dict[ str, Any ] ]
	num_results: Optional[ int ]
	api_key: Optional[ str ]
	mode: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	coordinates: Optional[ Tuple[ float, float ] ]
	address: Optional[ str ]
	directions: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	
	def __init__( self ) -> None:
		super( ).__init__( )
		self.api_key = cfg.GOOGLE_API_KEY
		self.headers = { }
		self.params = { }
		self.longitude = None
		self.latitude = None
		self.mode = None
		self.url = None
		self.file_path = None
		self.coordinates = None
		self.fetcher = None
		self.address = None
		self.directions = None
		self.agents = cfg.AGENTS
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
	
	def geocode_location( self, address: str ) -> Tuple[ float, float ]:
		'''Uses gmaps to get coordinates from a given address.

			Parameters:
			-----------
			address (str): address

			Returns:
			--------
			Tuple[ float, float ] - a tuple of floats representing latitude and longitude (lat, lng)

		'''
		try:
			throw_if( 'address', address )
			self.address = address
			self.url = "https://maps.googleapis.com/maps/api/geocode/json"
			self.params = { 'address': self.address, 'key': self.api_key, 'headers': self.headers }
			self.response = requests.get( url=self.url, params=self.params )
			self.response.raise_for_status( )
			_response = self.response.json( )
			_result = _response[ 'results' ][ 0 ]
			_geo = _result[ 'geometry' ]
			_loc = _geo[ 'location' ]
			_lat = _loc[ 'lat' ]
			_lng = _loc[ 'lng' ]
			return ( _lat, _lng )
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleMaps'
			exception.method = 'fetch_location( self, address: str ) -> Tuple[ float, float ]'
			raise exception
			

	def geocode_coordinates( self, lat: float, long: float ) -> str | None:
		'''Uses the Google Maps API to get address from coordinates.

			Parameters:
			-----------
			lat (float): The geographic latitude of a given location
			long (floa): The geographic longitude of a given location

			Returns:
			--------
			List[ Document ]: List of Document objects parsed from HTML content.

		'''
		try:
			throw_if( 'latitiude', lat )
			throw_if( 'longitude', long )
			self.latitude = lat
			self.longitude = long
			self.coordinates =  ( lat, long )
			self.url = r'https://maps.googleapis.com/maps/api/geocode/json?latlng='
			self.url += f'{lat},' + f'{long}' + f'&key={self.api_key}'
			_response = requests.get( self.url ).json( )
			_address = _response[ 'results' ][0][ 'formatted_address' ]
			return _address
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleMaps'
			exception.method = 'fetch_location( self, address: str ) -> Tuple[ float, float ]'
			raise exception
			
	
	def validate_address( self, address: List[ str ]  ) -> Dict[ Any, Any ] | None:
		"""
			
			Purpose:
			--------
			Validate an address using Google's Address Validation API.
	
			Parameters:
			-----------
			address (list): List of address lines (e.g. ["1600 Amphitheatre Parkway"]).
	
			Returns:
			--------
			dict: Parsed JSON response from Google.
			
		"""
		try:
			throw_if( 'address', address )
			url = 'https://addressvalidation.googleapis.com/v1:validateAddress'
			payload = \
			{
				'address': { 'addressLines': address, }
			}
			
			self.params = \
			{
				'key': self.api_key
			}
			
			response = requests.post( url, params=self.params, json=payload )
			if response.status_code != 200:
				msg = f'Request failed: {response.status_code} – {response.text}'
				raise RuntimeError( msg )
			return response.json( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleMaps'
			exception.method = 'validate_address( self, address: str ) -> str'
			raise exception
			
	
	def request_directions( self, origin: str, destination: str, mode: str='driving' ) -> str | None:
		"""
		
			Purpose:
			----------
			Request route directions from Google Maps Directions API.
		
			Parameters:
			-----------
			api_key     (str): Google Maps Platform API key.
			origin      (str): Starting location (address or lat,lng).
			destination (str): Ending location (address or lat,lng).
			mode        (str): travel mode: 'driving', 'walking', bicycling', or 'transit'.
		
			Returns:
			---------
			dict: Parsed JSON response from Google Directions API.
			
		"""
		try:
			throw_if( 'origin', origin )
			throw_if( 'destination', destination )
			self.mode = mode
			self.url = "https://maps.googleapis.com/maps/api/directions/json"
			self.params = \
			{
				'origin': origin,
				'destination': destination,
				'mode': self.mode,
				'key': self.api_key
			}
			
			self.response = requests.get( url=self.url, params=self.params )
			self.response.raise_for_status( )
			_results = self.response.json( )
			_route = _results.get( 'routes', [ { } ] )[ 0 ]
			return _route
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleMaps'
			exception.method = 'request_directions( self, origin: str, destination: str ) -> dict'
			raise exception
			
		
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict, required: list[ str ] ) -> Dict[ str, str ] | None:
		"""

			Purpose:
			________
			Construct and return a fully dynamic OpenAI Tool API schema definition.
			Supports arbitrary parameters, types, nested objects, and required fields.

			Parameters:
			___________
			function (str):
			The function name exposed to the LLM.

			tool (str):
			The underlying system or service the function wraps
			(e.g., “Google Maps”, “SQLite”, “Weather API”).

			description (str):
			Precise explanation of what the function does.

			parameters (dict):
			A dictionary defining parameter names and JSON schema descriptors.
			Each value must itself be a valid JSON-schema fragment.

				Example:
					{
						"origin": {
							"type": "string",
							"description": "Starting location."
						},
						"destination": {
							"type": "string",
							"description": "Ending location."
						},
						"mode": {
							"type": "string",
							"enum": ["driving", "walking", "bicycling", "transit"],
							"description": "Travel mode."
						}
					}

			required (list[str] | None):
			List of required parameter names.
			If None, required = list(parameters.keys()).

			Returns:
			________
			dict:
			A JSON-compatible dictionary defining the tool schema.

		"""
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			if not isinstance( parameters, dict ):
				msg = 'parameters must be a dict of param_name → schema definitions.'
				raise ValueError( msg )
			func_name = function.strip( )
			tool_name = tool.strip( )
			desc = description.strip( )
			if required is None:
				required = list( parameters.keys( ) )
			_schema  = \
			{
				'name': func_name,
				'description': f'{desc} This function uses the {tool_name} service.',
				'parameters':
				{
					'type': 'object',
					'properties': parameters,
					'required': required
				}
			}
			return _schema
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleMaps'
			exception.method = 'create_schema( self, *params ) -> Dict[ str, str ]'
			raise exception

class GoogleWeather( Fetcher ):
	'''

		Purpose:
		--------
		Provides Google Weather current conditions, forecasts, hourly history,
		and public weather alert requests.

		Attributes:
		-----------
		gmaps,
		headers,
		api_key,
		mode,
		latitude,
		longitude,
		coordinates,
		address,
		params,
		response,
		result,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		resolve_coordinates(...): Performs the resolve_coordinates operation for this fetcher.
		request(...): Performs the request operation for this fetcher.
		fetch_current(...): Performs the fetch_current operation for this fetcher.
		fetch_hourly_forecast(...): Performs the fetch_hourly_forecast operation for this fetcher.
		fetch_daily_forecast(...): Performs the fetch_daily_forecast operation for this fetcher.
		fetch_hourly_history(...): Performs the fetch_hourly_history operation for this fetcher.
		fetch_alerts(...): Performs the fetch_alerts operation for this fetcher.

	'''
	gmaps: Optional[ GoogleMaps ]
	headers: Optional[ Dict[ str, Any ] ]
	api_key: Optional[ str ]
	mode: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	coordinates: Optional[ Tuple[ float, float ] ]
	address: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	response: Optional[ Response ]
	result: Optional[ Dict[ str, Any ] ]
	
	def __init__( self ) -> None:
		'''
			
			Purpose:
			--------
			Initialize the Google Weather wrapper with API, request, and coordinate state.
			
			Parameters:
			-----------
			None
			
			Returns:
			--------
			None
			
		'''
		super( ).__init__( )
		self.api_key = cfg.GOOGLE_WEATHER_API_KEY
		self.headers = { }
		self.gmaps = GoogleMaps( )
		self.mode = None
		self.url = 'https://weather.googleapis.com/v1'
		self.longitude = 0.0
		self.latitude = 0.0
		self.coordinates = (0.0, 0.0)
		self.fetcher = None
		self.address = None
		self.params = { }
		self.response = None
		self.result = None
		self.timeout = 10
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		if 'Accept' not in self.headers:
			self.headers[ 'Accept' ]='application/json'
	
	def __dir__( self ) -> List[ str ]:
		'''
			
			Purpose:
			--------
			Return stable introspection names for the Google Weather wrapper.
			
			Parameters:
			-----------
			None
			
			Returns:
			--------
			List[str]: Ordered attribute and method names.
			
		'''
		return [
				'api_key',
				'url',
				'timeout',
				'headers',
				'gmaps',
				'mode',
				'latitude',
				'longitude',
				'coordinates',
				'address',
				'params',
				'response',
				'result',
				'resolve_coordinates',
				'request',
				'fetch_current',
				'fetch_hourly_forecast',
				'fetch_daily_forecast',
				'fetch_hourly_history',
				'fetch_alerts'
		]
	
	def resolve_coordinates( self, address: str ) -> Tuple[ float, float ]:
		'''
			
			Purpose:
			--------
			Resolve a user-supplied address into latitude and longitude using the existing
			Google Maps helper.
			
			Parameters:
			-----------
			address (str): Physical address, named place, city, or other geocodable location.
			
			Returns:
			--------
			Tuple[float, float]: Latitude and longitude coordinates.
			
		'''
		try:
			throw_if( 'address', address )
			self.address = address.strip( )
			if not self.address:
				raise ValueError( 'Address cannot be empty.' )
			
			lat, lng = self.gmaps.geocode_location( address=self.address )
			self.latitude = float( lat )
			self.longitude = float( lng )
			self.coordinates = (self.latitude, self.longitude)
			return self.coordinates
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GoogleWeather'
			exception.method = (
					'resolve_coordinates( self, address: str ) -> Tuple[ float, float ]')
			raise exception
	
	def request( self, path: str, params: Dict[ str, Any ], time: int=10 ) -> Dict[ str, Any ] | None:
		'''
			
			Purpose:
			--------
			Send a GET request to a Google Weather API endpoint and return the JSON response.
			
			Parameters:
			-----------
			path (str): Google Weather API path relative to https://weather.googleapis.com/v1.
			params (Dict[str, Any]): Query parameters for the request.
			time (int): Request timeout in seconds.
			
			Returns:
			--------
			Dict[str, Any] | None: JSON response from the Google Weather API.
			
		'''
		try:
			throw_if( 'path', path )
			
			active_key = (self.api_key or '').strip( )
			if not active_key:
				raise ValueError( 'Google Weather API key is required.' )
			
			self.timeout = int( time )
			if self.timeout < 1:
				self.timeout = 10
			
			request_params = dict( params or { } )
			request_params[ 'key' ]=active_key
			
			clean_path = path.strip( ).lstrip( '/' )
			request_url = f'{self.url}/{clean_path}'
			self.params = request_params
			self.response = requests.get( url=request_url, params=request_params,
				headers=self.headers, timeout=self.timeout )
			
			self.response.raise_for_status( )
			self.result = self.response.json( )
			return self.result
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GoogleWeather'
			exception.method = (
					'request( self, path: str, params: Dict[ str, Any ], '
					'time: int=10 ) -> Dict[ str, Any ] | None')
			raise exception
	
	def fetch_current( self, address: str, units_system: str = 'METRIC',
			language_code: str = 'en', time: int=10 ) -> Dict[ str, Any ] | None:
		'''
			
			Purpose:
			--------
			Retrieve current weather conditions for an address or named location.
			
			Parameters:
			-----------
			address (str): Physical address, named place, city, or geocodable location.
			units_system (str): Units system used by the response, usually METRIC or IMPERIAL.
			language_code (str): BCP-47 language code used by the response.
			time (int): Request timeout in seconds.
			
			Returns:
			--------
			Dict[str, Any] | None: Google Weather current conditions response.
			
		'''
		try:
			lat, lng = self.resolve_coordinates( address )
			self.mode = 'current'
			self.params = {
					'location.latitude': lat,
					'location.longitude': lng,
					'unitsSystem': units_system,
					'languageCode': language_code
			}
			return self.request( path='currentConditions:lookup', params=self.params,
				time=time )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GoogleWeather'
			exception.method = (
					'fetch_current( self, address: str, units_system: str="METRIC", '
					'language_code: str="en", time: int=10 ) -> Dict[ str, Any ] | None')
			raise exception
	
	def fetch_hourly_forecast( self, address: str, hours: int=24, units_system: str = 'METRIC',
			language_code: str = 'en', time: int=10 ) -> Dict[ str, Any ] | None:
		'''
			
			Purpose:
			--------
			Retrieve hourly weather forecast data for an address or named location.
			
			Parameters:
			-----------
			address (str): Physical address, named place, city, or geocodable location.
			hours (int): Number of forecast hours to request, clamped to 1 through 240.
			units_system (str): Units system used by the response, usually METRIC or IMPERIAL.
			language_code (str): BCP-47 language code used by the response.
			time (int): Request timeout in seconds.
			
			Returns:
			--------
			Dict[str, Any] | None: Google Weather hourly forecast response.
			
		'''
		try:
			lat, lng = self.resolve_coordinates( address )
			self.mode = 'hourly_forecast'
			forecast_hours = max( 1, min( int( hours ), 240 ) )
			self.params = {
					'location.latitude': lat,
					'location.longitude': lng,
					'hours': forecast_hours,
					'unitsSystem': units_system,
					'languageCode': language_code
			}
			return self.request( path='forecast/hours:lookup', params=self.params, time=time )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GoogleWeather'
			exception.method = (
					'fetch_hourly_forecast( self, address: str, hours: int=24, '
					'units_system: str="METRIC", language_code: str="en", '
					'time: int=10 ) -> Dict[ str, Any ] | None')
			raise exception
	
	def fetch_daily_forecast( self, address: str, days: int=5, units_system: str = 'METRIC',
			language_code: str = 'en', time: int=10 ) -> Dict[ str, Any ] | None:
		'''
			
			Purpose:
			--------
			Retrieve daily weather forecast data for an address or named location.
			
			Parameters:
			-----------
			address (str): Physical address, named place, city, or geocodable location.
			days (int): Number of forecast days to request, clamped to 1 through 10.
			units_system (str): Units system used by the response, usually METRIC or IMPERIAL.
			language_code (str): BCP-47 language code used by the response.
			time (int): Request timeout in seconds.
			
			Returns:
			--------
			Dict[str, Any] | None: Google Weather daily forecast response.
			
		'''
		try:
			lat, lng = self.resolve_coordinates( address )
			self.mode = 'daily_forecast'
			forecast_days = max( 1, min( int( days ), 10 ) )
			self.params = {
					'location.latitude': lat,
					'location.longitude': lng,
					'days': forecast_days,
					'unitsSystem': units_system,
					'languageCode': language_code
			}
			return self.request( path='forecast/days:lookup', params=self.params, time=time )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GoogleWeather'
			exception.method = (
					'fetch_daily_forecast( self, address: str, days: int=5, '
					'units_system: str="METRIC", language_code: str="en", '
					'time: int=10 ) -> Dict[ str, Any ] | None')
			raise exception
	
	def fetch_hourly_history( self, address: str, hours: int=24, units_system: str = 'METRIC',
			language_code: str = 'en', time: int=10 ) -> Dict[ str, Any ] | None:
		'''
			
			Purpose:
			--------
			Retrieve hourly historical weather data for an address or named location.
			
			Parameters:
			-----------
			address (str): Physical address, named place, city, or geocodable location.
			hours (int): Number of historical hours to request, clamped to 1 through 24.
			units_system (str): Units system used by the response, usually METRIC or IMPERIAL.
			language_code (str): BCP-47 language code used by the response.
			time (int): Request timeout in seconds.
			
			Returns:
			--------
			Dict[str, Any] | None: Google Weather hourly history response.
			
		'''
		try:
			lat, lng = self.resolve_coordinates( address )
			self.mode = 'hourly_history'
			history_hours = max( 1, min( int( hours ), 24 ) )
			self.params = {
					'location.latitude': lat,
					'location.longitude': lng,
					'hours': history_hours,
					'unitsSystem': units_system,
					'languageCode': language_code
			}
			return self.request( path='history/hours:lookup', params=self.params, time=time )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GoogleWeather'
			exception.method = (
					'fetch_hourly_history( self, address: str, hours: int=24, '
					'units_system: str="METRIC", language_code: str="en", '
					'time: int=10 ) -> Dict[ str, Any ] | None')
			raise exception
	
	def fetch_alerts( self, address: str, language_code: str = 'en',
			time: int=10 ) -> Dict[ str, Any ] | None:
		'''
			
			Purpose:
			--------
			Retrieve public weather alerts for an address or named location.
			
			Parameters:
			-----------
			address (str): Physical address, named place, city, or geocodable location.
			language_code (str): BCP-47 language code used by the response.
			time (int): Request timeout in seconds.
			
			Returns:
			--------
			Dict[str, Any] | None: Google Weather public alerts response.
			
		'''
		try:
			lat, lng = self.resolve_coordinates( address )
			self.mode = 'alerts'
			self.params = {
					'location.latitude': lat,
					'location.longitude': lng,
					'languageCode': language_code
			}
			return self.request( path='publicAlerts:lookup', params=self.params, time=time )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GoogleWeather'
			exception.method = (
					'fetch_alerts( self, address: str, language_code: str="en", '
					'time: int=10 ) -> Dict[ str, Any ] | None')
			raise exception

class NavalObservatory( Fetcher ):
	'''Fetches celestial-navigation data from the U.S. Naval Observatory API.

		Attributes:
		-----------
		base_url,
		url,
		params,
		date_value,
		time_value,
		latitude,
		longitude,
		location_label,
		agents,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		validate_date(...): Performs the validate_date operation for this fetcher.
		validate_time(...): Performs the validate_time operation for this fetcher.
		validate_coordinates(...): Performs the validate_coordinates operation for this fetcher.
		fetch_celnav(...): Performs the fetch_celnav operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	base_url: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	date_value: Optional[ str ]
	time_value: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	location_label: Optional[ str ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the Naval Observatory fetcher with current API defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.headers = { }
		self.base_url = 'https://aa.usno.navy.mil/api'
		self.url = None
		self.params = { }
		self.date_value = ''
		self.time_value = ''
		self.latitude = 38.9072
		self.longitude = -77.0369
		self.location_label = ''
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [ 'base_url', 'url', 'params', 'date_value', 'time_value', 'latitude', 'longitude', 
		         'location_label', 'fetch_celnav', 'fetch', 'create_schema' ]
	
	def validate_date( self, date_value: str ) -> str:
		'''Validate and normalize a USNO date string.

			Parameters:
			-----------
			date_value (str):
				Date in YYYY-MM-DD format.

			Returns:
			--------
			str
		'''
		try:
			value = str( date_value ).strip( )
			throw_if( 'date_value', value )
			dt.datetime.strptime( value, '%Y-%m-%d' )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NavalObservatory'
			exception.method = 'validate_date( self, date_value: str ) -> str'
			raise exception
	
	def validate_time( self, time_value: str ) -> str:
		'''Validate and normalize a USNO time string.

			Parameters:
			-----------
			time_value (str):
				Time in HH:MM, HH:MM:SS, or HH:MM:SS.S format.

			Returns:
			--------
			str
		'''
		try:
			value = str( time_value ).strip( )
			throw_if( 'time_value', value )
			pattern = ( r'^(?:[01]\d|2[0-3]):[0-5]\d'
					r'(?:'
					r':[0-5]\d(?:\.\d{1,6})?'
					r')?$' )
			
			if not re.fullmatch( pattern, value ):
				raise ValueError( "Invalid time format. Use HH:MM, HH:MM:SS, or HH:MM:SS.S" )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NavalObservatory'
			exception.method = 'validate_time( self, time_value: str ) -> str'
			raise exception
	
	def validate_coordinates( self, latitude: float, longitude: float ) -> tuple[ float, float ]:
		'''Validate latitude and longitude against documented decimal-degree ranges.

			Parameters:
			-----------
			latitude (float):
				Latitude in decimal degrees.

			longitude (float):
				Longitude in decimal degrees.

			Returns:
			--------
			tuple[float, float]
		'''
		try:
			lat = float( latitude )
			lon = float( longitude )
			if lat < -90.0 or lat > 90.0:
				raise ValueError( 'Latitude must be between -90 and 90.' )
			
			if lon < -180.0 or lon > 180.0:
				raise ValueError( 'Longitude must be between -180 and 180.' )
			
			return lat, lon
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NavalObservatory'
			exception.method = 'validate_coordinates( self, *params ) -> tuple[ float, float ]'
			raise exception
	
	def fetch_celnav( self, date_value: str, time_value: str, latitude: float,
			longitude: float, location_label: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch celestial navigation data for an assumed position and time.

			Parameters:
			-----------
			date_value (str):
				Date in YYYY-MM-DD format.

			time_value (str):
				Time in HH:MM, HH:MM:SS, or HH:MM:SS.S format.

			latitude (float):
				Latitude in decimal degrees. North positive.

			longitude (float):
				Longitude in decimal degrees. East positive.

			location_label (str):
				Optional client-side label preserved in the result payload.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
			
		'''
		try:
			self.date_value = self.validate_date( date_value )
			self.time_value = self.validate_time( time_value )
			self.latitude, self.longitude = self.validate_coordinates( latitude=latitude,
				longitude=longitude )
			self.location_label = str( location_label or '' ).strip( )
			self.url = f'{self.base_url}/celnav'
			self.params = { 'date': self.date_value, 'time': self.time_value,
					'coords': f'{self.latitude},{self.longitude}' }
			
			self.response = requests.get( url=self.url, params=self.params,
				headers=self.headers, timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			
			return { 'mode': 'celnav', 'url': self.url, 'params': self.params,
					'location_label': self.location_label, 'data': payload }
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NavalObservatory'
			exception.method = 'fetch_celnav( self, *params ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch( self, mode: str='celnav', date_value: str='',
			time_value: str='', latitude: float=0.0, longitude: float=0.0,
			location_label: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''Unified dispatcher for Naval Observatory requests.

			Parameters:
			-----------
			mode (str):
				Currently supported:
				- celnav

			date_value (str):
				Date in YYYY-MM-DD format.

			time_value (str):
				Time in HH:MM, HH:MM:SS, or HH:MM:SS.S format.

			latitude (float):
				Latitude in decimal degrees.

			longitude (float):
				Longitude in decimal degrees.

			location_label (str):
				Optional display label.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'celnav' ).strip( ).lower( )
			if active_mode == 'celnav':
				return self.fetch_celnav( date_value=date_value, time_value=time_value,
					latitude=latitude, longitude=longitude, location_label=location_label,
					time=time )
			
			raise ValueError( 'Unsupported mode.' )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'NavalObservatory'
			exception.method = 'fetch( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def create_schema( self, function: str, tool: str, description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f'{description.strip( )} '
							f'This function uses the {tool.strip( )} service.'
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NavalObservatory'
			exception.method = 'create_schema( self, *params ) -> Dict[ str, str ]'
			raise exception

class SatelliteCenter( Fetcher ):
	'''Fetches satellite observatory, ground-station, and location data from SSC Web Services.
	
		Attributes:
		-----------
		ssc,
		url,
		params,
		observatories,
		ground_stations,
		timeout,
	
		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		fetch_observatories(...): Performs the fetch_observatories operation for this fetcher.
		fetch_ground_stations(...): Performs the fetch_ground_stations operation for this fetcher.
		fetch_locations(...): Performs the fetch_locations operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
	
	'''
	ssc: Optional[ SscWs ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	observatories: Optional[ List[ Dict[ str, Any ] ] ]
	ground_stations: Optional[ List[ Dict[ str, Any ] ] ]
	timeout: Optional[ int ]
	
	def __init__( self ) -> None:
		super( ).__init__( )
		self.ssc = None
		self.url = 'https://sscweb.gsfc.nasa.gov/WS/sscr/2'
		self.params = { }
		self.observatories = [ ]
		self.ground_stations = [ ]
		self.timeout = 20
		self.headers = { }
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		if 'Accept' not in self.headers:
			self.headers[ 'Accept' ]='application/json'
	
	def __dir__( self ) -> List[ str ]:
		return [ 'url', 'timeout', 'headers', 'fetch_observatories', 'fetch_ground_stations',
				'fetch_locations', 'fetch', ]
	
	def fetch_observatories( self ) -> Dict[ str, Any ] | None:
		"""Get descriptions of the observatories available from SSC.
			
			Returns:
			--------
			Dict[str, Any] | None

		"""
		try:
			self.ssc = SscWs( user_agent=self.agents, timeout=self.timeout )
			result = self.ssc.get_observatories( )
			return result
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'SatelliteCenter'
			exception.method = 'fetch_observatories( self ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_ground_stations( self ) -> Dict[ str, Any ] | None:
		"""Get descriptions of the ground stations available from SSC.

			Returns:
			--------
			Dict[str, Any] | None

		"""
		try:
			self.ssc = SscWs( user_agent=self.agents, timeout=self.timeout )
			result = self.ssc.get_ground_stations( )
			return result
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'SatelliteCenter'
			exception.method = 'fetch_ground_stations( self ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_locations( self, observatories: str, start_time: str, end_time: str,
			coordinate_systems: str='gse', resolution_factor: int=1,
			time: int=20 ) -> Dict[ str, Any ] | None:
		"""Get location data for one or more observatories over a time range using the documented
		SSC REST GET endpoint.

			Parameters:
			-----------
			observatories:
				Comma-separated observatory identifiers such as "iss" or "mms1,mms2".
				
			start_time:
				ISO 8601 UTC start like "2026-03-15T00:00:00Z".
				
			end_time:
				ISO 8601 UTC end like "2026-03-15T02:00:00Z".
				
			coordinate_systems:
				Comma-separated coordinate systems such as "gse", "geo", "gsm".
				
			resolution_factor:
				Return one out of every N values.
				
			time:
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		"""
		try:
			throw_if( 'observatories', observatories )
			throw_if( 'start_time', start_time )
			throw_if( 'end_time', end_time )
			self.timeout = int( time )
			obs = observatories.strip( )
			time_range = f'{start_time.strip( )},{end_time.strip( )}'
			coords = (coordinate_systems or 'gse').strip( )
			request_url = ( f'{self.url}/locations/'
					f'{obs}/'
					f'{time_range}/'
					f'{coords}/' )
			
			self.params = { 'resolutionFactor': max( 1, int( resolution_factor ) ) }
			self.response = requests.get( url=request_url, params=self.params, headers=self.headers,
				timeout=self.timeout )
			
			self.response.raise_for_status( )
			return self.response.json( )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'SatelliteCenter'
			exception.method = 'fetch_locations( self, *params ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch( self, mode: str='observatories', query: str='', start_time: str='', end_time: str='',
			coordinate_systems: str='gse', resolution_factor: int=1, time: int=20 ) -> Dict[ str, Any ] | None:
		"""Unified dispatch method for Satellite Center requests.

			Returns:
			--------
			Dict[str, Any] | None

		"""
		try:
			active_mode = (mode or 'observatories').strip( ).lower( )
			if active_mode == 'observatories':
				return self.fetch_observatories( )
			
			if active_mode == 'ground_stations':
				return self.fetch_ground_stations( )
			
			if active_mode == 'locations':
				return self.fetch_locations( observatories=query, start_time=start_time,
					end_time=end_time, coordinate_systems=coordinate_systems,
					resolution_factor=resolution_factor, time=time )
			
			raise ValueError( "Use 'observatories', 'ground_stations', or 'locations'." )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'SatelliteCenter'
			exception.method = 'fetch( self, *kwargs ) -> Dict[ str, Any ]'
			raise exception

class EarthObservatory( Fetcher ):
	'''

		Purpose:
		--------
		NASA Earth Observatory's Natural Event Tracker (EONET) allows users to access imagery,
		often in near real-time (NRT), of natural events such as dust storms, forest fires, and
		tropical cyclones—empowering people all across the planet to locate, track, and potentially
		prepare for and manage events that affect communities in their paths.
		Version 3 API for events, categories, sources, and layers.

		This class is aligned to the current documented EONET v3 API and supports:
		- events
		- categories
		- sources
		- layers

		Referenced API Requirements:
		----------------------------
		Base:
			https://eonet.gsfc.nasa.gov/api/v3

		Events:
			https://eonet.gsfc.nasa.gov/api/v3/events
			Optional parameters:
				- source
				- category
				- status
				- limit
				- days
				- start
				- end

		Categories:
			https://eonet.gsfc.nasa.gov/api/v3/categories

		Sources:
			https://eonet.gsfc.nasa.gov/api/v3/sources

		Layers:
			https://eonet.gsfc.nasa.gov/api/v3/layers
			Optional category-specific path:
				https://eonet.gsfc.nasa.gov/api/v3/layers/{category}

		Attributes:
		-----------
		base_url: Optional[str]
			Base EONET API URL.

		url: Optional[str]
			Resolved request URL.

		params: Optional[Dict[str, Any]]
			Request parameters.

		mode: Optional[str]
			Selected API mode.

		query: Optional[str]
			Reserved generic query field.

		status: Optional[str]
			Event status filter.

		category: Optional[str]
			Event or layer category filter.

		source: Optional[str]
			Event source filter.

		days: Optional[int]
			Prior-day filter.

		limit: Optional[int]
			Returned record limit.

		start_date: Optional[str]
			Event-range start date in YYYY-MM-DD format.

		end_date: Optional[str]
			Event-range end date in YYYY-MM-DD format.

		agents: Optional[str]
			User-Agent string.

		Methods:
		--------
		__init__() -> None
			Initialize fetcher defaults.

		__dir__() -> List[str]
			Provide ordered member visibility.

		fetch_events(...) -> Dict[str, Any] | None
			Fetch event records.

		fetch_categories() -> Dict[str, Any] | None
			Fetch category metadata.

		fetch_sources() -> Dict[str, Any] | None
			Fetch source metadata.

		fetch_layers(...) -> Dict[str, Any] | None
			Fetch layer metadata, optionally filtered by category.

		fetch(...) -> Dict[str, Any] | None
			Unified dispatcher.

		create_schema(...) -> Dict[str, str] | None
			Construct a dynamic tool schema.

	'''
	base_url: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	mode: Optional[ str ]
	status: Optional[ str ]
	category: Optional[ str ]
	source: Optional[ str ]
	days: Optional[ int ]
	limit: Optional[ int ]
	start_date: Optional[ str ]
	end_date: Optional[ str ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the EONET fetcher with current API defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.headers = { }
		self.base_url = 'https://eonet.gsfc.nasa.gov/api/v3'
		self.url = None
		self.params = { }
		self.mode = 'events'
		self.status = 'open'
		self.category = ''
		self.source = ''
		self.days = 30
		self.limit = 20
		self.start_date = ''
		self.end_date = ''
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'url',
				'params',
				'mode',
				'status',
				'category',
				'source',
				'days',
				'limit',
				'start_date',
				'end_date',
				'fetch_events',
				'fetch_categories',
				'fetch_sources',
				'fetch_layers',
				'fetch',
				'create_schema'
		]
	
	def fetch_events( self, status: str='open', category: str='', source: str='', limit: int=20,
			days: int=30, start_date: str='', end_date: str='', time: int=20 ) -> Dict[ str, Any ]:
		'''Fetch EONET events using documented v3 filters.

			Parameters:
			-----------
			status (str):
				Event status filter. Typical values: open, closed, all.

			category (str):
				Optional category slug or comma-separated category list.

			source (str):
				Optional source id or comma-separated source ids.

			limit (int):
				Maximum number of events to return.

			days (int):
				Number of prior days, including today, from which to return events.

			start_date (str):
				Optional inclusive start date in YYYY-MM-DD format.

			end_date (str):
				Optional inclusive end date in YYYY-MM-DD format.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'events'
			self.status = str( status or 'open' ).strip( ).lower( )
			self.category = str( category or '' ).strip( )
			self.source = str( source or '' ).strip( )
			self.limit = int( limit )
			self.days = int( days )
			self.start_date = str( start_date or '' ).strip( )
			self.end_date = str( end_date or '' ).strip( )
			self.url = f'{self.base_url}/events'
			self.params = { }
			
			if self.status:
				self.params[ 'status' ]=self.status
			
			if self.category:
				self.params[ 'category' ]=self.category
			
			if self.source:
				self.params[ 'source' ]=self.source
			
			if self.limit > 0:
				self.params[ 'limit' ]=self.limit
			
			if self.start_date and self.end_date:
				self.params[ 'start' ]=self.start_date
				self.params[ 'end' ]=self.end_date
			elif self.days > 0:
				self.params[ 'days' ]=self.days
			
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'events': payload.get( 'events', [ ] ),
					'title': payload.get( 'title', '' ),
					'description': payload.get( 'description', '' )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EarthObservatory'
			exception.method = 'fetch_events( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_categories( self, time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch EONET category metadata.

			Parameters:
			-----------
			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'categories'
			self.url = f'{self.base_url}/categories'
			self.params = { }
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'categories': payload.get( 'categories', [ ] ),
					'title': payload.get( 'title', '' ),
					'description': payload.get( 'description', '' )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EarthObservatory'
			exception.method = 'fetch_categories( self, time: int=20 ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_sources( self, time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch EONET source metadata.

			Parameters:
			-----------
			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'sources'
			self.url = f'{self.base_url}/sources'
			self.params = { }
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'sources': payload.get( 'sources', [ ] ),
					'title': payload.get( 'title', '' ),
					'description': payload.get( 'description', '' )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EarthObservatory'
			exception.method = 'fetch_sources( self, time: int=20 ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_layers( self, category: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch EONET layer metadata, optionally scoped to a category.

			Parameters:
			-----------
			category (str):
				Optional category slug.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'layers'
			self.category = str( category or '' ).strip( )
			if self.category:
				self.url = f'{self.base_url}/layers/{self.category}'
			else:
				self.url = f'{self.base_url}/layers'
			
			self.params = { }
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'category': self.category,
					'layers': payload.get( 'layers', [ ] ),
					'title': payload.get( 'title', '' ),
					'description': payload.get( 'description', '' )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EarthObservatory'
			exception.method = 'fetch_layers( self, c**kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch( self, mode: str='events', status: str='open', category: str='', source: str='', limit: int=20,
			days: int=30, start_date: str='', end_date: str='', time: int=20 ) -> Dict[ str, Any ]:
		'''Unified dispatcher for EONET v3 operations.

			Parameters:
			-----------
			mode (str):
				One of: events, categories, sources, layers

			status (str):
				Event status filter for events mode.

			category (str):
				Category filter for events mode or category path for layers mode.

			source (str):
				Source filter for events mode.

			limit (int):
				Event record limit for events mode.

			days (int):
				Prior-day window for events mode.

			start_date (str):
				Optional start date in YYYY-MM-DD format.

			end_date (str):
				Optional end date in YYYY-MM-DD format.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = (mode or 'events').strip( ).lower( )
			if active_mode == 'events':
				return self.fetch_events( status=status, category=category, source=source,
					limit=limit, days=days, start_date=start_date, end_date=end_date, time=time )
			
			if active_mode == 'categories':
				return self.fetch_categories( time=time )
			
			if active_mode == 'sources':
				return self.fetch_sources( time=time )
			
			if active_mode == 'layers':
				return self.fetch_layers( category=category, time=time )
			
			raise ValueError( "Use 'events', 'categories', 'sources', or 'layers'." )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'EarthObservatory'
			exception.method = 'fetch( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': f'{description.strip( )} This function uses the {tool.strip( )} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EarthObservatory'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class GlobalImagery( Fetcher ):
	'''
		Purpose:
		--------
		Fetches NASA Global Imagery Browse Services (GIBS) WMS imagery and service
		metadata.

		Attributes:
		-----------
		file_path,
		api_key,
		url,
		latitude,
		longitude,
		coordinates,
		calendar_date,
		julian_date,
		sidereal_time,
		utc_time,
		local_time,
		params,
		era,
		year,
		month,
		day,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		get_capabilities_url(...): Performs the get_capabilities_url operation.
		build_wms_url(...): Performs the build_wms_url operation.
		fetch_wms_map(...): Performs the fetch_wms_map operation.
		fetch_map_services(...): Performs the fetch_map_services operation.
		fetch_mercator_map(...): Performs the fetch_mercator_map operation.
		create_schema(...): Performs the create_schema operation.

	'''
	file_path: Optional[ str ]
	api_key: Optional[ str ]
	url: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	coordinates: Optional[ Tuple[ float, float ] ]
	calendar_date: Optional[ dt.datetime ]
	julian_date: Optional[ float ]
	sidereal_time: Optional[ str ]
	utc_time: Optional[ dt.time ]
	local_time: Optional[ dt.time ]
	params: Optional[ Dict[ str, Any ] ]
	era: Optional[ str ]
	year: Optional[ str ]
	month: Optional[ str ]
	day: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the NASA GIBS imagery wrapper with request defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.api_key = cfg.NASA_API_KEY
		self.mode = None
		self.url = 'https://gibs.earthdata.nasa.gov/wms'
		self.file_path = None
		self.longitude = None
		self.latitude = None
		self.coordinates = None
		self.fetcher = None
		self.calendar_date = None
		self.julian_date = None
		self.sidereal_time = None
		self.local_time = None
		self.utc_time = None
		self.params = { }
		self.response = None
		self.result = None
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = { }
		self.headers[ 'User-Agent' ] = self.agents
		self.era = None
		self.year = None
		self.month = None
		self.day = None
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Return stable introspection names for the NASA GIBS wrapper.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]: Ordered attribute and method names.
		'''
		return [
				'file_path',
				'api_key',
				'url',
				'latitude',
				'longitude',
				'coordinates',
				'calendar_date',
				'julian_date',
				'sidereal_time',
				'utc_time',
				'local_time',
				'params',
				'response',
				'result',
				'mode',
				'timeout',
				'headers',
				'get_capabilities_url',
				'build_wms_url',
				'fetch_wms_map',
				'fetch_map_services',
				'fetch_mercator_map',
				'create_schema'
		]
	
	def get_capabilities_url( self, projection: str = 'epsg4326',
			quality: str = 'best', version: str = '1.1.1' ) -> str:
		'''
			Purpose:
			--------
			Build a NASA GIBS WMS GetCapabilities URL.

			Parameters:
			-----------
			projection (str):
				GIBS projection path segment such as epsg4326 or epsg3857.

			quality (str):
				GIBS quality path segment such as best or std.

			version (str):
				WMS version.

			Returns:
			--------
			str: GetCapabilities URL.
		'''
		try:
			projection_value = str( projection or 'epsg4326' ).strip( ).lower( )
			quality_value = str( quality or 'best' ).strip( ).lower( )
			version_value = str( version or '1.1.1' ).strip( )
			
			base_url = (
					f'https://gibs.earthdata.nasa.gov/wms/'
					f'{projection_value}/{quality_value}/wms.cgi'
			)
			
			params = {
					'SERVICE': 'WMS',
					'REQUEST': 'GetCapabilities',
					'VERSION': version_value
			}
			
			return f'{base_url}?{urllib.parse.urlencode( params )}'
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalImagery'
			exception.method = (
					'get_capabilities_url( self, projection: str="epsg4326", '
					'quality: str="best", version: str="1.1.1" ) -> str'
			)
			raise exception
	
	def build_wms_url( self, layer: str, image_date: str, bbox: Tuple[ float, float, float, float ],
			width: int = 1200, height: int = 600, projection: str = 'epsg4326',
			quality: str = 'best', image_format: str = 'image/png',
			transparent: bool = True, version: str = '1.1.1' ) -> str:
		'''
			Purpose:
			--------
			Build a NASA GIBS WMS GetMap URL.

			Parameters:
			-----------
			layer (str):
				GIBS layer identifier.

			image_date (str):
				Layer date in YYYY-MM-DD format.

			bbox (Tuple[float, float, float, float]):
				Bounding box as west, south, east, north.

			width (int):
				Output image width in pixels.

			height (int):
				Output image height in pixels.

			projection (str):
				GIBS projection path segment such as epsg4326 or epsg3857.

			quality (str):
				GIBS quality path segment such as best or std.

			image_format (str):
				Output MIME type.

			transparent (bool):
				Whether to request transparent no-data pixels.

			version (str):
				WMS version.

			Returns:
			--------
			str: Fully-qualified WMS GetMap URL.
		'''
		try:
			throw_if( 'layer', layer )
			throw_if( 'image_date', image_date )
			throw_if( 'bbox', bbox )
			
			if len( bbox ) != 4:
				raise ValueError( 'bbox must contain west, south, east, north.' )
			
			projection_value = str( projection or 'epsg4326' ).strip( ).lower( )
			quality_value = str( quality or 'best' ).strip( ).lower( )
			version_value = str( version or '1.1.1' ).strip( )
			
			west, south, east, north = [ float( value ) for value in bbox ]
			width_value = max( 1, int( width ) )
			height_value = max( 1, int( height ) )
			
			base_url = (
					f'https://gibs.earthdata.nasa.gov/wms/'
					f'{projection_value}/{quality_value}/wms.cgi'
			)
			
			params = {
					'SERVICE': 'WMS',
					'VERSION': version_value,
					'REQUEST': 'GetMap',
					'LAYERS': str( layer ).strip( ),
					'STYLES': '',
					'FORMAT': str( image_format or 'image/png' ).strip( ),
					'TRANSPARENT': str( bool( transparent ) ).lower( ),
					'SRS': 'EPSG:4326' if projection_value == 'epsg4326' else 'EPSG:3857',
					'BBOX': f'{west},{south},{east},{north}',
					'WIDTH': width_value,
					'HEIGHT': height_value,
					'TIME': str( image_date ).strip( )
			}
			
			self.params = params
			return f'{base_url}?{urllib.parse.urlencode( params )}'
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalImagery'
			exception.method = (
					'build_wms_url( self, layer: str, image_date: str, '
					'bbox: Tuple[ float, float, float, float ], width: int=1200, '
					'height: int=600, projection: str="epsg4326", quality: str="best", '
					'image_format: str="image/png", transparent: bool=True, '
					'version: str="1.1.1" ) -> str'
			)
			raise exception
	
	def fetch_wms_map( self, layer: str, image_date: str,
			bbox: Tuple[ float, float, float, float ], width: int = 1200, height: int = 600,
			projection: str = 'epsg4326', quality: str = 'best',
			image_format: str = 'image/png', transparent: bool = True,
			output_dir: str = 'python-examples', output_name: str = '',
			time: int = 20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch a NASA GIBS WMS map image and save it to disk.

			Parameters:
			-----------
			layer (str):
				GIBS layer identifier.

			image_date (str):
				Layer date in YYYY-MM-DD format.

			bbox (Tuple[float, float, float, float]):
				Bounding box as west, south, east, north.

			width (int):
				Output image width in pixels.

			height (int):
				Output image height in pixels.

			projection (str):
				GIBS projection path segment.

			quality (str):
				GIBS quality path segment.

			image_format (str):
				Output MIME type.

			transparent (bool):
				Whether to request transparent no-data pixels.

			output_dir (str):
				Directory where the image will be written.

			output_name (str):
				Optional output filename. If empty, a deterministic filename is generated.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None: Normalized request and image metadata.
		'''
		try:
			self.mode = 'wms_map'
			self.timeout = int( time )
			
			request_url = self.build_wms_url(
				layer=layer,
				image_date=image_date,
				bbox=bbox,
				width=width,
				height=height,
				projection=projection,
				quality=quality,
				image_format=image_format,
				transparent=transparent )
			
			directory = Path( output_dir or 'python-examples' )
			directory.mkdir( parents=True, exist_ok=True )
			
			if output_name:
				filename = output_name
			else:
				safe_layer = re.sub( r'[^A-Za-z0-9_\-]+', '_', str( layer ).strip( ) )
				safe_date = re.sub( r'[^0-9\-]+', '_', str( image_date ).strip( ) )
				extension = '.jpg' if image_format == 'image/jpeg' else '.png'
				filename = f'{safe_layer}_{safe_date}{extension}'
			
			self.file_path = str( directory / filename )
			self.url = request_url
			self.response = requests.get( request_url, headers=self.headers,
				timeout=self.timeout )
			self.response.raise_for_status( )
			
			content_type = self.response.headers.get( 'Content-Type', '' )
			if 'image' not in content_type.lower( ):
				message = (
						'NASA GIBS did not return an image. '
						f'Content-Type: {content_type}. '
						f'Response preview: {self.response.text[ :500 ]}'
				)
				raise ValueError( message )
			
			Path( self.file_path ).write_bytes( self.response.content )
			
			self.result = {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'image_path': self.file_path,
					'content_type': content_type,
					'status_code': self.response.status_code,
					'bytes': len( self.response.content ),
					'layer': layer,
					'image_date': image_date,
					'bbox': {
							'west': float( bbox[ 0 ] ),
							'south': float( bbox[ 1 ] ),
							'east': float( bbox[ 2 ] ),
							'north': float( bbox[ 3 ] )
					},
					'summary': {
							'rows': 1,
							'columns': 8,
							'description': 'NASA GIBS WMS image written to disk.'
					}
			}
			
			return self.result
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalImagery'
			exception.method = (
					'fetch_wms_map( self, layer: str, image_date: str, '
					'bbox: Tuple[ float, float, float, float ], width: int=1200, '
					'height: int=600, projection: str="epsg4326", quality: str="best", '
					'image_format: str="image/png", transparent: bool=True, '
					'output_dir: str="python-examples", output_name: str="", '
					'time: int=20 ) -> Dict[ str, Any ] | None'
			)
			raise exception
	
	def fetch_map_services( self ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the legacy default NASA GIBS EPSG:4326 corrected-reflectance image.

			Parameters:
			-----------
			None

			Returns:
			--------
			Dict[str, Any] | None: Normalized request and image metadata.
		'''
		try:
			self.mode = 'fetch_map_services'
			return self.fetch_wms_map( layer='MODIS_Terra_CorrectedReflectance_TrueColor',
				image_date='2021-09-21', bbox=(-180.0, -90.0, 180.0, 90.0),
				width=1200, height=600, projection='epsg4326', quality='best',
				image_format='image/png', transparent=True, output_dir='python-examples',
				output_name='MODIS_Terra_CorrectedReflectance_TrueColor.png',
				time=20 )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalImagery'
			exception.method = 'fetch_map_services( self ) -> Dict[ str, Any ] | None'
			raise exception
	
	def fetch_mercator_map( self, ccrs=None ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the legacy default NASA GIBS EPSG:3857 Web Mercator image.

			Parameters:
			-----------
			ccrs (Any | None):
				Preserved for backward compatibility. The replacement fetches and writes the
				image without attempting Cartopy rendering.

			Returns:
			--------
			Dict[str, Any] | None: Normalized request and image metadata.
		'''
		try:
			self.mode = 'mercator_map'
			return self.fetch_wms_map(
				layer='Landsat_WELD_CorrectedReflectance_Bands157_Global_Annual',
				image_date='2000-12-01', bbox=(-8000000.0, -8000000.0, 8000000.0, 8000000.0),
				width=600, height=600, projection='epsg3857', quality='best',
				image_format='image/png', transparent=True, output_dir='python-examples',
				output_name='Landsat_WELD_CorrectedReflectance_Bands157_Global_Annual.png',
				time=20 )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalImagery'
			exception.method = 'fetch_mercator_map( self, ccrs=None ) -> Dict[ str, Any ] | None'
			raise exception
	
	def create_schema( self, function: str, tool: str, description: str,
			parameters: dict, required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a dynamic tool schema definition.

			Parameters:
			-----------
			function (str):
				Function name exposed to the model.

			tool (str):
				Underlying service or system name.

			description (str):
				Description of the exposed function.

			parameters (dict):
				JSON-schema-style parameter definitions.

			required (list[str]):
				Required parameter names.

			Returns:
			--------
			Dict[str, str] | None: JSON-compatible tool schema dictionary.
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError( 'parameters must be a dict of parameter schema definitions.' )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': f'{description.strip( )} This function uses the {tool.strip( )} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalImagery'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ] | None'
			)
			raise exception
		
class NearbyObjects( Fetcher ):
	'''Provides access to current JPL SSD / CNEOS APIs relevant to near-Earth
		objects, close approaches, and human-accessible target screening.

		This class is aligned to the current documented APIs and supports the
		following modes:

		- close_approaches
		- object_lookup
		- nhats_summary
		- nhats_object
		- fireballs

		Referenced API Requirements:
		----------------------------
		CAD API:
			GET https://ssd-api.jpl.nasa.gov/cad.api
			Common parameters used here:
				- date-min
				- date-max
				- dist-max
				- body
				- sort
				- limit

		SBDB API:
			GET https://ssd-api.jpl.nasa.gov/sbdb.api
			One and only one of:
				- sstr
				- spk
				- des
			Optional parameters used here:
				- phys-par
				- ca-data
				- ca-body
				- discovery

		NHATS API:
			GET https://ssd-api.jpl.nasa.gov/nhats.api
			Summary filters optionally include:
				- dv
				- dur
				- stay
				- launch
				- h
				- occ
			Object-specific details use:
				- des

		Fireball API:
			GET https://ssd-api.jpl.nasa.gov/fireball.api
			Common parameters used here:
				- date-min
				- limit

		Attributes:
		-----------
		base_url: Optional[str]
			Base SSD API URL.

		url: Optional[str]
			Resolved request URL.

		params: Optional[Dict[str, Any]]
			Request parameters for the active call.

		mode: Optional[str]
			Selected operating mode.

		start_date: Optional[str]
			Inclusive start date in YYYY-MM-DD format.

		end_date: Optional[str]
			Inclusive end date in YYYY-MM-DD format.

		query: Optional[str]
			Generic object lookup string or designation.

		dist_max: Optional[str]
			Close-approach maximum distance filter.

		body: Optional[str]
			Close-approach body selector, typically Earth.

		sort: Optional[str]
			CAD sorting key.

		limit: Optional[int]
			Result limit.

		agents: Optional[str]
			User-Agent string.

		Methods:
		--------
		__init__() -> None
			Initialize fetcher defaults.

		__dir__() -> List[str]
			Provide ordered member visibility.

		fetch_close_approaches(...) -> Dict[str, Any] | None
			Fetch close-approach records from the CAD API.

		fetch_object_lookup(...) -> Dict[str, Any] | None
			Fetch detailed object information from the SBDB API.

		fetch_nhats_summary(...) -> Dict[str, Any] | None
			Fetch NHATS summary rows using screening constraints.

		fetch_nhats_object(...) -> Dict[str, Any] | None
			Fetch NHATS details for a single designation.

		fetch_fireballs(...) -> Dict[str, Any] | None
			Fetch fireball atmospheric impact records.

		fetch(...) -> Dict[str, Any] | None
			Unified dispatcher for NEO-related operations.

		create_schema(...) -> Dict[str, str] | None
			Construct a dynamic tool schema.

	'''
	base_url: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	mode: Optional[ str ]
	start_date: Optional[ str ]
	end_date: Optional[ str ]
	query: Optional[ str ]
	dist_max: Optional[ str ]
	body: Optional[ str ]
	sort: Optional[ str ]
	limit: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the NearbyObjects fetcher with current JPL SSD defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.headers = { }
		self.base_url = 'https://ssd-api.jpl.nasa.gov'
		self.url = None
		self.params = { }
		self.mode = 'close_approaches'
		self.start_date = ''
		self.end_date = ''
		self.query = ''
		self.dist_max = '10LD'
		self.body = 'Earth'
		self.sort = 'date'
		self.limit = 20
		self.agents = cfg.AGENTS
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'url',
				'params',
				'mode',
				'start_date',
				'end_date',
				'query',
				'dist_max',
				'body',
				'sort',
				'limit',
				'fetch_close_approaches',
				'fetch_object_lookup',
				'fetch_nhats_summary',
				'fetch_nhats_object',
				'fetch_fireballs',
				'fetch',
				'create_schema'
		]
	
	def fetch_close_approaches( self, start_date: str, end_date: str, dist_max: str='10LD',
			body: str='Earth', sort: str='date', limit: int=20, time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch close-approach data from the JPL SB Close Approach Data API.

			Parameters:
			-----------
			start_date (str):
				Inclusive lower date bound in YYYY-MM-DD format.

			end_date (str):
				Inclusive upper date bound in YYYY-MM-DD format.

			dist_max (str):
				Maximum close-approach distance. Examples:
				- 10LD
				- 0.05AU

			body (str):
				Close-approach body selector. Example values include Earth, Moon,
				Mars, Juptr.

			sort (str):
				Sort key for the returned records. Example values include date and dist.

			limit (int):
				Maximum number of rows to return.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'start_date', start_date )
			throw_if( 'end_date', end_date )
			self.mode = 'close_approaches'
			self.start_date = str( start_date ).strip( )
			self.end_date = str( end_date ).strip( )
			self.dist_max = str( dist_max or '10LD' ).strip( )
			self.body = str( body or 'Earth' ).strip( )
			self.sort = str( sort or 'date' ).strip( )
			self.limit = int( limit )
			self.url = f'{self.base_url}/cad.api'
			self.params = {
					'date-min': self.start_date,
					'date-max': self.end_date,
					'dist-max': self.dist_max,
					'body': self.body,
					'sort': self.sort,
					'limit': self.limit
			}
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'count': payload.get( 'count', 0 ),
					'fields': payload.get( 'fields', [ ] ),
					'data': payload.get( 'data', [ ] ),
					'signature': payload.get( 'signature', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NearbyObjects'
			exception.method = 'fetch_close_approaches( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_object_lookup( self, query: str, query_type: str='sstr',
			include_physical: bool=True, include_close_approaches: bool=True,
			ca_body: str='Earth', include_discovery: bool=True,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch a single-object record from the JPL SBDB API.

			Parameters:
			-----------
			query (str):
				Object identifier or name. Examples:
				- Apophis
				- Eros
				- 2000 SG344
				- 99942

			query_type (str):
				Exactly one of:
				- sstr
				- spk
				- des

			include_physical (bool):
				If True, request physical parameters.

			include_close_approaches (bool):
				If True, request close-approach data.

			ca_body (str):
				Body filter for close-approach data, typically Earth.

			include_discovery (bool):
				If True, request discovery circumstances when available.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'query', query )
			throw_if( 'query_type', query_type )
			self.mode = 'object_lookup'
			self.query = str( query ).strip( )
			active_type = str( query_type ).strip( ).lower( )
			if active_type not in [ 'sstr', 'spk', 'des' ]:
				raise ValueError( "query_type must be 'sstr', 'spk', or 'des'." )
			
			self.url = f'{self.base_url}/sbdb.api'
			self.params = {
					active_type: self.query,
					'phys-par': '1' if bool( include_physical ) else '0',
					'ca-data': '1' if bool( include_close_approaches ) else '0',
					'discovery': '1' if bool( include_discovery ) else '0'
			}
			
			if include_close_approaches and str( ca_body or '' ).strip( ):
				self.params[ 'ca-body' ]=str( ca_body ).strip( )
			
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NearbyObjects'
			exception.method = 'fetch_object_lookup( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_nhats_summary( self, dv: float=6.0, dur: int=360, stay: int=8, launch: str='2020-2045',
			h: float=26.0, occ: int=7, time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch NHATS summary data using standard screening constraints.

			Parameters:
			-----------
			dv (float):
				Maximum total delta-V in km/s.

			dur (int):
				Maximum mission duration in days.

			stay (int):
				Minimum stay duration in days.

			launch (str):
				Launch window year range. Example: 2020-2045.

			h (float):
				Maximum H magnitude.

			occ (int):
				Maximum Orbit Condition Code.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'nhats_summary'
			self.url = f'{self.base_url}/nhats.api'
			self.params = {
					'dv': float( dv ),
					'dur': int( dur ),
					'stay': int( stay ),
					'launch': str( launch ).strip( ),
					'h': float( h ),
					'occ': int( occ )
			}
			
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NearbyObjects'
			exception.method = 'fetch_nhats_summary( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_nhats_object( self, designation: str, dv: float=6.0, dur: int=360, stay: int=8,
			launch: str='2020-2045', time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch NHATS details for a single object designation.

			Parameters:
			-----------
			designation (str):
				Designation of the NEO. Examples:
				- 99942
				- 2000 SG344

			dv (float):
				Maximum total delta-V in km/s.

			dur (int):
				Maximum mission duration in days.

			stay (int):
				Minimum stay duration in days.

			launch (str):
				Launch window year range.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'designation', designation )
			self.mode = 'nhats_object'
			self.query = str( designation ).strip( )
			self.url = f'{self.base_url}/nhats.api'
			self.params = {
					'des': self.query,
					'dv': float( dv ),
					'dur': int( dur ),
					'stay': int( stay ),
					'launch': str( launch ).strip( )
			}
			
			self.response = requests.get( url=self.url, params=self.params,
				headers=self.headers, timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NearbyObjects'
			exception.method = 'fetch_nhats_object( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_fireballs( self, date_min: str='', limit: int=20, time: int=20 ) -> Dict[ str, Any ] | None:
		'''Fetch atmospheric fireball records from the JPL Fireball API.

			Parameters:
			-----------
			date_min (str):
				Optional lower date bound in YYYY-MM-DD or
				YYYY-MM-DDThh:mm:ss format.

			limit (int):
				Maximum number of rows to return.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'fireballs'
			self.url = f'{self.base_url}/fireball.api'
			self.params = { 'limit': int( limit ) }
			
			if str( date_min or '' ).strip( ):
				self.params[ 'date-min' ]=str( date_min ).strip( )
			
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'count': payload.get( 'count', 0 ),
					'fields': payload.get( 'fields', [ ] ),
					'data': payload.get( 'data', [ ] ),
					'signature': payload.get( 'signature', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NearbyObjects'
			exception.method = 'fetch_fireballs( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch( self, mode: str='close_approaches', start_date: str='',
			end_date: str='', query: str='', query_type: str='sstr',
			dist_max: str='10LD', body: str='Earth', sort: str='date',
			limit: int=20, dv: float=6.0, dur: int=360,
			stay: int=8, launch: str='2020-2045', h: float=26.0,
			occ: int=7, include_physical: bool=True,
			include_close_approaches: bool=True, ca_body: str='Earth',
			include_discovery: bool=True, time: int=20 ) -> Dict[ str, Any ] | None:
		'''Unified dispatcher for JPL SSD / CNEOS NEO-related endpoints.

			Parameters:
			-----------
			mode (str):
				One of:
				- close_approaches
				- object_lookup
				- nhats_summary
				- nhats_object
				- fireballs

			start_date (str):
				Date lower bound for close_approaches.

			end_date (str):
				Date upper bound for close_approaches.

			query (str):
				Object query or designation for object_lookup or nhats_object.

			query_type (str):
				Object lookup selector: sstr, spk, or des.

			dist_max (str):
				Close-approach distance ceiling.

			body (str):
				Close-approach body selector.

			sort (str):
				Close-approach sort key.

			limit (int):
				Result limit.

			dv (float):
				NHATS delta-V filter.

			dur (int):
				NHATS duration filter.

			stay (int):
				NHATS stay filter.

			launch (str):
				NHATS launch window.

			h (float):
				NHATS H-magnitude filter.

			occ (int):
				NHATS OCC filter.

			include_physical (bool):
				SBDB physical-parameter switch.

			include_close_approaches (bool):
				SBDB close-approach section switch.

			ca_body (str):
				SBDB close-approach body filter.

			include_discovery (bool):
				SBDB discovery-data switch.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'close_approaches' ).strip( ).lower( )
			
			if active_mode == 'close_approaches':
				return self.fetch_close_approaches( start_date=start_date, end_date=end_date,
					dist_max=dist_max, body=body, sort=sort, limit=limit,
					time=time )
			
			if active_mode == 'object_lookup':
				return self.fetch_object_lookup( query=query, query_type=query_type,
					include_physical=include_physical,
					include_close_approaches=include_close_approaches, ca_body=ca_body,
					include_discovery=include_discovery, time=time )
			
			if active_mode == 'nhats_summary':
				return self.fetch_nhats_summary( dv=dv, dur=dur, stay=stay, launch=launch,
					h=h, occ=occ, time=time )
			
			if active_mode == 'nhats_object':
				return self.fetch_nhats_object( designation=query, dv=dv, dur=dur, stay=stay,
					launch=launch, time=time )
			
			if active_mode == 'fireballs':
				return self.fetch_fireballs( date_min=start_date, limit=limit,
					time=time )
			
			raise ValueError( "Unsupported mode." )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'NearbyObjects'
			exception.method = 'fetch( self, **kwargs) -> Dict[ str, Any ]'
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': f'{description.strip( )} This function uses the {tool.strip( )} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'NearbyObjects'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class OpenScience( Fetcher ):
	'''

		Purpose:
		--------
		Fetches open-science dataset, metadata, assay, and data resources.

		Attributes:
		-----------
		base_url,
		url,
		params,
		query_text,
		format_value,
		size,
		endpoint,
		agents,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_validate_format(...): Performs the _validate_format operation for this fetcher.
		_coerce_response(...): Performs the _coerce_response operation for this fetcher.
		fetch_dataset(...): Performs the fetch_dataset operation for this fetcher.
		fetch_metadata(...): Performs the fetch_metadata operation for this fetcher.
		fetch_assays(...): Performs the fetch_assays operation for this fetcher.
		fetch_data(...): Performs the fetch_data operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	base_url: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	query_text: Optional[ str ]
	format_value: Optional[ str ]
	size: Optional[ int ]
	endpoint: Optional[ str ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the OpenScience fetcher with current OSDR defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.headers = { }
		self.base_url = 'https://visualization.osdr.nasa.gov/biodata/api'
		self.url = None
		self.params = { }
		self.query_text = ''
		self.format_value = 'json'
		self.size = 100
		self.endpoint = ''
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'url',
				'params',
				'query_text',
				'format_value',
				'size',
				'endpoint',
				'fetch_dataset',
				'fetch_metadata',
				'fetch_assays',
				'fetch_data',
				'fetch',
				'create_schema'
		]
	
	def _validate_format( self, format_value: str ) -> str:
		'''
			Purpose:
			--------
			Validate output format for OSDR query endpoints.

			Parameters:
			-----------
			format_value (str):
				Desired format.

			Returns:
			--------
			str
		'''
		try:
			value = str( format_value or 'json' ).strip( ).lower( )
			
			allowed = { 'json', 'csv', 'tsv', 'browser' }
			if value not in allowed:
				raise ValueError(
					"Unsupported format. Use one of: json, csv, tsv, browser."
				)
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenScience'
			exception.method = '_validate_format( self, format_value: str ) -> str'
			raise exception
	
	def _coerce_response( self, response: requests.Response ) -> Dict[ str, Any ] | str:
		'''Convert an HTTP response into JSON when possible, otherwise text.

			Parameters:
			-----------
			response (requests.Response):
				HTTP response object.

			Returns:
			--------
			Dict[str, Any] | str
		'''
		try:
			content_type = str( response.headers.get( 'Content-Type', '' ) ).lower( )
			
			if 'application/json' in content_type:
				return response.json( )
			
			try:
				return response.json( )
			except Exception:
				return response.text
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenScience'
			exception.method = (
					'_coerce_response( self, response: requests.Response ) '
					'-> Dict[ str, Any ] | str'
			)
			raise exception
	
	def fetch_dataset( self, accession: str, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch dataset-level metadata by OSDR accession.

			Parameters:
			-----------
			accession (str):
				OSDR accession such as OSD-48.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'accession', accession )
			value = str( accession ).strip( )
			self.endpoint = f'/v2/dataset/{value}/'
			self.url = f'{self.base_url}{self.endpoint}'
			self.params = { }
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			return {
					'mode': 'dataset',
					'url': self.url,
					'params': self.params,
					'data': self._coerce_response( self.response )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenScience'
			exception.method = 'fetch_dataset( self, **kwargs ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_metadata( self, query: str, format_value: str='json',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Query OSDR sample-level metadata using the current metadata query endpoint.

			Parameters:
			-----------
			query (str):
				Query string to pass through to the endpoint.

			format_value (str):
				Output format. Supports json, csv, tsv, browser.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'query', query )
			self.query_text = str( query ).strip( )
			self.format_value = self._validate_format( format_value )
			self.endpoint = '/v2/query/metadata/'
			self.url = f'{self.base_url}{self.endpoint}'
			self.params = {
					'query': self.query_text,
					'format': self.format_value
			}
			
			self.response = requests.get( url=self.url, params=self.params,
				headers=self.headers, timeout=int( time ) )
			self.response.raise_for_status( )
			
			return {
					'mode': 'metadata',
					'url': self.url,
					'params': self.params,
					'data': self._coerce_response( self.response )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenScience'
			exception.method = (
					'fetch_metadata( self, query: str, format_value: str=json, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_assays( self, query: str, format_value: str='json',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Query OSDR assay-grouped metadata using the current assays query endpoint.

			Parameters:
			-----------
			query (str):
				Query string to pass through to the endpoint.

			format_value (str):
				Output format. Supports json, csv, tsv, browser.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'query', query )
			
			self.query_text = str( query ).strip( )
			self.format_value = self._validate_format( format_value )
			self.endpoint = '/v2/query/assays/'
			self.url = f'{self.base_url}{self.endpoint}'
			self.params = {
					'query': self.query_text,
					'format': self.format_value
			}
			
			self.response = requests.get( url=self.url, params=self.params, headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			return {
					'mode': 'assays',
					'url': self.url,
					'params': self.params,
					'data': self._coerce_response( self.response )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenScience'
			exception.method = (
					'fetch_assays( self, query: str, format_value: str=json, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_data( self, query: str, format_value: str='json',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Query OSDR data using the current data query endpoint.

			Parameters:
			-----------
			query (str):
				Query string to pass through to the endpoint.

			format_value (str):
				Output format. Supports json, csv, tsv, browser.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'query', query )
			
			self.query_text = str( query ).strip( )
			self.format_value = self._validate_format( format_value )
			self.endpoint = '/v2/query/data/'
			self.url = f'{self.base_url}{self.endpoint}'
			self.params = {
					'query': self.query_text,
					'format': self.format_value
			}
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'data',
					'url': self.url,
					'params': self.params,
					'data': self._coerce_response( self.response )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenScience'
			exception.method = (
					'fetch_data( self, query: str, format_value: str=json, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='dataset', query: str='',
			accession: str='', format_value: str='json',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for Open Science requests.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- dataset
				- metadata
				- assays
				- data

			query (str):
				Query expression for metadata, assays, or data modes.

			accession (str):
				OSDR dataset accession for dataset mode.

			format_value (str):
				Output format for query modes.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'dataset' ).strip( ).lower( )
			
			if active_mode == 'dataset':
				return self.fetch_dataset(
					accession=accession,
					time=time
				)
			
			if active_mode == 'metadata':
				return self.fetch_metadata(
					query=query,
					format_value=format_value,
					time=time
				)
			
			if active_mode == 'assays':
				return self.fetch_assays(
					query=query,
					format_value=format_value,
					time=time
				)
			
			if active_mode == 'data':
				return self.fetch_data(
					query=query,
					format_value=format_value,
					time=time
				)
			
			raise ValueError(
				"Unsupported mode. Use one of: dataset, metadata, assays, data."
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'OpenScience'
			exception.method = (
					'fetch( self, mode: str=dataset, query: str=, accession: str=, '
					'format_value: str=json, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f'{description.strip( )} '
							f'This function uses the {tool.strip( )} service.'
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenScience'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class SpaceWeather( Fetcher ):
	'''

		Purpose:
		--------
		Provides access to NASA DONKI space weather endpoints through the
		NASA Open APIs gateway.

		This class is aligned to the currently documented DONKI endpoints and
		supports the following modes:

		- cme
		- cme_analysis
		- gst
		- ips
		- flr
		- sep
		- mpc
		- rbe
		- hss
		- wsa_enlil
		- notifications

		Referenced API Requirements:
		----------------------------
		Base:
			https://api.nasa.gov/DONKI

		Common parameters:
			- startDate
			- endDate
			- api_key

		Endpoint-specific parameters supported here:
			- location
			- catalog
			- type
			- mostAccurateOnly
			- completeEntryOnly
			- speed
			- halfAngle
			- keyword

		Attributes:
		-----------
		base_url: Optional[str]
			Base DONKI API URL.

		api_key: Optional[str]
			NASA API key from configuration.

		url: Optional[str]
			Resolved endpoint URL.

		params: Optional[Dict[str, Any]]
			Request parameters sent to DONKI.

		mode: Optional[str]
			Selected DONKI endpoint mode.

		start_date: Optional[str]
			Inclusive start date in YYYY-MM-DD format.

		end_date: Optional[str]
			Inclusive end date in YYYY-MM-DD format.

		location: Optional[str]
			IPS endpoint location filter.

		catalog: Optional[str]
			CMEAnalysis or IPS catalog filter.

		notification_type: Optional[str]
			Notifications endpoint event type filter.

		limit_note: Optional[str]
			Reserved descriptive note.

		agents: Optional[str]
			User-Agent string.

		Methods:
		--------
		__init__() -> None
			Initialize fetcher defaults.

		__dir__() -> List[str]
			Provide ordered member visibility.

		fetch_endpoint(...) -> Dict[str, Any] | None
			Fetch a single DONKI endpoint with normalized parameters.

		fetch(...) -> Dict[str, Any] | None
			Unified dispatcher for DONKI modes.

		create_schema(...) -> Dict[str, str] | None
			Construct a dynamic tool schema.

	'''
	base_url: Optional[ str ]
	api_key: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	mode: Optional[ str ]
	start_date: Optional[ str ]
	end_date: Optional[ str ]
	location: Optional[ str ]
	catalog: Optional[ str ]
	notification_type: Optional[ str ]
	limit_note: Optional[ str ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the DONKI fetcher with current endpoint defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.headers = { }
		self.base_url = 'https://api.nasa.gov/DONKI'
		self.api_key = cfg.NASA_API_KEY
		self.url = None
		self.params = { }
		self.mode = 'cme'
		self.start_date = ''
		self.end_date = ''
		self.location = 'ALL'
		self.catalog = 'ALL'
		self.notification_type = 'all'
		self.limit_note = None
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'api_key',
				'url',
				'params',
				'mode',
				'start_date',
				'end_date',
				'location',
				'catalog',
				'notification_type',
				'fetch_endpoint',
				'fetch',
				'create_schema'
		]
	
	def fetch_endpoint( self, endpoint: str, start_date: str, end_date: str,
			time: int=20, location: str='', catalog: str='',
			notification_type: str='', most_accurate_only: bool=True,
			complete_entry_only: bool=True, speed: int=0,
			half_angle: int=0, keyword: str='',
			api_key: str=None ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Send a request to a specific DONKI endpoint and return normalized JSON.

			Parameters:
			-----------
			endpoint (str):
				DONKI endpoint path fragment.

			start_date (str):
				Inclusive start date in YYYY-MM-DD format.

			end_date (str):
				Inclusive end date in YYYY-MM-DD format.

			time (int):
				Request timeout in seconds.

			location (str):
				IPS location filter.

			catalog (str):
				CMEAnalysis or IPS catalog filter.

			notification_type (str):
				Notifications type filter.

			most_accurate_only (bool):
				CMEAnalysis filter.

			complete_entry_only (bool):
				CMEAnalysis filter.

			speed (int):
				CMEAnalysis lower-bound speed filter.

			half_angle (int):
				CMEAnalysis lower-bound half-angle filter.

			keyword (str):
				CMEAnalysis keyword filter.

			api_key (str | None):
				Optional runtime override for NASA API key.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'endpoint', endpoint )
			throw_if( 'start_date', start_date )
			throw_if( 'end_date', end_date )
			
			active_key = str( api_key or self.api_key or '' ).strip( )
			if not active_key:
				raise ValueError( 'NASA API key is required for DONKI requests.' )
			
			self.url = f'{self.base_url}/{endpoint}'
			self.params = {
					'startDate': str( start_date ).strip( ),
					'endDate': str( end_date ).strip( ),
					'api_key': active_key
			}
			
			if endpoint == 'IPS' and location.strip( ):
				self.params[ 'location' ]=location.strip( )
			
			if endpoint == 'IPS' and catalog.strip( ):
				self.params[ 'catalog' ]=catalog.strip( )
			
			if endpoint == 'CMEAnalysis':
				self.params[ 'mostAccurateOnly' ]=str( bool( most_accurate_only ) ).lower( )
				self.params[ 'completeEntryOnly' ]=str( bool( complete_entry_only ) ).lower( )
				self.params[ 'speed' ]=int( speed )
				self.params[ 'halfAngle' ]=int( half_angle )
				
				if catalog.strip( ):
					self.params[ 'catalog' ]=catalog.strip( )
				
				if keyword.strip( ):
					self.params[ 'keyword' ]=keyword.strip( )
			
			if endpoint == 'notifications' and notification_type.strip( ):
				self.params[ 'type' ]=notification_type.strip( )
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			payload = self.response.json( )
			
			return {
					'mode': self.mode,
					'endpoint': endpoint,
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'SpaceWeather'
			exception.method = (
					'fetch_endpoint( self, endpoint: str, start_date: str, end_date: str, '
					'time: int=20, location: str=, catalog: str=, notification_type: str=, '
					'most_accurate_only: bool=True, complete_entry_only: bool=True, '
					'speed: int=0, half_angle: int=0, keyword: str=, '
					'api_key: str|None=None ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='cme', start_date: str='', end_date: str='',
			time: int=20, location: str='ALL', catalog: str='ALL',
			notification_type: str='all', most_accurate_only: bool=True,
			complete_entry_only: bool=True, speed: int=0,
			half_angle: int=0, keyword: str='',
			api_key: str=None ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for NASA DONKI endpoints.

			Parameters:
			-----------
			mode (str):
				One of:
				- cme
				- cme_analysis
				- gst
				- ips
				- flr
				- sep
				- mpc
				- rbe
				- hss
				- wsa_enlil
				- notifications

			start_date (str):
				Inclusive start date in YYYY-MM-DD format.

			end_date (str):
				Inclusive end date in YYYY-MM-DD format.

			time (int):
				Request timeout in seconds.

			location (str):
				IPS location filter.

			catalog (str):
				CMEAnalysis or IPS catalog filter.

			notification_type (str):
				Notifications type filter.

			most_accurate_only (bool):
				CMEAnalysis filter.

			complete_entry_only (bool):
				CMEAnalysis filter.

			speed (int):
				CMEAnalysis speed filter.

			half_angle (int):
				CMEAnalysis half-angle filter.

			keyword (str):
				CMEAnalysis keyword filter.

			api_key (str | None):
				Optional runtime override for NASA API key.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'cme' ).strip( ).lower( )
			self.mode = active_mode
			
			endpoint_map = {
					'cme': 'CME',
					'cme_analysis': 'CMEAnalysis',
					'gst': 'GST',
					'ips': 'IPS',
					'flr': 'FLR',
					'sep': 'SEP',
					'mpc': 'MPC',
					'rbe': 'RBE',
					'hss': 'HSS',
					'wsa_enlil': 'WSAEnlilSimulations',
					'notifications': 'notifications'
			}
			
			if active_mode not in endpoint_map:
				raise ValueError(
					"Unsupported mode. Use 'cme', 'cme_analysis', 'gst', 'ips', "
					"'flr', 'sep', 'mpc', 'rbe', 'hss', 'wsa_enlil', or 'notifications'."
				)
			
			return self.fetch_endpoint(
				endpoint=endpoint_map[ active_mode ],
				start_date=str( start_date ).strip( ),
				end_date=str( end_date ).strip( ),
				time=int( time ),
				location=str( location or 'ALL' ).strip( ),
				catalog=str( catalog or 'ALL' ).strip( ),
				notification_type=str( notification_type or 'all' ).strip( ),
				most_accurate_only=bool( most_accurate_only ),
				complete_entry_only=bool( complete_entry_only ),
				speed=int( speed ),
				half_angle=int( half_angle ),
				keyword=str( keyword or '' ).strip( ),
				api_key=api_key
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'SpaceWeather'
			exception.method = (
					'fetch( self, mode: str=cme, start_date: str=, end_date: str=, '
					'time: int=20, location: str=ALL, catalog: str=ALL, '
					'notification_type: str=all, most_accurate_only: bool=True, '
					'complete_entry_only: bool=True, speed: int=0, half_angle: int=0, '
					'keyword: str=, api_key: str|None=None ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': f'{description.strip( )} This function uses the {tool.strip( )} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'SpaceWeather'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class AstroCatalog( Fetcher ):
	'''

		Purpose:
		--------
		Provides structured access to the Open Astronomy Catalog API (OACAPI).

	'''
	base_url: Optional[ str ]
	format: Optional[ str ]
	name: Optional[ str ]
	declination: Optional[ str ]
	right_ascension: Optional[ str ]
	radius: Optional[ int ]
	params: Optional[ Dict[ str, Any ] ]
	
	def __init__( self ):
		super( ).__init__( )
		self.base_url = 'https://api.astrocats.space'
		self.format = 'json'
		self.name = None
		self.right_ascension = None
		self.declination = None
		self.radius = None
		self.params = { }
		self.headers = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		if 'Accept' not in self.headers:
			self.headers[ 'Accept' ]='application/json'
	
	def __dir__( self ) -> List[ str ]:
		return [
				'base_url',
				'timeout',
				'headers',
				'fetch_object',
				'cone_search',
				'fetch',
		]
	
	def _normalize_attribute_path( self, quantity: str='', attributes: str='' ) -> str:
		"""
			Purpose:
			--------
			Build the OAC route path segment from quantity and attribute inputs.

			Returns:
			--------
			str
		"""
		parts: list[ str ]=[ ]
		if quantity and quantity.strip( ):
			parts.append( quantity.strip( ) )
		
		if attributes and attributes.strip( ):
			attr_parts = [ a.strip( ) for a in attributes.split( ',' ) if a.strip( ) ]
			parts.extend( attr_parts )
		
		return '/'.join( parts )
	
	def _parse_argument_string( self, argument_string: str ) -> Dict[ str, Any ]:
		"""
			Purpose:
			--------
			Parse a comma-separated or newline-separated list of OAC query
			arguments into a dictionary.

			Examples:
			---------
			band=R,time,e_magnitude,complete
		"""
		params: Dict[ str, Any ]={ }
		
		if not argument_string or not argument_string.strip( ):
			return params
		
		raw_items = re.split( r'[\n,]+', argument_string )
		items = [ item.strip( ) for item in raw_items if item and item.strip( ) ]
		
		for item in items:
			if '=' in item:
				k, v = item.split( '=', 1 )
				params[ k.strip( ) ]=v.strip( )
			else:
				params[ item ]=''
		
		return params
	
	def request( self, route: str, params: Dict[ str, Any ] | None=None,
			time: int=20 ) -> Any:
		"""
			Purpose:
			--------
			Send an HTTP request to the OAC API and return parsed JSON when possible.

			Returns:
			--------
			Any
		"""
		try:
			self.timeout = int( time )
			self.url = f'{self.base_url}/{route.lstrip( "/" )}'
			self.params = params or { }
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=self.timeout )
			
			self.response.raise_for_status( )
			
			content_type = (self.response.headers.get( 'Content-Type', '' ) or '').lower( )
			if 'json' in content_type:
				return self.response.json( )
			
			return self.response.text
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroCatalog'
			exception.method = 'request( self, route: str, params: Dict[ str, Any ] | None=None, time: int=20 ) -> Any'
			raise exception
	
	def fetch_object( self, name: str, quantity: str='', attributes: str='',
			arguments: str='', data_format: str='json', time: int=20 ) -> Any:
		"""
			Purpose:
			--------
			Query OAC by object/event name using the documented route pattern.

			Returns:
			--------
			Any
		"""
		try:
			throw_if( 'name', name )
			self.name = name.strip( )
			self.format = (data_format or 'json').strip( ).lower( )
			
			route_parts = [ urllib.parse.quote( self.name ) ]
			attr_path = self._normalize_attribute_path( quantity, attributes )
			if attr_path:
				route_parts.append( attr_path )
			
			route = '/'.join( route_parts )
			params = self._parse_argument_string( arguments )
			
			if self.format:
				params[ 'format' ]=self.format
			
			return self.request( route=route, params=params, time=time )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroCatalog'
			exception.method = (
					'fetch_object( self, name: str, quantity: str=, attributes: str=, '
					'arguments: str=, data_format: str=json, time: int=20 ) -> Any'
			)
			raise exception
	
	def cone_search( self, ra: str, dec: str, radius: int=2, quantity: str='',
			attributes: str='', arguments: str='', data_format: str='json', time: int=20 ) -> Any:
		"""
			Purpose:
			--------
			Query OAC using a coordinate cone search via special arguments.

			Returns:
			--------
			Any
		"""
		try:
			throw_if( 'ra', ra )
			throw_if( 'dec', dec )
			self.right_ascension = ra.strip( )
			self.declination = dec.strip( )
			self.radius = max( 1, int( radius ) )
			self.format = (data_format or 'json').strip( ).lower( )
			route = 'catalog'
			attr_path = self._normalize_attribute_path( quantity, attributes )
			if attr_path:
				route = f'{route}/{attr_path}'
			
			params = self._parse_argument_string( arguments )
			params[ 'ra' ]=self.right_ascension
			params[ 'dec' ]=self.declination
			params[ 'radius' ]=str( self.radius )
			if self.format:
				params[ 'format' ]=self.format
			
			return self.request( route=route, params=params, time=time )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroCatalog'
			exception.method = ( 'cone_search( self, ra: str, dec: str, radius: int=2, '
					'quantity: str=, attributes: str=, arguments: str=, '
					'data_format: str=json, time: int=20 ) -> Any' )
			raise exception
	
	def fetch( self, mode: str='object_query', query: str='', quantity: str='',
			attributes: str='', arguments: str='', ra: str='', dec: str='',
			radius: int=2, data_format: str='json', time: int=20 ) -> Any:
		"""
			Purpose:
			--------
			Unified dispatch for Astronomy Catalog operations.

			Returns:
			--------
			Any
		"""
		try:
			active_mode = (mode or 'object_query').strip( ).lower( )
			
			if active_mode == 'object_query':
				return self.fetch_object(
					name=query,
					quantity=quantity,
					attributes=attributes,
					arguments=arguments,
					data_format=data_format,
					time=time )
			
			if active_mode == 'cone_search':
				return self.cone_search(
					ra=ra,
					dec=dec,
					radius=radius,
					quantity=quantity,
					attributes=attributes,
					arguments=arguments,
					data_format=data_format,
					time=time )
			
			raise ValueError( "Unsupported mode. Use 'object_query' or 'cone_search'." )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroCatalog'
			exception.method = (
					'fetch( self, mode: str=object_query, query: str=, quantity: str=, '
					'attributes: str=, arguments: str=, ra: str=, dec: str=, '
					'radius: int=2, data_format: str=json, time: int=20 ) -> Any'
			)
			raise exception

class AstroQuery( Fetcher ):
	'''
	
		Purpose:
		--------
		Fetches astronomical object and region data with astroquery SIMBAD operations.
	
		Attributes:
		-----------
		url,
		radius,
		name,
		declination,
		right_ascension,
		params,
		row_limit,
	
		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_table_to_records(...): Performs the _table_to_records operation for this fetcher.
		object_search(...): Performs the object_search operation for this fetcher.
		object_ids(...): Performs the object_ids operation for this fetcher.
		region_search(...): Performs the region_search operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
	
	'''
	url: Optional[ str ]
	radius: Optional[ float ]
	name: Optional[ str ]
	declination: Optional[ str ]
	right_ascension: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	row_limit: Optional[ int ]
	
	def __init__( self ) -> None:
		super( ).__init__( )
		self.url = None
		self.radius = None
		self.name = None
		self.right_ascension = None
		self.declination = None
		self.params = { }
		self.row_limit = 100
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
	
	def __dir__( self ) -> List[ str ]:
		return [
				'headers',
				'row_limit',
				'object_search',
				'object_ids',
				'region_search',
				'fetch',
		]
	
	def _table_to_records( self, table: Table | None ) -> List[ Dict[ str, Any ] ]:
		"""

			Purpose:
			--------
			Convert an Astropy Table into a list of row dictionaries that can be
			rendered easily in Streamlit.

			Parameters:
			-----------
			table:
				An astropy.table.Table returned by astroquery.

			Returns:
			--------
			List[Dict[str, Any]]

		"""
		try:
			if table is None:
				return [ ]
			
			records: List[ Dict[ str, Any ] ]=[ ]
			for row in table:
				record: Dict[ str, Any ]={ }
				for col in table.colnames:
					try:
						value = row[ col ]
						if hasattr( value, 'item' ):
							try:
								value = value.item( )
							except Exception:
								pass
						record[ str( col ) ]=str( value )
					except Exception:
						record[ str( col ) ]=''
				records.append( record )
			
			return records
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroQuery'
			exception.method = '_table_to_records( self, table: Table | None ) -> List[ Dict[ str, Any ] ]'
			raise exception
	
	def object_search( self, name: str, row_limit: int=100 ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
			--------
			Query SIMBAD for a named astronomical object.

			Parameters:
			-----------
			name:
				Object identifier or common name such as "M81", "Sirius", or
				"NGC 1300".
			row_limit:
				Maximum number of rows to return.

			Returns:
			--------
			Dict[str, Any] | None

		"""
		try:
			throw_if( 'name', name )
			self.name = name.strip( )
			self.row_limit = max( 1, int( row_limit ) )
			
			simbad = Simbad( )
			simbad.ROW_LIMIT = self.row_limit
			result_table = simbad.query_object( self.name )
			
			return {
					'mode': 'object_search',
					'query': self.name,
					'row_limit': self.row_limit,
					'columns': list( result_table.colnames ) if result_table is not None else [ ],
					'rows': self._table_to_records( result_table ),
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroQuery'
			exception.method = 'object_search( self, name: str, row_limit: int=100 ) -> Dict[ str, Any ]'
			raise exception
	
	def object_ids( self, name: str, row_limit: int=100 ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
			--------
			Query SIMBAD for alternate identifiers of a named astronomical object.

			Parameters:
			-----------
			name:
				Object identifier or common name such as "M81" or "Sirius".
			row_limit:
				Maximum number of rows to return.

			Returns:
			--------
			Dict[str, Any] | None

		"""
		try:
			throw_if( 'name', name )
			self.name = name.strip( )
			self.row_limit = max( 1, int( row_limit ) )
			
			simbad = Simbad( )
			simbad.ROW_LIMIT = self.row_limit
			result_table = simbad.query_objectids( self.name )
			
			return {
					'mode': 'object_ids',
					'query': self.name,
					'row_limit': self.row_limit,
					'columns': list( result_table.colnames ) if result_table is not None else [ ],
					'rows': self._table_to_records( result_table ),
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroQuery'
			exception.method = 'object_ids( self, name: str, row_limit: int=100 ) -> Dict[ str, Any ]'
			raise exception
	
	def region_search( self, ra: str, dec: str, radius: float=0.5,
			radius_unit: str='deg', row_limit: int=100 ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
			--------
			Query SIMBAD in a cone around a sky position.

			Parameters:
			-----------
			ra:
				Right Ascension of the search center. This is the east-west sky
				coordinate. Example values:
				- "13:09:48.09"
				- "197.45037"

			dec:
				Declination of the search center. This is the north-south sky
				coordinate. Example values:
				- "-23:22:53.3"
				- "-23.38148"

			radius:
				Angular search radius around the sky position.

			radius_unit:
				Unit for the radius. Supported values here are "deg", "arcmin",
				and "arcsec".

			row_limit:
				Maximum number of rows to return.

			Returns:
			--------
			Dict[str, Any] | None

		"""
		try:
			throw_if( 'ra', ra )
			throw_if( 'dec', dec )
			
			self.right_ascension = ra.strip( )
			self.declination = dec.strip( )
			self.radius = float( radius )
			self.row_limit = max( 1, int( row_limit ) )
			
			unit_map = {
					'deg': u.deg,
					'arcmin': u.arcmin,
					'arcsec': u.arcsec,
			}
			
			active_unit = unit_map.get( (radius_unit or 'deg').strip( ).lower( ), u.deg )
			
			coord = SkyCoord(
				ra=self.right_ascension,
				dec=self.declination,
				unit=(u.hourangle, u.deg) )
			
			simbad = Simbad( )
			simbad.ROW_LIMIT = self.row_limit
			result_table = simbad.query_region(
				coordinates=coord,
				radius=self.radius * active_unit )
			
			return {
					'mode': 'region_search',
					'ra': self.right_ascension,
					'dec': self.declination,
					'radius': self.radius,
					'radius_unit': (radius_unit or 'deg').strip( ).lower( ),
					'row_limit': self.row_limit,
					'columns': list( result_table.colnames ) if result_table is not None else [ ],
					'rows': self._table_to_records( result_table ),
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroQuery'
			exception.method = (
					'region_search( self, ra: str, dec: str, radius: float=0.5, '
					'radius_unit: str=deg, row_limit: int=100 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='object_search', query: str='', ra: str='', dec: str='',
			radius: float=0.5, radius_unit: str='deg', row_limit: int=100 ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
			--------
			Unified dispatch for AstroQuery / SIMBAD operations.

			Parameters:
			-----------
			mode:
				One of:
				- "object_search"
				- "object_ids"
				- "region_search"

			query:
				Named object for object-based modes.

			ra:
				Right Ascension used for region_search.

			dec:
				Declination used for region_search.

			radius:
				Angular radius used for region_search.

			radius_unit:
				Unit for radius used for region_search.

			row_limit:
				Maximum number of rows to return.

			Returns:
			--------
			Dict[str, Any] | None

		"""
		try:
			active_mode = (mode or 'object_search').strip( ).lower( )
			
			if active_mode == 'object_search':
				return self.object_search(
					name=query,
					row_limit=row_limit )
			
			if active_mode == 'object_ids':
				return self.object_ids(
					name=query,
					row_limit=row_limit )
			
			if active_mode == 'region_search':
				return self.region_search(
					ra=ra,
					dec=dec,
					radius=radius,
					radius_unit=radius_unit,
					row_limit=row_limit )
			
			raise ValueError(
				"Unsupported mode. Use 'object_search', 'object_ids', or 'region_search'."
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'AstroQuery'
			exception.method = (
					'fetch( self, mode: str=object_search, query: str=, ra: str=, '
					'dec: str=, radius: float=0.5, radius_unit: str=deg, '
					'row_limit: int=100 ) -> Dict[ str, Any ]'
			)
			raise exception

class StarMap( Fetcher ):
	'''

		Purpose:
		--------
		Builds star-map links and image snapshots for objects or coordinates.

		Attributes:
		-----------
		base_url,
		snapshot_url,
		image_source,
		object,
		right_ascension,
		declination,
		box_color,
		show_box,
		show_grid,
		show_lines,
		show_boundaries,
		show_const_names,
		zoom,
		params,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_normalize_bool(...): Performs the _normalize_bool operation for this fetcher.
		_extract_snapshot_links(...): Performs the _extract_snapshot_links operation for this fetcher.
		fetch_object_link(...): Performs the fetch_object_link operation for this fetcher.
		fetch_coordinate_link(...): Performs the fetch_coordinate_link operation for this fetcher.
		fetch_snapshot(...): Performs the fetch_snapshot operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.

	'''
	base_url: Optional[ str ]
	snapshot_url: Optional[ str ]
	image_source: Optional[ str ]
	object: Optional[ str ]
	right_ascension: Optional[ float ]
	declination: Optional[ float ]
	box_color: Optional[ str ]
	show_box: Optional[ bool ]
	show_grid: Optional[ bool ]
	show_lines: Optional[ bool ]
	show_boundaries: Optional[ bool ]
	show_const_names: Optional[ bool ]
	zoom: Optional[ int ]
	params: Optional[ Dict[ str, Any ] ]
	
	def __init__( self ) -> None:
		'''
		
			Purpose:
			--------
			Initialize the StarMap

			Returns:
			--------
			None

		'''
		super( ).__init__( )
		self.base_url = 'https://www.sky-map.org/'
		self.snapshot_url = 'https://www.sky-map.org/snapshot'
		self.image_source = 'DSS2'
		self.object = None
		self.right_ascension = None
		self.declination = None
		self.box_color = 'yellow'
		self.show_box = True
		self.show_grid = True
		self.show_lines = True
		self.show_boundaries = True
		self.show_const_names = False
		self.zoom = 5
		self.params = { }
		self.timeout = 20
		self.headers = { }
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		if 'Accept' not in self.headers:
			self.headers[
				'Accept' ]='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	
	def __dir__( self ) -> List[ str ]:
		return [
				'base_url',
				'snapshot_url',
				'object',
				'right_ascension',
				'declination',
				'image_source',
				'zoom',
				'show_box',
				'show_grid',
				'show_lines',
				'show_boundaries',
				'show_const_names',
				'box_color',
				'params',
				'fetch_object_link',
				'fetch_coordinate_link',
				'fetch_snapshot',
				'fetch',
		]
	
	def _normalize_bool( self, value: bool ) -> str:
		'''
		
			Purpose:
			--------
			Convert a Python bool into the integer-style string form frequently
			used by Sky-Map query parameters.

			Parameters:
			-----------
			value:
				Boolean value to convert.

			Returns:
			--------
			str

		'''
		return '1' if bool( value ) else '0'
	
	def _extract_snapshot_links( self, html: str, base_url: str ) -> Dict[ str, str ]:
		'''
		
			Purpose:
			--------
			Parse the snapshot HTML page and extract save-as image links for
			formats like jpeg, png, gif, bmp, and tiff.

			Parameters:
			-----------
			html:
				Raw HTML returned by the snapshot endpoint.
			base_url:
				Base URL used to resolve relative hyperlinks.

			Returns:
			--------
			Dict[str, str]

		'''
		try:
			links: Dict[ str, str ]={ }
			if not html or not isinstance( html, str ):
				return links
			
			pattern = re.compile(
				r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>\s*(jpeg|png|gif|bmp|tiff)\s*</a>',
				flags=re.IGNORECASE )
			
			for match in pattern.finditer( html ):
				href = match.group( 1 )
				label = match.group( 2 ).lower( )
				links[ label ]=urllib.parse.urljoin( base_url, href )
			
			return links
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'StarMap'
			exception.method = '_extract_snapshot_links( self, html: str, base_url: str ) -> Dict[ str, str ]'
			raise exception
	
	def fetch_object_link(
			self,
			name: str,
			zoom: int=5,
			box_color: str='yellow',
			show_box: bool=True,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
		
			Purpose:
			--------
			Construct an interactive Sky-Map link centered on a named object.

			Parameters:
			-----------
			name:
				Object name or identifier such as "Polaris", "M31", or
				"NGC 1300".
			zoom:
				Map zoom level. Smaller values show a wider field; larger values
				zoom further in.
			box_color:
				Color of the selection/highlight box.
			show_box:
				Whether to show the highlight box around the object.
			time:
				Request timeout in seconds used for validation.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			throw_if( 'name', name )
			
			self.object = name.strip( )
			self.zoom = max( 1, min( int( zoom ), 18 ) )
			self.box_color = box_color or 'yellow'
			self.show_box = bool( show_box )
			self.timeout = int( time )
			
			self.params = {
					'object': self.object,
					'show_box': self._normalize_bool( self.show_box ),
					'zoom': str( self.zoom ),
					'box_color': self.box_color,
					'box_width': '50',
					'box_height': '50',
			}
			
			interactive_url = f'{self.base_url}?{urllib.parse.urlencode( self.params )}'
			
			self.response = requests.get(
				url=self.base_url,
				params=self.params,
				headers=self.headers,
				timeout=self.timeout )
			self.response.raise_for_status( )
			
			return {
					'mode': 'object_link',
					'object': self.object,
					'zoom': self.zoom,
					'params': self.params,
					'interactive_url': interactive_url,
					'status_code': self.response.status_code,
					'html_preview': self.response.text[ : 2000 ],
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'StarMap'
			exception.method = (
					'fetch_object_link( self, name: str, zoom: int=5, box_color: str=yellow, '
					'show_box: bool=True, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_coordinate_link(
			self,
			ra: float,
			dec: float,
			zoom: int=5,
			box_color: str='yellow',
			show_box: bool=True,
			show_grid: bool=True,
			show_lines: bool=True,
			show_boundaries: bool=True,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
		
			Purpose:
			--------
			Construct an interactive Sky-Map link centered on sky coordinates.

			Parameters:
			-----------
			ra:
				Right Ascension of the map center in hours.
				Example values:
				- 15.2976
				- 5.9195

			dec:
				Declination of the map center in degrees.
				Example values:
				- -17.5892
				- 41.2692

			zoom:
				Map zoom level.
			box_color:
				Color of the selection/highlight box.
			show_box:
				Whether to show the highlight box.
			show_grid:
				Whether to display coordinate grid lines.
			show_lines:
				Whether to display constellation lines.
			show_boundaries:
				Whether to display constellation boundaries.
			time:
				Request timeout in seconds used for validation.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			throw_if( 'ra', ra )
			throw_if( 'dec', dec )
			
			self.right_ascension = float( ra )
			self.declination = float( dec )
			self.zoom = max( 1, min( int( zoom ), 18 ) )
			self.box_color = box_color or 'yellow'
			self.show_box = bool( show_box )
			self.show_grid = bool( show_grid )
			self.show_lines = bool( show_lines )
			self.show_boundaries = bool( show_boundaries )
			self.timeout = int( time )
			
			self.params = {
					'ra': f'{self.right_ascension}',
					'de': f'{self.declination}',
					'show_box': self._normalize_bool( self.show_box ),
					'zoom': str( self.zoom ),
					'box_color': self.box_color,
					'show_grid': self._normalize_bool( self.show_grid ),
					'show_constellation_lines': self._normalize_bool( self.show_lines ),
					'show_constellation_boundaries': self._normalize_bool( self.show_boundaries ),
			}
			
			interactive_url = f'{self.base_url}?{urllib.parse.urlencode( self.params )}'
			
			self.response = requests.get(
				url=self.base_url,
				params=self.params,
				headers=self.headers,
				timeout=self.timeout )
			self.response.raise_for_status( )
			
			return {
					'mode': 'coordinate_link',
					'ra': self.right_ascension,
					'dec': self.declination,
					'zoom': self.zoom,
					'params': self.params,
					'interactive_url': interactive_url,
					'status_code': self.response.status_code,
					'html_preview': self.response.text[ : 2000 ],
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'StarMap'
			exception.method = (
					'fetch_coordinate_link( self, ra: float, dec: float, zoom: int=5, '
					'box_color: str=yellow, show_box: bool=True, show_grid: bool=True, '
					'show_lines: bool=True, show_boundaries: bool=True, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_snapshot(
			self,
			ra: float,
			dec: float,
			zoom: int=10,
			image_source: str='DSS2',
			show_grid: bool=True,
			show_lines: bool=True,
			show_boundaries: bool=True,
			show_const_names: bool=False,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
		
			Purpose:
			--------
			Request the Sky-Map snapshot generator page and extract the available
			static image links.

			Parameters:
			-----------
			ra:
				Right Ascension of the image center in hours.
				Example values:
				- 15.2976
				- 5.9195

			dec:
				Declination of the image center in degrees.
				Example values:
				- -17.5892
				- 41.2692

			zoom:
				Snapshot zoom level / field scale.
			image_source:
				Survey source such as DSS2, SDSS, GALEX, IRAS, or RASS.
			show_grid:
				Whether to display the coordinate grid.
			show_lines:
				Whether to display constellation lines.
			show_boundaries:
				Whether to display constellation boundaries.
			show_const_names:
				Whether to display constellation names.
			time:
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			throw_if( 'ra', ra )
			throw_if( 'dec', dec )
			
			self.right_ascension = float( ra )
			self.declination = float( dec )
			self.zoom = max( 1, min( int( zoom ), 18 ) )
			self.image_source = (image_source or 'DSS2').strip( )
			self.show_grid = bool( show_grid )
			self.show_lines = bool( show_lines )
			self.show_boundaries = bool( show_boundaries )
			self.show_const_names = bool( show_const_names )
			self.timeout = int( time )
			
			self.params = {
					'ra': f'{self.right_ascension}',
					'de': f'{self.declination}',
					'zoom': str( self.zoom ),
					'img_source': self.image_source,
					'show_grid': self._normalize_bool( self.show_grid ),
					'show_constellation_lines': self._normalize_bool( self.show_lines ),
					'show_constellation_boundaries': self._normalize_bool( self.show_boundaries ),
					'show_const_names': self._normalize_bool( self.show_const_names ),
			}
			
			page_url = f'{self.snapshot_url}?{urllib.parse.urlencode( self.params )}'
			
			self.response = requests.get(
				url=self.snapshot_url,
				params=self.params,
				headers=self.headers,
				timeout=self.timeout )
			self.response.raise_for_status( )
			
			image_links = self._extract_snapshot_links(
				html=self.response.text,
				base_url=self.snapshot_url )
			
			return {
					'mode': 'snapshot',
					'ra': self.right_ascension,
					'dec': self.declination,
					'zoom': self.zoom,
					'image_source': self.image_source,
					'params': self.params,
					'snapshot_page_url': page_url,
					'image_links': image_links,
					'preferred_image_url': image_links.get( 'png' ) or image_links.get( 'jpeg', '' ),
					'status_code': self.response.status_code,
					'html_preview': self.response.text[ : 2000 ],
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'StarMap'
			exception.method = (
					'fetch_snapshot( self, ra: float, dec: float, zoom: int=10, '
					'image_source: str=DSS2, show_grid: bool=True, show_lines: bool=True, '
					'show_boundaries: bool=True, show_const_names: bool=False, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch(
			self,
			mode: str='object_link',
			query: str='',
			ra: float=0.0,
			dec: float=0.0,
			zoom: int=5,
			image_source: str='DSS2',
			box_color: str='yellow',
			show_box: bool=True,
			show_grid: bool=True,
			show_lines: bool=True,
			show_boundaries: bool=True,
			show_const_names: bool=False,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
		
			Purpose:
			--------
			Unified dispatch for StarMap object links, coordinate links, and
			static snapshot generation.

			Parameters:
			-----------
			mode:
				One of:
				- "object_link"
				- "coordinate_link"
				- "snapshot"

			query:
				Object name used for object_link.

			ra:
				Right Ascension used for coordinate_link and snapshot.

			dec:
				Declination used for coordinate_link and snapshot.

			zoom:
				Zoom level.

			image_source:
				Sky survey source used for snapshot.

			box_color:
				Highlight box color for interactive modes.

			show_box:
				Show highlight box for interactive modes.

			show_grid:
				Show grid for coordinate/snapshot modes.

			show_lines:
				Show constellation lines.

			show_boundaries:
				Show constellation boundaries.

			show_const_names:
				Show constellation names for snapshot mode.

			time:
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			active_mode = (mode or 'object_link').strip( ).lower( )
			
			if active_mode == 'object_link':
				return self.fetch_object_link(
					name=query,
					zoom=zoom,
					box_color=box_color,
					show_box=show_box,
					time=time )
			
			if active_mode == 'coordinate_link':
				return self.fetch_coordinate_link(
					ra=ra,
					dec=dec,
					zoom=zoom,
					box_color=box_color,
					show_box=show_box,
					show_grid=show_grid,
					show_lines=show_lines,
					show_boundaries=show_boundaries,
					time=time )
			
			if active_mode == 'snapshot':
				return self.fetch_snapshot(
					ra=ra,
					dec=dec,
					zoom=zoom,
					image_source=image_source,
					show_grid=show_grid,
					show_lines=show_lines,
					show_boundaries=show_boundaries,
					show_const_names=show_const_names,
					time=time )
			
			raise ValueError(
				"Unsupported mode. Use 'object_link', 'coordinate_link', or 'snapshot'."
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'StarMap'
			exception.method = (
					'fetch( self, mode: str=object_link, query: str=, ra: float=0.0, '
					'dec: float=0.0, zoom: int=5, image_source: str=DSS2, '
					'box_color: str=yellow, show_box: bool=True, show_grid: bool=True, '
					'show_lines: bool=True, show_boundaries: bool=True, '
					'show_const_names: bool=False, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception

class GovData( Fetcher ):
	'''

		Purpose:
		--------
		Fetches Data.gov package search, package summary, and collection records.

		Attributes:
		-----------
		api_key,
		base_url,
		url,
		params,
		payload,
		query,
		page_size,
		offset_mark,
		sort_field,
		sort_order,
		package_id,
		collection,
		start_date,
		agents,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_resolve_api_key(...): Performs the _resolve_api_key operation for this fetcher.
		_validate_page_size(...): Performs the _validate_page_size operation for this fetcher.
		_validate_sort_field(...): Performs the _validate_sort_field operation for this fetcher.
		_validate_sort_order(...): Performs the _validate_sort_order operation for this fetcher.
		fetch_search(...): Performs the fetch_search operation for this fetcher.
		fetch_package_summary(...): Performs the fetch_package_summary operation for this fetcher.
		fetch_collection(...): Performs the fetch_collection operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	api_key: Optional[ str ]
	base_url: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Dict[ str, Any ] ]
	query: Optional[ str ]
	page_size: Optional[ int ]
	offset_mark: Optional[ str ]
	sort_field: Optional[ str ]
	sort_order: Optional[ str ]
	package_id: Optional[ str ]
	collection: Optional[ str ]
	start_date: Optional[ str ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the GovInfo fetcher with current API defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.api_key = cfg.GOVINFO_API_KEY
		self.base_url = 'https://api.govinfo.gov'
		self.url = None
		self.params = { }
		self.payload = { }
		self.query = ''
		self.page_size = 10
		self.offset_mark = '*'
		self.sort_field = 'score'
		self.sort_order = 'DESC'
		self.package_id = ''
		self.collection = ''
		self.start_date = ''
		self.headers = {
				'Accept': 'application/json',
				'Content-Type': 'application/json',
				'User-Agent': cfg.AGENTS
		}
		self.agents = cfg.AGENTS
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'api_key',
				'base_url',
				'url',
				'params',
				'payload',
				'query',
				'page_size',
				'offset_mark',
				'sort_field',
				'sort_order',
				'package_id',
				'collection',
				'start_date',
				'fetch_search',
				'fetch_package_summary',
				'fetch_collection',
				'fetch',
				'create_schema'
		]
	
	def _resolve_api_key( self ) -> str:
		'''
			Purpose:
			--------
			Resolve the GovInfo API key, falling back to DEMO_KEY if none is set.

			Parameters:
			-----------
			None

			Returns:
			--------
			str
		'''
		try:
			value = str( self.api_key or '' ).strip( )
			return value if value else 'DEMO_KEY'
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = '_resolve_api_key( self ) -> str'
			raise exception
	
	def _validate_page_size( self, page_size: int ) -> int:
		'''
			Purpose:
			--------
			Validate GovInfo page size.

			Parameters:
			-----------
			page_size (int):
				Requested page size.

			Returns:
			--------
			int
		'''
		try:
			value = int( page_size )
			if value < 1 or value > 1000:
				raise ValueError( 'page_size must be between 1 and 1000.' )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = '_validate_page_size( self, page_size: int ) -> int'
			raise exception
	
	def _validate_sort_field( self, sort_field: str ) -> str:
		'''
			Purpose:
			--------
			Validate supported sort field values for the search expander.

			Parameters:
			-----------
			sort_field (str):
				Sort field.

			Returns:
			--------
			str
		'''
		try:
			value = str( sort_field or 'score' ).strip( )
			allowed = { 'score', 'lastModified' }
			
			if value not in allowed:
				raise ValueError(
					"Unsupported sort field. Use 'score' or 'lastModified'."
				)
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = '_validate_sort_field( self, sort_field: str ) -> str'
			raise exception
	
	def _validate_sort_order( self, sort_order: str ) -> str:
		'''
			Purpose:
			--------
			Validate supported sort order values.

			Parameters:
			-----------
			sort_order (str):
				Sort order.

			Returns:
			--------
			str
		'''
		try:
			value = str( sort_order or 'DESC' ).strip( ).upper( )
			allowed = { 'ASC', 'DESC' }
			
			if value not in allowed:
				raise ValueError( "Unsupported sort order. Use 'ASC' or 'DESC'." )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = '_validate_sort_order( self, sort_order: str ) -> str'
			raise exception
	
	def fetch_search( self, query: str, page_size: int=10,
			offset_mark: str='*', sort_field: str='score',
			sort_order: str='DESC', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
		
			Purpose:
			--------
			Execute a GovInfo Search Service query.

			Parameters:
			-----------
			query (str):
				GovInfo search expression. May include field operators such as
				collection, congress, publishdate, and lastModified.

			page_size (int):
				Number of records to return. GovInfo allows up to 1000.

			offset_mark (str):
				Use '*' for the first page; for subsequent pages use the offsetMark
				returned by the prior response.

			sort_field (str):
				Supported here:
				- score
				- lastModified

			sort_order (str):
				ASC or DESC.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'query', query )
			
			self.query = str( query ).strip( )
			self.page_size = self._validate_page_size( page_size )
			self.offset_mark = str( offset_mark or '*' ).strip( )
			self.sort_field = self._validate_sort_field( sort_field )
			self.sort_order = self._validate_sort_order( sort_order )
			
			self.url = f'{self.base_url}/search'
			self.params = {
					'api_key': self._resolve_api_key( )
			}
			self.payload = {
					'query': self.query,
					'pageSize': self.page_size,
					'offsetMark': self.offset_mark,
					'sorts': [
							{
									'field': self.sort_field,
									'sortOrder': self.sort_order
							}
					]
			}
			
			self.response = requests.post(
				url=self.url,
				params=self.params,
				json=self.payload,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'search',
					'url': self.url,
					'params': self.params,
					'payload': self.payload,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = (
					'fetch_search( self, query: str, page_size: int=10, '
					'offset_mark: str=*, sort_field: str=score, '
					'sort_order: str=DESC, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_package_summary( self, package_id: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch a GovInfo package summary by package ID.

			Parameters:
			-----------
			package_id (str):
				GovInfo package identifier, such as CREC-2018-10-10.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'package_id', package_id )
			
			self.package_id = str( package_id ).strip( )
			self.url = f'{self.base_url}/packages/{self.package_id}/summary'
			self.params = {
					'api_key': self._resolve_api_key( )
			}
			self.payload = { }
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'package_summary',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = (
					'fetch_package_summary( self, package_id: str, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_collection( self, collection: str, start_date: str,
			page_size: int=10, offset_mark: str='*',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch packages from a GovInfo collection since a given ISO timestamp.

			Parameters:
			-----------
			collection (str):
				Collection code, such as CREC, FR, or BILLS.

			start_date (str):
				ISO timestamp such as 2018-10-01T00:00:00Z.

			page_size (int):
				Number of records to return.

			offset_mark (str):
				Use '*' for the first page.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'collection', collection )
			throw_if( 'start_date', start_date )
			
			self.collection = str( collection ).strip( )
			self.start_date = str( start_date ).strip( )
			self.page_size = self._validate_page_size( page_size )
			self.offset_mark = str( offset_mark or '*' ).strip( )
			
			self.url = f'{self.base_url}/collections/{self.collection}/{self.start_date}'
			self.params = {
					'pageSize': self.page_size,
					'offsetMark': self.offset_mark,
					'api_key': self._resolve_api_key( )
			}
			self.payload = { }
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'collection',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = (
					'fetch_collection( self, collection: str, start_date: str, '
					'page_size: int=10, offset_mark: str=*, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='search', query: str='',
			page_size: int=10, offset_mark: str='*',
			sort_field: str='score', sort_order: str='DESC',
			package_id: str='', collection: str='',
			start_date: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for GovInfo requests.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- search
				- package_summary
				- collection

			query (str):
				GovInfo search query for search mode.

			page_size (int):
				Page size for search or collection mode.

			offset_mark (str):
				Offset marker for search or collection mode.

			sort_field (str):
				Sort field for search mode.

			sort_order (str):
				Sort order for search mode.

			package_id (str):
				Package ID for package_summary mode.

			collection (str):
				Collection code for collection mode.

			start_date (str):
				ISO timestamp for collection mode.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'search' ).strip( ).lower( )
			
			if active_mode == 'search':
				return self.fetch_search(
					query=query,
					page_size=page_size,
					offset_mark=offset_mark,
					sort_field=sort_field,
					sort_order=sort_order,
					time=time
				)
			
			if active_mode == 'package_summary':
				return self.fetch_package_summary(
					package_id=package_id,
					time=time
				)
			
			if active_mode == 'collection':
				return self.fetch_collection(
					collection=collection,
					start_date=start_date,
					page_size=page_size,
					offset_mark=offset_mark,
					time=time
				)
			
			raise ValueError(
				"Unsupported mode. Use one of: search, package_summary, collection."
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = (
					'fetch( self, mode: str=search, query: str=, page_size: int=10, '
					'offset_mark: str=*, sort_field: str=score, '
					'sort_order: str=DESC, package_id: str=, collection: str=, '
					'start_date: str=, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f'{description.strip( )} '
							f'This function uses the {tool.strip( )} service.'
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GovData'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class StarChart( Fetcher ):
	'''

		Purpose:
		--------
		Provides static and link-based star chart generation using the SKY-MAP.ORG
		XML API, Site Linker, and Image Generator interfaces.

		This class is intentionally chart-focused and kept separate from StarMap.

		Referenced API Requirements:
		----------------------------
		XML Search:
			- Endpoint: https://server1.sky-map.org/search
			- Required parameter:
				- star

		Site Linker:
			- Endpoint: https://www.sky-map.org/
			- Supported parameters used here:
				- object
				- ra
				- de
				- zoom
				- show_box
				- box_color
				- show_grid
				- show_constellation_lines
				- show_constellation_boundaries
				- img_source

		Image Generator:
			- Endpoint: https://server2.sky-map.org/map
			- Supported parameters used here:
				- ra
				- de
				- zoom
				- show_grid
				- show_constellation_lines
				- show_constellation_boundaries
				- show_const_names
				- img_source
				- w
				- h
				- mag

		Attributes:
		-----------
		search_url: Optional[str]
			SKY-MAP XML search endpoint.

		link_url: Optional[str]
			SKY-MAP site-link endpoint.

		image_url: Optional[str]
			SKY-MAP image-generator endpoint.

		url: Optional[str]
			Resolved request URL.

		params: Optional[Dict[str, Any]]
			Request parameters.

		mode: Optional[str]
			Selected chart mode.

		query: Optional[str]
			Object query string.

		ra: Optional[float]
			Right Ascension in decimal hours.

		dec: Optional[float]
			Declination in decimal degrees.

		zoom: Optional[int]
			Chart zoom level.

		image_source: Optional[str]
			Chart image source.

		box_color: Optional[str]
			Pointer box color.

		show_box: Optional[bool]
			Show highlight box.

		show_grid: Optional[bool]
			Show coordinate grid.

		show_lines: Optional[bool]
			Show constellation lines.

		show_boundaries: Optional[bool]
			Show constellation boundaries.

		show_const_names: Optional[bool]
			Show constellation names.

		width: Optional[int]
			Generated image width.

		height: Optional[int]
			Generated image height.

		magnitude: Optional[float]
			Image generator limiting magnitude.

		agents: Optional[str]
			User-Agent string.

		Methods:
		--------
		__init__() -> None
			Initialize chart defaults.

		__dir__() -> List[str]
			Provide ordered member visibility.

		search_object(...) -> Dict[str, Any] | None
			Resolve an object name through the SKY-MAP XML API.

		fetch_object_chart(...) -> Dict[str, Any] | None
			Build an object-based chart link.

		fetch_coordinate_chart(...) -> Dict[str, Any] | None
			Build a coordinate-based chart link.

		fetch_static_chart(...) -> Dict[str, Any] | None
			Build a static chart image URL.

		fetch(...) -> Dict[str, Any] | None
			Unified dispatcher.

		create_schema(...) -> Dict[str, str] | None
			Construct a dynamic tool schema.

	'''
	search_url: Optional[ str ]
	link_url: Optional[ str ]
	image_url: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	mode: Optional[ str ]
	query: Optional[ str ]
	ra: Optional[ float ]
	dec: Optional[ float ]
	zoom: Optional[ int ]
	image_source: Optional[ str ]
	box_color: Optional[ str ]
	show_box: Optional[ bool ]
	show_grid: Optional[ bool ]
	show_lines: Optional[ bool ]
	show_boundaries: Optional[ bool ]
	show_const_names: Optional[ bool ]
	width: Optional[ int ]
	height: Optional[ int ]
	magnitude: Optional[ float ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the StarChart fetcher with current SKY-MAP defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.headers = { }
		self.search_url = 'https://server1.sky-map.org/search'
		self.link_url = 'https://www.sky-map.org/'
		self.image_url = 'https://server2.sky-map.org/map'
		self.url = None
		self.params = { }
		self.mode = 'object_chart'
		self.query = ''
		self.ra = 0.0
		self.dec = 0.0
		self.zoom = 5
		self.image_source = 'DSS2'
		self.box_color = 'yellow'
		self.show_box = True
		self.show_grid = True
		self.show_lines = True
		self.show_boundaries = True
		self.show_const_names = False
		self.width = 900
		self.height = 450
		self.magnitude = 7.5
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
			
		'''
		return [
				'search_url',
				'link_url',
				'image_url',
				'url',
				'params',
				'mode',
				'query',
				'ra',
				'dec',
				'zoom',
				'image_source',
				'box_color',
				'show_box',
				'show_grid',
				'show_lines',
				'show_boundaries',
				'show_const_names',
				'width',
				'height',
				'magnitude',
				'search_object',
				'fetch_object_chart',
				'fetch_coordinate_chart',
				'fetch_static_chart',
				'fetch',
				'create_schema'
		]
	
	def _flag( self, value: bool, invert: bool=False ) -> int:
		'''
			Purpose:
			--------
			Convert boolean UI flags into SKY-MAP numeric flags.

			Parameters:
			-----------
			value (bool):
				Input boolean value.

			invert (bool):
				If True, invert the SKY-MAP convention.

			Returns:
			--------
			int
		'''
		if invert:
			return 0 if bool( value ) else 1
		
		return 1 if bool( value ) else 0
	
	def search_object( self, name: str, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Resolve an object name into SKY-MAP coordinates using the XML API.

			Parameters:
			-----------
			name (str):
				Object name or catalog id. Examples:
				- Polaris
				- M31
				- NGC 1300

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'name', name )
			self.query = str( name ).strip( )
			self.url = self.search_url
			self.params = { 'star': self.query }
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			root = ET.fromstring( self.response.text )
			status = root.findtext( 'status', default='' )
			verbiage = root.findtext( 'verbiage', default='' )
			star = root.find( 'star' )
			
			if star is None:
				return {
						'mode': 'object_search',
						'url': self.url,
						'params': self.params,
						'status': status,
						'verbiage': verbiage,
						'data': { }
				}
			
			result = {
					'id': star.attrib.get( 'id', '' ),
					'catalog_id': star.findtext( 'catId', default='' ),
					'constellation': star.findtext( 'constellation', default='' ),
					'ra': float( star.findtext( 'ra', default='0' ) ),
					'dec': float( star.findtext( 'de', default='0' ) ),
					'magnitude': star.findtext( 'mag', default='' )
			}
			
			self.ra = result[ 'ra' ]
			self.dec = result[ 'dec' ]
			
			return {
					'mode': 'object_search',
					'url': self.url,
					'params': self.params,
					'status': status,
					'verbiage': verbiage,
					'data': result
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'StarChart'
			exception.method = (
					'search_object( self, name: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_object_chart( self, name: str, zoom: int=5,
			box_color: str='yellow', show_box: bool=True,
			image_source: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Build an object-based SKY-MAP chart link.

			Parameters:
			-----------
			name (str):
				Object name or catalog id.

			zoom (int):
				Chart zoom level.

			box_color (str):
				Pointer box color.

			show_box (bool):
				Show pointer box.

			image_source (str):
				Optional image source such as SDSS.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'name', name )
			self.mode = 'object_chart'
			self.query = str( name ).strip( )
			self.zoom = int( zoom )
			self.box_color = str( box_color or 'yellow' ).strip( )
			self.show_box = bool( show_box )
			self.image_source = str( image_source or '' ).strip( )
			
			self.url = self.link_url
			self.params = {
					'object': self.query,
					'zoom': self.zoom,
					'show_box': self._flag( self.show_box ),
					'box_color': self.box_color
			}
			
			if self.image_source:
				self.params[ 'img_source' ]=self.image_source
			
			link = requests.Request( 'GET', self.url, params=self.params ).prepare( ).url
			
			search = self.search_object( name=self.query, time=time ) or { }
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'chart_url': link,
					'search': search
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'StarChart'
			exception.method = (
					'fetch_object_chart( self, name: str, zoom: int=5, '
					'box_color: str=yellow, show_box: bool=True, image_source: str=, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_coordinate_chart( self, ra: float, dec: float, zoom: int=5,
			box_color: str='yellow', show_box: bool=True,
			show_grid: bool=True, show_lines: bool=True,
			show_boundaries: bool=True, image_source: str='' ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Build a coordinate-based SKY-MAP chart link.

			Parameters:
			-----------
			ra (float):
				Right Ascension in decimal hours.

			dec (float):
				Declination in decimal degrees.

			zoom (int):
				Chart zoom level.

			box_color (str):
				Pointer box color.

			show_box (bool):
				Show pointer box.

			show_grid (bool):
				Show coordinate grid.

			show_lines (bool):
				Show constellation lines.

			show_boundaries (bool):
				Show constellation boundaries.

			image_source (str):
				Optional image source such as SDSS.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'coordinate_chart'
			self.ra = float( ra )
			self.dec = float( dec )
			self.zoom = int( zoom )
			self.box_color = str( box_color or 'yellow' ).strip( )
			self.show_box = bool( show_box )
			self.show_grid = bool( show_grid )
			self.show_lines = bool( show_lines )
			self.show_boundaries = bool( show_boundaries )
			self.image_source = str( image_source or '' ).strip( )
			
			self.url = self.link_url
			self.params = {
					'ra': self.ra,
					'de': self.dec,
					'zoom': self.zoom,
					'show_box': self._flag( self.show_box ),
					'box_color': self.box_color,
					'show_grid': self._flag( self.show_grid, invert=True ),
					'show_constellation_lines': self._flag( self.show_lines, invert=True ),
					'show_constellation_boundaries': self._flag( self.show_boundaries, invert=True )
			}
			
			if self.image_source:
				self.params[ 'img_source' ]=self.image_source
			
			link = requests.Request( 'GET', self.url, params=self.params ).prepare( ).url
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'chart_url': link
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'StarChart'
			exception.method = (
					'fetch_coordinate_chart( self, ra: float, dec: float, zoom: int=5, '
					'box_color: str=yellow, show_box: bool=True, show_grid: bool=True, '
					'show_lines: bool=True, show_boundaries: bool=True, image_source: str= ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_static_chart( self, ra: float, dec: float, zoom: int=5,
			image_source: str='DSS2', show_grid: bool=True,
			show_lines: bool=True, show_boundaries: bool=True,
			show_const_names: bool=False, width: int=900,
			height: int=450, magnitude: float=7.5 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Build a static SKY-MAP chart image URL.

			Parameters:
			-----------
			ra (float):
				Right Ascension in decimal hours.

			dec (float):
				Declination in decimal degrees.

			zoom (int):
				Chart zoom level.

			image_source (str):
				Image survey source.

			show_grid (bool):
				Show grid.

			show_lines (bool):
				Show constellation lines.

			show_boundaries (bool):
				Show constellation boundaries.

			show_const_names (bool):
				Show constellation names.

			width (int):
				Image width in pixels.

			height (int):
				Image height in pixels.

			magnitude (float):
				Limiting magnitude.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'static_chart'
			self.ra = float( ra )
			self.dec = float( dec )
			self.zoom = int( zoom )
			self.image_source = str( image_source or 'DSS2' ).strip( )
			self.show_grid = bool( show_grid )
			self.show_lines = bool( show_lines )
			self.show_boundaries = bool( show_boundaries )
			self.show_const_names = bool( show_const_names )
			self.width = int( width )
			self.height = int( height )
			self.magnitude = float( magnitude )
			
			self.url = self.image_url
			self.params = {
					'type': 'FULL',
					'w': self.width,
					'h': self.height,
					'ra': self.ra,
					'de': self.dec,
					'zoom': self.zoom,
					'mag': self.magnitude,
					'show_grid': self._flag( self.show_grid ),
					'grid_color': '404040',
					'grid_color_zero': '808080',
					'show_constellation_lines': self._flag( self.show_lines ),
					'show_constellation_boundaries': self._flag( self.show_boundaries ),
					'show_const_names': self._flag( self.show_const_names ),
					'img_source': self.image_source
			}
			
			image_link = requests.Request( 'GET', self.url, params=self.params ).prepare( ).url
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'image_url': image_link
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'StarChart'
			exception.method = (
					'fetch_static_chart( self, ra: float, dec: float, zoom: int=5, '
					'image_source: str=DSS2, show_grid: bool=True, show_lines: bool=True, '
					'show_boundaries: bool=True, show_const_names: bool=False, '
					'width: int=900, height: int=450, magnitude: float=7.5 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='object_chart', query: str='',
			ra: float=0.0, dec: float=0.0, zoom: int=5,
			image_source: str='DSS2', box_color: str='yellow',
			show_box: bool=True, show_grid: bool=True,
			show_lines: bool=True, show_boundaries: bool=True,
			show_const_names: bool=False, width: int=900,
			height: int=450, magnitude: float=7.5,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for SKY-MAP chart generation.

			Parameters:
			-----------
			mode (str):
				One of:
				- object_search
				- object_chart
				- coordinate_chart
				- static_chart

			query (str):
				Object query for object_search and object_chart.

			ra (float):
				Right Ascension for coordinate_chart and static_chart.

			dec (float):
				Declination for coordinate_chart and static_chart.

			zoom (int):
				Chart zoom level.

			image_source (str):
				Image source.

			box_color (str):
				Pointer box color.

			show_box (bool):
				Show pointer box.

			show_grid (bool):
				Show coordinate grid.

			show_lines (bool):
				Show constellation lines.

			show_boundaries (bool):
				Show constellation boundaries.

			show_const_names (bool):
				Show constellation names.

			width (int):
				Static image width.

			height (int):
				Static image height.

			magnitude (float):
				Static image limiting magnitude.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = (mode or 'object_chart').strip( ).lower( )
			if active_mode == 'object_search':
				return self.search_object( name=query, time=time )
			if active_mode == 'object_chart':
				return self.fetch_object_chart( name=query, zoom=zoom, box_color=box_color,
					show_box=show_box, image_source=image_source if image_source != 'DSS2' else '',
					time=time )
			if active_mode == 'coordinate_chart':
				return self.fetch_coordinate_chart(
					ra=ra,
					dec=dec,
					zoom=zoom,
					box_color=box_color,
					show_box=show_box,
					show_grid=show_grid,
					show_lines=show_lines,
					show_boundaries=show_boundaries,
					image_source=image_source if image_source != 'DSS2' else '')
			
			if active_mode == 'static_chart':
				return self.fetch_static_chart(
					ra=ra,
					dec=dec,
					zoom=zoom,
					image_source=image_source,
					show_grid=show_grid,
					show_lines=show_lines,
					show_boundaries=show_boundaries,
					show_const_names=show_const_names,
					width=width,
					height=height,
					magnitude=magnitude
				)
			
			raise ValueError(
				"Unsupported mode. Use 'object_search', 'object_chart', "
				"'coordinate_chart', or 'static_chart'."
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'StarChart'
			exception.method = (
					'fetch( self, mode: str=object_chart, query: str=, ra: float=0.0, '
					'dec: float=0.0, zoom: int=5, image_source: str=DSS2, '
					'box_color: str=yellow, show_box: bool=True, show_grid: bool=True, '
					'show_lines: bool=True, show_boundaries: bool=True, '
					'show_const_names: bool=False, width: int=900, height: int=450, '
					'magnitude: float=7.5, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': f'{description.strip( )} This function uses the {tool.strip( )} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'StarChart'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class Congress( Fetcher ):
	'''

		Purpose:
		--------
		Fetches Congress.gov congress, bill, law, and report resources.

		Attributes:
		-----------
		api_key,
		base_url,
		url,
		params,
		mode,
		congress_number,
		bill_type,
		bill_number,
		law_type,
		law_number,
		report_type,
		report_number,
		offset,
		limit,
		sort,
		from_date_time,
		to_date_time,
		conference,
		agents,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_resolve_api_key(...): Performs the _resolve_api_key operation for this fetcher.
		_validate_limit(...): Performs the _validate_limit operation for this fetcher.
		_validate_offset(...): Performs the _validate_offset operation for this fetcher.
		_normalize_bill_type(...): Performs the _normalize_bill_type operation for this fetcher.
		_normalize_law_type(...): Performs the _normalize_law_type operation for this fetcher.
		_normalize_report_type(...): Performs the _normalize_report_type operation for this fetcher.
		_base_params(...): Performs the _base_params operation for this fetcher.
		fetch_congresses(...): Performs the fetch_congresses operation for this fetcher.
		fetch_bills(...): Performs the fetch_bills operation for this fetcher.
		fetch_bill(...): Performs the fetch_bill operation for this fetcher.
		fetch_laws(...): Performs the fetch_laws operation for this fetcher.
		fetch_law(...): Performs the fetch_law operation for this fetcher.
		fetch_reports(...): Performs the fetch_reports operation for this fetcher.
		fetch_report(...): Performs the fetch_report operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	api_key: Optional[ str ]
	base_url: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	mode: Optional[ str ]
	congress_number: Optional[ int ]
	bill_type: Optional[ str ]
	bill_number: Optional[ int ]
	law_type: Optional[ str ]
	law_number: Optional[ int ]
	report_type: Optional[ str ]
	report_number: Optional[ int ]
	offset: Optional[ int ]
	limit: Optional[ int ]
	sort: Optional[ str ]
	from_date_time: Optional[ str ]
	to_date_time: Optional[ str ]
	conference: Optional[ bool ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the Congress fetcher with current API defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.api_key = cfg.CONGRESS_API_KEY
		self.base_url = 'https://api.congress.gov/v3'
		self.url = None
		self.params = { }
		self.mode = 'congresses'
		self.congress_number = None
		self.bill_type = None
		self.bill_number = None
		self.law_type = None
		self.law_number = None
		self.report_type = None
		self.report_number = None
		self.offset = 0
		self.limit = 20
		self.sort = 'updateDate+desc'
		self.from_date_time = ''
		self.to_date_time = ''
		self.conference = False
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': cfg.AGENTS
		}
		self.agents = cfg.AGENTS
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'api_key',
				'base_url',
				'url',
				'params',
				'mode',
				'congress_number',
				'bill_type',
				'bill_number',
				'law_type',
				'law_number',
				'report_type',
				'report_number',
				'offset',
				'limit',
				'sort',
				'from_date_time',
				'to_date_time',
				'conference',
				'fetch_congresses',
				'fetch_bills',
				'fetch_bill',
				'fetch_laws',
				'fetch_law',
				'fetch_reports',
				'fetch_report',
				'fetch',
				'create_schema'
		]
	
	def _resolve_api_key( self ) -> str:
		'''
			Purpose:
			--------
			Resolve the Congress.gov API key.

			Parameters:
			-----------
			None

			Returns:
			--------
			str
		'''
		try:
			value = str( self.api_key or '' ).strip( )
			throw_if( 'CONGRESS_API_KEY', value )
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = '_resolve_api_key( self ) -> str'
			raise exception
	
	def _validate_limit( self, limit: int ) -> int:
		'''
			Purpose:
			--------
			Validate list request page size.

			Parameters:
			-----------
			limit (int):
				Page size.

			Returns:
			--------
			int
		'''
		try:
			value = int( limit )
			if value < 1 or value > 250:
				raise ValueError( 'limit must be between 1 and 250.' )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = '_validate_limit( self, limit: int ) -> int'
			raise exception
	
	def _validate_offset( self, offset: int ) -> int:
		'''
			Purpose:
			--------
			Validate list request offset.

			Parameters:
			-----------
			offset (int):
				Offset value.

			Returns:
			--------
			int
		'''
		try:
			value = int( offset )
			if value < 0:
				raise ValueError( 'offset must be greater than or equal to 0.' )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = '_validate_offset( self, offset: int ) -> int'
			raise exception
	
	def _normalize_bill_type( self, bill_type: str ) -> str:
		'''
			Purpose:
			--------
			Normalize bill type codes.

			Parameters:
			-----------
			bill_type (str):
				Bill type code.

			Returns:
			--------
			str
		'''
		try:
			value = str( bill_type or '' ).strip( ).lower( )
			throw_if( 'bill_type', value )
			
			allowed = {
					'hr', 's', 'hjres', 'sjres',
					'hconres', 'sconres', 'hres', 'sres'
			}
			
			if value not in allowed:
				raise ValueError(
					"Unsupported bill_type. Use hr, s, hjres, sjres, "
					"hconres, sconres, hres, or sres."
				)
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = '_normalize_bill_type( self, bill_type: str ) -> str'
			raise exception
	
	def _normalize_law_type( self, law_type: str ) -> str:
		'''
			Purpose:
			--------
			Normalize law type codes.

			Parameters:
			-----------
			law_type (str):
				Law type code.

			Returns:
			--------
			str
		'''
		try:
			value = str( law_type or '' ).strip( ).lower( )
			throw_if( 'law_type', value )
			
			allowed = { 'pub', 'priv' }
			
			if value not in allowed:
				raise ValueError( "Unsupported law_type. Use 'pub' or 'priv'." )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = '_normalize_law_type( self, law_type: str ) -> str'
			raise exception
	
	def _normalize_report_type( self, report_type: str ) -> str:
		'''
			Purpose:
			--------
			Normalize committee report type codes.

			Parameters:
			-----------
			report_type (str):
				Committee report type code.

			Returns:
			--------
			str
		'''
		try:
			value = str( report_type or '' ).strip( ).lower( )
			throw_if( 'report_type', value )
			
			allowed = { 'hrpt', 'srpt', 'erpt' }
			
			if value not in allowed:
				raise ValueError(
					"Unsupported report_type. Use 'hrpt', 'srpt', or 'erpt'."
				)
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = '_normalize_report_type( self, report_type: str ) -> str'
			raise exception
	
	def _base_params( self, limit: int=20, offset: int=0,
			sort: str='updateDate+desc' ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Construct shared list-query parameters.

			Parameters:
			-----------
			limit (int):
				Page size.

			offset (int):
				Result offset.

			sort (str):
				Sort directive.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			return {
					'api_key': self._resolve_api_key( ),
					'format': 'json',
					'limit': self._validate_limit( limit ),
					'offset': self._validate_offset( offset ),
					'sort': str( sort or 'updateDate+desc' ).strip( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'_base_params( self, limit: int=20, offset: int=0, '
					'sort: str=updateDate+desc ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_congresses( self, limit: int=20, offset: int=0,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the list of congresses and sessions.

			Parameters:
			-----------
			limit (int):
				Page size.

			offset (int):
				Result offset.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.url = f'{self.base_url}/congress'
			self.params = self._base_params(
				limit=limit,
				offset=offset,
				sort='updateDate+desc'
			)
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'congresses',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'fetch_congresses( self, limit: int=20, offset: int=0, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_bills( self, congress: int, bill_type: str='',
			offset: int=0, limit: int=20, from_date_time: str='',
			to_date_time: str='', sort: str='updateDate+desc',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch bills for a congress, optionally filtered by bill type.

			Parameters:
			-----------
			congress (int):
				Congress number.

			bill_type (str):
				Optional bill type code.

			offset (int):
				Result offset.

			limit (int):
				Page size.

			from_date_time (str):
				Optional ISO timestamp filter.

			to_date_time (str):
				Optional ISO timestamp filter.

			sort (str):
				Sort directive.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'congress', congress )
			
			self.congress_number = int( congress )
			self.bill_type = str( bill_type or '' ).strip( ).lower( )
			
			if self.bill_type:
				self.bill_type = self._normalize_bill_type( self.bill_type )
				self.url = f'{self.base_url}/bill/{self.congress_number}/{self.bill_type}'
			else:
				self.url = f'{self.base_url}/bill/{self.congress_number}'
			
			self.params = self._base_params(
				limit=limit,
				offset=offset,
				sort=sort
			)
			
			if from_date_time:
				self.params[ 'fromDateTime' ]=str( from_date_time ).strip( )
			
			if to_date_time:
				self.params[ 'toDateTime' ]=str( to_date_time ).strip( )
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'bills',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'fetch_bills( self, congress: int, bill_type: str=, '
					'offset: int=0, limit: int=20, from_date_time: str=, '
					'to_date_time: str=, sort: str=updateDate+desc, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_bill( self, congress: int, bill_type: str,
			bill_number: int, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch a specific bill by congress, bill type, and bill number.

			Parameters:
			-----------
			congress (int):
				Congress number.

			bill_type (str):
				Bill type code.

			bill_number (int):
				Bill number.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'congress', congress )
			throw_if( 'bill_type', bill_type )
			throw_if( 'bill_number', bill_number )
			
			self.congress_number = int( congress )
			self.bill_type = self._normalize_bill_type( bill_type )
			self.bill_number = int( bill_number )
			
			self.url = (
					f'{self.base_url}/bill/{self.congress_number}/'
					f'{self.bill_type}/{self.bill_number}'
			)
			self.params = {
					'api_key': self._resolve_api_key( ),
					'format': 'json'
			}
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'bill_detail',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'fetch_bill( self, congress: int, bill_type: str, '
					'bill_number: int, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_laws( self, congress: int, law_type: str='',
			offset: int=0, limit: int=20,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch laws for a congress, optionally filtered by law type.

			Parameters:
			-----------
			congress (int):
				Congress number.

			law_type (str):
				Optional law type code: pub or priv.

			offset (int):
				Result offset.

			limit (int):
				Page size.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'congress', congress )
			
			self.congress_number = int( congress )
			self.law_type = str( law_type or '' ).strip( ).lower( )
			
			if self.law_type:
				self.law_type = self._normalize_law_type( self.law_type )
				self.url = f'{self.base_url}/law/{self.congress_number}/{self.law_type}'
			else:
				self.url = f'{self.base_url}/law/{self.congress_number}'
			
			self.params = self._base_params(
				limit=limit,
				offset=offset,
				sort='updateDate+desc'
			)
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'laws',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'fetch_laws( self, congress: int, law_type: str=, '
					'offset: int=0, limit: int=20, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_law( self, congress: int, law_type: str,
			law_number: int, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch a specific law by congress, law type, and law number.

			Parameters:
			-----------
			congress (int):
				Congress number.

			law_type (str):
				Law type code: pub or priv.

			law_number (int):
				Law number.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'congress', congress )
			throw_if( 'law_type', law_type )
			throw_if( 'law_number', law_number )
			
			self.congress_number = int( congress )
			self.law_type = self._normalize_law_type( law_type )
			self.law_number = int( law_number )
			
			self.url = (
					f'{self.base_url}/law/{self.congress_number}/'
					f'{self.law_type}/{self.law_number}'
			)
			self.params = {
					'api_key': self._resolve_api_key( ),
					'format': 'json'
			}
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'law_detail',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'fetch_law( self, congress: int, law_type: str, '
					'law_number: int, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_reports( self, congress: int, report_type: str='',
			offset: int=0, limit: int=20, conference: bool=False,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch committee reports for a congress, optionally filtered by
			report type.

			Parameters:
			-----------
			congress (int):
				Congress number.

			report_type (str):
				Optional report type code: hrpt, srpt, or erpt.

			offset (int):
				Result offset.

			limit (int):
				Page size.

			conference (bool):
				Whether to request conference reports where supported.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'congress', congress )
			
			self.congress_number = int( congress )
			self.report_type = str( report_type or '' ).strip( ).lower( )
			self.conference = bool( conference )
			
			if self.report_type:
				self.report_type = self._normalize_report_type( self.report_type )
				self.url = (
						f'{self.base_url}/committee-report/'
						f'{self.congress_number}/{self.report_type}'
				)
			else:
				self.url = f'{self.base_url}/committee-report/{self.congress_number}'
			
			self.params = self._base_params(
				limit=limit,
				offset=offset,
				sort='updateDate+desc'
			)
			self.params[ 'conference' ]=str( self.conference ).lower( )
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'reports',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'fetch_reports( self, congress: int, report_type: str=, '
					'offset: int=0, limit: int=20, conference: bool=False, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_report( self, congress: int, report_type: str,
			report_number: int, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch a specific committee report.

			Parameters:
			-----------
			congress (int):
				Congress number.

			report_type (str):
				Report type code.

			report_number (int):
				Report number.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'congress', congress )
			throw_if( 'report_type', report_type )
			throw_if( 'report_number', report_number )
			
			self.congress_number = int( congress )
			self.report_type = self._normalize_report_type( report_type )
			self.report_number = int( report_number )
			
			self.url = (
					f'{self.base_url}/committee-report/{self.congress_number}/'
					f'{self.report_type}/{self.report_number}'
			)
			self.params = {
					'api_key': self._resolve_api_key( ),
					'format': 'json'
			}
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			return {
					'mode': 'report_detail',
					'url': self.url,
					'params': self.params,
					'data': self.response.json( )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'fetch_report( self, congress: int, report_type: str, '
					'report_number: int, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='congresses', congress: int=0,
			bill_type: str='', bill_number: int=0, law_type: str='',
			law_number: int=0, report_type: str='',
			report_number: int=0, offset: int=0, limit: int=20,
			sort: str='updateDate+desc', from_date_time: str='',
			to_date_time: str='', conference: bool=False,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for Congress.gov requests.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- congresses
				- bills
				- bill_detail
				- laws
				- law_detail
				- reports
				- report_detail

			congress (int):
				Congress number for congress-scoped modes.

			bill_type (str):
				Bill type code for bill modes.

			bill_number (int):
				Bill number for bill_detail mode.

			law_type (str):
				Law type code for law modes.

			law_number (int):
				Law number for law_detail mode.

			report_type (str):
				Report type code for report modes.

			report_number (int):
				Report number for report_detail mode.

			offset (int):
				Result offset for list modes.

			limit (int):
				Page size for list modes.

			sort (str):
				Sort directive for bill list modes.

			from_date_time (str):
				Optional ISO timestamp for bill list mode.

			to_date_time (str):
				Optional ISO timestamp for bill list mode.

			conference (bool):
				Conference report filter for report list mode.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'congresses' ).strip( ).lower( )
			
			if active_mode == 'congresses':
				return self.fetch_congresses(
					limit=limit,
					offset=offset,
					time=time
				)
			
			if active_mode == 'bills':
				return self.fetch_bills(
					congress=congress,
					bill_type=bill_type,
					offset=offset,
					limit=limit,
					from_date_time=from_date_time,
					to_date_time=to_date_time,
					sort=sort,
					time=time
				)
			
			if active_mode == 'bill_detail':
				return self.fetch_bill(
					congress=congress,
					bill_type=bill_type,
					bill_number=bill_number,
					time=time
				)
			
			if active_mode == 'laws':
				return self.fetch_laws(
					congress=congress,
					law_type=law_type,
					offset=offset,
					limit=limit,
					time=time
				)
			
			if active_mode == 'law_detail':
				return self.fetch_law(
					congress=congress,
					law_type=law_type,
					law_number=law_number,
					time=time
				)
			
			if active_mode == 'reports':
				return self.fetch_reports(
					congress=congress,
					report_type=report_type,
					offset=offset,
					limit=limit,
					conference=conference,
					time=time
				)
			
			if active_mode == 'report_detail':
				return self.fetch_report(
					congress=congress,
					report_type=report_type,
					report_number=report_number,
					time=time
				)
			
			raise ValueError(
				"Unsupported mode. Use one of: congresses, bills, bill_detail, "
				"laws, law_detail, reports, report_detail."
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'fetch( self, mode: str=congresses, congress: int=0, '
					'bill_type: str=, bill_number: int=0, law_type: str=, '
					'law_number: int=0, report_type: str=, report_number: int=0, '
					'offset: int=0, limit: int=20, sort: str=updateDate+desc, '
					'from_date_time: str=, to_date_time: str=, '
					'conference: bool=False, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f'{description.strip( )} '
							f'This function uses the {tool.strip( )} service.'
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Congress'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class InternetArchive( Fetcher ):
	'''
	
		Purpose:
		--------
		Fetches Internet Archive search records.
	
		Attributes:
		-----------
		keywords,
		url,
		response,
		fields,
		rows,
		page,
		sort,
		media_type,
		collection,
		params,
		agents,
	
		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_validate_rows(...): Performs the _validate_rows operation for this fetcher.
		_validate_page(...): Performs the _validate_page operation for this fetcher.
		_build_query(...): Performs the _build_query operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.
	
	'''
	keywords: Optional[ str ]
	url: Optional[ str ]
	response: Optional[ Response ]
	fields: Optional[ List[ str ] ]
	rows: Optional[ int ]
	page: Optional[ int ]
	sort: Optional[ str ]
	media_type: Optional[ str ]
	collection: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the Internet Archive wrapper with sane defaults.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.url = 'https://archive.org/advancedsearch.php'
		self.headers = { }
		self.timeout = 20
		self.keywords = ''
		self.params = { }
		self.fields = [
				'identifier',
				'title',
				'creator',
				'mediatype',
				'collection',
				'publicdate',
				'description'
		]
		self.rows = 10
		self.page = 1
		self.sort = 'downloads desc'
		self.media_type = ''
		self.collection = ''
		self.response = None
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		if 'Accept' not in self.headers:
			self.headers[ 'Accept' ]='application/json'
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'keywords',
				'url',
				'timeout',
				'headers',
				'fields',
				'rows',
				'page',
				'sort',
				'media_type',
				'collection',
				'params',
				'agents',
				'fetch',
				'create_schema'
		]
	
	def _validate_rows( self, rows: int ) -> int:
		'''
			Purpose:
			--------
			Validate requested page size.

			Parameters:
			-----------
			rows (int):
				Requested number of results.

			Returns:
			--------
			int
		'''
		try:
			value = int( rows )
			if value < 1 or value > 100:
				raise ValueError( 'rows must be between 1 and 100.' )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'InternetArchive'
			exception.method = '_validate_rows( self, rows: int ) -> int'
			raise exception
	
	def _validate_page( self, page: int ) -> int:
		'''
			Purpose:
			--------
			Validate requested page number.

			Parameters:
			-----------
			page (int):
				Requested page number.

			Returns:
			--------
			int
		'''
		try:
			value = int( page )
			if value < 1:
				raise ValueError( 'page must be greater than or equal to 1.' )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'InternetArchive'
			exception.method = '_validate_page( self, page: int ) -> int'
			raise exception
	
	def _build_query( self, keywords: str, media_type: str='',
			collection: str='' ) -> str:
		'''
			Purpose:
			--------
			Build an Internet Archive advanced search query expression.

			Parameters:
			-----------
			keywords (str):
				Base free-text query.

			media_type (str):
				Optional mediatype filter.

			collection (str):
				Optional collection filter.

			Returns:
			--------
			str
		'''
		try:
			throw_if( 'keywords', keywords )
			
			parts: List[ str ]=[ f'({str( keywords ).strip( )})' ]
			
			if media_type and str( media_type ).strip( ):
				parts.append( f'AND mediatype:({str( media_type ).strip( )})' )
			
			if collection and str( collection ).strip( ):
				parts.append( f'AND collection:({str( collection ).strip( )})' )
			
			return ' '.join( parts )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'InternetArchive'
			exception.method = (
					'_build_query( self, keywords: str, media_type: str=, '
					'collection: str= ) -> str'
			)
			raise exception
	
	def fetch( self, keywords: str, fields: List[ str ] | None=None,
			rows: int=10, page: int=1, sort: str='downloads desc',
			media_type: str='', collection: str='',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Execute an Internet Archive advanced search request.

			Parameters:
			-----------
			keywords (str):
				Free-text Internet Archive query.

			fields (List[str] | None):
				Optional list of result fields to request.

			rows (int):
				Number of results per page.

			page (int):
				Page number.

			sort (str):
				Archive sort directive such as downloads desc or publicdate desc.

			media_type (str):
				Optional media type filter.

			collection (str):
				Optional collection filter.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.keywords = str( keywords ).strip( )
			throw_if( 'keywords', self.keywords )
			
			self.timeout = int( time )
			self.rows = self._validate_rows( rows )
			self.page = self._validate_page( page )
			self.sort = str( sort or 'downloads desc' ).strip( )
			self.media_type = str( media_type or '' ).strip( )
			self.collection = str( collection or '' ).strip( )
			
			active_fields = fields if fields else self.fields
			if not isinstance( active_fields, list ) or not active_fields:
				raise ValueError( 'fields must be a non-empty list of field names.' )
			
			query_text = self._build_query(
				keywords=self.keywords,
				media_type=self.media_type,
				collection=self.collection
			)
			
			self.params = {
					'q': query_text,
					'fl[]': active_fields,
					'rows': self.rows,
					'page': self.page,
					'sort[]': self.sort,
					'output': 'json'
			}
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=self.timeout
			)
			self.response.raise_for_status( )
			
			payload = self.response.json( ) or { }
			
			return {
					'mode': 'advanced_search',
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'InternetArchive'
			exception.method = (
					'fetch( self, keywords: str, fields: List[ str ] | None=None, '
					'rows: int=10, page: int=1, sort: str=downloads desc, '
					'media_type: str=, collection: str=, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f'{description.strip( )} '
							f'This function uses the {tool.strip( )} service.'
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'InternetArchive'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class OpenWeather( Fetcher ):
	'''

		Purpose:
		--------
		Provides forecast weather retrieval by location name using the Open-Meteo
		Geocoding API and Open-Meteo Forecast API.

		This class is forecast-only by design and intentionally excludes archive /
		historical date-based retrieval so it does not overlap with the separate
		HistoricalWeather class.

		Referenced API Requirements:
		----------------------------
		Geocoding API:
			- Endpoint: https://geocoding-api.open-meteo.com/v1/search
			- Required parameter: name
			- Optional parameter: count

		Forecast API:
			- Endpoint: https://api.open-meteo.com/v1/forecast
			- Required parameters: latitude, longitude
			- Optional parameters used here:
				- current
				- hourly
				- daily
				- timezone
				- forecast_days
				- past_days
				- temperature_unit
				- wind_speed_unit
				- precipitation_unit

		Attributes:
		-----------
		geocode_url: Optional[str]
			The Open-Meteo geocoding endpoint.

		forecast_url: Optional[str]
			The Open-Meteo forecast endpoint.

		location: Optional[str]
			User-supplied location query.

		latitude: Optional[float]
			Resolved latitude from geocoding.

		longitude: Optional[float]
			Resolved longitude from geocoding.

		timezone: Optional[str]
			Resolved or user-requested timezone.

		mode: Optional[str]
			Forecast mode: current, hourly, or daily.

		current_metrics: Optional[List[str]]
			Current weather metrics requested from the API.

		hourly_metrics: Optional[List[str]]
			Hourly metrics requested from the API.

		daily_metrics: Optional[List[str]]
			Daily metrics requested from the API.

		windspeed_unit: Optional[str]
			Wind speed unit passed to the API.

		temperature_unit: Optional[str]
			Temperature unit passed to the API.

		precipitation_unit: Optional[str]
			Precipitation unit passed to the API.

		params: Optional[Dict[str, Any]]
			Request parameters for the forecast call.

		geocode_params: Optional[Dict[str, Any]]
			Request parameters for the geocoding call.

		result_limit: Optional[int]
			Maximum number of geocoding candidates to request.

		Methods:
		--------
		__init__() -> None
			Initialize the fetcher and default metric sets.

		__dir__() -> List[str]
			Provide ordered member visibility.

		geocode_location(...) -> Dict[str, Any] | None
			Resolve a place name into a selected geocoding record.

		fetch(...) -> Dict[str, Any] | None
			Resolve a location string and retrieve forecast weather.

		fetch_current(...) -> Dict[str, Any] | None
			Retrieve current forecast conditions only.

		fetch_hourly(...) -> Dict[str, Any] | None
			Retrieve hourly forecast data.

		fetch_daily(...) -> Dict[str, Any] | None
			Retrieve daily forecast data.

		create_schema(...) -> Dict[str, str] | None
			Generate a dynamic tool schema definition.

	'''
	geocode_url: Optional[ str ]
	forecast_url: Optional[ str ]
	location: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	timezone: Optional[ str ]
	mode: Optional[ str ]
	current_metrics: Optional[ List[ str ] ]
	hourly_metrics: Optional[ List[ str ] ]
	daily_metrics: Optional[ List[ str ] ]
	windspeed_unit: Optional[ str ]
	temperature_unit: Optional[ str ]
	precipitation_unit: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	geocode_params: Optional[ Dict[ str, Any ] ]
	result_limit: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''

			Purpose:
			--------
			Initialize the OpenWeather forecast fetcher with forecast-only defaults,
			endpoints, headers, unit selections, and metric collections.

			Parameters:
			-----------
			None

			Returns:
			--------
			None

		'''
		super( ).__init__( )
		self.headers = { }
		self.agents = cfg.AGENTS
		self.location = None
		self.latitude = None
		self.longitude = None
		self.timezone = 'auto'
		self.mode = 'current'
		self.result_limit = 10
		self.geocode_url = 'https://geocoding-api.open-meteo.com/v1/search'
		self.forecast_url = 'https://api.open-meteo.com/v1/forecast'
		self.temperature_unit = 'fahrenheit'
		self.windspeed_unit = 'kn'
		self.precipitation_unit = 'inch'
		self.geocode_params = None
		self.params = None
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		self.current_metrics = [
				'temperature_2m',
				'relative_humidity_2m',
				'apparent_temperature',
				'is_day',
				'precipitation',
				'rain',
				'showers',
				'snowfall',
				'weather_code',
				'cloud_cover',
				'pressure_msl',
				'surface_pressure',
				'wind_speed_10m',
				'wind_direction_10m',
				'wind_gusts_10m'
		]
		
		self.hourly_metrics = [
				'temperature_2m',
				'relative_humidity_2m',
				'apparent_temperature',
				'precipitation_probability',
				'precipitation',
				'rain',
				'showers',
				'snowfall',
				'weather_code',
				'cloud_cover',
				'pressure_msl',
				'surface_pressure',
				'visibility',
				'wind_speed_10m',
				'wind_direction_10m',
				'wind_gusts_10m'
		]
		
		self.daily_metrics = [
				'weather_code',
				'temperature_2m_max',
				'temperature_2m_min',
				'apparent_temperature_max',
				'apparent_temperature_min',
				'sunrise',
				'sunset',
				'daylight_duration',
				'sunshine_duration',
				'precipitation_sum',
				'rain_sum',
				'showers_sum',
				'snowfall_sum',
				'precipitation_hours',
				'precipitation_probability_max',
				'wind_speed_10m_max',
				'wind_gusts_10m_max',
				'wind_direction_10m_dominant'
		]
	
	def __dir__( self ) -> List[ str ]:
		'''

			Purpose:
			--------
			Provide ordered member visibility for introspection and editor discovery.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]:
				Ordered attribute and method names.

		'''
		return [
				'geocode_url',
				'forecast_url',
				'location',
				'latitude',
				'longitude',
				'timezone',
				'mode',
				'current_metrics',
				'hourly_metrics',
				'daily_metrics',
				'windspeed_unit',
				'temperature_unit',
				'precipitation_unit',
				'params',
				'geocode_params',
				'result_limit',
				'geocode_location',
				'fetch',
				'fetch_current',
				'fetch_hourly',
				'fetch_daily',
				'create_schema'
		]
	
	def geocode_location( self, location: str, count: int=10 ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Resolve a user-supplied location string into a geocoding result from
			the Open-Meteo Geocoding API.

			Parameters:
			-----------
			location (str):
				The place name or postal code to search for.

			count (int):
				The maximum number of geocoding matches to request.

			Returns:
			--------
			Dict[str, Any] | None:
				The selected geocoding record, typically the first result.

		'''
		try:
			throw_if( 'location', location )
			self.location = location.strip( )
			self.geocode_params = {
					'name': self.location,
					'count': int( count )
			}
			
			self.url = self.geocode_url
			self.response = requests.get(
				self.url,
				params=self.geocode_params,
				headers=self.headers,
				timeout=20
			)
			self.response.raise_for_status( )
			
			payload = self.response.json( ) or { }
			results = payload.get( 'results', [ ] ) or [ ]
			
			if not results:
				return None
			
			selected = results[ 0 ]
			self.latitude = selected.get( 'latitude', None )
			self.longitude = selected.get( 'longitude', None )
			
			resolved_timezone = selected.get( 'timezone', None )
			if resolved_timezone:
				self.timezone = resolved_timezone
			
			return selected
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenWeather'
			exception.method = (
					'geocode_location( self, location: str, count: int=10 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_current( self, lat: float, long: float, zone: str='auto',
			past_days: int=0 ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Retrieve current forecast conditions for a coordinate pair.

			Parameters:
			-----------
			lat (float):
				The latitude of the resolved location.

			long (float):
				The longitude of the resolved location.

			zone (str):
				The timezone for the response. Supports 'auto'.

			past_days (int):
				Optional number of previous days to include when supported by
				the forecast API.

			Returns:
			--------
			Dict[str, Any] | None:
				Normalized forecast response containing current conditions.

		'''
		try:
			throw_if( 'lat', lat )
			throw_if( 'long', long )
			throw_if( 'zone', zone )
			
			self.mode = 'current'
			self.latitude = float( lat )
			self.longitude = float( long )
			self.timezone = str( zone or 'auto' ).strip( )
			
			self.params = {
					'latitude': self.latitude,
					'longitude': self.longitude,
					'current': self.current_metrics,
					'timezone': self.timezone,
					'temperature_unit': self.temperature_unit,
					'wind_speed_unit': self.windspeed_unit,
					'precipitation_unit': self.precipitation_unit,
					'past_days': int( past_days )
			}
			
			self.url = self.forecast_url
			self.response = requests.get(
				self.url,
				params=self.params,
				headers=self.headers,
				timeout=30
			)
			self.response.raise_for_status( )
			
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'location': self.location,
					'latitude': payload.get( 'latitude', self.latitude ),
					'longitude': payload.get( 'longitude', self.longitude ),
					'timezone': payload.get( 'timezone', self.timezone ),
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenWeather'
			exception.method = (
					'fetch_current( self, lat: float, long: float, zone: str=auto, '
					'past_days: int=0 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_hourly( self, lat: float, long: float, zone: str='auto',
			forecast_days: int=7, past_days: int=0 ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Retrieve hourly forecast data for a coordinate pair.

			Parameters:
			-----------
			lat (float):
				The latitude of the resolved location.

			long (float):
				The longitude of the resolved location.

			zone (str):
				The timezone for the response. Supports 'auto'.

			forecast_days (int):
				Number of forecast days to request.

			past_days (int):
				Optional number of previous days to include.

			Returns:
			--------
			Dict[str, Any] | None:
				Normalized forecast response containing hourly data.

		'''
		try:
			throw_if( 'lat', lat )
			throw_if( 'long', long )
			throw_if( 'zone', zone )
			
			self.mode = 'hourly'
			self.latitude = float( lat )
			self.longitude = float( long )
			self.timezone = str( zone or 'auto' ).strip( )
			
			self.params = {
					'latitude': self.latitude,
					'longitude': self.longitude,
					'hourly': self.hourly_metrics,
					'timezone': self.timezone,
					'forecast_days': int( forecast_days ),
					'past_days': int( past_days ),
					'temperature_unit': self.temperature_unit,
					'wind_speed_unit': self.windspeed_unit,
					'precipitation_unit': self.precipitation_unit
			}
			
			self.url = self.forecast_url
			self.response = requests.get(
				self.url,
				params=self.params,
				headers=self.headers,
				timeout=30
			)
			self.response.raise_for_status( )
			
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'location': self.location,
					'latitude': payload.get( 'latitude', self.latitude ),
					'longitude': payload.get( 'longitude', self.longitude ),
					'timezone': payload.get( 'timezone', self.timezone ),
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenWeather'
			exception.method = (
					'fetch_hourly( self, lat: float, long: float, zone: str=auto, '
					'forecast_days: int=7, past_days: int=0 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_daily( self, lat: float, long: float, zone: str='auto',
			forecast_days: int=7, past_days: int=0 ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Retrieve daily forecast data for a coordinate pair.

			Parameters:
			-----------
			lat (float):
				The latitude of the resolved location.

			long (float):
				The longitude of the resolved location.

			zone (str):
				The timezone for the response. Supports 'auto'.

			forecast_days (int):
				Number of forecast days to request.

			past_days (int):
				Optional number of previous days to include.

			Returns:
			--------
			Dict[str, Any] | None:
				Normalized forecast response containing daily data.

		'''
		try:
			throw_if( 'lat', lat )
			throw_if( 'long', long )
			throw_if( 'zone', zone )
			
			self.mode = 'daily'
			self.latitude = float( lat )
			self.longitude = float( long )
			self.timezone = str( zone or 'auto' ).strip( )
			
			self.params = {
					'latitude': self.latitude,
					'longitude': self.longitude,
					'daily': self.daily_metrics,
					'timezone': self.timezone,
					'forecast_days': int( forecast_days ),
					'past_days': int( past_days ),
					'temperature_unit': self.temperature_unit,
					'wind_speed_unit': self.windspeed_unit,
					'precipitation_unit': self.precipitation_unit
			}
			
			self.url = self.forecast_url
			self.response = requests.get(
				self.url,
				params=self.params,
				headers=self.headers,
				timeout=30
			)
			self.response.raise_for_status( )
			
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'location': self.location,
					'latitude': payload.get( 'latitude', self.latitude ),
					'longitude': payload.get( 'longitude', self.longitude ),
					'timezone': payload.get( 'timezone', self.timezone ),
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenWeather'
			exception.method = (
					'fetch_daily( self, lat: float, long: float, zone: str=auto, '
					'forecast_days: int=7, past_days: int=0 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, location: str, mode: str='current', zone: str='auto',
			forecast_days: int=7, past_days: int=0,
			count: int=10 ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Resolve a location string to coordinates, then retrieve forecast weather
			using the selected non-historical mode.

			Parameters:
			-----------
			location (str):
				The place name entered by the user.

			mode (str):
				Forecast mode. Supported values are current, hourly, and daily.

			zone (str):
				The timezone requested for the forecast response. If 'auto', the API
				will resolve the local timezone for the coordinates.

			forecast_days (int):
				Number of forecast days to request for hourly and daily modes.

			past_days (int):
				Optional number of previous days to include.

			count (int):
				Maximum number of geocoding matches to request before selecting the
				first result.

			Returns:
			--------
			Dict[str, Any] | None:
				Combined geocoding and forecast result.

		'''
		try:
			throw_if( 'location', location )
			throw_if( 'mode', mode )
			throw_if( 'zone', zone )
			
			selected = self.geocode_location( location=location, count=count )
			
			if not selected:
				return {
						'location': location,
						'mode': mode,
						'message': 'No geocoding results found.',
						'data': { }
				}
			
			lat = selected.get( 'latitude', None )
			long = selected.get( 'longitude', None )
			
			if lat is None or long is None:
				return {
						'location': location,
						'mode': mode,
						'message': 'Geocoding returned no usable coordinates.',
						'geocoding': selected,
						'data': { }
				}
			
			active_mode = str( mode ).strip( ).lower( )
			if active_mode == 'current':
				result = self.fetch_current(
					lat=float( lat ),
					long=float( long ),
					zone=str( zone or 'auto' ).strip( ),
					past_days=int( past_days )
				) or { }
			
			elif active_mode == 'hourly':
				result = self.fetch_hourly(
					lat=float( lat ),
					long=float( long ),
					zone=str( zone or 'auto' ).strip( ),
					forecast_days=int( forecast_days ),
					past_days=int( past_days )
				) or { }
			
			elif active_mode == 'daily':
				result = self.fetch_daily(
					lat=float( lat ),
					long=float( long ),
					zone=str( zone or 'auto' ).strip( ),
					forecast_days=int( forecast_days ),
					past_days=int( past_days )
				) or { }
			
			else:
				raise ValueError(
					"Unsupported mode. Use 'current', 'hourly', or 'daily'."
				)
			
			result[ 'geocoding' ]=selected
			return result
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenWeather'
			exception.method = (
					'fetch( self, location: str, mode: str=current, zone: str=auto, '
					'forecast_days: int=7, past_days: int=0, count: int=10 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''

			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None:
				A JSON-compatible dictionary defining the tool schema.

		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': f"{description.strip( )} This function uses the {tool.strip( )} service.",
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenWeather'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class HistoricalWeather( Fetcher ):
	'''

		Purpose:
		--------
		Provides historical weather retrieval by location name and date using the
		Open-Meteo Geocoding API and Open-Meteo Historical Weather API.

		This class is intentionally designed around the actual user-facing need in
		the Foo fetcher expander: enter a location and a date, resolve that location
		to coordinates, then retrieve historical weather for that date.

		Referenced API Requirements:
		----------------------------
		Geocoding API:
			- Endpoint: https://geocoding-api.open-meteo.com/v1/search
			- Required parameter: name
			- Optional parameter: count

		Historical Weather API:
			- Endpoint: https://archive-api.open-meteo.com/v1/archive
			- Required parameters: latitude, longitude, start_date, end_date
			- Optional parameters used here:
				- timezone
				- daily
				- hourly
				- temperature_unit
				- wind_speed_unit
				- precipitation_unit

		Attributes:
		-----------
		geocode_url: Optional[str]
			The Open-Meteo geocoding endpoint.

		archive_url: Optional[str]
			The Open-Meteo historical weather endpoint.

		location: Optional[str]
			User-supplied location query.

		latitude: Optional[float]
			Resolved latitude from geocoding.

		longitude: Optional[float]
			Resolved longitude from geocoding.

		timezone: Optional[str]
			Resolved or user-requested timezone. Defaults to 'auto'.

		target_date: Optional[dt.date]
			The requested historical date.

		daily_metrics: Optional[List[str]]
			Daily historical metrics requested from the archive API.

		hourly_metrics: Optional[List[str]]
			Hourly historical metrics requested from the archive API.

		windspeed_unit: Optional[str]
			Wind speed unit passed to the API.

		temperature_unit: Optional[str]
			Temperature unit passed to the API.

		precipitation_unit: Optional[str]
			Precipitation unit passed to the API.

		params: Optional[Dict[str, Any]]
			Request parameters for the historical weather call.

		geocode_params: Optional[Dict[str, Any]]
			Request parameters for the geocoding call.

		result_limit: Optional[int]
			Maximum number of geocoding candidates to request.

		Methods:
		--------
		__init__() -> None
			Initialize the fetcher and default metrics.

		__dir__() -> List[str]
			Provide ordered introspection members.

		fetch(...) -> Dict[str, Any] | None
			Resolve a location string and retrieve historical weather for one date.

		geocode_location(...) -> Dict[str, Any] | None
			Resolve a place name into a selected geocoding record.

		fetch_historical(...) -> Dict[str, Any] | None
			Retrieve historical weather for resolved coordinates and a date.

		create_schema(...) -> Dict[str, str] | None
			Generate a dynamic tool schema definition.

	'''
	geocode_url: Optional[ str ]
	archive_url: Optional[ str ]
	location: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	timezone: Optional[ str ]
	target_date: Optional[ dt.date ]
	daily_metrics: Optional[ List[ str ] ]
	hourly_metrics: Optional[ List[ str ] ]
	windspeed_unit: Optional[ str ]
	temperature_unit: Optional[ str ]
	precipitation_unit: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	geocode_params: Optional[ Dict[ str, Any ] ]
	result_limit: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''

			Purpose:
			--------
			Initialize the HistoricalWeather fetcher with default endpoints,
			request headers, metric collections, and unit selections.

			Parameters:
			-----------
			None

			Returns:
			--------
			None

		'''
		super( ).__init__( )
		self.headers = { }
		self.agents = cfg.AGENTS
		self.location = None
		self.latitude = None
		self.longitude = None
		self.timezone = 'auto'
		self.target_date = None
		self.result_limit = 10
		self.geocode_url = 'https://geocoding-api.open-meteo.com/v1/search'
		self.archive_url = 'https://archive-api.open-meteo.com/v1/archive'
		self.temperature_unit = 'fahrenheit'
		self.windspeed_unit = 'kn'
		self.precipitation_unit = 'inch'
		self.geocode_params = None
		self.params = None
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ]=self.agents
		
		self.daily_metrics = [
				'weather_code',
				'temperature_2m_max',
				'temperature_2m_min',
				'apparent_temperature_max',
				'apparent_temperature_min',
				'sunrise',
				'sunset',
				'daylight_duration',
				'sunshine_duration',
				'precipitation_sum',
				'rain_sum',
				'showers_sum',
				'snowfall_sum',
				'precipitation_hours',
				'wind_speed_10m_max',
				'wind_gusts_10m_max',
				'wind_direction_10m_dominant'
		]
		
		self.hourly_metrics = [
				'temperature_2m',
				'relative_humidity_2m',
				'apparent_temperature',
				'precipitation',
				'rain',
				'showers',
				'snowfall',
				'weather_code',
				'cloud_cover',
				'pressure_msl',
				'surface_pressure',
				'wind_speed_10m',
				'wind_direction_10m',
				'wind_gusts_10m'
		]
	
	def __dir__( self ) -> List[ str ]:
		'''

			Purpose:
			--------
			Provide ordered member visibility for introspection and editor discovery.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]:
				Ordered attribute and method names.

		'''
		return [
				'geocode_url',
				'archive_url',
				'location',
				'latitude',
				'longitude',
				'timezone',
				'target_date',
				'daily_metrics',
				'hourly_metrics',
				'windspeed_unit',
				'temperature_unit',
				'precipitation_unit',
				'params',
				'geocode_params',
				'result_limit',
				'fetch',
				'geocode_location',
				'fetch_historical',
				'create_schema'
		]
	
	def geocode_location( self, location: str, count: int=10 ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Resolve a user-supplied location string into a geocoding result from
			the Open-Meteo Geocoding API.

			Parameters:
			-----------
			location (str):
				The place name or postal code to search for.

			count (int):
				The maximum number of geocoding matches to request.

			Returns:
			--------
			Dict[str, Any] | None:
				The selected geocoding record, typically the first result.

		'''
		try:
			throw_if( 'location', location )
			self.location = location.strip( )
			self.geocode_params = {
					'name': self.location,
					'count': int( count )
			}
			
			self.url = self.geocode_url
			self.response = requests.get(
				self.url,
				params=self.geocode_params,
				headers=self.headers,
				timeout=20
			)
			self.response.raise_for_status( )
			
			payload = self.response.json( ) or { }
			results = payload.get( 'results', [ ] ) or [ ]
			
			if not results:
				return None
			
			selected = results[ 0 ]
			self.latitude = selected.get( 'latitude', None )
			self.longitude = selected.get( 'longitude', None )
			
			resolved_timezone = selected.get( 'timezone', None )
			if resolved_timezone:
				self.timezone = resolved_timezone
			
			return selected
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HistoricalWeather'
			exception.method = (
					'geocode_location( self, location: str, count: int=10 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_historical( self, lat: float, long: float, date: dt.date,
			zone: str='auto' ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Retrieve historical weather for a single date using the Open-Meteo
			Historical Weather API.

			Parameters:
			-----------
			lat (float):
				The latitude of the resolved location.

			long (float):
				The longitude of the resolved location.

			date (dt.date):
				The requested historical date. This is used for both start_date
				and end_date so the response is limited to that day.

			zone (str):
				The timezone to use in the response. Supports 'auto'.

			Returns:
			--------
			Dict[str, Any] | None:
				Normalized response payload including request metadata, selected
				location metadata, and archive data.

		'''
		try:
			throw_if( 'lat', lat )
			throw_if( 'long', long )
			throw_if( 'date', date )
			throw_if( 'zone', zone )
			
			self.latitude = float( lat )
			self.longitude = float( long )
			self.target_date = date
			self.timezone = zone.strip( ) if zone else 'auto'
			
			self.params = {
					'latitude': self.latitude,
					'longitude': self.longitude,
					'start_date': self.target_date.isoformat( ),
					'end_date': self.target_date.isoformat( ),
					'timezone': self.timezone,
					'daily': self.daily_metrics,
					'hourly': self.hourly_metrics,
					'temperature_unit': self.temperature_unit,
					'wind_speed_unit': self.windspeed_unit,
					'precipitation_unit': self.precipitation_unit
			}
			
			self.url = self.archive_url
			self.response = requests.get(
				self.url,
				params=self.params,
				headers=self.headers,
				timeout=30
			)
			self.response.raise_for_status( )
			
			payload = self.response.json( ) or { }
			
			return {
					'location': self.location,
					'latitude': self.latitude,
					'longitude': self.longitude,
					'timezone': payload.get( 'timezone', self.timezone ),
					'date': self.target_date.isoformat( ),
					'url': self.url,
					'params': self.params,
					'data': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HistoricalWeather'
			exception.method = (
					'fetch_historical( self, lat: float, long: float, date: dt.date, '
					'zone: str=auto ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, location: str, date: dt.date,
			zone: str='auto', count: int=10 ) -> Dict[ str, Any ] | None:
		'''

			Purpose:
			--------
			Resolve a location string to coordinates, then retrieve historical
			weather for the requested date.

			Parameters:
			-----------
			location (str):
				The place name entered by the user.

			date (dt.date):
				The requested historical date.

			zone (str):
				The timezone requested for the archive response. If 'auto', the API
				will resolve the local timezone for the coordinates.

			count (int):
				Maximum number of geocoding matches to request before selecting the
				first result.

			Returns:
			--------
			Dict[str, Any] | None:
				Combined geocoding and historical weather result.

		'''
		try:
			throw_if( 'location', location )
			throw_if( 'date', date )
			throw_if( 'zone', zone )
			
			selected = self.geocode_location( location=location, count=count )
			
			if not selected:
				return {
						'location': location,
						'date': date.isoformat( ),
						'message': 'No geocoding results found.',
						'data': { }
				}
			
			lat = selected.get( 'latitude', None )
			long = selected.get( 'longitude', None )
			
			if lat is None or long is None:
				return {
						'location': location,
						'date': date.isoformat( ),
						'message': 'Geocoding returned no usable coordinates.',
						'geocoding': selected,
						'data': { }
				}
			
			result = self.fetch_historical(
				lat=float( lat ),
				long=float( long ),
				date=date,
				zone=str( zone or 'auto' ).strip( )
			) or { }
			
			result[ 'geocoding' ]=selected
			return result
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HistoricalWeather'
			exception.method = (
					'fetch( self, location: str, date: dt.date, zone: str=auto, '
					'count: int=10 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''

			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None:
				A JSON-compatible dictionary defining the tool schema.

		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': f"{description.strip( )} This function uses the {tool.strip( )} service.",
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HistoricalWeather'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class Grokipedia( Fetcher ):
	'''

		Purpose:
		--------
		Fetches Grokipedia search results and page content.

		Attributes:
		-----------
		api_key,
		client,
		query,
		page,
		limit,
		offset,
		include_content,
		response,
		params,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_validate_limit(...): Performs the _validate_limit operation for this fetcher.
		_validate_offset(...): Performs the _validate_offset operation for this fetcher.
		_get_client(...): Performs the _get_client operation for this fetcher.
		fetch_search(...): Performs the fetch_search operation for this fetcher.
		fetch_page(...): Performs the fetch_page operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	api_key: Optional[ str ]
	client: Optional[ GrokipediaClient ]
	query: Optional[ str ]
	page: Optional[ str ]
	limit: Optional[ int ]
	offset: Optional[ int ]
	include_content: Optional[ bool ]
	response: Optional[ Dict[ str, Any ] ]
	params: Optional[ Dict[ str, Any ] ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the Grokipedia wrapper.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.api_key = cfg.XAI_API_KEY
		self.url = None
		self.client = None
		self.query = ''
		self.page = ''
		self.response = None
		self.params = { }
		self.limit = 12
		self.offset = 0
		self.include_content = True
		self.headers = { }
		self.timeout = 20
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'api_key',
				'client',
				'query',
				'page',
				'limit',
				'offset',
				'include_content',
				'response',
				'params',
				'fetch_search',
				'fetch_page',
				'fetch',
				'create_schema'
		]
	
	def _validate_limit( self, limit: int ) -> int:
		'''
			Purpose:
			--------
			Validate result limit.

			Parameters:
			-----------
			limit (int):
				Requested maximum number of results.

			Returns:
			--------
			int
		'''
		try:
			value = int( limit )
			if value < 1 or value > 100:
				raise ValueError( 'limit must be between 1 and 100.' )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Grokipedia'
			exception.method = '_validate_limit( self, limit: int ) -> int'
			raise exception
	
	def _validate_offset( self, offset: int ) -> int:
		'''
			Purpose:
			--------
			Validate pagination offset.

			Parameters:
			-----------
			offset (int):
				Requested result offset.

			Returns:
			--------
			int
		'''
		try:
			value = int( offset )
			if value < 0:
				raise ValueError( 'offset must be greater than or equal to 0.' )
			
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Grokipedia'
			exception.method = '_validate_offset( self, offset: int ) -> int'
			raise exception
	
	def _get_client( self ) -> GrokipediaClient:
		'''
			Purpose:
			--------
			Create a Grokipedia client instance.

			Parameters:
			-----------
			None

			Returns:
			--------
			GrokipediaClient
		'''
		try:
			return GrokipediaClient( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Grokipedia'
			exception.method = '_get_client( self ) -> GrokipediaClient'
			raise exception
	
	def fetch_search( self, query: str, limit: int=12,
			offset: int=0 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Search Grokipedia for matching articles.

			Parameters:
			-----------
			query (str):
				Free-text search query.

			limit (int):
				Maximum number of results to request.

			offset (int):
				Result offset for pagination.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'query', query )
			
			self.query = str( query ).strip( )
			self.limit = self._validate_limit( limit )
			self.offset = self._validate_offset( offset )
			self.client = self._get_client( )
			self.params = {
					'query': self.query,
					'limit': self.limit,
					'offset': self.offset
			}
			
			_results = self.client.search(
				query=self.query,
				limit=self.limit,
				offset=self.offset
			)
			
			return {
					'mode': 'search',
					'url': 'grokipedia.search',
					'params': self.params,
					'api_key_configured': bool( str( self.api_key or '' ).strip( ) ),
					'data': _results
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Grokipedia'
			exception.method = (
					'fetch_search( self, query: str, limit: int=12, '
					'offset: int=0 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_page( self, page: str,
			include_content: bool=True ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch a specific Grokipedia page by slug or page identifier.

			Parameters:
			-----------
			page (str):
				Page slug or page identifier.

			include_content (bool):
				If True, request full page content.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'page', page )
			
			self.page = str( page ).strip( )
			self.include_content = bool( include_content )
			self.client = self._get_client( )
			self.params = {
					'page': self.page,
					'include_content': self.include_content
			}
			
			_result = self.client.get_page(
				self.page,
				include_content=self.include_content
			)
			
			return {
					'mode': 'page',
					'url': 'grokipedia.get_page',
					'params': self.params,
					'api_key_configured': bool( str( self.api_key or '' ).strip( ) ),
					'data': _result
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Grokipedia'
			exception.method = (
					'fetch_page( self, page: str, include_content: bool=True ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='search', query: str='',
			page: str='', limit: int=12, offset: int=0,
			include_content: bool=True ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for Grokipedia operations.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- search
				- page

			query (str):
				Free-text search query for search mode.

			page (str):
				Page slug or identifier for page mode.

			limit (int):
				Maximum search results for search mode.

			offset (int):
				Pagination offset for search mode.

			include_content (bool):
				Whether to request full page content for page mode.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'search' ).strip( ).lower( )
			
			if active_mode == 'search':
				return self.fetch_search(
					query=query,
					limit=limit,
					offset=offset
				)
			
			if active_mode == 'page':
				return self.fetch_page(
					page=page,
					include_content=include_content
				)
			
			raise ValueError( "Unsupported mode. Use 'search' or 'page'." )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Grokipedia'
			exception.method = (
					'fetch( self, mode: str=search, query: str=, page: str=, '
					'limit: int=12, offset: int=0, include_content: bool=True ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError(
					'parameters must be a dict of param_name → schema definitions.'
				)
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f'{description.strip( )} '
							f'This function uses the {tool.strip( )} service.'
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Grokipedia'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class GoogleGeocoding( Fetcher ):
	'''

		Purpose:
		--------
		Fetches Google Geocoding forward, reverse, and place lookup records.

		Attributes:
		-----------
		api_key,
		url,
		params,
		mode,
		query,
		latitude,
		longitude,
		place_id,
		language,
		region,
		result_type,
		location_type,
		timeout,
		agents,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_resolve_api_key(...): Performs the _resolve_api_key operation for this fetcher.
		request(...): Performs the request operation for this fetcher.
		fetch_forward(...): Performs the fetch_forward operation for this fetcher.
		fetch_reverse(...): Performs the fetch_reverse operation for this fetcher.
		fetch_place(...): Performs the fetch_place operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	api_key: Optional[ str ]
	url: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	mode: Optional[ str ]
	query: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	place_id: Optional[ str ]
	language: Optional[ str ]
	region: Optional[ str ]
	result_type: Optional[ str ]
	location_type: Optional[ str ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the Google Geocoding fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.api_key = cfg.GOOGLE_API_KEY
		self.url = 'https://maps.googleapis.com/maps/api/geocode/json'
		self.params = { }
		self.mode = 'forward'
		self.query = ''
		self.latitude = None
		self.longitude = None
		self.place_id = ''
		self.language = 'en'
		self.region = ''
		self.result_type = ''
		self.location_type = ''
		self.timeout = 10
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'api_key',
				'url',
				'params',
				'mode',
				'query',
				'latitude',
				'longitude',
				'place_id',
				'language',
				'region',
				'result_type',
				'location_type',
				'timeout',
				'fetch_forward',
				'fetch_reverse',
				'fetch_place',
				'fetch',
				'create_schema'
		]
	
	def _resolve_api_key( self, api_key: Optional[ str ]=None ) -> str:
		'''
			Purpose:
			--------
			Resolve the Google API key.

			Parameters:
			-----------
			api_key (Optional[str]):
				Optional explicit API key override.

			Returns:
			--------
			str
		'''
		try:
			value = str( api_key or self.api_key or '' ).strip( )
			throw_if( 'GOOGLE_API_KEY', value )
			return value
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleGeocoding'
			exception.method = '_resolve_api_key( self, api_key: Optional[ str ]=None ) -> str'
			raise exception
	
	def request( self, params: Dict[ str, Any ], time: int=10,
			api_key: Optional[ str ]=None ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Submit a request to the Google Geocoding API.

			Parameters:
			-----------
			params (Dict[str, Any]):
				Request parameters excluding the key.

			time (int):
				Request timeout in seconds.

			api_key (Optional[str]):
				Optional explicit API key override.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			request_params = dict( params or { } )
			request_params[ 'key' ]=self._resolve_api_key( api_key=api_key )
			
			self.params = request_params
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			payload = self.response.json( ) or { }
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'status': payload.get( 'status', '' ),
					'results': payload.get( 'results', [ ] ),
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleGeocoding'
			exception.method = (
					'request( self, params: Dict[ str, Any ], time: int=10, '
					'api_key: Optional[ str ]=None ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_forward( self, query: str, language: str='en',
			region: str='', time: int=10,
			api_key: Optional[ str ]=None ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Forward geocode an address or place string.

			Parameters:
			-----------
			query (str):
				Human-readable address or place query.

			language (str):
				Preferred response language.

			region (str):
				Optional region bias, such as 'us'.

			time (int):
				Request timeout in seconds.

			api_key (Optional[str]):
				Optional explicit API key override.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'query', query )
			
			self.mode = 'forward'
			self.query = str( query ).strip( )
			self.language = str( language or 'en' ).strip( )
			self.region = str( region or '' ).strip( )
			
			params = {
					'address': self.query,
					'language': self.language
			}
			
			if self.region:
				params[ 'region' ]=self.region
			
			return self.request(
				params=params,
				time=int( time ),
				api_key=api_key
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleGeocoding'
			exception.method = (
					'fetch_forward( self, query: str, language: str=en, '
					'region: str=, time: int=10, api_key: Optional[ str ]=None ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_reverse( self, latitude: float, longitude: float,
			language: str='en', result_type: str='',
			location_type: str='', time: int=10,
			api_key: Optional[ str ]=None ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Reverse geocode a latitude / longitude coordinate pair.

			Parameters:
			-----------
			latitude (float):
				Latitude.

			longitude (float):
				Longitude.

			language (str):
				Preferred response language.

			result_type (str):
				Optional pipe-delimited result type filter.

			location_type (str):
				Optional pipe-delimited location type filter.

			time (int):
				Request timeout in seconds.

			api_key (Optional[str]):
				Optional explicit API key override.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'reverse'
			self.latitude = float( latitude )
			self.longitude = float( longitude )
			self.language = str( language or 'en' ).strip( )
			self.result_type = str( result_type or '' ).strip( )
			self.location_type = str( location_type or '' ).strip( )
			
			params = {
					'latlng': f'{self.latitude},{self.longitude}',
					'language': self.language
			}
			
			if self.result_type:
				params[ 'result_type' ]=self.result_type
			
			if self.location_type:
				params[ 'location_type' ]=self.location_type
			
			return self.request(
				params=params,
				time=int( time ),
				api_key=api_key
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleGeocoding'
			exception.method = (
					'fetch_reverse( self, latitude: float, longitude: float, '
					'language: str=en, result_type: str=, location_type: str=, '
					'time: int=10, api_key: Optional[ str ]=None ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_place( self, place_id: str, language: str='en',
			region: str='', time: int=10,
			api_key: Optional[ str ]=None ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Geocode a Google place_id into address details.

			Parameters:
			-----------
			place_id (str):
				Google place ID.

			language (str):
				Preferred response language.

			region (str):
				Optional region bias.

			time (int):
				Request timeout in seconds.

			api_key (Optional[str]):
				Optional explicit API key override.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'place_id', place_id )
			
			self.mode = 'place'
			self.place_id = str( place_id ).strip( )
			self.language = str( language or 'en' ).strip( )
			self.region = str( region or '' ).strip( )
			
			params = {
					'place_id': self.place_id,
					'language': self.language
			}
			
			if self.region:
				params[ 'region' ]=self.region
			
			return self.request(
				params=params,
				time=int( time ),
				api_key=api_key
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleGeocoding'
			exception.method = (
					'fetch_place( self, place_id: str, language: str=en, region: str=, '
					'time: int=10, api_key: Optional[ str ]=None ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='forward', query: str='',
			latitude: float=0.0, longitude: float=0.0,
			place_id: str='', language: str='en', region: str='',
			result_type: str='', location_type: str='', time: int=10,
			api_key: Optional[ str ]=None ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for Google Geocoding requests.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- forward
				- reverse
				- place

			query (str):
				Address / place query for forward mode.

			latitude (float):
				Latitude for reverse mode.

			longitude (float):
				Longitude for reverse mode.

			place_id (str):
				Place ID for place mode.

			language (str):
				Response language.

			region (str):
				Region bias for forward / place mode.

			result_type (str):
				Reverse-geocoding result filter.

			location_type (str):
				Reverse-geocoding location filter.

			time (int):
				Request timeout in seconds.

			api_key (Optional[str]):
				Optional explicit API key override.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'forward' ).strip( ).lower( )
			
			if active_mode == 'forward':
				return self.fetch_forward(
					query=query,
					language=language,
					region=region,
					time=time,
					api_key=api_key
				)
			
			if active_mode == 'reverse':
				return self.fetch_reverse(
					latitude=latitude,
					longitude=longitude,
					language=language,
					result_type=result_type,
					location_type=location_type,
					time=time,
					api_key=api_key
				)
			
			if active_mode == 'place':
				return self.fetch_place(
					place_id=place_id,
					language=language,
					region=region,
					time=time,
					api_key=api_key
				)
			
			raise ValueError( "Unsupported mode. Use 'forward', 'reverse', or 'place'." )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleGeocoding'
			exception.method = (
					'fetch( self, mode: str=forward, query: str=, latitude: float=0.0, '
					'longitude: float=0.0, place_id: str=, language: str=en, '
					'region: str=, result_type: str=, location_type: str=, '
					'time: int=10, api_key: Optional[ str ]=None ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GoogleGeocoding'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class CensusData( Fetcher ):
	'''

		Purpose:
		--------
		Fetches Census API variables and tabular data.

		Attributes:
		-----------
		api_key,
		base_url,
		year,
		dataset,
		mode,
		fields,
		geography_for,
		geography_in,
		predicates,
		params,
		payload,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_resolve_api_key(...): Performs the _resolve_api_key operation for this fetcher.
		_normalize_fields(...): Performs the _normalize_fields operation for this fetcher.
		_parse_predicates(...): Performs the _parse_predicates operation for this fetcher.
		_shape_table(...): Performs the _shape_table operation for this fetcher.
		fetch_variables(...): Performs the fetch_variables operation for this fetcher.
		fetch_data(...): Performs the fetch_data operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	api_key: Optional[ str ]
	base_url: Optional[ str ]
	year: Optional[ str ]
	dataset: Optional[ str ]
	mode: Optional[ str ]
	fields: Optional[ List[ str ] ]
	geography_for: Optional[ str ]
	geography_in: Optional[ str ]
	predicates: Optional[ Dict[ str, Any ] ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Dict[ str, Any ] ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize the U.S. Census Bureau API wrapper.

			Parameters:
			-----------
			None

			Returns:
			-----------
			None

		'''
		super( ).__init__( )
		self.api_key = getattr( cfg, 'CENSUS_API_KEY', '' )
		self.base_url = 'https://api.census.gov/data'
		self.year = None
		self.dataset = None
		self.mode = None
		self.fields = [ ]
		self.geography_for = None
		self.geography_in = None
		self.predicates = { }
		self.params = { }
		self.payload = { }
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': cfg.AGENTS,
		}
		self.timeout = 20
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			-----------
			Return ordered CensusData members.

			Parameters:
			-----------
			None

			Returns:
			-----------
			List[str]

		'''
		return [
				'api_key',
				'base_url',
				'year',
				'dataset',
				'mode',
				'fields',
				'geography_for',
				'geography_in',
				'predicates',
				'params',
				'payload',
				'_resolve_api_key',
				'_normalize_fields',
				'_parse_predicates',
				'_shape_table',
				'fetch_variables',
				'fetch_data',
				'fetch',
				'create_schema',
		]
	
	def _resolve_api_key( self ) -> Optional[ str ]:
		'''
			Purpose:
			-----------
			Resolve the configured Census API key.

			Parameters:
			-----------
			None

			Returns:
			-----------
			Optional[str]

		'''
		key = str( self.api_key or '' ).strip( )
		return key if key else None
	
	def _normalize_fields( self, fields: str ) -> str:
		'''
			Purpose:
			-----------
			Normalize the comma-delimited Census get-field string.

			Parameters:
			-----------
			fields (str): Comma-delimited field list.

			Returns:
			-----------
			str

		'''
		try:
			throw_if( 'fields', fields )
			parts = [ p.strip( ) for p in str( fields ).split( ',' ) if p.strip( ) ]
			if not parts:
				raise ValueError( "Argument 'fields' cannot be empty!" )
			self.fields = parts
			return ','.join( parts )
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'CensusData'
			exception.method = '_normalize_fields( self, fields: str ) -> str'
			raise exception
	
	def _parse_predicates( self, predicates: str ) -> Dict[ str, Any ]:
		'''
			Purpose:
			-----------
			Parse optional Census predicate text into a parameter dictionary.

			Parameters:
			-----------
			predicates (str):
				Newline-delimited key=value pairs.

			Returns:
			-----------
			Dict[str, Any]

		'''
		try:
			output: Dict[ str, Any ]={ }
			text = str( predicates or '' ).strip( )
			if not text:
				return output
			
			for line in text.splitlines( ):
				item = str( line ).strip( )
				if not item:
					continue
				
				if '=' not in item:
					raise ValueError(
						"Each predicate line must use the form 'key=value'."
					)
				
				key, value = item.split( '=', 1 )
				k = str( key ).strip( )
				v = str( value ).strip( )
				
				if not k:
					raise ValueError( 'Predicate key cannot be empty.' )
				
				output[ k ]=v
			
			return output
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'CensusData'
			exception.method = (
					'_parse_predicates( self, predicates: str ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_table( self, rows: List[ Any ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			-----------
			Transform Census array-style responses into header/row dictionaries.

			Parameters:
			-----------
			rows (List[Any]):
				Raw Census API response payload.

			Returns:
			-----------
			Dict[str, Any]

		'''
		try:
			if not isinstance( rows, list ) or not rows:
				return {
						'columns': [ ],
						'rows': [ ],
						'count': 0,
				}
			
			headers = [ str( h ) for h in rows[ 0 ] ] if isinstance( rows[ 0 ], list ) else [ ]
			data_rows = rows[ 1: ] if len( rows ) > 1 else [ ]
			records: List[ Dict[ str, Any ] ]=[ ]
			
			for row in data_rows:
				if isinstance( row, list ) and headers:
					records.append(
						{
								headers[ idx ]: row[ idx ] if idx < len( row ) else ''
								for idx in range( len( headers ) )
						}
					)
			
			return {
					'columns': headers,
					'rows': records,
					'count': len( records ),
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'CensusData'
			exception.method = '_shape_table( self, rows: List[ Any ] ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_variables( self, year: str, dataset: str, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the variables metadata for a Census dataset.

			Parameters:
			-----------
			year (str):
				Dataset year such as 2022.

			dataset (str):
				Dataset path such as acs/acs5 or 2020/dec/dhc.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			throw_if( 'year', year )
			throw_if( 'dataset', dataset )
			
			self.mode = 'variables'
			self.year = str( year ).strip( )
			self.dataset = str( dataset ).strip( ).strip( '/' )
			self.url = f'{self.base_url}/{self.year}/{self.dataset}/variables.json'
			self.params = { }
			api_key = self._resolve_api_key( )
			if api_key:
				self.params[ 'key' ]=api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.response.json( ),
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'CensusData'
			exception.method = (
					'fetch_variables( self, year: str, dataset: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_data( self, year: str, dataset: str, fields: str,
			geography_for: str='', geography_in: str='',
			predicates: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch tabular Census dataset values.

			Parameters:
			-----------
			year (str):
				Dataset year such as 2022.

			dataset (str):
				Dataset path such as acs/acs5.

			fields (str):
				Comma-delimited get variables such as NAME,B01001_001E.

			geography_for (str):
				Census `for` geography clause, e.g. state:*.

			geography_in (str):
				Optional Census `in` geography clause.

			predicates (str):
				Optional newline-delimited key=value predicates.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			throw_if( 'year', year )
			throw_if( 'dataset', dataset )
			throw_if( 'fields', fields )
			
			self.mode = 'data'
			self.year = str( year ).strip( )
			self.dataset = str( dataset ).strip( ).strip( '/' )
			self.geography_for = str( geography_for or '' ).strip( )
			self.geography_in = str( geography_in or '' ).strip( )
			self.predicates = self._parse_predicates( predicates )
			self.url = f'{self.base_url}/{self.year}/{self.dataset}'
			self.params = {
					'get': self._normalize_fields( fields ),
			}
			
			if self.geography_for:
				self.params[ 'for' ]=self.geography_for
			
			if self.geography_in:
				self.params[ 'in' ]=self.geography_in
			
			if self.predicates:
				self.params.update( self.predicates )
			
			api_key = self._resolve_api_key( )
			if api_key:
				self.params[ 'key' ]=api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self._shape_table( self.payload ),
					'raw': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'CensusData'
			exception.method = (
					'fetch_data( self, year: str, dataset: str, fields: str, '
					'geography_for: str="", geography_in: str="", predicates: str="", '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='variables', year: str='2022',
			dataset: str='acs/acs5', fields: str='NAME,B01001_001E',
			geography_for: str='state:*', geography_in: str='',
			predicates: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Dispatch Census API operations.

			Parameters:
			-----------
			mode (str):
				One of variables or data.

			year (str):
				Dataset year.

			dataset (str):
				Dataset path.

			fields (str):
				Comma-delimited data fields for data mode.

			geography_for (str):
				Census `for` clause for data mode.

			geography_in (str):
				Optional Census `in` clause for data mode.

			predicates (str):
				Optional newline-delimited key=value predicates.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = str( mode or 'variables' ).strip( ).lower( )
			
			if self.mode == 'variables':
				return self.fetch_variables(
					year=year,
					dataset=dataset,
					time=int( time ) )
			
			if self.mode == 'data':
				return self.fetch_data(
					year=year,
					dataset=dataset,
					fields=fields,
					geography_for=geography_for,
					geography_in=geography_in,
					predicates=predicates,
					time=int( time ) )
			
			raise ValueError(
				"mode must be one of: 'variables', 'data'."
			)
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'CensusData'
			exception.method = (
					'fetch( self, mode: str="variables", year: str="2022", '
					'dataset: str="acs/acs5", fields: str="NAME,B01001_001E", '
					'geography_for: str="state:*", geography_in: str="", '
					'predicates: str="", time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		"""
			Purpose:
			________
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			___________
			function (str): Tool function name.
			tool (str): Service name.
			description (str): What the function does.
			parameters (dict): JSON-schema properties.
			required (list[str]): Required parameter names.

			Returns:
			________
			dict

		"""
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError(
					'parameters must be a dict of param_name -> schema definition.'
				)
			
			func_name = function.strip( )
			tool_name = tool.strip( )
			desc = description.strip( )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			_schema = {
					'name': func_name,
					'description': f'{desc} This function uses the {tool_name} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required,
					}
			}
			
			return _schema
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'CensusData'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class Socrata( Fetcher ):
	'''

		Purpose:
		--------
		Fetches metadata and rows from Socrata-backed open-data portals.

		Attributes:
		-----------
		api_key,
		base_url,
		domain,
		dataset_id,
		mode,
		select_clause,
		where_clause,
		order_clause,
		group_clause,
		limit_value,
		offset_value,
		params,
		payload,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_resolve_api_key(...): Performs the _resolve_api_key operation for this fetcher.
		_normalize_domain(...): Performs the _normalize_domain operation for this fetcher.
		_normalize_dataset_id(...): Performs the _normalize_dataset_id operation for this fetcher.
		fetch_metadata(...): Performs the fetch_metadata operation for this fetcher.
		fetch_rows(...): Performs the fetch_rows operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	api_key: Optional[ str ]
	base_url: Optional[ str ]
	domain: Optional[ str ]
	dataset_id: Optional[ str ]
	mode: Optional[ str ]
	select_clause: Optional[ str ]
	where_clause: Optional[ str ]
	order_clause: Optional[ str ]
	group_clause: Optional[ str ]
	limit_value: Optional[ int ]
	offset_value: Optional[ int ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize the Socrata API wrapper.

			Parameters:
			-----------
			None

			Returns:
			-----------
			None

		'''
		super( ).__init__( )
		self.api_key = getattr( cfg, 'SOCRATA_API_KEY', '' )
		self.base_url = 'https://{domain}/resource/{dataset}.json'
		self.domain = 'data.cdc.gov'
		self.dataset_id = ''
		self.mode = 'rows'
		self.select_clause = ''
		self.where_clause = ''
		self.order_clause = ''
		self.group_clause = ''
		self.limit_value = 25
		self.offset_value = 0
		self.params = { }
		self.payload = [ ]
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': cfg.AGENTS,
		}
		self.timeout = 20
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			-----------
			Return ordered Socrata members.

			Parameters:
			-----------
			None

			Returns:
			-----------
			List[str]

		'''
		return [
				'api_key',
				'base_url',
				'domain',
				'dataset_id',
				'mode',
				'select_clause',
				'where_clause',
				'order_clause',
				'group_clause',
				'limit_value',
				'offset_value',
				'params',
				'payload',
				'_resolve_api_key',
				'_normalize_domain',
				'_normalize_dataset_id',
				'fetch_metadata',
				'fetch_rows',
				'fetch',
				'create_schema',
		]
	
	def _resolve_api_key( self ) -> Optional[ str ]:
		'''
			Purpose:
			-----------
			Resolve the configured Socrata application token.

			Parameters:
			-----------
			None

			Returns:
			-----------
			Optional[str]

		'''
		key = str( self.api_key or '' ).strip( )
		return key if key else None
	
	def _normalize_domain( self, domain: str ) -> str:
		'''
			Purpose:
			-----------
			Normalize the Socrata domain.

			Parameters:
			-----------
			domain (str): Domain such as data.cdc.gov.

			Returns:
			-----------
			str

		'''
		try:
			throw_if( 'domain', domain )
			value = str( domain ).strip( )
			value = value.replace( 'https://', '' ).replace( 'http://', '' ).strip( '/' )
			if not value:
				raise ValueError( "Argument 'domain' cannot be empty!" )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Socrata'
			exception.method = '_normalize_domain( self, domain: str ) -> str'
			raise exception
	
	def _normalize_dataset_id( self, dataset_id: str ) -> str:
		'''
			Purpose:
			-----------
			Normalize the Socrata dataset identifier.

			Parameters:
			-----------
			dataset_id (str): 4x4 dataset identifier.

			Returns:
			-----------
			str

		'''
		try:
			throw_if( 'dataset_id', dataset_id )
			value = str( dataset_id ).strip( )
			value = value.replace( '.json', '' ).strip( '/' )
			if not value:
				raise ValueError( "Argument 'dataset_id' cannot be empty!" )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Socrata'
			exception.method = '_normalize_dataset_id( self, dataset_id: str ) -> str'
			raise exception
	
	def fetch_metadata( self, domain: str, dataset_id: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch Socrata dataset metadata.

			Parameters:
			-----------
			domain (str):
				Portal domain such as data.cdc.gov.

			dataset_id (str):
				Dataset identifier such as q8xq-ygsk.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'metadata'
			self.domain = self._normalize_domain( domain )
			self.dataset_id = self._normalize_dataset_id( dataset_id )
			self.url = f'https://{self.domain}/api/views/{self.dataset_id}.json'
			self.params = { }
			
			api_key = self._resolve_api_key( )
			if api_key:
				self.headers[ 'X-App-Token' ]=api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.response.json( ),
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Socrata'
			exception.method = (
					'fetch_metadata( self, domain: str, dataset_id: str, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_rows( self, domain: str, dataset_id: str, select: str='',
			where: str='', order: str='', group: str='',
			limit: int=25, offset: int=0,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch Socrata dataset rows using standard SoQL query options.

			Parameters:
			-----------
			domain (str):
				Portal domain such as data.cdc.gov.

			dataset_id (str):
				Dataset identifier such as q8xq-ygsk.

			select (str):
				Optional $select clause.

			where (str):
				Optional $where clause.

			order (str):
				Optional $order clause.

			group (str):
				Optional $group clause.

			limit (int):
				Optional row limit.

			offset (int):
				Optional offset for pagination.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'rows'
			self.domain = self._normalize_domain( domain )
			self.dataset_id = self._normalize_dataset_id( dataset_id )
			self.select_clause = str( select or '' ).strip( )
			self.where_clause = str( where or '' ).strip( )
			self.order_clause = str( order or '' ).strip( )
			self.group_clause = str( group or '' ).strip( )
			self.limit_value = int( limit )
			self.offset_value = int( offset )
			
			self.url = self.base_url.format(
				domain=self.domain,
				dataset=self.dataset_id )
			
			self.params = {
					'$limit': self.limit_value,
					'$offset': self.offset_value,
			}
			
			if self.select_clause:
				self.params[ '$select' ]=self.select_clause
			
			if self.where_clause:
				self.params[ '$where' ]=self.where_clause
			
			if self.order_clause:
				self.params[ '$order' ]=self.order_clause
			
			if self.group_clause:
				self.params[ '$group' ]=self.group_clause
			
			api_key = self._resolve_api_key( )
			if api_key:
				self.headers[ 'X-App-Token' ]=api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'count': len( self.payload ) if isinstance( self.payload, list ) else 0,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Socrata'
			exception.method = (
					'fetch_rows( self, domain: str, dataset_id: str, select: str="", '
					'where: str="", order: str="", group: str="", limit: int=25, '
					'offset: int=0, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='rows', domain: str='data.cdc.gov',
			dataset_id: str='', select: str='', where: str='',
			order: str='', group: str='', limit: int=25,
			offset: int=0, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Dispatch Socrata API operations.

			Parameters:
			-----------
			mode (str):
				One of metadata or rows.

			domain (str):
				Portal domain.

			dataset_id (str):
				Dataset identifier.

			select (str):
				Optional $select clause.

			where (str):
				Optional $where clause.

			order (str):
				Optional $order clause.

			group (str):
				Optional $group clause.

			limit (int):
				Optional row limit.

			offset (int):
				Optional row offset.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			active_mode = str( mode or 'rows' ).strip( ).lower( )
			
			if active_mode == 'metadata':
				return self.fetch_metadata(
					domain=domain,
					dataset_id=dataset_id,
					time=int( time ) )
			
			if active_mode == 'rows':
				return self.fetch_rows(
					domain=domain,
					dataset_id=dataset_id,
					select=select,
					where=where,
					order=order,
					group=group,
					limit=int( limit ),
					offset=int( offset ),
					time=int( time ) )
			
			raise ValueError( "mode must be one of: 'metadata', 'rows'." )
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Socrata'
			exception.method = (
					'fetch( self, mode: str="rows", domain: str="data.cdc.gov", '
					'dataset_id: str="", select: str="", where: str="", order: str="", '
					'group: str="", limit: int=25, offset: int=0, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		"""
			Purpose:
			________
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			___________
			function (str): Tool function name.
			tool (str): Service name.
			description (str): What the function does.
			parameters (dict): JSON-schema properties.
			required (list[str]): Required parameter names.

			Returns:
			________
			dict

		"""
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError(
					'parameters must be a dict of param_name -> schema definition.'
				)
			
			func_name = function.strip( )
			tool_name = tool.strip( )
			desc = description.strip( )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			_schema = {
					'name': func_name,
					'description': f'{desc} This function uses the {tool_name} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required,
					}
			}
			
			return _schema
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Socrata'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class HealthData( Fetcher ):
	'''

		Purpose:
		--------
		Fetches metadata and rows from HealthData.gov Socrata datasets.

		Attributes:
		-----------
		api_key,
		base_url,
		domain,
		dataset_id,
		mode,
		select_clause,
		where_clause,
		order_clause,
		group_clause,
		limit_value,
		offset_value,
		params,
		payload,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_resolve_api_key(...): Performs the _resolve_api_key operation for this fetcher.
		_normalize_domain(...): Performs the _normalize_domain operation for this fetcher.
		_normalize_dataset_id(...): Performs the _normalize_dataset_id operation for this fetcher.
		fetch_metadata(...): Performs the fetch_metadata operation for this fetcher.
		fetch_rows(...): Performs the fetch_rows operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	api_key: Optional[ str ]
	base_url: Optional[ str ]
	domain: Optional[ str ]
	dataset_id: Optional[ str ]
	mode: Optional[ str ]
	select_clause: Optional[ str ]
	where_clause: Optional[ str ]
	order_clause: Optional[ str ]
	group_clause: Optional[ str ]
	limit_value: Optional[ int ]
	offset_value: Optional[ int ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize the HealthData.gov API wrapper.

			Parameters:
			-----------
			None

			Returns:
			-----------
			None

		'''
		super( ).__init__( )
		self.api_key = getattr( cfg, 'HEALTHDATA_API_KEY', '' )
		self.base_url = 'https://{domain}/resource/{dataset}.json'
		self.domain = 'healthdata.gov'
		self.dataset_id = ''
		self.mode = 'rows'
		self.select_clause = ''
		self.where_clause = ''
		self.order_clause = ''
		self.group_clause = ''
		self.limit_value = 25
		self.offset_value = 0
		self.params = { }
		self.payload = [ ]
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': cfg.AGENTS,
		}
		self.timeout = 20
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			-----------
			Return ordered HealthData members.

			Parameters:
			-----------
			None

			Returns:
			-----------
			List[str]

		'''
		return [
				'api_key',
				'base_url',
				'domain',
				'dataset_id',
				'mode',
				'select_clause',
				'where_clause',
				'order_clause',
				'group_clause',
				'limit_value',
				'offset_value',
				'params',
				'payload',
				'_resolve_api_key',
				'_normalize_domain',
				'_normalize_dataset_id',
				'fetch_metadata',
				'fetch_rows',
				'fetch',
				'create_schema',
		]
	
	def _resolve_api_key( self ) -> Optional[ str ]:
		'''
			Purpose:
			-----------
			Resolve the configured HealthData.gov application token.

			Parameters:
			-----------
			None

			Returns:
			-----------
			Optional[str]

		'''
		key = str( self.api_key or '' ).strip( )
		return key if key else None
	
	def _normalize_domain( self, domain: str ) -> str:
		'''
			Purpose:
			-----------
			Normalize the HealthData.gov domain.

			Parameters:
			-----------
			domain (str):
				Domain such as healthdata.gov.

			Returns:
			-----------
			str

		'''
		try:
			throw_if( 'domain', domain )
			value = str( domain ).strip( )
			value = value.replace( 'https://', '' ).replace( 'http://', '' ).strip( '/' )
			if not value:
				raise ValueError( "Argument 'domain' cannot be empty!" )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HealthData'
			exception.method = '_normalize_domain( self, domain: str ) -> str'
			raise exception
	
	def _normalize_dataset_id( self, dataset_id: str ) -> str:
		'''
			Purpose:
			-----------
			Normalize the HealthData.gov dataset identifier.

			Parameters:
			-----------
			dataset_id (str):
				Dataset identifier.

			Returns:
			-----------
			str

		'''
		try:
			throw_if( 'dataset_id', dataset_id )
			value = str( dataset_id ).strip( )
			value = value.replace( '.json', '' ).strip( '/' )
			if not value:
				raise ValueError( "Argument 'dataset_id' cannot be empty!" )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HealthData'
			exception.method = '_normalize_dataset_id( self, dataset_id: str ) -> str'
			raise exception
	
	def fetch_metadata( self, domain: str, dataset_id: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch HealthData.gov dataset metadata.

			Parameters:
			-----------
			domain (str):
				Portal domain such as healthdata.gov.

			dataset_id (str):
				Dataset identifier.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'metadata'
			self.domain = self._normalize_domain( domain )
			self.dataset_id = self._normalize_dataset_id( dataset_id )
			self.url = f'https://{self.domain}/api/views/{self.dataset_id}.json'
			self.params = { }
			
			api_key = self._resolve_api_key( )
			if api_key:
				self.headers[ 'X-App-Token' ]=api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.response.json( ),
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HealthData'
			exception.method = (
					'fetch_metadata( self, domain: str, dataset_id: str, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_rows( self, domain: str, dataset_id: str, select: str='',
			where: str='', order: str='', group: str='',
			limit: int=25, offset: int=0,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch HealthData.gov dataset rows using standard SoQL query options.

			Parameters:
			-----------
			domain (str):
				Portal domain such as healthdata.gov.

			dataset_id (str):
				Dataset identifier.

			select (str):
				Optional $select clause.

			where (str):
				Optional $where clause.

			order (str):
				Optional $order clause.

			group (str):
				Optional $group clause.

			limit (int):
				Optional row limit.

			offset (int):
				Optional offset for pagination.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'rows'
			self.domain = self._normalize_domain( domain )
			self.dataset_id = self._normalize_dataset_id( dataset_id )
			self.select_clause = str( select or '' ).strip( )
			self.where_clause = str( where or '' ).strip( )
			self.order_clause = str( order or '' ).strip( )
			self.group_clause = str( group or '' ).strip( )
			self.limit_value = int( limit )
			self.offset_value = int( offset )
			
			self.url = self.base_url.format(
				domain=self.domain,
				dataset=self.dataset_id )
			
			self.params = {
					'$limit': self.limit_value,
					'$offset': self.offset_value,
			}
			
			if self.select_clause:
				self.params[ '$select' ]=self.select_clause
			
			if self.where_clause:
				self.params[ '$where' ]=self.where_clause
			
			if self.order_clause:
				self.params[ '$order' ]=self.order_clause
			
			if self.group_clause:
				self.params[ '$group' ]=self.group_clause
			
			api_key = self._resolve_api_key( )
			if api_key:
				self.headers[ 'X-App-Token' ]=api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'count': len( self.payload ) if isinstance( self.payload, list ) else 0,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HealthData'
			exception.method = (
					'fetch_rows( self, domain: str, dataset_id: str, select: str="", '
					'where: str="", order: str="", group: str="", limit: int=25, '
					'offset: int=0, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='rows', domain: str='healthdata.gov',
			dataset_id: str='', select: str='', where: str='',
			order: str='', group: str='', limit: int=25,
			offset: int=0, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Dispatch HealthData.gov API operations.

			Parameters:
			-----------
			mode (str):
				One of metadata or rows.

			domain (str):
				Portal domain.

			dataset_id (str):
				Dataset identifier.

			select (str):
				Optional $select clause.

			where (str):
				Optional $where clause.

			order (str):
				Optional $order clause.

			group (str):
				Optional $group clause.

			limit (int):
				Optional row limit.

			offset (int):
				Optional row offset.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			active_mode = str( mode or 'rows' ).strip( ).lower( )
			
			if active_mode == 'metadata':
				return self.fetch_metadata(
					domain=domain,
					dataset_id=dataset_id,
					time=int( time ) )
			
			if active_mode == 'rows':
				return self.fetch_rows(
					domain=domain,
					dataset_id=dataset_id,
					select=select,
					where=where,
					order=order,
					group=group,
					limit=int( limit ),
					offset=int( offset ),
					time=int( time ) )
			
			raise ValueError( "mode must be one of: 'metadata', 'rows'." )
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HealthData'
			exception.method = (
					'fetch( self, mode: str="rows", domain: str="healthdata.gov", '
					'dataset_id: str="", select: str="", where: str="", order: str="", '
					'group: str="", limit: int=25, offset: int=0, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			-----------
			Construct and return a dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				Tool function name.

			tool (str):
				Service name.

			description (str):
				Description of what the tool does.

			parameters (dict):
				JSON-schema properties.

			required (list[str]):
				Required parameter names.

			Returns:
			-----------
			Dict[str, str] | None

		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError(
					'parameters must be a dict of param_name -> schema definition.'
				)
			
			func_name = function.strip( )
			tool_name = tool.strip( )
			desc = description.strip( )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			_schema = {
					'name': func_name,
					'description': f'{desc} This function uses the {tool_name} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required,
					}
			}
			
			return _schema
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'HealthData'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class GlobalHealthData( Fetcher ):
	'''
	
		Purpose:
		--------
		Fetches United Nations SDMX catalog and query data.
	
		Attributes:
		-----------
		base_url,
		catalog_url,
		mode,
		query_path,
		params,
		payload,
	
		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_normalize_query_path(...): Performs the _normalize_query_path operation for this fetcher.
		fetch_datasets(...): Performs the fetch_datasets operation for this fetcher.
		fetch_sdmx_query(...): Performs the fetch_sdmx_query operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.
	
	'''
	api_key: Optional[ str ]
	base_url: Optional[ str ]
	athena_base_url: Optional[ str ]
	mode: Optional[ str ]
	query_path: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize the WHO Global Health Observatory API wrapper.

			Parameters:
			-----------
			None

			Returns:
			-----------
			None

		'''
		super( ).__init__( )
		self.api_key = getattr( cfg, 'WHO_API_KEY', '' )
		self.base_url = 'https://www.who.int/data/gho'
		self.athena_base_url = 'https://ghoapi.azureedge.net/api'
		self.mode = 'indicator_registry'
		self.query_path = ''
		self.params = { }
		self.payload = { }
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': cfg.AGENTS,
		}
		self.timeout = 20
	
	def __dir__( self ) -> List[ str ]:
		return [
				'api_key',
				'base_url',
				'athena_base_url',
				'mode',
				'query_path',
				'params',
				'payload',
				'_resolve_api_key',
				'_normalize_query_path',
				'fetch_indicator_registry',
				'fetch_athena',
				'fetch',
				'create_schema',
		]
	
	def _resolve_api_key( self ) -> Optional[ str ]:
		'''

			Purpose:
			--------
			Fetch a NASA GIBS Mercator map image and render it through the provided
			Cartopy coordinate reference system module.
		
			Parameters:
			-----------
			ccrs (Any | None): Optional Cartopy coordinate reference system module used
			to project and render the returned map image.
		
			Returns:
			--------
			Any | None: The rendered map result or None when the request fails.
		
		'''
		key = str( self.api_key or '' ).strip( )
		return key if key else None
	
	def _normalize_query_path( self, query_path: str ) -> str:
		'''
		
			Purpose:
			--------
			Normalize a Global Health query path by trimming whitespace and removing
			leading path separators before composing a request URL.
		
			Parameters:
			-----------
			query_path (str): Raw Global Health query path supplied by the caller.
		
			Returns:
			--------
			str: Normalized query path suitable for request URL composition.
		
		'''
		try:
			throw_if( 'query_path', query_path )
			value = str( query_path ).strip( )
			value = value.lstrip( '/' )
			if not value:
				raise ValueError( "Argument 'query_path' cannot be empty!" )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalHealthData'
			exception.method = '_normalize_query_path( self, query_path: str ) -> str'
			raise exception
	
	def fetch_indicator_registry( self, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the WHO indicator metadata registry landing content.

			Parameters:
			-----------
			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'indicator_registry'
			self.url = f'{self.base_url}/indicator-metadata-registry'
			self.params = { }
			
			api_key = self._resolve_api_key( )
			if api_key:
				self.headers[ 'X-API-Key' ]=api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			content_type = str( self.response.headers.get( 'Content-Type', '' ) ).lower( )
			
			if 'application/json' in content_type:
				self.payload = self.response.json( )
			else:
				self.payload = {
						'html': self.response.text,
				}
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalHealthData'
			exception.method = (
					'fetch_indicator_registry( self, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_athena( self, query_path: str, fmt: str='json',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Execute a WHO GHO Athena/OData-style query path.

			Parameters:
			-----------
			query_path (str):
				The path segment to append after the base WHO API endpoint.

			fmt (str):
				Response format hint, typically json or xml.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'athena'
			self.query_path = self._normalize_query_path( query_path )
			self.url = f'{self.athena_base_url}/{self.query_path}'
			self.params = { }
			
			if str( fmt or '' ).strip( ):
				self.params[ '$format' ]=str( fmt ).strip( )
			
			api_key = self._resolve_api_key( )
			if api_key:
				self.headers[ 'X-API-Key' ]=api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			content_type = str( self.response.headers.get( 'Content-Type', '' ) ).lower( )
			
			if 'application/json' in content_type:
				self.payload = self.response.json( )
			else:
				self.payload = {
						'text': self.response.text,
				}
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalHealthData'
			exception.method = (
					'fetch_athena( self, query_path: str, fmt: str="json", '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='indicator_registry', query_path: str='',
			fmt: str='json', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Dispatch WHO Global Health Observatory API operations.

			Parameters:
			-----------
			mode (str):
				One of indicator_registry or athena.

			query_path (str):
				Query path for athena mode.

			fmt (str):
				Response format hint.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			active_mode = str( mode or 'indicator_registry' ).strip( ).lower( )
			
			if active_mode == 'indicator_registry':
				return self.fetch_indicator_registry(
					time=int( time ) )
			
			if active_mode == 'athena':
				return self.fetch_athena(
					query_path=query_path,
					fmt=fmt,
					time=int( time ) )
			
			raise ValueError(
				"mode must be one of: 'indicator_registry', 'athena'."
			)
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalHealthData'
			exception.method = (
					'fetch( self, mode: str="indicator_registry", query_path: str="", '
					'fmt: str="json", time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError(
					'parameters must be a dict of param_name -> schema definition.'
				)
			
			func_name = function.strip( )
			tool_name = tool.strip( )
			desc = description.strip( )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			_schema = {
					'name': func_name,
					'description': f'{desc} This function uses the {tool_name} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required,
					}
			}
			
			return _schema
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'GlobalHealthData'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class UnitedNations( Fetcher ):
	'''
		Purpose:
		--------
		Fetch catalog and SDMX query results from the United Nations UNdata API.

		Attribues:
		-----------
		base_url - Optional[ str ]
		catalog_url - Optional[ str ]
		mode - Optional[ str ]
		query_path - Optional[ str ]
		params - Optional[ Dict[ str, Any ] ]
		payload - Optional[ Any ]

		Methods:
		-----------
		_normalize_query_path( query_path: str ) -> str
		fetch_datasets( time: int=20 ) -> Dict[ str, Any ]
		fetch_sdmx_query( query_path: str, time: int=20 ) -> Dict[ str, Any ]
		fetch( mode: str='datasets', query_path: str='', time: int=20 )
			-> Dict[ str, Any ]
		create_schema( self, function: str, tool: str, description: str,
			parameters: dict, required: list[ str ] ) -> Dict[ str, str ] | None

	'''
	base_url: Optional[ str ]
	catalog_url: Optional[ str ]
	mode: Optional[ str ]
	query_path: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize the United Nations UNdata API wrapper.

			Parameters:
			-----------
			None

			Returns:
			-----------
			None

		'''
		super( ).__init__( )
		self.base_url = 'https://data.un.org/WS/rest'
		self.catalog_url = 'https://data.un.org/datamartinfo.aspx'
		self.mode = 'datasets'
		self.query_path = ''
		self.params = { }
		self.payload = { }
		self.headers = {
				'Accept': 'application/json, text/xml, application/xml, text/html',
				'User-Agent': cfg.AGENTS,
		}
		self.timeout = 20
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			-----------
			Return ordered UnitedNations members.

			Parameters:
			-----------
			None

			Returns:
			-----------
			List[str]

		'''
		return [
				'base_url',
				'catalog_url',
				'mode',
				'query_path',
				'params',
				'payload',
				'_normalize_query_path',
				'fetch_datasets',
				'fetch_sdmx_query',
				'fetch',
				'create_schema',
		]
	
	def _normalize_query_path( self, query_path: str ) -> str:
		'''
			Purpose:
			-----------
			Normalize the SDMX query path appended to the UNdata REST endpoint.

			Parameters:
			-----------
			query_path (str):
				Path appended after the UNdata REST base endpoint.

			Returns:
			-----------
			str

		'''
		try:
			throw_if( 'query_path', query_path )
			value = str( query_path ).strip( )
			value = value.lstrip( '/' )
			if not value:
				raise ValueError( "Argument 'query_path' cannot be empty!" )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UnitedNations'
			exception.method = '_normalize_query_path( self, query_path: str ) -> str'
			raise exception
	
	def fetch_datasets( self, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the UNdata dataset catalog landing page.

			Parameters:
			-----------
			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'datasets'
			self.url = self.catalog_url
			self.params = { }
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			content_type = str( self.response.headers.get( 'Content-Type', '' ) ).lower( )
			
			if 'application/json' in content_type:
				self.payload = self.response.json( )
			else:
				self.payload = {
						'html': self.response.text,
				}
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UnitedNations'
			exception.method = (
					'fetch_datasets( self, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_sdmx_query( self, query_path: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Execute a REST SDMX query against the UNdata API.

			Parameters:
			-----------
			query_path (str):
				Path appended after the UNdata REST base endpoint.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'sdmx_query'
			self.query_path = self._normalize_query_path( query_path )
			self.url = f'{self.base_url}/{self.query_path}'
			self.params = { }
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			content_type = str( self.response.headers.get( 'Content-Type', '' ) ).lower( )
			
			if 'application/json' in content_type:
				self.payload = self.response.json( )
			else:
				self.payload = {
						'text': self.response.text,
				}
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UnitedNations'
			exception.method = (
					'fetch_sdmx_query( self, query_path: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='datasets', query_path: str='',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Dispatch United Nations UNdata API operations.

			Parameters:
			-----------
			mode (str):
				One of datasets or sdmx_query.

			query_path (str):
				Query path for sdmx_query mode.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			active_mode = str( mode or 'datasets' ).strip( ).lower( )
			
			if active_mode == 'datasets':
				return self.fetch_datasets(
					time=int( time ) )
			
			if active_mode == 'sdmx_query':
				return self.fetch_sdmx_query(
					query_path=query_path,
					time=int( time ) )
			
			raise ValueError(
				"mode must be one of: 'datasets', 'sdmx_query'."
			)
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UnitedNations'
			exception.method = (
					'fetch( self, mode: str="datasets", query_path: str="", '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			-----------
			Construct and return a dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				Tool function name.

			tool (str):
				Service name.

			description (str):
				Description of what the tool does.

			parameters (dict):
				JSON-schema properties.

			required (list[str]):
				Required parameter names.

			Returns:
			-----------
			Dict[str, str] | None

		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError(
					'parameters must be a dict of param_name -> schema definition.'
				)
			
			func_name = function.strip( )
			tool_name = tool.strip( )
			desc = description.strip( )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			_schema = {
					'name': func_name,
					'description': f'{desc} This function uses the {tool_name} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required,
					}
			}
			
			return _schema
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UnitedNations'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class WorldPopulation( Fetcher ):
	'''

		Purpose:
		--------
		Fetches WorldPop catalog and raster metadata records.

		Attributes:
		-----------
		base_url,
		stac_url,
		mode,
		query_text,
		asset_path,
		params,
		payload,

		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_normalize_asset_path(...): Performs the _normalize_asset_path operation for this fetcher.
		fetch_catalog(...): Performs the fetch_catalog operation for this fetcher.
		search_catalog(...): Performs the search_catalog operation for this fetcher.
		fetch_raster_metadata(...): Performs the fetch_raster_metadata operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.

	'''
	base_url: Optional[ str ]
	stac_url: Optional[ str ]
	mode: Optional[ str ]
	query_text: Optional[ str ]
	asset_path: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize the WorldPop API wrapper.

			Parameters:
			-----------
			None

			Returns:
			-----------
			None

		'''
		super( ).__init__( )
		self.base_url = 'https://api.worldpop.org/v1'
		self.stac_url = 'https://api.worldpop.org/stac'
		self.mode = 'catalog'
		self.query_text = ''
		self.asset_path = ''
		self.params = { }
		self.payload = { }
		self.headers = {
				'Accept': 'application/json, text/html',
				'User-Agent': cfg.AGENTS,
		}
		self.timeout = 20
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			-----------
			Return ordered WorldPopulation members.

			Parameters:
			-----------
			None

			Returns:
			-----------
			List[str]

		'''
		return [
				'base_url',
				'stac_url',
				'mode',
				'query_text',
				'asset_path',
				'params',
				'payload',
				'_normalize_asset_path',
				'fetch_catalog',
				'search_catalog',
				'fetch_raster_metadata',
				'fetch',
				'create_schema',
		]
	
	def _normalize_asset_path( self, asset_path: str ) -> str:
		'''
			Purpose:
			-----------
			Normalize an asset or metadata path appended to the WorldPop API.

			Parameters:
			-----------
			asset_path (str):
				Path appended after the API base endpoint.

			Returns:
			-----------
			str

		'''
		try:
			throw_if( 'asset_path', asset_path )
			value = str( asset_path ).strip( )
			value = value.lstrip( '/' )
			if not value:
				raise ValueError( "Argument 'asset_path' cannot be empty!" )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'WorldPopulation'
			exception.method = '_normalize_asset_path( self, asset_path: str ) -> str'
			raise exception
	
	def fetch_catalog( self, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the WorldPop API catalog or landing payload.

			Parameters:
			-----------
			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'catalog'
			self.url = self.base_url
			self.params = { }
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			content_type = str( self.response.headers.get( 'Content-Type', '' ) ).lower( )
			
			if 'application/json' in content_type:
				self.payload = self.response.json( )
			else:
				self.payload = {
						'html': self.response.text,
				}
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'WorldPopulation'
			exception.method = (
					'fetch_catalog( self, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def search_catalog( self, query: str='', page: int=1, page_size: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Execute a simple WorldPop catalog search request.

			Parameters:
			-----------
			query (str):
				Free-text search query.

			page (int):
				Page number.

			page_size (int):
				Requested page size.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'search'
			self.query_text = str( query or '' ).strip( )
			self.url = f'{self.base_url}/search'
			self.params = {
					'page': int( page ),
					'page_size': int( page_size ),
			}
			
			if self.query_text:
				self.params[ 'q' ]=self.query_text
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			content_type = str( self.response.headers.get( 'Content-Type', '' ) ).lower( )
			
			if 'application/json' in content_type:
				self.payload = self.response.json( )
			else:
				self.payload = {
						'text': self.response.text,
				}
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'WorldPopulation'
			exception.method = (
					'search_catalog( self, query: str="", page: int=1, '
					'page_size: int=25, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_raster_metadata( self, asset_path: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch metadata or asset information for a WorldPop raster path.

			Parameters:
			-----------
			asset_path (str):
				Path appended after the API base endpoint.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'raster_metadata'
			self.asset_path = self._normalize_asset_path( asset_path )
			self.url = f'{self.base_url}/{self.asset_path}'
			self.params = { }
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			content_type = str( self.response.headers.get( 'Content-Type', '' ) ).lower( )
			
			if 'application/json' in content_type:
				self.payload = self.response.json( )
			else:
				self.payload = {
						'text': self.response.text,
				}
			
			return {
					'mode': self.mode,
					'url': self.response.url,
					'params': self.params,
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'WorldPopulation'
			exception.method = (
					'fetch_raster_metadata( self, asset_path: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='catalog', query: str='',
			asset_path: str='', page: int=1, page_size: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Dispatch WorldPop API operations.

			Parameters:
			-----------
			mode (str):
				One of catalog, search, or raster_metadata.

			query (str):
				Free-text query for search mode.

			asset_path (str):
				Asset or metadata path for raster_metadata mode.

			page (int):
				Page number for search mode.

			page_size (int):
				Page size for search mode.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None

		'''
		try:
			active_mode = str( mode or 'catalog' ).strip( ).lower( )
			
			if active_mode == 'catalog':
				return self.fetch_catalog(
					time=int( time ) )
			
			if active_mode == 'search':
				return self.search_catalog(
					query=query,
					page=int( page ),
					page_size=int( page_size ),
					time=int( time ) )
			
			if active_mode == 'raster_metadata':
				return self.fetch_raster_metadata(
					asset_path=asset_path,
					time=int( time ) )
			
			raise ValueError(
				"mode must be one of: 'catalog', 'search', 'raster_metadata'."
			)
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'WorldPopulation'
			exception.method = (
					'fetch( self, mode: str="catalog", query: str="", asset_path: str="", '
					'page: int=1, page_size: int=25, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			-----------
			Construct and return a dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				Tool function name.

			tool (str):
				Service name.

			description (str):
				Description of what the tool does.

			parameters (dict):
				JSON-schema properties.

			required (list[str]):
				Required parameter names.

			Returns:
			-----------
			Dict[str, str] | None

		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError(
					'parameters must be a dict of param_name -> schema definition.'
				)
			
			func_name = function.strip( )
			tool_name = tool.strip( )
			desc = description.strip( )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			_schema = {
					'name': func_name,
					'description': f'{desc} This function uses the {tool_name} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required,
					}
			}
			
			return _schema
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'WorldPopulation'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class Wonder( Fetcher ):
	'''
	
		Purpose:
		--------
		Builds and submits CDC WONDER query templates.
	
		Attributes:
		-----------
		base_url,
		mode,
		dataset_id,
		request_xml,
		params,
		payload,
	
		Methods:
		--------
		__init__(...): Performs the __init__ operation for this fetcher.
		__dir__(...): Performs the __dir__ operation for this fetcher.
		_normalize_dataset_id(...): Performs the _normalize_dataset_id operation for this fetcher.
		build_template(...): Performs the build_template operation for this fetcher.
		fetch_template(...): Performs the fetch_template operation for this fetcher.
		submit_query(...): Performs the submit_query operation for this fetcher.
		fetch(...): Performs the fetch operation for this fetcher.
		create_schema(...): Performs the create_schema operation for this fetcher.
	
	'''
	base_url: Optional[ str ]
	mode: Optional[ str ]
	dataset_id: Optional[ str ]
	request_xml: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			-----------
			Initialize the CDC WONDER API wrapper.

			Parameters:
			-----------
			None

			Returns:
			-----------
			None

		'''
		super( ).__init__( )
		self.base_url = 'https://wonder.cdc.gov/controller/datarequest'
		self.mode = 'metadata_template'
		self.dataset_id = 'D76'
		self.request_xml = ''
		self.params = { }
		self.payload = { }
		self.headers = {
				'Accept': 'application/xml, text/xml, text/plain',
				'Content-Type': 'application/x-www-form-urlencoded',
				'User-Agent': cfg.AGENTS,
		}
		self.timeout = 20
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			-----------
			Return ordered Wonder members.

			Parameters:
			-----------
			None

			Returns:
			-----------
			List[str]

		'''
		return [
				'base_url',
				'mode',
				'dataset_id',
				'request_xml',
				'params',
				'payload',
				'_normalize_dataset_id',
				'build_template',
				'fetch_template',
				'submit_query',
				'fetch',
				'create_schema',
		]
	
	def _normalize_dataset_id( self, dataset_id: str ) -> str:
		'''
			Purpose:
			-----------
			Normalize the CDC WONDER database identifier.

			Parameters:
			-----------
			dataset_id (str):
				Database identifier such as D76.

			Returns:
			-----------
			str

		'''
		try:
			throw_if( 'dataset_id', dataset_id )
			value = str( dataset_id ).strip( ).upper( )
			if not value:
				raise ValueError( "Argument 'dataset_id' cannot be empty!" )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Wonder'
			exception.method = '_normalize_dataset_id( self, dataset_id: str ) -> str'
			raise exception
	
	def build_template( self, dataset_id: str='D76' ) -> str:
		'''
			Purpose:
			-----------
			Build a starter XML request document for a CDC WONDER query.

			Parameters:
			-----------
			dataset_id (str):
				Database identifier such as D76.

			Returns:
			-----------
			str

		'''
		try:
			self.dataset_id = self._normalize_dataset_id( dataset_id )
			
			return (
					f'<request>\n'
					f'  <request-parameters>\n'
					f'    <parameter>\n'
					f'      <name>accept_datause_restrictions</name>\n'
					f'      <value>true</value>\n'
					f'    </parameter>\n'
					f'    <parameter>\n'
					f'      <name>B_1</name>\n'
					f'      <value>{self.dataset_id}.V1</value>\n'
					f'    </parameter>\n'
					f'    <parameter>\n'
					f'      <name>M_1</name>\n'
					f'      <value>{self.dataset_id}.M1</value>\n'
					f'    </parameter>\n'
					f'    <parameter>\n'
					f'      <name>O_show_totals</name>\n'
					f'      <value>true</value>\n'
					f'    </parameter>\n'
					f'  </request-parameters>\n'
					f'</request>'
			)
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Wonder'
			exception.method = 'build_template( self, dataset_id: str="D76" ) -> str'
			raise exception
	
	def fetch_template( self, dataset_id: str='D76' ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			-----------
			Return a local CDC WONDER XML request template.

			Parameters:
			-----------
			dataset_id (str):
				Database identifier such as D76.

			Returns:
			-----------
			Dict[str, Any] | None

		'''
		try:
			self.mode = 'metadata_template'
			self.dataset_id = self._normalize_dataset_id( dataset_id )
			self.payload = {
					'dataset_id': self.dataset_id,
					'request_xml': self.build_template( dataset_id=self.dataset_id ),
					'notes': (
							'CDC WONDER expects POST requests to '
							'https://wonder.cdc.gov/controller/datarequest/[database ID] '
							'with a request_xml parameter and acceptance of data-use restrictions.'
					),
			}
			
			return {
					'mode': self.mode,
					'url': f'{self.base_url}/{self.dataset_id}',
					'params': { 'dataset_id': self.dataset_id },
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Wonder'
			exception.method = (
					'fetch_template( self, dataset_id: str="D76" ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def submit_query( self, dataset_id: str, request_xml: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			-----------
			Submit a CDC WONDER XML query request.

			Parameters:
			-----------
			dataset_id (str):
				Database identifier such as D76.

			request_xml (str):
				Full XML query document to POST as request_xml.

			time (int):
				Request timeout in seconds.

			Returns:
			-----------
			Dict[str, Any] | None

		'''
		try:
			throw_if( 'dataset_id', dataset_id )
			throw_if( 'request_xml', request_xml )
			
			self.mode = 'query_xml'
			self.dataset_id = self._normalize_dataset_id( dataset_id )
			self.request_xml = str( request_xml ).strip( )
			self.url = f'{self.base_url}/{self.dataset_id}'
			
			self.params = {
					'request_xml': self.request_xml,
					'accept_datause_restrictions': 'true',
			}
			
			self.response = requests.post(
				url=self.url,
				data=self.params,
				headers=self.headers,
				timeout=int( time ) )
			self.response.raise_for_status( )
			
			self.payload = {
					'xml': self.response.text,
			}
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': {
							'dataset_id': self.dataset_id,
							'accept_datause_restrictions': 'true',
					},
					'data': self.payload,
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Wonder'
			exception.method = (
					'submit_query( self, dataset_id: str, request_xml: str, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='metadata_template', dataset_id: str='D76',
			request_xml: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			-----------
			Dispatch CDC WONDER API operations.

			Parameters:
			-----------
			mode (str):
				One of metadata_template or query_xml.

			dataset_id (str):
				Database identifier such as D76.

			request_xml (str):
				Full XML request document for query_xml mode.

			time (int):
				Request timeout in seconds.

			Returns:
			-----------
			Dict[str, Any] | None

		'''
		try:
			active_mode = str( mode or 'metadata_template' ).strip( ).lower( )
			
			if active_mode == 'metadata_template':
				return self.fetch_template(
					dataset_id=dataset_id )
			
			if active_mode == 'query_xml':
				return self.submit_query(
					dataset_id=dataset_id,
					request_xml=request_xml,
					time=int( time ) )
			
			raise ValueError(
				"mode must be one of: 'metadata_template', 'query_xml'."
			)
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Wonder'
			exception.method = (
					'fetch( self, mode: str="metadata_template", dataset_id: str="D76", '
					'request_xml: str="", time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			-----------
			Construct and return a dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				Tool function name.

			tool (str):
				Service name.

			description (str):
				Description of what the tool does.

			parameters (dict):
				JSON-schema properties.

			required (list[str]):
				Required parameter names.

			Returns:
			-----------
			Dict[str, str] | None

		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if not isinstance( parameters, dict ):
				raise ValueError(
					'parameters must be a dict of param_name -> schema definition.'
				)
			
			func_name = function.strip( )
			tool_name = tool.strip( )
			desc = description.strip( )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			_schema = {
					'name': func_name,
					'description': f'{desc} This function uses the {tool_name} service.',
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required,
					}
			}
			
			return _schema
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Wonder'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class USGSEarthquakes( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to the U.S. Geological Survey (USGS) earthquake feeds and
		event search API for human-readable geospatial earthquake retrieval.

		Referenced API Requirements:
		----------------------------
		USGS GeoJSON Summary Feeds:
			- Endpoint:
			  https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/
			- Examples:
			  - all_hour.geojson
			  - all_day.geojson
			  - all_week.geojson
			  - all_month.geojson
			  - significant_day.geojson

		USGS Earthquake Catalog API:
			- Endpoint:
			  https://earthquake.usgs.gov/fdsnws/event/1/query
			- Required parameter used here:
			  - format=geojson
			- Optional parameters used here:
			  - starttime
			  - endtime
			  - minmagnitude
			  - maxmagnitude
			  - limit
			  - orderby
			  - eventtype
			  - latitude
			  - longitude
			  - maxradiuskm

	'''
	feed_url: Optional[ str ]
	search_url: Optional[ str ]
	mode: Optional[ str ]
	feed: Optional[ str ]
	start_date: Optional[ str ]
	end_date: Optional[ str ]
	min_magnitude: Optional[ float ]
	max_magnitude: Optional[ float ]
	limit: Optional[ int ]
	order_by: Optional[ str ]
	event_type: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	max_radius_km: Optional[ float ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Dict[ str, Any ] ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the USGS earthquake fetcher with feed and catalog endpoints.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.feed_url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary'
		self.search_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
		self.mode = 'feed'
		self.feed = 'all_day.geojson'
		self.start_date = ''
		self.end_date = ''
		self.min_magnitude = None
		self.max_magnitude = None
		self.limit = 25
		self.order_by = 'time'
		self.event_type = 'earthquake'
		self.latitude = None
		self.longitude = None
		self.max_radius_km = None
		self.params = { }
		self.payload = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'feed_url',
				'search_url',
				'mode',
				'feed',
				'start_date',
				'end_date',
				'min_magnitude',
				'max_magnitude',
				'limit',
				'order_by',
				'event_type',
				'latitude',
				'longitude',
				'max_radius_km',
				'params',
				'payload',
				'timeout',
				'_shape_feature_rows',
				'_summarize_features',
				'fetch_feed',
				'fetch_search',
				'fetch',
				'create_schema'
		]
	
	def _shape_feature_rows( self, features: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize USGS GeoJSON feature records into human-readable tabular rows.

			Parameters:
			-----------
			features (List[Dict[str, Any]]):
				Feature collection returned by the USGS feed or search API.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for feature in features or [ ]:
				properties = feature.get( 'properties', { } ) or { }
				geometry = feature.get( 'geometry', { } ) or { }
				coordinates = geometry.get( 'coordinates', [ ] ) or [ ]
				
				longitude = coordinates[ 0 ] if len( coordinates ) > 0 else None
				latitude = coordinates[ 1 ] if len( coordinates ) > 1 else None
				depth = coordinates[ 2 ] if len( coordinates ) > 2 else None
				
				epoch_ms = properties.get( 'time', None )
				updated_ms = properties.get( 'updated', None )
				
				event_time = None
				updated_time = None
				
				if epoch_ms is not None:
					try:
						event_time = dt.datetime.utcfromtimestamp(
							float( epoch_ms ) / 1000.0
						).strftime( '%Y-%m-%d %H:%M:%S UTC' )
					except Exception:
						event_time = str( epoch_ms )
				
				if updated_ms is not None:
					try:
						updated_time = dt.datetime.utcfromtimestamp(
							float( updated_ms ) / 1000.0
						).strftime( '%Y-%m-%d %H:%M:%S UTC' )
					except Exception:
						updated_time = str( updated_ms )
				
				rows.append(
					{
							'Id': feature.get( 'id', '' ),
							'Magnitude': properties.get( 'mag', None ),
							'Place': properties.get( 'place', '' ),
							'Time': event_time,
							'Updated': updated_time,
							'Alert': properties.get( 'alert', '' ),
							'Status': properties.get( 'status', '' ),
							'Tsunami': properties.get( 'tsunami', None ),
							'Felt Reports': properties.get( 'felt', None ),
							'Depth (km)': depth,
							'Latitude': latitude,
							'Longitude': longitude,
							'Event Type': properties.get( 'type', '' ),
							'URL': properties.get( 'url', '' )
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSEarthquakes'
			exception.method = (
					'_shape_feature_rows( self, features: List[ Dict[ str, Any ] ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_features( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Build a compact summary block from normalized earthquake rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized earthquake rows.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			max_magnitude = None
			strongest_place = ''
			most_recent = ''
			
			for row in rows or [ ]:
				magnitude = row.get( 'Magnitude', None )
				
				if magnitude is not None:
					try:
						if max_magnitude is None or float( magnitude ) > float( max_magnitude ):
							max_magnitude = float( magnitude )
							strongest_place = str( row.get( 'Place', '' ) )
					except Exception:
						pass
				
				if not most_recent and row.get( 'Time', '' ):
					most_recent = str( row.get( 'Time', '' ) )
			
			return {
					'count': count,
					'max_magnitude': max_magnitude,
					'strongest_place': strongest_place,
					'most_recent': most_recent
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSEarthquakes'
			exception.method = (
					'_summarize_features( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_feed( self, feed: str='all_day.geojson',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Retrieve one of the USGS real-time GeoJSON summary feeds.

			Parameters:
			-----------
			feed (str):
				Feed filename such as:
				- all_hour.geojson
				- all_day.geojson
				- all_week.geojson
				- all_month.geojson
				- significant_day.geojson

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'feed', feed )
			
			self.mode = 'feed'
			self.feed = str( feed ).strip( )
			self.params = { }
			self.url = f'{self.feed_url}/{self.feed}'
			
			self.response = requests.get(
				url=self.url,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( ) or { }
			features = self.payload.get( 'features', [ ] ) or [ ]
			rows = self._shape_feature_rows( features )
			
			return {
					'mode': self.mode,
					'feed': self.feed,
					'url': self.url,
					'params': self.params,
					'title': self.payload.get( 'metadata', { } ).get( 'title', '' ),
					'generated': self.payload.get( 'metadata', { } ).get( 'generated', None ),
					'count': self.payload.get( 'metadata', { } ).get( 'count', len( rows ) ),
					'bbox': self.payload.get( 'bbox', [ ] ),
					'summary': self._summarize_features( rows ),
					'rows': rows,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSEarthquakes'
			exception.method = (
					'fetch_feed( self, feed: str=all_day.geojson, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_search( self, start_date: str, end_date: str, min_magnitude: float=1.0,
			max_magnitude: float=10.0, limit: int=25, order_by: str='time',
			event_type: str='earthquake', latitude: float | None=None,
			longitude: float | None=None, max_radius_km: float | None=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Retrieve earthquake events from the USGS catalog search endpoint.

			Parameters:
			-----------
			start_date (str):
				Inclusive start date in YYYY-MM-DD format.

			end_date (str):
				Inclusive end date in YYYY-MM-DD format.

			min_magnitude (float):
				Minimum magnitude filter.

			max_magnitude (float):
				Maximum magnitude filter.

			limit (int):
				Maximum number of returned events.

			order_by (str):
				Catalog sort order such as:
				- time
				- time-asc
				- magnitude
				- magnitude-asc

			event_type (str):
				Event type filter, usually 'earthquake'.

			latitude (float | None):
				Optional latitude center for radial searches.

			longitude (float | None):
				Optional longitude center for radial searches.

			max_radius_km (float | None):
				Optional radial search distance in kilometers. Only used when both
				latitude and longitude are supplied.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'start_date', start_date )
			throw_if( 'end_date', end_date )
			
			self.mode = 'search'
			self.start_date = str( start_date ).strip( )
			self.end_date = str( end_date ).strip( )
			self.min_magnitude = float( min_magnitude )
			self.max_magnitude = float( max_magnitude )
			self.limit = max( 1, int( limit ) )
			self.order_by = str( order_by or 'time' ).strip( )
			self.event_type = str( event_type or 'earthquake' ).strip( )
			self.latitude = None if latitude is None else float( latitude )
			self.longitude = None if longitude is None else float( longitude )
			self.max_radius_km = None if max_radius_km is None else float( max_radius_km )
			
			self.params = {
					'format': 'geojson',
					'starttime': self.start_date,
					'endtime': self.end_date,
					'minmagnitude': self.min_magnitude,
					'maxmagnitude': self.max_magnitude,
					'limit': self.limit,
					'orderby': self.order_by,
					'eventtype': self.event_type
			}
			
			if self.latitude is not None and self.longitude is not None:
				self.params[ 'latitude' ]=self.latitude
				self.params[ 'longitude' ]=self.longitude
				
				if self.max_radius_km is not None:
					self.params[ 'maxradiuskm' ]=self.max_radius_km
			
			self.url = self.search_url
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( ) or { }
			features = self.payload.get( 'features', [ ] ) or [ ]
			rows = self._shape_feature_rows( features )
			
			return {
					'mode': self.mode,
					'url': self.url,
					'params': self.params,
					'title': self.payload.get( 'metadata', { } ).get( 'title', '' ),
					'generated': self.payload.get( 'metadata', { } ).get( 'generated', None ),
					'count': self.payload.get( 'metadata', { } ).get( 'count', len( rows ) ),
					'bbox': self.payload.get( 'bbox', [ ] ),
					'summary': self._summarize_features( rows ),
					'rows': rows,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSEarthquakes'
			exception.method = (
					'fetch_search( self, start_date: str, end_date: str, '
					'min_magnitude: float=1.0, max_magnitude: float=10.0, '
					'limit: int=25, order_by: str=time, event_type: str=earthquake, '
					'latitude: float | None=None, longitude: float | None=None, '
					'max_radius_km: float | None=None, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='feed', feed: str='all_day.geojson',
			start_date: str='', end_date: str='', min_magnitude: float=1.0,
			max_magnitude: float=10.0, limit: int=25, order_by: str='time',
			event_type: str='earthquake', latitude: float | None=None,
			longitude: float | None=None, max_radius_km: float | None=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for USGS earthquake feed and search retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- feed
				- search

			feed (str):
				USGS summary feed filename for feed mode.

			start_date (str):
				Start date for search mode.

			end_date (str):
				End date for search mode.

			min_magnitude (float):
				Minimum magnitude filter for search mode.

			max_magnitude (float):
				Maximum magnitude filter for search mode.

			limit (int):
				Maximum returned rows for search mode.

			order_by (str):
				Sort order for search mode.

			event_type (str):
				Event type for search mode.

			latitude (float | None):
				Optional latitude center for radial search mode.

			longitude (float | None):
				Optional longitude center for radial search mode.

			max_radius_km (float | None):
				Optional radial search distance.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'feed' ).strip( ).lower( )
			
			if active_mode == 'feed':
				return self.fetch_feed(
					feed=feed,
					time=int( time )
				)
			
			if active_mode == 'search':
				return self.fetch_search(
					start_date=start_date,
					end_date=end_date,
					min_magnitude=min_magnitude,
					max_magnitude=max_magnitude,
					limit=limit,
					order_by=order_by,
					event_type=event_type,
					latitude=latitude,
					longitude=longitude,
					max_radius_km=max_radius_km,
					time=int( time )
				)
			
			raise ValueError( "Unsupported mode. Use 'feed' or 'search'." )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSEarthquakes'
			exception.method = (
					'fetch( self, mode: str=feed, feed: str=all_day.geojson, '
					'start_date: str=, end_date: str=, min_magnitude: float=1.0, '
					'max_magnitude: float=10.0, limit: int=25, order_by: str=time, '
					'event_type: str=earthquake, latitude: float | None=None, '
					'longitude: float | None=None, max_radius_km: float | None=None, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSEarthquakes'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class USGSWaterData( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to the modern USGS Water Data APIs for monitoring
		locations, time-series metadata, latest continuous values, and latest
		daily values.

		Referenced API Requirements:
		----------------------------
		Base Endpoint:
			- https://api.waterdata.usgs.gov/ogcapi/v0

		Collections used here:
			- monitoring-locations
			- time-series-metadata
			- latest-continuous
			- latest-daily

		Optional Authentication:
			- X-Api-Key header
			- API keys increase rate limits but are not required for basic use

	'''
	base_url: Optional[ str ]
	mode: Optional[ str ]
	api_key: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Dict[ str, Any ] ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the USGS Water Data wrapper.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://api.waterdata.usgs.gov/ogcapi/v0'
		self.mode = 'monitoring-locations'
		self.api_key = self._resolve_api_key( )
		self.params = { }
		self.payload = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
		
		if self.api_key:
			self.headers[ 'X-Api-Key' ]=self.api_key
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'mode',
				'api_key',
				'params',
				'payload',
				'timeout',
				'_resolve_api_key',
				'_coalesce',
				'request',
				'_shape_monitoring_locations',
				'_shape_time_series_metadata',
				'_shape_latest_values',
				'_summarize_rows',
				'fetch_monitoring_locations',
				'fetch_time_series_metadata',
				'fetch_latest_continuous',
				'fetch_latest_daily',
				'fetch',
				'create_schema'
		]
	
	def _resolve_api_key( self ) -> Optional[ str ]:
		'''
			Purpose:
			--------
			Resolve an API key for the USGS Water Data APIs.

			Parameters:
			-----------
			None

			Returns:
			--------
			Optional[str]
		'''
		try:
			candidates: List[ Optional[ str ] ]=[
					os.getenv( 'USGS_WATERDATA_API_KEY' ),
					os.getenv( 'DATA_GOV_API_KEY' ),
					os.getenv( 'GOVINFO_API_KEY' )
			]
			
			for candidate in candidates:
				if candidate is not None and str( candidate ).strip( ):
					return str( candidate ).strip( )
			
			return None
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = '_resolve_api_key( self ) -> Optional[ str ]'
			raise exception
	
	def _coalesce( self, payload: Any ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize several possible USGS Water Data response layouts into a list
			of record dictionaries.

			Parameters:
			-----------
			payload (Any):
				Decoded JSON payload returned by the API.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			if isinstance( payload, list ):
				return [ item for item in payload if isinstance( item, dict ) ]
			
			if not isinstance( payload, dict ):
				return [ ]
			
			for key in [ 'features', 'value', 'items', 'data' ]:
				value = payload.get( key, None )
				if isinstance( value, list ):
					return [ item for item in value if isinstance( item, dict ) ]
			
			return [ ]
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = '_coalesce( self, payload: Any ) -> List[ Dict[ str, Any ] ]'
			raise exception
	
	def request( self, collection: str,
			params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to a USGS Water Data collection endpoint.

			Parameters:
			-----------
			collection (str):
				Collection name under the OGC API base path.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'collection', collection )
			
			self.url = f'{self.base_url}/collections/{str( collection ).strip( )}'
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( ) or { }
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'request( self, collection: str, '
					'params: Optional[ Dict[ str, Any ] ]=None, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_monitoring_locations( self,
			records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize monitoring-location records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Monitoring location records.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				properties = item.get( 'properties', { } ) or item
				geometry = item.get( 'geometry', { } ) or { }
				coordinates = geometry.get( 'coordinates', [ ] ) or [ ]
				
				longitude = coordinates[
					0 ] if len( coordinates ) > 0 else properties.get( 'longitude', None )
				latitude = coordinates[
					1 ] if len( coordinates ) > 1 else properties.get( 'latitude', None )
				
				identifier = (
						properties.get( 'monitoring_location_id', None ) or
						properties.get( 'monitoringLocationIdentifier', None ) or
						properties.get( 'site_no', None ) or
						properties.get( 'siteNumber', None ) or
						item.get( 'id', '' )
				)
				
				name = (
						properties.get( 'monitoring_location_name', None ) or
						properties.get( 'monitoringLocationName', None ) or
						properties.get( 'site_name', None ) or
						properties.get( 'siteName', '' )
				)
				
				state = (
						properties.get( 'state', None ) or
						properties.get( 'state_code', None ) or
						properties.get( 'stateCode', '' )
				)
				
				county = (
						properties.get( 'county', None ) or
						properties.get( 'county_name', None ) or
						properties.get( 'countyName', '' )
				)
				
				site_type = (
						properties.get( 'site_type', None ) or
						properties.get( 'siteType', '' )
				)
				
				huc = (
						properties.get( 'huc', None ) or
						properties.get( 'huc_cd', None ) or
						properties.get( 'hucCode', '' )
				)
				
				rows.append(
					{
							'Monitoring Location ID': identifier,
							'Name': name,
							'Site Type': site_type,
							'State': state,
							'County': county,
							'HUC': huc,
							'Latitude': latitude,
							'Longitude': longitude
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'_shape_monitoring_locations( self, records: '
					'List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _shape_time_series_metadata( self,
			records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize time-series metadata records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Time-series metadata records.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				properties = item.get( 'properties', { } ) or item
				
				rows.append(
					{
							'Monitoring Location ID': (
									properties.get( 'monitoring_location_id', None ) or
									properties.get( 'monitoringLocationIdentifier', None ) or
									properties.get( 'site_no', '' )
							),
							'Parameter Code': (
									properties.get( 'parameter_code', None ) or
									properties.get( 'parameterCode', '' )
							),
							'Parameter Name': (
									properties.get( 'parameter_name', None ) or
									properties.get( 'parameterName', '' )
							),
							'Statistic ID': (
									properties.get( 'statistic_id', None ) or
									properties.get( 'statisticId', '' )
							),
							'Statistic Name': (
									properties.get( 'statistic_name', None ) or
									properties.get( 'statisticName', '' )
							),
							'Unit': (
									properties.get( 'unit_of_measure', None ) or
									properties.get( 'unitOfMeasure', '' )
							),
							'Begin Time': (
									properties.get( 'begin_time', None ) or
									properties.get( 'beginTime', '' )
							),
							'End Time': (
									properties.get( 'end_time', None ) or
									properties.get( 'endTime', '' )
							)
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'_shape_time_series_metadata( self, records: '
					'List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _shape_latest_values( self,
			records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize latest continuous or daily value records into a readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Value records.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				properties = item.get( 'properties', { } ) or item
				
				rows.append(
					{
							'Monitoring Location ID': (
									properties.get( 'monitoring_location_id', None ) or
									properties.get( 'monitoringLocationIdentifier', None ) or
									properties.get( 'site_no', '' )
							),
							'Name': (
									properties.get( 'monitoring_location_name', None ) or
									properties.get( 'monitoringLocationName', None ) or
									properties.get( 'site_name', '' )
							),
							'Parameter Code': (
									properties.get( 'parameter_code', None ) or
									properties.get( 'parameterCode', '' )
							),
							'Parameter Name': (
									properties.get( 'parameter_name', None ) or
									properties.get( 'parameterName', '' )
							),
							'Statistic ID': (
									properties.get( 'statistic_id', None ) or
									properties.get( 'statisticId', '' )
							),
							'Value': (
									properties.get( 'result_value', None ) or
									properties.get( 'value', None ) or
									properties.get( 'primary_value', '' )
							),
							'Unit': (
									properties.get( 'unit_of_measure', None ) or
									properties.get( 'unitOfMeasure', '' )
							),
							'Time': (
									properties.get( 'time', None ) or
									properties.get( 'result_time', None ) or
									properties.get( 'resultTime', '' )
							),
							'Approval Status': (
									properties.get( 'approval_status', None ) or
									properties.get( 'approvalStatus', '' )
							)
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'_shape_latest_values( self, records: '
					'List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			first_site = ''
			first_parameter = ''
			first_value = ''
			
			if rows:
				first_site = str(
					rows[ 0 ].get( 'Name', '' ) or
					rows[ 0 ].get( 'Monitoring Location ID', '' ) or ''
				)
				first_parameter = str( rows[ 0 ].get( 'Parameter Name', '' ) or '' )
				first_value = str( rows[ 0 ].get( 'Value', '' ) or '' )
			
			return {
					'count': count,
					'first_site': first_site,
					'first_parameter': first_parameter,
					'first_value': first_value
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_monitoring_locations( self, monitoring_location_id: str='',
			state_code: str='', county_code: str='', site_type: str='',
			limit: int=25, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch monitoring locations.

			Parameters:
			-----------
			monitoring_location_id (str):
				Optional monitoring location identifier such as USGS-01491000.

			state_code (str):
				Optional state filter.

			county_code (str):
				Optional county filter.

			site_type (str):
				Optional site type filter.

			limit (int):
				Maximum rows requested.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'monitoring-locations'
			base = self.request(
				collection='monitoring-locations',
				params={
						'monitoring_location_id': str( monitoring_location_id ).strip( ),
						'state_code': str( state_code ).strip( ),
						'county_code': str( county_code ).strip( ),
						'site_type': str( site_type ).strip( ),
						'limit': max( 1, int( limit ) )
				},
				time=int( time )
			) or { }
			
			records = self._coalesce( base.get( 'raw', { } ) )
			rows = self._shape_monitoring_locations( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'fetch_monitoring_locations( self, monitoring_location_id: str=, '
					'state_code: str=, county_code: str=, site_type: str=, '
					'limit: int=25, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_time_series_metadata( self, monitoring_location_id: str='',
			parameter_code: str='', limit: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch time-series metadata for a monitoring location and optional
			parameter code.

			Parameters:
			-----------
			monitoring_location_id (str):
				Optional monitoring location identifier.

			parameter_code (str):
				Optional USGS parameter code.

			limit (int):
				Maximum rows requested.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'time-series-metadata'
			base = self.request(
				collection='time-series-metadata',
				params={
						'monitoring_location_id': str( monitoring_location_id ).strip( ),
						'parameter_code': str( parameter_code ).strip( ),
						'limit': max( 1, int( limit ) )
				},
				time=int( time )
			) or { }
			
			records = self._coalesce( base.get( 'raw', { } ) )
			rows = self._shape_time_series_metadata( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'fetch_time_series_metadata( self, monitoring_location_id: str=, '
					'parameter_code: str=, limit: int=25, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_latest_continuous( self, monitoring_location_id: str='',
			parameter_code: str='', limit: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the latest continuous values for a monitoring location.

			Parameters:
			-----------
			monitoring_location_id (str):
				Optional monitoring location identifier.

			parameter_code (str):
				Optional USGS parameter code.

			limit (int):
				Maximum rows requested.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'latest-continuous'
			base = self.request(
				collection='latest-continuous',
				params={
						'monitoring_location_id': str( monitoring_location_id ).strip( ),
						'parameter_code': str( parameter_code ).strip( ),
						'limit': max( 1, int( limit ) )
				},
				time=int( time )
			) or { }
			
			records = self._coalesce( base.get( 'raw', { } ) )
			rows = self._shape_latest_values( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'fetch_latest_continuous( self, monitoring_location_id: str=, '
					'parameter_code: str=, limit: int=25, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_latest_daily( self, monitoring_location_id: str='',
			parameter_code: str='', limit: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch the latest daily values for a monitoring location.

			Parameters:
			-----------
			monitoring_location_id (str):
				Optional monitoring location identifier.

			parameter_code (str):
				Optional USGS parameter code.

			limit (int):
				Maximum rows requested.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'latest-daily'
			base = self.request(
				collection='latest-daily',
				params={
						'monitoring_location_id': str( monitoring_location_id ).strip( ),
						'parameter_code': str( parameter_code ).strip( ),
						'limit': max( 1, int( limit ) )
				},
				time=int( time )
			) or { }
			
			records = self._coalesce( base.get( 'raw', { } ) )
			rows = self._shape_latest_values( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'fetch_latest_daily( self, monitoring_location_id: str=, '
					'parameter_code: str=, limit: int=25, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='monitoring-locations',
			monitoring_location_id: str='', state_code: str='',
			county_code: str='', site_type: str='',
			parameter_code: str='', limit: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for USGS Water Data retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- monitoring-locations
				- time-series-metadata
				- latest-continuous
				- latest-daily

			monitoring_location_id (str):
				Optional monitoring location identifier.

			state_code (str):
				Optional state filter for monitoring locations.

			county_code (str):
				Optional county filter for monitoring locations.

			site_type (str):
				Optional site type filter for monitoring locations.

			parameter_code (str):
				Optional USGS parameter code.

			limit (int):
				Maximum rows requested.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'monitoring-locations' ).strip( ).lower( )
			
			if active_mode == 'monitoring-locations':
				return self.fetch_monitoring_locations(
					monitoring_location_id=monitoring_location_id,
					state_code=state_code,
					county_code=county_code,
					site_type=site_type,
					limit=limit,
					time=int( time )
				)
			
			if active_mode == 'time-series-metadata':
				return self.fetch_time_series_metadata(
					monitoring_location_id=monitoring_location_id,
					parameter_code=parameter_code,
					limit=limit,
					time=int( time )
				)
			
			if active_mode == 'latest-continuous':
				return self.fetch_latest_continuous(
					monitoring_location_id=monitoring_location_id,
					parameter_code=parameter_code,
					limit=limit,
					time=int( time )
				)
			
			if active_mode == 'latest-daily':
				return self.fetch_latest_daily(
					monitoring_location_id=monitoring_location_id,
					parameter_code=parameter_code,
					limit=limit,
					time=int( time )
				)
			
			raise ValueError(
				"Unsupported mode. Use 'monitoring-locations', "
				"'time-series-metadata', 'latest-continuous', or 'latest-daily'."
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'fetch( self, mode: str=monitoring-locations, '
					'monitoring_location_id: str=, state_code: str=, '
					'county_code: str=, site_type: str=, parameter_code: str=, '
					'limit: int=25, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSWaterData'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class USGSTheNationalMap( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to the USGS The National Map (TNM) TNMAccess API for
		dataset discovery and downloadable product search.

		Referenced API Requirements:
		----------------------------
		Base Endpoint:
			- https://tnmaccess.nationalmap.gov/api/v1

		Resources used here:
			- /datasets
			- /products

		Common product query concepts:
			- datasets
			- q
			- bbox
			- prodFormats
			- max
			- offset

	'''
	base_url: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Dict[ str, Any ] ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the USGS The National Map wrapper.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://tnmaccess.nationalmap.gov/api/v1'
		self.mode = 'products'
		self.params = { }
		self.payload = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'mode',
				'params',
				'payload',
				'timeout',
				'request',
				'_coalesce',
				'_shape_dataset_rows',
				'_shape_product_rows',
				'_summarize_rows',
				'fetch_datasets',
				'fetch_products',
				'fetch',
				'create_schema'
		]
	
	def request( self, endpoint: str,
			params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to a TNMAccess endpoint.

			Parameters:
			-----------
			endpoint (str):
				Endpoint path under the TNMAccess base URL.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'endpoint', endpoint )
			
			self.url = f'{self.base_url}/{str( endpoint ).strip( )}'
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( ) or { }
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = (
					'request( self, endpoint: str, '
					'params: Optional[ Dict[ str, Any ] ]=None, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _coalesce( self, payload: Any ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize possible TNMAccess response layouts into a list of records.

			Parameters:
			-----------
			payload (Any):
				Decoded JSON payload returned by the API.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			if isinstance( payload, list ):
				return [ item for item in payload if isinstance( item, dict ) ]
			
			if not isinstance( payload, dict ):
				return [ ]
			
			for key in [ 'items', 'datasets', 'data', 'results' ]:
				value = payload.get( key, None )
				if isinstance( value, list ):
					return [ item for item in value if isinstance( item, dict ) ]
			
			return [ ]
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = '_coalesce( self, payload: Any ) -> List[ Dict[ str, Any ] ]'
			raise exception
	
	def _shape_dataset_rows( self,
			records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize TNM dataset records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Dataset records returned by TNMAccess.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				rows.append(
					{
							'Id': item.get( 'id', '' ),
							'Dataset': (
									item.get( 'sbDatasetTag', None ) or
									item.get( 'dataset', None ) or
									item.get( 'tag', '' )
							),
							'Name': (
									item.get( 'sbDatasetName', None ) or
									item.get( 'name', '' )
							),
							'Category': item.get( 'category', '' ),
							'Type': item.get( 'type', '' ),
							'Description': (
									item.get( 'description', None ) or
									item.get( 'summary', '' )
							)
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = (
					'_shape_dataset_rows( self, records: '
					'List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _shape_product_rows( self,
			records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize TNM product records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Product records returned by TNMAccess.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				download_url = (
						item.get( 'downloadURL', None ) or
						item.get( 'downloadUrl', None ) or
						item.get( 'url', '' )
				)
				
				meta_url = (
						item.get( 'metaUrl', None ) or
						item.get( 'metadataURL', None ) or
						item.get( 'metadataUrl', '' )
				)
				
				formats = item.get( 'format', None )
				if isinstance( formats, list ):
					formats = ', '.join( [ str( value ) for value in formats ] )
				
				rows.append(
					{
							'Id': (
									item.get( 'sourceId', None ) or
									item.get( 'id', '' )
							),
							'Title': (
									item.get( 'title', None ) or
									item.get( 'name', '' )
							),
							'Dataset': (
									item.get( 'sbDatasetTag', None ) or
									item.get( 'dataset', '' )
							),
							'Format': (
									formats or
									item.get( 'format', '' )
							),
							'Publication Date': (
									item.get( 'publicationDate', None ) or
									item.get( 'lastUpdated', '' )
							),
							'Bounding Box': (
									item.get( 'boundingBox', None ) or
									item.get( 'bbox', '' )
							),
							'Download URL': download_url,
							'Metadata URL': meta_url
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = (
					'_shape_product_rows( self, records: '
					'List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			first_title = ''
			first_dataset = ''
			
			if rows:
				first_title = str(
					rows[ 0 ].get( 'Title', '' ) or
					rows[ 0 ].get( 'Name', '' ) or ''
				)
				first_dataset = str( rows[ 0 ].get( 'Dataset', '' ) or '' )
			
			return {
					'count': count,
					'first_title': first_title,
					'first_dataset': first_dataset
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_datasets( self, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch dataset metadata from TNMAccess.

			Parameters:
			-----------
			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'datasets'
			base = self.request(
				endpoint='datasets',
				params={ },
				time=int( time )
			) or { }
			
			records = self._coalesce( base.get( 'raw', { } ) )
			rows = self._shape_dataset_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = 'fetch_datasets( self, time: int=20 ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_products( self, dataset: str='', q: str='',
			bbox: str='', prod_formats: str='', max_items: int=25,
			offset: int=0, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch downloadable product records from TNMAccess.

			Parameters:
			-----------
			dataset (str):
				Optional TNM dataset filter.

			q (str):
				Optional free-text search string.

			bbox (str):
				Optional bounding box in minx,miny,maxx,maxy format.

			prod_formats (str):
				Optional product format filter such as GeoTIFF, IMG, LAS, or LAZ.

			max_items (int):
				Maximum number of returned products.

			offset (int):
				Result offset for paging.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'products'
			base = self.request(
				endpoint='products',
				params={
						'datasets': str( dataset ).strip( ),
						'q': str( q ).strip( ),
						'bbox': str( bbox ).strip( ),
						'prodFormats': str( prod_formats ).strip( ),
						'max': max( 1, int( max_items ) ),
						'offset': max( 0, int( offset ) )
				},
				time=int( time )
			) or { }
			
			records = self._coalesce( base.get( 'raw', { } ) )
			rows = self._shape_product_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = (
					'fetch_products( self, dataset: str=, q: str=, bbox: str=, '
					'prod_formats: str=, max_items: int=25, offset: int=0, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='products', dataset: str='',
			q: str='', bbox: str='', prod_formats: str='',
			max_items: int=25, offset: int=0,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for TNMAccess dataset and product retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- datasets
				- products

			dataset (str):
				Optional TNM dataset filter for product search.

			q (str):
				Optional free-text search string for product search.

			bbox (str):
				Optional bounding box string for product search.

			prod_formats (str):
				Optional format filter for product search.

			max_items (int):
				Maximum returned products.

			offset (int):
				Result offset for paging.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'products' ).strip( ).lower( )
			
			if active_mode == 'datasets':
				return self.fetch_datasets(
					time=int( time )
				)
			
			if active_mode == 'products':
				return self.fetch_products(
					dataset=dataset,
					q=q,
					bbox=bbox,
					prod_formats=prod_formats,
					max_items=max_items,
					offset=offset,
					time=int( time )
				)
			
			raise ValueError( "Unsupported mode. Use 'datasets' or 'products'." )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = (
					'fetch( self, mode: str=products, dataset: str=, q: str=, '
					'bbox: str=, prod_formats: str=, max_items: int=25, '
					'offset: int=0, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSTheNationalMap'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class USGSScienceBase( Fetcher ):
	'''
		Purpose:
		--------
		Provides read-only access to the USGS ScienceBase REST/JSON API for
		item search and item retrieval.

		Referenced API Requirements:
		----------------------------
		Base Endpoint:
			- https://www.sciencebase.gov/catalog

		Resources used here:
			- /items
			- /item/{id}

		Common query concepts:
			- q
			- max
			- offset
			- fields

	'''
	base_url: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Dict[ str, Any ] ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the USGS ScienceBase wrapper.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://www.sciencebase.gov/catalog'
		self.mode = 'items'
		self.params = { }
		self.payload = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'mode',
				'params',
				'payload',
				'timeout',
				'request',
				'_coalesce',
				'_shape_item_rows',
				'_shape_single_item',
				'_summarize_rows',
				'fetch_items',
				'fetch_item',
				'fetch',
				'create_schema'
		]
	
	def request( self, endpoint: str,
			params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to a ScienceBase endpoint.

			Parameters:
			-----------
			endpoint (str):
				Endpoint path under the ScienceBase base URL.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'endpoint', endpoint )
			
			self.url = f'{self.base_url}/{str( endpoint ).strip( )}'
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( ) or { }
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = (
					'request( self, endpoint: str, '
					'params: Optional[ Dict[ str, Any ] ]=None, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _coalesce( self, payload: Any ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize possible ScienceBase response layouts into a list of items.

			Parameters:
			-----------
			payload (Any):
				Decoded JSON payload returned by the API.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			if isinstance( payload, list ):
				return [ item for item in payload if isinstance( item, dict ) ]
			
			if not isinstance( payload, dict ):
				return [ ]
			
			for key in [ 'items', 'results', 'data' ]:
				value = payload.get( key, None )
				if isinstance( value, list ):
					return [ item for item in value if isinstance( item, dict ) ]
			
			if 'id' in payload and isinstance( payload.get( 'id' ), str ):
				return [ payload ]
			
			return [ ]
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = '_coalesce( self, payload: Any ) -> List[ Dict[ str, Any ] ]'
			raise exception
	
	def _shape_item_rows( self,
			records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize ScienceBase item records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Item records returned by ScienceBase.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				title = item.get( 'title', '' )
				item_id = item.get( 'id', '' )
				item_type = item.get( 'itemType', '' )
				summary = (
						item.get( 'summary', None ) or
						item.get( 'body', None ) or
						''
				)
				
				if isinstance( summary, str ) and len( summary ) > 300:
					summary = summary[ :300 ].rstrip( ) + '...'
				
				has_spatial = False
				if item.get( 'spatial', None ) is not None:
					has_spatial = True
				if item.get( 'facets', None ):
					try:
						for facet in item.get( 'facets', [ ] ) or [ ]:
							if isinstance( facet, dict ) and facet.get( 'boundingBox', None ) is not None:
								has_spatial = True
								break
					except Exception:
						pass
				
				dates = item.get( 'dates', [ ] ) or [ ]
				latest_date = ''
				if isinstance( dates, list ) and dates:
					first_date = dates[ 0 ]
					if isinstance( first_date, dict ):
						latest_date = (
								first_date.get( 'dateString', None ) or
								first_date.get( 'date', '' )
						)
				
				rows.append(
					{
							'Id': item_id,
							'Title': title,
							'Type': item_type,
							'Updated': (
									item.get( 'dateUpdated', None ) or
									item.get( 'lastUpdated', None ) or
									latest_date
							),
							'Has Spatial Metadata': has_spatial,
							'Summary': summary
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = (
					'_shape_item_rows( self, records: '
					'List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _shape_single_item( self, item: Dict[ str, Any ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Normalize a single ScienceBase item into a readable detail dictionary.

			Parameters:
			-----------
			item (Dict[str, Any]):
				Single item payload returned by ScienceBase.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			files_value = item.get( 'files', [ ] ) or [ ]
			file_count = len( files_value ) if isinstance( files_value, list ) else 0
			
			web_links = item.get( 'webLinks', [ ] ) or [ ]
			link_count = len( web_links ) if isinstance( web_links, list ) else 0
			
			contacts = item.get( 'contacts', [ ] ) or [ ]
			contact_count = len( contacts ) if isinstance( contacts, list ) else 0
			
			return {
					'Id': item.get( 'id', '' ),
					'Title': item.get( 'title', '' ),
					'Type': item.get( 'itemType', '' ),
					'Updated': (
							item.get( 'dateUpdated', None ) or
							item.get( 'lastUpdated', '' )
					),
					'Summary': (
							item.get( 'summary', None ) or
							item.get( 'body', '' )
					),
					'Has Spatial Metadata': item.get( 'spatial', None ) is not None,
					'File Count': file_count,
					'Web Link Count': link_count,
					'Contact Count': contact_count,
					'Raw Item': item
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = (
					'_shape_single_item( self, item: Dict[ str, Any ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			first_title = ''
			first_type = ''
			spatial_count = 0
			
			for row in rows or [ ]:
				if row.get( 'Has Spatial Metadata', False ):
					spatial_count += 1
			
			if rows:
				first_title = str( rows[ 0 ].get( 'Title', '' ) or '' )
				first_type = str( rows[ 0 ].get( 'Type', '' ) or '' )
			
			return {
					'count': count,
					'first_title': first_title,
					'first_type': first_type,
					'spatial_count': spatial_count
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_items( self, q: str='', max_items: int=25,
			offset: int=0, fields: str='',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Search ScienceBase items.

			Parameters:
			-----------
			q (str):
				Optional search query string.

			max_items (int):
				Maximum number of returned items.

			offset (int):
				Result offset for paging.

			fields (str):
				Optional fields selector.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'items'
			base = self.request(
				endpoint='items',
				params={
						'q': str( q ).strip( ),
						'max': max( 1, int( max_items ) ),
						'offset': max( 0, int( offset ) ),
						'fields': str( fields ).strip( )
				},
				time=int( time )
			) or { }
			
			records = self._coalesce( base.get( 'raw', { } ) )
			rows = self._shape_item_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = (
					'fetch_items( self, q: str=, max_items: int=25, offset: int=0, '
					'fields: str=, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_item( self, item_id: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Retrieve a single ScienceBase item by identifier.

			Parameters:
			-----------
			item_id (str):
				ScienceBase item identifier.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'item_id', item_id )
			
			self.mode = 'item'
			base = self.request(
				endpoint=f'item/{str( item_id ).strip( )}',
				params={ },
				time=int( time )
			) or { }
			
			item = base.get( 'raw', { } ) or { }
			detail = self._shape_single_item( item )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': {
							'count': 1,
							'first_title': detail.get( 'Title', '' ),
							'first_type': detail.get( 'Type', '' ),
							'spatial_count': 1 if detail.get( 'Has Spatial Metadata', False ) else 0
					},
					'rows': [ detail ],
					'raw': base.get( 'raw', { } )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = (
					'fetch_item( self, item_id: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='items', q: str='',
			item_id: str='', max_items: int=25, offset: int=0,
			fields: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for ScienceBase item search and item retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- items
				- item

			q (str):
				Optional search query for items mode.

			item_id (str):
				Item identifier for item mode.

			max_items (int):
				Maximum number of items returned in items mode.

			offset (int):
				Result offset for items mode.

			fields (str):
				Optional fields selector for items mode.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'items' ).strip( ).lower( )
			
			if active_mode == 'items':
				return self.fetch_items(
					q=q,
					max_items=max_items,
					offset=offset,
					fields=fields,
					time=int( time )
				)
			
			if active_mode == 'item':
				return self.fetch_item(
					item_id=item_id,
					time=int( time )
				)
			
			raise ValueError( "Unsupported mode. Use 'items' or 'item'." )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = (
					'fetch( self, mode: str=items, q: str=, item_id: str=, '
					'max_items: int=25, offset: int=0, fields: str=, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'USGSScienceBase'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class AirNow( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to the AirNow API for current observations and forecasts by
		Zip code or latitude/longitude, returning human-readable normalized rows.

		Referenced API Requirements:
		----------------------------
		AirNow Web Services support:
			- Current observations by Zip code
			- Current observations by latitude/longitude
			- Forecasts by Zip code
			- Forecasts by latitude/longitude

		Optional Authentication:
			- API key required by AirNow web services

	'''
	base_url: Optional[ str ]
	api_key: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the AirNow fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://www.airnowapi.org/aq'
		self.api_key = self._resolve_api_key( )
		self.mode = 'current-zip'
		self.params = { }
		self.payload = [ ]
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'api_key',
				'mode',
				'params',
				'payload',
				'timeout',
				'_resolve_api_key',
				'request',
				'_shape_rows',
				'_summarize_rows',
				'fetch_current_zip',
				'fetch_current_latlon',
				'fetch_forecast_zip',
				'fetch_forecast_latlon',
				'fetch',
				'create_schema'
		]
	
	def _resolve_api_key( self ) -> Optional[ str ]:
		'''
			Purpose:
			--------
			Resolve the AirNow API key from environment variables.

			Parameters:
			-----------
			None

			Returns:
			--------
			Optional[str]
		'''
		try:
			candidates: List[ Optional[ str ] ]=[
					os.getenv( 'AIRNOW_API_KEY' ),
					os.getenv( 'EPA_AIRNOW_API_KEY' )
			]
			
			for candidate in candidates:
				if candidate is not None and str( candidate ).strip( ):
					return str( candidate ).strip( )
			
			return None
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = '_resolve_api_key( self ) -> Optional[ str ]'
			raise exception
	
	def request( self, endpoint: str, params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to an AirNow endpoint.

			Parameters:
			-----------
			endpoint (str):
				Endpoint path under the AirNow base URL.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'endpoint', endpoint )
			
			if self.api_key is None or not str( self.api_key ).strip( ):
				raise ValueError(
					'AirNow API key not found. Set AIRNOW_API_KEY or EPA_AIRNOW_API_KEY.'
				)
			
			self.url = f'{self.base_url}/{str( endpoint ).strip( )}'
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.params[ 'format' ]='application/json'
			self.params[ 'API_KEY' ]=self.api_key
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'request( self, endpoint: str, params: Optional[ Dict[ str, Any ] ]=None, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_rows( self, records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize AirNow records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				AirNow records returned by the API.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				rows.append(
					{
							'Date Observed': item.get( 'DateObserved', '' ),
							'Hour Observed': item.get( 'HourObserved', '' ),
							'Local Time Zone': item.get( 'LocalTimeZone', '' ),
							'Reporting Area': item.get( 'ReportingArea', '' ),
							'State Code': item.get( 'StateCode', '' ),
							'Latitude': item.get( 'Latitude', None ),
							'Longitude': item.get( 'Longitude', None ),
							'Parameter Name': item.get( 'ParameterName', '' ),
							'AQI': item.get( 'AQI', None ),
							'Category': (
									(item.get( 'Category', { } ) or { }).get( 'Name', '' )
									if isinstance( item.get( 'Category', { } ), dict )
									else ''
							),
							'Action Day': item.get( 'ActionDay', '' ),
							'Discussion': item.get( 'Discussion', '' )
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'_shape_rows( self, records: List[ Dict[ str, Any ] ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized AirNow rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized AirNow row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			max_aqi = None
			dominant_parameter = ''
			top_category = ''
			reporting_area = ''
			
			for row in rows or [ ]:
				if not reporting_area and row.get( 'Reporting Area', '' ):
					reporting_area = str( row.get( 'Reporting Area', '' ) )
				
				aqi_value = row.get( 'AQI', None )
				try:
					if aqi_value is not None:
						if max_aqi is None or float( aqi_value ) > float( max_aqi ):
							max_aqi = float( aqi_value )
							dominant_parameter = str( row.get( 'Parameter Name', '' ) or '' )
							top_category = str( row.get( 'Category', '' ) or '' )
				except Exception:
					pass
			
			return {
					'count': count,
					'max_aqi': max_aqi,
					'dominant_parameter': dominant_parameter,
					'top_category': top_category,
					'reporting_area': reporting_area
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_current_zip( self, zip_code: str, distance: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch current AQI observations by Zip code.

			Parameters:
			-----------
			zip_code (str):
				U.S. Zip code.

			distance (int):
				Radius distance in miles.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'zip_code', zip_code )
			
			self.mode = 'current-zip'
			base = self.request(
				endpoint='observation/zipCode/current/',
				params={
						'zipCode': str( zip_code ).strip( ),
						'distance': max( 0, int( distance ) )
				},
				time=int( time )
			) or { }
			
			records = base.get( 'raw', [ ] ) or [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', [ ] )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'fetch_current_zip( self, zip_code: str, distance: int=25, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_current_latlon( self, latitude: float, longitude: float,
			distance: int=25, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch current AQI observations by latitude and longitude.

			Parameters:
			-----------
			latitude (float):
				Latitude of the query point.

			longitude (float):
				Longitude of the query point.

			distance (int):
				Radius distance in miles.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'current-latlon'
			base = self.request(
				endpoint='observation/latLong/current/',
				params={
						'latitude': float( latitude ),
						'longitude': float( longitude ),
						'distance': max( 0, int( distance ) )
				},
				time=int( time )
			) or { }
			
			records = base.get( 'raw', [ ] ) or [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', [ ] )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'fetch_current_latlon( self, latitude: float, longitude: float, '
					'distance: int=25, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_forecast_zip( self, zip_code: str, date: str,
			distance: int=25, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch AQI forecasts by Zip code.

			Parameters:
			-----------
			zip_code (str):
				U.S. Zip code.

			date (str):
				Forecast date in YYYY-MM-DD format.

			distance (int):
				Radius distance in miles.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'zip_code', zip_code )
			throw_if( 'date', date )
			
			self.mode = 'forecast-zip'
			base = self.request(
				endpoint='forecast/zipCode/',
				params={
						'zipCode': str( zip_code ).strip( ),
						'date': str( date ).strip( ),
						'distance': max( 0, int( distance ) )
				},
				time=int( time )
			) or { }
			
			records = base.get( 'raw', [ ] ) or [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', [ ] )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'fetch_forecast_zip( self, zip_code: str, date: str, distance: int=25, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_forecast_latlon( self, latitude: float, longitude: float,
			date: str, distance: int=25, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch AQI forecasts by latitude and longitude.

			Parameters:
			-----------
			latitude (float):
				Latitude of the query point.

			longitude (float):
				Longitude of the query point.

			date (str):
				Forecast date in YYYY-MM-DD format.

			distance (int):
				Radius distance in miles.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'date', date )
			
			self.mode = 'forecast-latlon'
			base = self.request(
				endpoint='forecast/latLong/',
				params={
						'latitude': float( latitude ),
						'longitude': float( longitude ),
						'date': str( date ).strip( ),
						'distance': max( 0, int( distance ) )
				},
				time=int( time )
			) or { }
			
			records = base.get( 'raw', [ ] ) or [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', [ ] )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'fetch_forecast_latlon( self, latitude: float, longitude: float, '
					'date: str, distance: int=25, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='current-zip', zip_code: str='',
			latitude: float | None=None, longitude: float | None=None,
			date: str='', distance: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for AirNow observation and forecast retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- current-zip
				- current-latlon
				- forecast-zip
				- forecast-latlon

			zip_code (str):
				Optional U.S. Zip code.

			latitude (float | None):
				Optional latitude.

			longitude (float | None):
				Optional longitude.

			date (str):
				Optional forecast date in YYYY-MM-DD format.

			distance (int):
				Radius distance in miles.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'current-zip' ).strip( ).lower( )
			
			if active_mode == 'current-zip':
				return self.fetch_current_zip(
					zip_code=zip_code,
					distance=distance,
					time=int( time )
				)
			
			if active_mode == 'current-latlon':
				return self.fetch_current_latlon(
					latitude=float( latitude ),
					longitude=float( longitude ),
					distance=distance,
					time=int( time )
				)
			
			if active_mode == 'forecast-zip':
				return self.fetch_forecast_zip(
					zip_code=zip_code,
					date=date,
					distance=distance,
					time=int( time )
				)
			
			if active_mode == 'forecast-latlon':
				return self.fetch_forecast_latlon(
					latitude=float( latitude ),
					longitude=float( longitude ),
					date=date,
					distance=distance,
					time=int( time )
				)
			
			raise ValueError(
				"Unsupported mode. Use 'current-zip', 'current-latlon', "
				"'forecast-zip', or 'forecast-latlon'."
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'fetch( self, mode: str=current-zip, zip_code: str=, '
					'latitude: float | None=None, longitude: float | None=None, '
					'date: str=, distance: int=25, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'AirNow'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class ClimateData( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to NOAA NCEI climate data search and retrieval services for
		dataset discovery and subsetted climate data extraction.

		Referenced API Requirements:
		----------------------------
		NOAA NCEI Access Data Service:
			- Endpoint:
			  https://www.ncei.noaa.gov/access/services/data/v1
			- Common parameters:
			  - dataset
			  - startDate
			  - endDate
			  - stations
			  - dataTypes
			  - format

		NOAA NCEI Access Search Service:
			- Endpoint:
			  https://www.ncei.noaa.gov/access/services/search/v1/datasets
			- Common parameters:
			  - keyword
			  - startDate
			  - endDate
			  - offset
			  - limit

	'''
	data_url: Optional[ str ]
	search_url: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the NOAA climate data fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.data_url = 'https://www.ncei.noaa.gov/access/services/data/v1'
		self.search_url = 'https://www.ncei.noaa.gov/access/services/search/v1'
		self.mode = 'datasets'
		self.params = { }
		self.payload = [ ]
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'data_url',
				'search_url',
				'mode',
				'params',
				'payload',
				'timeout',
				'request',
				'_shape_dataset_rows',
				'_shape_data_rows',
				'_summarize_rows',
				'fetch_datasets',
				'fetch_data',
				'fetch',
				'create_schema'
		]
	
	def request( self, url: str, params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to a NOAA NCEI endpoint.

			Parameters:
			-----------
			url (str):
				Target endpoint URL.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'url', url )
			
			self.url = str( url ).strip( )
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ClimateData'
			exception.method = (
					'request( self, url: str, params: Optional[ Dict[ str, Any ] ]=None, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_dataset_rows( self, records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize NOAA dataset search records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Dataset discovery records returned by the search service.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				rows.append(
					{
							'Id': item.get( 'id', '' ),
							'Dataset': (
									item.get( 'dataset', None ) or
									item.get( 'name', '' )
							),
							'Title': (
									item.get( 'title', None ) or
									item.get( 'name', '' )
							),
							'Description': (
									item.get( 'description', None ) or
									item.get( 'summary', '' )
							),
							'Start Date': item.get( 'startDate', '' ),
							'End Date': item.get( 'endDate', '' )
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ClimateData'
			exception.method = (
					'_shape_dataset_rows( self, records: List[ Dict[ str, Any ] ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _shape_data_rows( self, records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize NOAA climate data records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Climate data records returned by the data service.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				row: Dict[ str, Any ]={ }
				
				for key, value in item.items( ):
					friendly_key = str( key ).replace( '_', ' ' ).title( )
					row[ friendly_key ]=value
				
				rows.append( row )
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ClimateData'
			exception.method = (
					'_shape_data_rows( self, records: List[ Dict[ str, Any ] ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			first_title = ''
			first_dataset = ''
			
			if rows:
				first_title = str(
					rows[ 0 ].get( 'Title', '' ) or
					rows[ 0 ].get( 'Station', '' ) or
					rows[ 0 ].get( 'Date', '' ) or ''
				)
				first_dataset = str(
					rows[ 0 ].get( 'Dataset', '' ) or
					rows[ 0 ].get( 'Datatype', '' ) or ''
				)
			
			return {
					'count': count,
					'first_title': first_title,
					'first_dataset': first_dataset
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ClimateData'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_datasets( self, keyword: str='', start_date: str='',
			end_date: str='', limit: int=25, offset: int=0,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch discoverable NOAA climate datasets.

			Parameters:
			-----------
			keyword (str):
				Optional dataset keyword search string.

			start_date (str):
				Optional ISO date lower bound.

			end_date (str):
				Optional ISO date upper bound.

			limit (int):
				Maximum returned datasets.

			offset (int):
				Result offset.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'datasets'
			base = self.request(
				url=f'{self.search_url}/datasets',
				params={
						'keyword': str( keyword ).strip( ),
						'startDate': str( start_date ).strip( ),
						'endDate': str( end_date ).strip( ),
						'limit': max( 1, int( limit ) ),
						'offset': max( 0, int( offset ) )
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			records = payload.get( 'results', [ ] ) if isinstance( payload, dict ) else [ ]
			rows = self._shape_dataset_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ClimateData'
			exception.method = (
					'fetch_datasets( self, keyword: str=, start_date: str=, end_date: str=, '
					'limit: int=25, offset: int=0, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_data( self, dataset: str, start_date: str, end_date: str,
			stations: str='', data_types: str='', limit: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch subsetted NOAA climate data records.

			Parameters:
			-----------
			dataset (str):
				NCEI dataset identifier, such as daily-summaries.

			start_date (str):
				ISO start date.

			end_date (str):
				ISO end date.

			stations (str):
				Optional comma-separated station identifiers.

			data_types (str):
				Optional comma-separated datatype identifiers.

			limit (int):
				Maximum returned rows.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'dataset', dataset )
			throw_if( 'start_date', start_date )
			throw_if( 'end_date', end_date )
			
			self.mode = 'data'
			base = self.request(
				url=self.data_url,
				params={
						'dataset': str( dataset ).strip( ),
						'startDate': str( start_date ).strip( ),
						'endDate': str( end_date ).strip( ),
						'stations': str( stations ).strip( ),
						'dataTypes': str( data_types ).strip( ),
						'format': 'json',
						'limit': max( 1, int( limit ) )
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', [ ] ) or [ ]
			rows = self._shape_data_rows( payload if isinstance( payload, list ) else [ ] )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ClimateData'
			exception.method = (
					'fetch_data( self, dataset: str, start_date: str, end_date: str, '
					'stations: str=, data_types: str=, limit: int=25, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='datasets', keyword: str='', dataset: str='',
			start_date: str='', end_date: str='', stations: str='',
			data_types: str='', limit: int=25, offset: int=0,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for NOAA climate dataset discovery and data retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- datasets
				- data

			keyword (str):
				Optional dataset search keyword.

			dataset (str):
				Dataset identifier for data mode.

			start_date (str):
				Optional start date.

			end_date (str):
				Optional end date.

			stations (str):
				Optional comma-separated station identifiers.

			data_types (str):
				Optional comma-separated datatype identifiers.

			limit (int):
				Maximum returned rows.

			offset (int):
				Result offset for datasets mode.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'datasets' ).strip( ).lower( )
			
			if active_mode == 'datasets':
				return self.fetch_datasets(
					keyword=keyword,
					start_date=start_date,
					end_date=end_date,
					limit=limit,
					offset=offset,
					time=int( time )
				)
			
			if active_mode == 'data':
				return self.fetch_data(
					dataset=dataset,
					start_date=start_date,
					end_date=end_date,
					stations=stations,
					data_types=data_types,
					limit=limit,
					time=int( time )
				)
			
			raise ValueError( "Unsupported mode. Use 'datasets' or 'data'." )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ClimateData'
			exception.method = (
					'fetch( self, mode: str=datasets, keyword: str=, dataset: str=, '
					'start_date: str=, end_date: str=, stations: str=, data_types: str=, '
					'limit: int=25, offset: int=0, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'ClimateData'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class EoNet( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to NASA EONET Version 3 for event discovery and category
		discovery, returning human-readable normalized rows.

		Referenced API Requirements:
		----------------------------
		EONET Version 3 Base Endpoint:
			- https://eonet.gsfc.nasa.gov/api/v3

		Resources used here:
			- /events
			- /events/geojson
			- /categories

		Common event filters:
			- source
			- category
			- status
			- limit
			- days
			- start
			- end
			- bbox

	'''
	base_url: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the NASA EONET fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://eonet.gsfc.nasa.gov/api/v3'
		self.mode = 'events'
		self.params = { }
		self.payload = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'mode',
				'params',
				'payload',
				'timeout',
				'request',
				'_shape_event_rows',
				'_shape_category_rows',
				'_summarize_rows',
				'fetch_events',
				'fetch_categories',
				'fetch',
				'create_schema'
		]
	
	def request( self, endpoint: str,
			params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to an EONET endpoint.

			Parameters:
			-----------
			endpoint (str):
				Endpoint path under the EONET base URL.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'endpoint', endpoint )
			
			self.url = f'{self.base_url}/{str( endpoint ).strip( )}'
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EoNet'
			exception.method = (
					'request( self, endpoint: str, '
					'params: Optional[ Dict[ str, Any ] ]=None, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_event_rows( self, records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize EONET event records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Event records returned by EONET.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				categories = item.get( 'categories', [ ] ) or [ ]
				sources = item.get( 'sources', [ ] ) or [ ]
				geometry = item.get( 'geometry', [ ] ) or [ ]
				
				category_titles = ', '.join(
					[
							str( category.get( 'title', '' ) )
							for category in categories
							if isinstance( category, dict )
					]
				)
				
				source_titles = ', '.join(
					[
							str(
								source.get( 'id', '' ) or
								source.get( 'title', '' )
							)
							for source in sources
							if isinstance( source, dict )
					]
				)
				
				last_geometry_date = ''
				if geometry:
					last_geometry = geometry[ -1 ]
					if isinstance( last_geometry, dict ):
						last_geometry_date = str( last_geometry.get( 'date', '' ) or '' )
				
				status = 'open'
				if item.get( 'closed', None ) is not None:
					status = 'closed'
				
				rows.append(
					{
							'Id': item.get( 'id', '' ),
							'Title': item.get( 'title', '' ),
							'Status': status,
							'Closed': item.get( 'closed', None ),
							'Categories': category_titles,
							'Sources': source_titles,
							'Geometry Count': len( geometry ),
							'Last Geometry Date': last_geometry_date,
							'Link': item.get( 'link', '' ),
							'Description': item.get( 'description', '' )
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EoNet'
			exception.method = (
					'_shape_event_rows( self, records: List[ Dict[ str, Any ] ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _shape_category_rows( self, records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize EONET category records into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Category records returned by EONET.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				rows.append(
					{
							'Id': item.get( 'id', '' ),
							'Title': item.get( 'title', '' ),
							'Description': item.get( 'description', '' ),
							'Link': item.get( 'link', '' )
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EoNet'
			exception.method = (
					'_shape_category_rows( self, records: List[ Dict[ str, Any ] ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized EONET rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			open_count = 0
			first_title = ''
			first_categories = ''
			
			for row in rows or [ ]:
				if str( row.get( 'Status', '' ) ).lower( ) == 'open':
					open_count += 1
			
			if rows:
				first_title = str( rows[ 0 ].get( 'Title', '' ) or '' )
				first_categories = str( rows[ 0 ].get( 'Categories', '' ) or '' )
			
			return {
					'count': count,
					'open_count': open_count,
					'first_title': first_title,
					'first_categories': first_categories
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EoNet'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_events( self, source: str='', category: str='',
			status: str='open', limit: int=25, days: int=30,
			start_date: str='', end_date: str='', bbox: str='',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch EONET events.

			Parameters:
			-----------
			source (str):
				Optional source identifier or comma-separated source identifiers.

			category (str):
				Optional category identifier or comma-separated category identifiers.

			status (str):
				Event status filter:
				- open
				- closed
				- all

			limit (int):
				Maximum returned events.

			days (int):
				Number of prior days including today.

			start_date (str):
				Optional ISO start date.

			end_date (str):
				Optional ISO end date.

			bbox (str):
				Optional bounding box in:
				min_lon,max_lat,max_lon,min_lat

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'events'
			base = self.request(
				endpoint='events',
				params={
						'source': str( source ).strip( ),
						'category': str( category ).strip( ),
						'status': str( status ).strip( ),
						'limit': max( 1, int( limit ) ),
						'days': max( 1, int( days ) ),
						'start': str( start_date ).strip( ),
						'end': str( end_date ).strip( ),
						'bbox': str( bbox ).strip( )
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			records = payload.get( 'events', [ ] ) if isinstance( payload, dict ) else [ ]
			rows = self._shape_event_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EoNet'
			exception.method = (
					'fetch_events( self, source: str=, category: str=, status: str=open, '
					'limit: int=25, days: int=30, start_date: str=, end_date: str=, '
					'bbox: str=, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_categories( self, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch EONET categories.

			Parameters:
			-----------
			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'categories'
			base = self.request(
				endpoint='categories',
				params={ },
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			records = payload.get( 'categories', [ ] ) if isinstance( payload, dict ) else [ ]
			rows = self._shape_category_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EoNet'
			exception.method = 'fetch_categories( self, time: int=20 ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch( self, mode: str='events', source: str='', category: str='',
			status: str='open', limit: int=25, days: int=30,
			start_date: str='', end_date: str='', bbox: str='',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for EONET event and category retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- events
				- categories

			source (str):
				Optional event source filter.

			category (str):
				Optional event category filter.

			status (str):
				Optional event status filter.

			limit (int):
				Maximum returned events.

			days (int):
				Number of prior days including today.

			start_date (str):
				Optional ISO start date.

			end_date (str):
				Optional ISO end date.

			bbox (str):
				Optional bounding box string.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'events' ).strip( ).lower( )
			
			if active_mode == 'events':
				return self.fetch_events(
					source=source,
					category=category,
					status=status,
					limit=limit,
					days=days,
					start_date=start_date,
					end_date=end_date,
					bbox=bbox,
					time=int( time )
				)
			
			if active_mode == 'categories':
				return self.fetch_categories(
					time=int( time )
				)
			
			raise ValueError( "Unsupported mode. Use 'events' or 'categories'." )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EoNet'
			exception.method = (
					'fetch( self, mode: str=events, source: str=, category: str=, '
					'status: str=open, limit: int=25, days: int=30, start_date: str=, '
					'end_date: str=, bbox: str=, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EoNet'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class EnviroFacts( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to selected EPA Envirofacts Data Service API tables using
		a constrained, human-readable wrapper for common environmental queries.

		Referenced API Requirements:
		----------------------------
		Envirofacts Data Service API:
			- Base:
			  https://enviro.epa.gov/enviro/efservice

		Supported first-pass tables in this wrapper:
			- TRI_FACILITY
			- TRI_RELEASE
			- EF_W_EMISSIONS_SOURCE_GHG

		Common query concepts:
			- table selection
			- row limiting
			- optional state filtering
			- optional facility-name prefix filtering
			- JSON output

	'''
	base_url: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the Envirofacts fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://enviro.epa.gov/enviro/efservice'
		self.mode = 'table'
		self.params = { }
		self.payload = [ ]
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'mode',
				'params',
				'payload',
				'timeout',
				'_resolve_table_path',
				'request',
				'_shape_rows',
				'_summarize_rows',
				'fetch_table',
				'fetch',
				'create_schema'
		]
	
	def _resolve_table_path( self, table_name: str,
			state_code: str='', facility_name: str='',
			limit: int=25 ) -> str:
		'''
			Purpose:
			--------
			Construct a constrained Envirofacts REST path for a supported table.

			Parameters:
			-----------
			table_name (str):
				Supported table name.

			state_code (str):
				Optional state code filter.

			facility_name (str):
				Optional facility name prefix filter.

			limit (int):
				Maximum number of returned rows.

			Returns:
			--------
			str
		'''
		try:
			throw_if( 'table_name', table_name )
			
			table_value = str( table_name ).strip( ).upper( )
			state_value = str( state_code ).strip( ).upper( )
			facility_value = str( facility_name ).strip( ).upper( )
			row_limit = max( 1, int( limit ) )
			
			base_path = f'{table_value}'
			segments: List[ str ]=[ ]
			
			if table_value in [ 'TRI_FACILITY', 'TRI_RELEASE' ]:
				if state_value:
					segments.append( f'STATE_ABBR/{state_value}' )
				
				if facility_value:
					segments.append( f'FACILITY_NAME/BEGINNING/{facility_value}' )
			
			if table_value == 'EF_W_EMISSIONS_SOURCE_GHG':
				if state_value:
					segments.append( f'STATE/{state_value}' )
				
				if facility_value:
					segments.append( f'FACILITY_NAME/BEGINNING/{facility_value}' )
			
			path = base_path
			
			if segments:
				path = f'{path}/' + '/'.join( segments )
			
			path = f'{path}/rows/0:{row_limit}/JSON'
			return path
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EnviroFacts'
			exception.method = (
					'_resolve_table_path( self, table_name: str, state_code: str=, '
					'facility_name: str=, limit: int=25 ) -> str'
			)
			raise exception
	
	def request( self, url: str, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to an Envirofacts endpoint.

			Parameters:
			-----------
			url (str):
				Fully qualified request URL.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'url', url )
			
			self.url = str( url ).strip( )
			self.params = { }
			
			self.response = requests.get(
				url=self.url,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EnviroFacts'
			exception.method = (
					'request( self, url: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_rows( self, records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize Envirofacts rows into a human-readable table by title-casing
			column names and preserving the original values.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				Envirofacts records returned by the service.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				row: Dict[ str, Any ]={ }
				
				for key, value in item.items( ):
					friendly_key = str( key ).replace( '_', ' ' ).title( )
					row[ friendly_key ]=value
				
				rows.append( row )
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EnviroFacts'
			exception.method = (
					'_shape_rows( self, records: List[ Dict[ str, Any ] ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized Envirofacts rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			first_facility = ''
			first_state = ''
			
			if rows:
				first_facility = str(
					rows[ 0 ].get( 'Facility Name', '' ) or
					rows[ 0 ].get( 'Primary Name', '' ) or
					rows[ 0 ].get( 'Name', '' ) or ''
				)
				
				first_state = str(
					rows[ 0 ].get( 'State', '' ) or
					rows[ 0 ].get( 'State Abbr', '' ) or ''
				)
			
			return {
					'count': count,
					'first_facility': first_facility,
					'first_state': first_state
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EnviroFacts'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_table( self, table_name: str, state_code: str='',
			facility_name: str='', limit: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch a constrained set of rows from a supported Envirofacts table.

			Parameters:
			-----------
			table_name (str):
				Supported table name:
				- TRI_FACILITY
				- TRI_RELEASE
				- EF_W_EMISSIONS_SOURCE_GHG

			state_code (str):
				Optional state filter.

			facility_name (str):
				Optional facility-name prefix filter.

			limit (int):
				Maximum returned rows.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'table_name', table_name )
			
			table_value = str( table_name ).strip( ).upper( )
			supported_tables: List[ str ]=[
					'TRI_FACILITY',
					'TRI_RELEASE',
					'EF_W_EMISSIONS_SOURCE_GHG'
			]
			
			if table_value not in supported_tables:
				raise ValueError(
					'Unsupported Envirofacts table. Use TRI_FACILITY, TRI_RELEASE, '
					'or EF_W_EMISSIONS_SOURCE_GHG.'
				)
			
			self.mode = 'table'
			path = self._resolve_table_path(
				table_name=table_value,
				state_code=state_code,
				facility_name=facility_name,
				limit=int( limit )
			)
			
			base = self.request(
				url=f'{self.base_url}/{path}',
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', [ ] ) or [ ]
			records = payload if isinstance( payload, list ) else [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'table_name': table_value,
					'url': base.get( 'url', '' ),
					'params': {
							'table_name': table_value,
							'state_code': str( state_code ).strip( ).upper( ),
							'facility_name': str( facility_name ).strip( ),
							'limit': max( 1, int( limit ) )
					},
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EnviroFacts'
			exception.method = (
					'fetch_table( self, table_name: str, state_code: str=, '
					'facility_name: str=, limit: int=25, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, table_name: str='TRI_FACILITY', state_code: str='',
			facility_name: str='', limit: int=25,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for the constrained Envirofacts table wrapper.

			Parameters:
			-----------
			table_name (str):
				Supported table name.

			state_code (str):
				Optional state filter.

			facility_name (str):
				Optional facility-name prefix filter.

			limit (int):
				Maximum returned rows.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			return self.fetch_table(
				table_name=table_name,
				state_code=state_code,
				facility_name=facility_name,
				limit=limit,
				time=int( time )
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EnviroFacts'
			exception.method = (
					'fetch( self, table_name: str=TRI_FACILITY, state_code: str=, '
					'facility_name: str=, limit: int=25, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'EnviroFacts'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class TidesAndCurrents( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to NOAA CO-OPS Tides and Currents APIs for station metadata,
		water-level observations, and tide predictions.

		Referenced API Requirements:
		----------------------------
		NOAA CO-OPS Data API:
			- https://api.tidesandcurrents.noaa.gov/api/prod/datagetter

		NOAA CO-OPS Metadata API:
			- https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi

		Common Data API parameters:
			- product
			- station
			- begin_date
			- end_date
			- datum
			- units
			- time_zone
			- format

	'''
	data_url: Optional[ str ]
	metadata_url: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the NOAA Tides and Currents fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.data_url = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'
		self.metadata_url = 'https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi'
		self.mode = 'water-level'
		self.params = { }
		self.payload = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'data_url',
				'metadata_url',
				'mode',
				'params',
				'payload',
				'timeout',
				'request',
				'_shape_station_rows',
				'_shape_data_rows',
				'_summarize_rows',
				'fetch_station',
				'fetch_water_level',
				'fetch_tide_predictions',
				'fetch',
				'create_schema'
		]
	
	def request( self, url: str, params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to a NOAA CO-OPS endpoint.

			Parameters:
			-----------
			url (str):
				Target endpoint URL.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'url', url )
			
			self.url = str( url ).strip( )
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'request( self, url: str, params: Optional[ Dict[ str, Any ] ]=None, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_station_rows( self, payload: Dict[ str, Any ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize station metadata into a human-readable table.

			Parameters:
			-----------
			payload (Dict[str, Any]):
				Station metadata payload.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			station = payload.get( 'stations', None )
			
			if isinstance( station, list ) and station:
				station = station[ 0 ]
			
			if not isinstance( station, dict ):
				station = payload
			
			row: Dict[ str, Any ]={
					'Station Id': station.get( 'id', '' ),
					'Name': station.get( 'name', '' ),
					'State': station.get( 'state', '' ),
					'Latitude': station.get( 'lat', '' ),
					'Longitude': station.get( 'lng', '' ),
					'Time Zone': station.get( 'timezone', '' ),
					'Great Lakes': station.get( 'greatlakes', '' ),
					'Shef Id': station.get( 'shefcode', '' ),
					'Details Link': station.get( 'self', '' )
			}
			
			return [ row ]
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'_shape_station_rows( self, payload: Dict[ str, Any ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _shape_data_rows( self, payload: Dict[ str, Any ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize NOAA CO-OPS data payloads into a human-readable table.

			Parameters:
			-----------
			payload (Dict[str, Any]):
				Data API payload.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			records = payload.get( 'data', None )
			
			if records is None:
				records = payload.get( 'predictions', [ ] )
			
			for item in records or [ ]:
				row: Dict[ str, Any ]={ }
				
				for key, value in item.items( ):
					friendly_key = str( key ).replace( '_', ' ' ).title( )
					row[ friendly_key ]=value
				
				rows.append( row )
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'_shape_data_rows( self, payload: Dict[ str, Any ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			first_time = ''
			first_value = ''
			first_station = ''
			
			if rows:
				first_time = str(
					rows[ 0 ].get( 'T', '' ) or
					rows[ 0 ].get( 'Time', '' ) or ''
				)
				first_value = str(
					rows[ 0 ].get( 'V', '' ) or
					rows[ 0 ].get( 'Value', '' ) or
					rows[ 0 ].get( 'Type', '' ) or ''
				)
				first_station = str(
					rows[ 0 ].get( 'Name', '' ) or
					rows[ 0 ].get( 'Station Id', '' ) or ''
				)
			
			return {
					'count': count,
					'first_time': first_time,
					'first_value': first_value,
					'first_station': first_station
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_station( self, station_id: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch station metadata.

			Parameters:
			-----------
			station_id (str):
				NOAA station identifier.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'station_id', station_id )
			
			self.mode = 'station'
			base = self.request(
				url=f'{self.metadata_url}/stations/{str( station_id ).strip( )}.json',
				params={ },
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_station_rows( payload )
			
			return {
					'mode': self.mode,
					'station_id': str( station_id ).strip( ),
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'fetch_station( self, station_id: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_water_level( self, station_id: str, begin_date: str, end_date: str, datum: str='MLLW',
			units: str='metric', time_zone: str='gmt', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch water-level observations.

			Parameters:
			-----------
			station_id (str):
				NOAA station identifier.

			begin_date (str):
				Begin date in YYYYMMDD format.

			end_date (str):
				End date in YYYYMMDD format.

			datum (str):
				Datum such as MLLW.

			units (str):
				english or metric.

			time_zone (str):
				gmt, lst, or lst_ldt.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'station_id', station_id )
			throw_if( 'begin_date', begin_date )
			throw_if( 'end_date', end_date )
			
			self.mode = 'water-level'
			base = self.request(
				url=self.data_url,
				params={
						'product': 'water_level',
						'application': 'Foo',
						'station': str( station_id ).strip( ),
						'begin_date': str( begin_date ).strip( ),
						'end_date': str( end_date ).strip( ),
						'datum': str( datum ).strip( ),
						'units': str( units ).strip( ),
						'time_zone': str( time_zone ).strip( ),
						'format': 'json'
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_data_rows( payload )
			
			return {
					'mode': self.mode,
					'station_id': str( station_id ).strip( ),
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'fetch_water_level( self, station_id: str, begin_date: str, '
					'end_date: str, datum: str=MLLW, units: str=metric, '
					'time_zone: str=gmt, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_tide_predictions( self, station_id: str, begin_date: str,
			end_date: str, datum: str='MLLW', units: str='metric',
			time_zone: str='gmt', interval: str='hilo',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch tide predictions.

			Parameters:
			-----------
			station_id (str):
				NOAA station identifier.

			begin_date (str):
				Begin date in YYYYMMDD format.

			end_date (str):
				End date in YYYYMMDD format.

			datum (str):
				Datum such as MLLW.

			units (str):
				english or metric.

			time_zone (str):
				gmt, lst, or lst_ldt.

			interval (str):
				Prediction interval such as hilo or h.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'station_id', station_id )
			throw_if( 'begin_date', begin_date )
			throw_if( 'end_date', end_date )
			
			self.mode = 'tide-predictions'
			base = self.request(
				url=self.data_url,
				params={
						'product': 'predictions',
						'application': 'Foo',
						'station': str( station_id ).strip( ),
						'begin_date': str( begin_date ).strip( ),
						'end_date': str( end_date ).strip( ),
						'datum': str( datum ).strip( ),
						'units': str( units ).strip( ),
						'time_zone': str( time_zone ).strip( ),
						'interval': str( interval ).strip( ),
						'format': 'json'
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_data_rows( payload )
			
			return {
					'mode': self.mode,
					'station_id': str( station_id ).strip( ),
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'fetch_tide_predictions( self, station_id: str, begin_date: str, '
					'end_date: str, datum: str=MLLW, units: str=metric, '
					'time_zone: str=gmt, interval: str=hilo, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='water-level', station_id: str='',
			begin_date: str='', end_date: str='', datum: str='MLLW',
			units: str='metric', time_zone: str='gmt',
			interval: str='hilo', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for NOAA Tides and Currents retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- station
				- water-level
				- tide-predictions

			station_id (str):
				NOAA station identifier.

			begin_date (str):
				Begin date in YYYYMMDD format.

			end_date (str):
				End date in YYYYMMDD format.

			datum (str):
				Datum.

			units (str):
				english or metric.

			time_zone (str):
				gmt, lst, or lst_ldt.

			interval (str):
				Prediction interval.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'water-level' ).strip( ).lower( )
			
			if active_mode == 'station':
				return self.fetch_station( station_id=station_id,
					time=int( time ) )
			
			if active_mode == 'water-level':
				return self.fetch_water_level( station_id=station_id, begin_date=begin_date,
					end_date=end_date, datum=datum, units=units,
					time_zone=time_zone, time=int( time ) )
			
			if active_mode == 'tide-predictions':
				return self.fetch_tide_predictions(
					station_id=station_id,
					begin_date=begin_date,
					end_date=end_date,
					datum=datum,
					units=units,
					time_zone=time_zone,
					interval=interval,
					time=int( time )
				)
			
			raise ValueError(
				"Unsupported mode. Use 'station', 'water-level', or "
				"'tide-predictions'."
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'fetch( self, mode: str=water-level, station_id: str=, '
					'begin_date: str=, end_date: str=, datum: str=MLLW, '
					'units: str=metric, time_zone: str=gmt, interval: str=hilo, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str, description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'TidesAndCurrents'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class UvIndex( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to the EPA UV Index web services for daily and hourly UV
		forecast retrieval by ZIP code or by city and state.

		Referenced API Requirements:
		----------------------------
		EPA Envirofacts UV Index Web Services:
			- Hourly by ZIP
			- Hourly by City/State
			- Daily by ZIP
			- Daily by City/State

		Base Endpoint:
			- https://enviro.epa.gov/enviro/efservice

	'''
	base_url: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the EPA UV Index fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://enviro.epa.gov/enviro/efservice'
		self.mode = 'daily-zip'
		self.params = { }
		self.payload = [ ]
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'mode',
				'params',
				'payload',
				'timeout',
				'request',
				'_shape_rows',
				'_summarize_rows',
				'fetch_daily_zip',
				'fetch_daily_city_state',
				'fetch_hourly_zip',
				'fetch_hourly_city_state',
				'fetch',
				'create_schema'
		]
	
	def request( self, url: str, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to a UV Index endpoint.

			Parameters:
			-----------
			url (str):
				Fully qualified request URL.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'url', url )
			
			self.url = str( url ).strip( )
			self.params = { }
			
			self.response = requests.get(
				url=self.url,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'request( self, url: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_rows( self, records: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize UV Index rows into a human-readable table.

			Parameters:
			-----------
			records (List[Dict[str, Any]]):
				UV Index records returned by the EPA web services.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for item in records or [ ]:
				row: Dict[ str, Any ]={ }
				
				for key, value in item.items( ):
					friendly_key = str( key ).replace( '_', ' ' ).title( )
					row[ friendly_key ]=value
				
				rows.append( row )
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'_shape_rows( self, records: List[ Dict[ str, Any ] ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized UV Index rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			max_uv = None
			first_location = ''
			first_alert = ''
			
			for row in rows or [ ]:
				if not first_location:
					first_location = str(
						row.get( 'City', '' ) or
						row.get( 'Zip', '' ) or ''
					)
				
				if not first_alert:
					first_alert = str( row.get( 'Uv Alert', '' ) or '' )
				
				uv_value = row.get( 'Uv Value', None )
				try:
					if uv_value is not None:
						if max_uv is None or float( uv_value ) > float( max_uv ):
							max_uv = float( uv_value )
				except Exception:
					pass
			
			return {
					'count': count,
					'max_uv': max_uv,
					'first_location': first_location,
					'first_alert': first_alert
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_daily_zip( self, zip_code: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch daily UV forecast and alert by ZIP code.

			Parameters:
			-----------
			zip_code (str):
				U.S. ZIP code.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'zip_code', zip_code )
			
			self.mode = 'daily-zip'
			base = self.request(
				url=f'{self.base_url}/getEnvirofactsUVDAILY/ZIP/{str( zip_code ).strip( )}/JSON',
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', [ ] ) or [ ]
			records = payload if isinstance( payload, list ) else [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': { 'zip_code': str( zip_code ).strip( ) },
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'fetch_daily_zip( self, zip_code: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_daily_city_state( self, city: str, state: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch daily UV forecast and alert by city and state.

			Parameters:
			-----------
			city (str):
				U.S. city name.

			state (str):
				U.S. state abbreviation.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'city', city )
			throw_if( 'state', state )
			
			self.mode = 'daily-city-state'
			base = self.request(
				url=(
						f'{self.base_url}/getEnvirofactsUVDAILY/CITY/'
						f'{str( city ).strip( )}/STATE/{str( state ).strip( )}/JSON'
				),
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', [ ] ) or [ ]
			records = payload if isinstance( payload, list ) else [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': {
							'city': str( city ).strip( ),
							'state': str( state ).strip( ).upper( )
					},
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'fetch_daily_city_state( self, city: str, state: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_hourly_zip( self, zip_code: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch hourly UV forecast by ZIP code.

			Parameters:
			-----------
			zip_code (str):
				U.S. ZIP code.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'zip_code', zip_code )
			
			self.mode = 'hourly-zip'
			base = self.request(
				url=f'{self.base_url}/getEnvirofactsUVHOURLY/ZIP/{str( zip_code ).strip( )}/JSON',
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', [ ] ) or [ ]
			records = payload if isinstance( payload, list ) else [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': { 'zip_code': str( zip_code ).strip( ) },
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'fetch_hourly_zip( self, zip_code: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_hourly_city_state( self, city: str, state: str,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch hourly UV forecast by city and state.

			Parameters:
			-----------
			city (str):
				U.S. city name.

			state (str):
				U.S. state abbreviation.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'city', city )
			throw_if( 'state', state )
			
			self.mode = 'hourly-city-state'
			base = self.request(
				url=(
						f'{self.base_url}/getEnvirofactsUVHOURLY/CITY/'
						f'{str( city ).strip( )}/STATE/{str( state ).strip( )}/JSON'
				),
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', [ ] ) or [ ]
			records = payload if isinstance( payload, list ) else [ ]
			rows = self._shape_rows( records )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': {
							'city': str( city ).strip( ),
							'state': str( state ).strip( ).upper( )
					},
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'fetch_hourly_city_state( self, city: str, state: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='daily-zip', zip_code: str='',
			city: str='', state: str='',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for UV Index forecast retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- daily-zip
				- daily-city-state
				- hourly-zip
				- hourly-city-state

			zip_code (str):
				Optional U.S. ZIP code.

			city (str):
				Optional city name.

			state (str):
				Optional state abbreviation.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'daily-zip' ).strip( ).lower( )
			
			if active_mode == 'daily-zip':
				return self.fetch_daily_zip(
					zip_code=zip_code,
					time=int( time )
				)
			
			if active_mode == 'daily-city-state':
				return self.fetch_daily_city_state(
					city=city,
					state=state,
					time=int( time )
				)
			
			if active_mode == 'hourly-zip':
				return self.fetch_hourly_zip(
					zip_code=zip_code,
					time=int( time )
				)
			
			if active_mode == 'hourly-city-state':
				return self.fetch_hourly_city_state(
					city=city,
					state=state,
					time=int( time )
				)
			
			raise ValueError(
				"Unsupported mode. Use 'daily-zip', 'daily-city-state', "
				"'hourly-zip', or 'hourly-city-state'."
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'fetch( self, mode: str=daily-zip, zip_code: str=, city: str=, '
					'state: str=, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'UvIndex'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class PurpleAir( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to the PurpleAir API for bounding-box sensor discovery and
		single-sensor detail retrieval using explicit field selection to reduce
		point consumption and improve readability.

		Referenced API Requirements:
		----------------------------
		PurpleAir API Base Endpoint:
			- https://api.purpleair.com/v1

		Resources used here:
			- /sensors
			- /sensors/{sensor_index}

		Common query concepts:
			- X-API-Key header
			- fields
			- location_type
			- nwlng
			- nwlat
			- selng
			- selat
			- max_age
			- modified_since

	'''
	base_url: Optional[ str ]
	api_key: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the PurpleAir fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://api.purpleair.com/v1'
		self.api_key = self._resolve_api_key( )
		self.mode = 'sensors'
		self.params = { }
		self.payload = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': self.agents
		}
		
		if self.api_key:
			self.headers[ 'X-API-Key' ]=self.api_key
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'api_key',
				'mode',
				'params',
				'payload',
				'timeout',
				'_resolve_api_key',
				'request',
				'_shape_sensor_list_rows',
				'_shape_sensor_detail_rows',
				'_summarize_rows',
				'fetch_sensors',
				'fetch_sensor',
				'fetch',
				'create_schema'
		]
	
	def _resolve_api_key( self ) -> Optional[ str ]:
		'''
			Purpose:
			--------
			Resolve the PurpleAir API key from environment variables.

			Parameters:
			-----------
			None

			Returns:
			--------
			Optional[str]
		'''
		try:
			candidates: List[ Optional[ str ] ]=[
					os.getenv( 'PURPLEAIR_API_KEY' ),
					os.getenv( 'PURPLE_AIR_API_KEY' )
			]
			
			for candidate in candidates:
				if candidate is not None and str( candidate ).strip( ):
					return str( candidate ).strip( )
			
			return None
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = '_resolve_api_key( self ) -> Optional[ str ]'
			raise exception
	
	def request( self, endpoint: str, params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to a PurpleAir endpoint.

			Parameters:
			-----------
			endpoint (str):
				Endpoint path under the PurpleAir base URL.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'endpoint', endpoint )
			
			if self.api_key is None or not str( self.api_key ).strip( ):
				raise ValueError(
					'PurpleAir API key not found. Set PURPLEAIR_API_KEY or '
					'PURPLE_AIR_API_KEY.'
				)
			
			self.url = f'{self.base_url}/{str( endpoint ).strip( )}'
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = (
					'request( self, endpoint: str, '
					'params: Optional[ Dict[ str, Any ] ]=None, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_sensor_list_rows( self, payload: Dict[ str, Any ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize PurpleAir sensor-list payloads into a human-readable table.

			Parameters:
			-----------
			payload (Dict[str, Any]):
				Sensor-list payload returned by PurpleAir.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			fields = payload.get( 'fields', [ ] ) or [ ]
			data = payload.get( 'data', [ ] ) or [ ]
			
			for record in data:
				row_map: Dict[ str, Any ]={ }
				
				if isinstance( record, list ):
					for index, field_name in enumerate( fields ):
						if index < len( record ):
							row_map[ str( field_name ) ]=record[ index ]
				elif isinstance( record, dict ):
					row_map = record
				
				rows.append(
					{
							'Sensor Index': row_map.get( 'sensor_index', '' ),
							'Name': row_map.get( 'name', '' ),
							'PM2.5': row_map.get( 'pm2.5', None ),
							'Temperature': row_map.get( 'temperature', None ),
							'Humidity': row_map.get( 'humidity', None ),
							'Latitude': row_map.get( 'latitude', None ),
							'Longitude': row_map.get( 'longitude', None ),
							'Last Seen': row_map.get( 'last_seen', None ),
							'Location Type': row_map.get( 'location_type', None )
					}
				)
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = (
					'_shape_sensor_list_rows( self, payload: Dict[ str, Any ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _shape_sensor_detail_rows( self, payload: Dict[ str, Any ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize PurpleAir single-sensor detail payload into a readable row.

			Parameters:
			-----------
			payload (Dict[str, Any]):
				Single-sensor payload returned by PurpleAir.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			sensor = payload.get( 'sensor', { } ) or { }
			
			row: Dict[ str, Any ]={
					'Sensor Index': sensor.get( 'sensor_index', '' ),
					'Name': sensor.get( 'name', '' ),
					'Model': sensor.get( 'model', '' ),
					'Hardware': sensor.get( 'hardware', '' ),
					'PM2.5 Cf 1 A': sensor.get( 'pm2.5_cf_1_a', None ),
					'PM2.5 Cf 1 B': sensor.get( 'pm2.5_cf_1_b', None ),
					'Temperature': sensor.get( 'temperature', None ),
					'Humidity': sensor.get( 'humidity', None ),
					'Pressure': sensor.get( 'pressure', None ),
					'Latitude': sensor.get( 'latitude', None ),
					'Longitude': sensor.get( 'longitude', None ),
					'Last Seen': sensor.get( 'last_seen', None ),
					'Firmware Version': sensor.get( 'firmware_version', '' ),
					'RSSI': sensor.get( 'rssi', None )
			}
			
			return [ row ]
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = (
					'_shape_sensor_detail_rows( self, payload: Dict[ str, Any ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized PurpleAir rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			max_pm25 = None
			first_name = ''
			
			for row in rows or [ ]:
				if not first_name:
					first_name = str( row.get( 'Name', '' ) or row.get( 'Sensor Index', '' ) or '' )
				
				pm25_value = row.get( 'PM2.5', None )
				if pm25_value is None:
					pm25_value = row.get( 'PM2.5 Cf 1 A', None )
				
				try:
					if pm25_value is not None:
						if max_pm25 is None or float( pm25_value ) > float( max_pm25 ):
							max_pm25 = float( pm25_value )
				except Exception:
					pass
			
			return {
					'count': count,
					'max_pm25': max_pm25,
					'first_name': first_name
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_sensors( self, nwlng: float, nwlat: float, selng: float, selat: float,
			location_type: int=0, max_age: int=0, modified_since: int=0,
			fields: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch PurpleAir sensors within a bounding box.
	
			Parameters:
			-----------
			nwlng (float):
				Northwest longitude.
	
			nwlat (float):
				Northwest latitude.
	
			selng (float):
				Southeast longitude.
	
			selat (float):
				Southeast latitude.
	
			location_type (int):
				PurpleAir location type. Public outdoor sensors are commonly 0.
	
			max_age (int):
				Maximum sensor age filter in minutes. 0 keeps current behavior broad.
	
			modified_since (int):
				UNIX timestamp filter. 0 disables the filter.
	
			fields (str):
				Optional comma-separated PurpleAir field list. If empty, the legacy
				default field list is used.
	
			time (int):
				Request timeout in seconds.
	
			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'sensors'			
			default_fields = ( 'name,pm2.5,temperature,humidity,latitude,longitude,last_seen,'
					'location_type' )
			
			selected_fields = str( fields or '' ).strip( )
			if not selected_fields:
				selected_fields = default_fields
			
			base = self.request( endpoint='sensors', params={
						'fields': selected_fields,
						'location_type': int( location_type ),
						'nwlng': float( nwlng ),
						'nwlat': float( nwlat ),
						'selng': float( selng ),
						'selat': float( selat ),
						'max_age': int( max_age ),
						'modified_since': int( modified_since )
				},
				time=int( time ) ) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_sensor_list_rows( payload )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = ('fetch_sensors( self, nwlng: float, nwlat: float, selng: float, '
					'selat: float, location_type: int=0, max_age: int=0, '
					'modified_since: int=0, fields: str="", time: int=20 ) '
					'-> Dict[ str, Any ]' )
			raise exception
	
	def fetch_sensor( self, sensor_index: int, fields: str='', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch a single PurpleAir sensor detail record.
	
			Parameters:
			-----------
			sensor_index (int):
				PurpleAir sensor index.
	
			fields (str):
				Optional comma-separated PurpleAir field list. If empty, the legacy
				default field list is used.
	
			time (int):
				Request timeout in seconds.
	
			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'sensor'
			default_fields = ( 'name,model,hardware,pm2.5_cf_1_a,pm2.5_cf_1_b,temperature,'
					'humidity,pressure,latitude,longitude,last_seen,firmware_version,rssi' )
			
			selected_fields = str( fields or '' ).strip( )
			if not selected_fields:
				selected_fields = default_fields
			
			base = self.request( endpoint=f'sensors/{int( sensor_index )}',
				params={ 'fields': selected_fields }, time=int( time ) ) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_sensor_detail_rows( payload )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': {
							'sensor_index': int( sensor_index ),
							'fields': base.get( 'params', { } ).get( 'fields', '' )
					},
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = ( 'fetch_sensor( self, sensor_index: int, fields: str="", time: int=20 ) '
					'-> Dict[ str, Any ]' )
			raise exception
	
	def fetch( self, mode: str = 'sensors', sensor_index: int=None,
			nwlng: float | None = None, nwlat: float | None = None,
			selng: float | None = None, selat: float | None = None,
			location_type: int=0, max_age: int=0, modified_since: int=0,
			fields: str = '', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for PurpleAir sensor discovery and sensor detail retrieval.
	
			Parameters:
			-----------
			mode (str):
				Supported modes:
				- sensors
				- sensor
	
			sensor_index (int | None):
				PurpleAir sensor index for single-sensor mode.
	
			nwlng (float | None):
				Northwest longitude.
	
			nwlat (float | None):
				Northwest latitude.
	
			selng (float | None):
				Southeast longitude.
	
			selat (float | None):
				Southeast latitude.
	
			location_type (int):
				PurpleAir location type.
	
			max_age (int):
				Maximum age filter.
	
			modified_since (int):
				UNIX timestamp filter.
	
			fields (str):
				Optional comma-separated PurpleAir field list.
	
			time (int):
				Request timeout in seconds.
	
			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			mode_value = str( mode or '' ).strip( ).lower( )
			if mode_value == 'sensors':
				return self.fetch_sensors( nwlng=nwlng,
					nwlat=nwlat,
					selng=selng,
					selat=selat,
					location_type=location_type,
					max_age=max_age,
					modified_since=modified_since,
					fields=fields,
					time=time )
			
			if mode_value == 'sensor':
				return self.fetch_sensor( sensor_index=int( sensor_index ), fields=fields,
					time=time )
			
			raise ValueError( "Use 'sensors' or 'sensor'." )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = (
					'fetch( self, mode: str=sensors, sensor_index: int | None=None, '
					'nwlng: float | None=None, nwlat: float | None=None, '
					'selng: float | None=None, selat: float | None=None, '
					'location_type: int=0, max_age: int=0, modified_since: int=0, '
					'fields: str="", time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'PurpleAir'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class OpenAQ( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to the OpenAQ v3 API for location discovery and latest
		measurement retrieval using authenticated requests and human-readable
		normalized output.

		Referenced API Requirements:
		----------------------------
		OpenAQ API Base Endpoint:
			- https://api.openaq.org/v3

		Resources used here:
			- /locations
			- /locations/{id}/latest

		Common query concepts:
			- X-API-Key header
			- country_id
			- coordinates
			- radius
			- providers_id
			- parameters_id
			- limit
			- page

	'''
	base_url: Optional[ str ]
	api_key: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the OpenAQ fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://api.openaq.org/v3'
		self.api_key = self._resolve_api_key( )
		self.mode = 'locations'
		self.params = { }
		self.payload = { }
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = { 'Accept': 'application/json', 'User-Agent': self.agents }		
		if self.api_key:
			self.headers[ 'X-API-Key' ]=self.api_key
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.
	
			Parameters:
			-----------
			None
	
			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'api_key',
				'mode',
				'params',
				'payload',
				'timeout',
				'_resolve_api_key',
				'request',
				'_shape_location_rows',
				'_shape_latest_rows',
				'_shape_resource_rows',
				'_summarize_rows',
				'fetch_countries',
				'fetch_providers',
				'fetch_parameters',
				'fetch_locations',
				'fetch_latest',
				'fetch_parameter_latest',
				'fetch',
				'create_schema'
		]
	
	def _resolve_api_key( self ) -> Optional[ str ]:
		'''
			Purpose:
			--------
			Resolve the OpenAQ API key from environment variables.

			Parameters:
			-----------
			None

			Returns:
			--------
			Optional[str]
		'''
		try:
			candidates: List[ Optional[ str ] ]=[ os.getenv( 'OPENAQ_API_KEY' ),
			                                      os.getenv( 'OPEN_AQ_API_KEY' ) ]
			
			for candidate in candidates:
				if candidate is not None and str( candidate ).strip( ):
					return str( candidate ).strip( )
			
			return None
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = '_resolve_api_key( self ) -> Optional[ str ]'
			raise exception
	
	def request( self, endpoint: str, params: Optional[ Dict[ str, Any ] ]=None,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to an OpenAQ endpoint.

			Parameters:
			-----------
			endpoint (str):
				Endpoint path under the OpenAQ base URL.

			params (Optional[Dict[str, Any]]):
				Query string parameters.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'endpoint', endpoint )
			if self.api_key is None or not str( self.api_key ).strip( ):
				raise ValueError(
					'OpenAQ API key not found. Set OPENAQ_API_KEY or OPEN_AQ_API_KEY.' )
			
			self.url = f'{self.base_url}/{str( endpoint ).strip( )}'
			self.params = { }
			
			for key, value in (params or { }).items( ):
				if value is None:
					continue
				if isinstance( value, str ) and not value.strip( ):
					continue
				self.params[ key ]=value
			
			self.response = requests.get(
				url=self.url,
				params=self.params,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.json( )
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = (
					'request( self, endpoint: str, '
					'params: Optional[ Dict[ str, Any ] ]=None, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _shape_location_rows( self, payload: Dict[ str, Any ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize OpenAQ location payloads into a human-readable table.

			Parameters:
			-----------
			payload (Dict[str, Any]):
				Location payload returned by OpenAQ.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			results = payload.get( 'results', [ ] ) or [ ]
			for item in results:
				country = item.get( 'country', { } ) or { }
				provider = item.get( 'provider', { } ) or { }
				owner = item.get( 'owner', { } ) or { }
				coordinates = item.get( 'coordinates', { } ) or { }
				rows.append( {
							'Location Id': item.get( 'id', '' ),
							'Name': item.get( 'name', '' ),
							'Locality': item.get( 'locality', '' ),
							'Country': country.get( 'name', '' ),
							'Country Code': country.get( 'code', '' ),
							'Provider': provider.get( 'name', '' ),
							'Owner': owner.get( 'name', '' ),
							'Latitude': coordinates.get( 'latitude', None ),
							'Longitude': coordinates.get( 'longitude', None ),
							'Time Zone': item.get( 'timezone', '' ),
							'Is Mobile': item.get( 'isMobile', None ),
							'Is Monitor': item.get( 'isMonitor', None )
					} )
			
			return rows
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = '_shape_location_rows( self, *args ) -> List[ Dict[ str, Any ] ]'
			raise exception
	
	def _shape_latest_rows( self, payload: Dict[ str, Any ] ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize OpenAQ latest-measurement payloads into a human-readable table.

			Parameters:
			-----------
			payload (Dict[str, Any]):
				Latest-measurement payload returned by OpenAQ.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ]=[ ]
			results = payload.get( 'results', [ ] ) or [ ]
			for item in results:
				parameter = item.get( 'parameter', { } ) or { }
				datetime_local = item.get( 'datetime', { } ) or { }
				rows.append( {
							'Parameter': (
									parameter.get( 'displayName', None ) or
									parameter.get( 'name', '' )
							),
							'Parameter Name': parameter.get( 'name', '' ),
							'Units': parameter.get( 'units', '' ),
							'Value': item.get( 'value', None ),
							'Date Time UTC': (
									(item.get( 'datetime', { } ) or { }).get( 'utc', '' )
									if isinstance( item.get( 'datetime', { } ), dict )
									else ''
							),
							'Date Time Local': datetime_local.get( 'local', '' ),
							'Sensor Id': (
									(item.get( 'sensorsId', [ ] ) or [ None ])[ 0 ]
									if isinstance( item.get( 'sensorsId', [ ] ), list )
									   and len( item.get( 'sensorsId', [ ] ) ) > 0
									else None
							)
					} )
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = (
					'_shape_latest_rows( self, payload: Dict[ str, Any ] ) '
					'-> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized OpenAQ rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			first_name = ''
			first_country = ''
			first_parameter = ''
			if rows:
				first_name = str(
					rows[ 0 ].get( 'Name', '' ) or
					rows[ 0 ].get( 'Location Id', '' ) or '' )
				first_country = str( rows[ 0 ].get( 'Country', '' ) or '' )
				first_parameter = str(
					rows[ 0 ].get( 'Parameter', '' ) or
					rows[ 0 ].get( 'Parameter Name', '' ) or '' )
			
			return {
					'count': count,
					'first_name': first_name,
					'first_country': first_country,
					'first_parameter': first_parameter
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = '_summarize_rows( self, *args )  -> Dict[ str, Any ]'
			raise exception
	
	def _shape_resource_rows( self, payload: Dict[ str, Any ], resource: str ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Normalize OpenAQ lookup resources into a human-readable table.
	
			Parameters:
			-----------
			payload (Dict[str, Any]):
				OpenAQ resource payload.
	
			resource (str):
				Resource name used to shape common fields.
	
			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			rows: List[ Dict[ str, Any ] ] = [ ]
			results = payload.get( 'results', [ ] ) or [ ]
			resource_name = str( resource or '' ).strip( ).lower( )
			for item in results:
				if not isinstance( item, dict ):
					continue
				
				row = {
						'Resource': resource_name,
						'Id': item.get( 'id', '' ),
						'Name': item.get( 'name', '' )
				}
				
				if resource_name == 'countries':
					row[ 'Code' ] = item.get( 'code', '' )
					row[ 'Locations' ] = item.get( 'locations', None )
					row[ 'Parameters' ] = item.get( 'parameters', None )
				
				elif resource_name == 'providers':
					row[ 'Description' ] = item.get( 'description', '' )
					row[ 'Source Name' ] = item.get( 'sourceName', '' )
					row[ 'Export Prefix' ] = item.get( 'exportPrefix', '' )
				
				elif resource_name == 'parameters':
					row[ 'Display Name' ] = item.get( 'displayName', '' )
					row[ 'Units' ] = item.get( 'units', '' )
					row[ 'Description' ] = item.get( 'description', '' )
				
				else:
					for key, value in item.items( ):
						if isinstance( value, (str, int, float, bool) ) or value is None:
							row[ str( key ) ] = value
				
				rows.append( row )
			
			return rows
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = '_shape_resource_rows( self, *args ) -> List[ Dict[ str, Any ] ]'
			raise exception
	
	def fetch_countries( self, providers_id: str = '', parameters_id: str = '',
			limit: int=100, page: int=1, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch OpenAQ countries for resource discovery.
	
			Parameters:
			-----------
			providers_id (str):
				Optional provider ID filter.
	
			parameters_id (str):
				Optional parameter ID filter.
	
			limit (int):
				Maximum returned countries.
	
			page (int):
				Result page number.
	
			time (int):
				Request timeout in seconds.
	
			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'countries'
			base = self.request(
				endpoint='countries',
				params={
						'providers_id': str( providers_id ).strip( ),
						'parameters_id': str( parameters_id ).strip( ),
						'limit': max( 1, int( limit ) ),
						'page': max( 1, int( page ) )
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_resource_rows( payload, 'countries' )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = (
					'fetch_countries( self, providers_id: str="", parameters_id: str="", '
					'limit: int=100, page: int=1, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_providers( self, limit: int=100, page: int=1,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch OpenAQ providers for resource discovery.
	
			Parameters:
			-----------
			limit (int):
				Maximum returned providers.
	
			page (int):
				Result page number.
	
			time (int):
				Request timeout in seconds.
	
			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'providers'
			base = self.request(
				endpoint='providers',
				params={
						'limit': max( 1, int( limit ) ),
						'page': max( 1, int( page ) )
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_resource_rows( payload, 'providers' )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = (
					'fetch_providers( self, limit: int=100, page: int=1, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_parameters( self, limit: int=100, page: int=1,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch OpenAQ parameters for resource discovery.
	
			Parameters:
			-----------
			limit (int):
				Maximum returned parameters.
	
			page (int):
				Result page number.
	
			time (int):
				Request timeout in seconds.
	
			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'parameters'
			base = self.request(
				endpoint='parameters',
				params={
						'limit': max( 1, int( limit ) ),
						'page': max( 1, int( page ) )
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_resource_rows( payload, 'parameters' )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = (
					'fetch_parameters( self, limit: int=100, page: int=1, '
					'time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_parameter_latest( self, parameter_id: int, limit: int=100,
			page: int=1, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch latest measurements for a single OpenAQ parameter.
	
			Parameters:
			-----------
			parameter_id (int):
				OpenAQ parameter identifier.
	
			limit (int):
				Maximum returned latest values.
	
			page (int):
				Result page number.
	
			time (int):
				Request timeout in seconds.
	
			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'parameter_latest'
			base = self.request(
				endpoint=f'parameters/{int( parameter_id )}/latest',
				params={
						'limit': max( 1, int( limit ) ),
						'page': max( 1, int( page ) )
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_latest_rows( payload )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': {
							'parameter_id': int( parameter_id ),
							'limit': max( 1, int( limit ) ),
							'page': max( 1, int( page ) )
					},
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = (
					'fetch_parameter_latest( self, parameter_id: int, limit: int=100, '
					'page: int=1, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
		
	def fetch_locations( self, country_id: int=None, coordinates: str='', radius: int=25000,
			providers_id: str='', parameters_id: str='', limit: int=25, page: int=1,
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch OpenAQ locations.

			Parameters:
			-----------
			country_id (int | None):
				Optional OpenAQ country identifier.

			coordinates (str):
				Optional latitude,longitude string for geospatial filtering.

			radius (int):
				Optional radius in meters when coordinates are supplied.

			providers_id (str):
				Optional provider ID filter.

			parameters_id (str):
				Optional parameter ID filter.

			limit (int):
				Maximum returned locations.

			page (int):
				Result page number.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'locations'
			base = self.request(
				endpoint='locations',
				params={
						'country_id': None if country_id is None else int( country_id ),
						'coordinates': str( coordinates ).strip( ),
						'radius': int( radius ),
						'providers_id': str( providers_id ).strip( ),
						'parameters_id': str( parameters_id ).strip( ),
						'limit': max( 1, int( limit ) ),
						'page': max( 1, int( page ) )
				},
				time=int( time )
			) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_location_rows( payload )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': base.get( 'params', { } ),
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = 'fetch_locations( self, *args) -> Dict[ str, Any ]'
			raise exception
	
	def fetch_latest( self, location_id: int, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch latest measurements for a single OpenAQ location.

			Parameters:
			-----------
			location_id (int):
				OpenAQ location identifier.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'latest'
			base = self.request( endpoint=f'locations/{int( location_id )}/latest', params={ },
				time=int( time ) ) or { }
			
			payload = base.get( 'raw', { } ) or { }
			rows = self._shape_latest_rows( payload )
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': { 'location_id': int( location_id ) },
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = 'fetch_latest( self, *args ) -> Dict[ str, Any ]'
			raise exception
	
	def fetch( self, mode: str = 'locations', location_id: int=None,
			parameter_id: int=None, country_id: int=None, coordinates: str = '',
			radius: int=25000, providers_id: str = '', parameters_id: str = '',
			limit: int=25, page: int=1, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for OpenAQ v3 discovery, location, and latest-measurement
			retrieval.
	
			Parameters:
			-----------
			mode (str):
				Supported modes:
				- countries
				- providers
				- parameters
				- locations
				- latest
				- parameter_latest
	
			location_id (int | None):
				OpenAQ location identifier for latest mode.
	
			parameter_id (int | None):
				OpenAQ parameter identifier for parameter_latest mode.
	
			country_id (int | None):
				Optional OpenAQ country identifier.
	
			coordinates (str):
				Optional latitude,longitude string.
	
			radius (int):
				Geospatial radius in meters.
	
			providers_id (str):
				Optional provider ID filter.
	
			parameters_id (str):
				Optional parameter ID filter.
	
			limit (int):
				Maximum returned rows.
	
			page (int):
				Result page number.
	
			time (int):
				Request timeout in seconds.
	
			Returns:
			--------
			Dict[str, Any] | None
		'''		
		try:
			active_mode = str( mode or 'locations' ).strip( ).lower( )
			if active_mode == 'countries':
				return self.fetch_countries( providers_id=providers_id, parameters_id=parameters_id,
					limit=limit, page=page, time=int( time ) )
			
			if active_mode == 'providers':
				return self.fetch_providers( limit=limit, page=page,
					time=int( time ) )
			
			if active_mode == 'parameters':
				return self.fetch_parameters( limit=limit, page=page,
					time=int( time ) )
			
			if active_mode == 'locations':
				return self.fetch_locations( country_id=country_id, coordinates=coordinates,
					radius=radius, providers_id=providers_id, parameters_id=parameters_id,
					limit=limit, page=page, time=int( time ) )
			
			if active_mode == 'latest':
				return self.fetch_latest( location_id=int( location_id ),
					time=int( time ) )
			
			if active_mode == 'parameter_latest':
				return self.fetch_parameter_latest(
					parameter_id=int( parameter_id ),
					limit=limit,
					page=page,
					time=int( time )
				)
			
			raise ValueError( "Unsupported mode" )
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = 'fetch( self, *args ) -> Dict[ str, Any ]'
			raise exception
	
	def create_schema( self, function: str, tool: str, description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			if required is None:
				required = list( parameters.keys( ) )
			
			return {
					'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'OpenAQ'
			exception.method = 'create_schema( self, *args ) -> Dict[ str, str ]'
			raise exception

class Firms( Fetcher ):
	'''
		Purpose:
		--------
		Provides access to NASA FIRMS area fire-detection and data-availability
		services using a MAP_KEY and human-readable normalized output.

		Referenced API Requirements:
		----------------------------
		NASA FIRMS API Base Endpoint:
			- https://firms.modaps.eosdis.nasa.gov/api

		Resources used here:
			- /area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]
			- /area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]/[DATE]
			- /data_availability/csv/[MAP_KEY]/[SENSOR]

		Common query concepts:
			- MAP_KEY
			- SOURCE or SENSOR
			- AREA_COORDINATES as west,south,east,north or world
			- DAY_RANGE from 1 to 5
			- Optional DATE in YYYY-MM-DD format

	'''
	base_url: Optional[ str ]
	map_key: Optional[ str ]
	mode: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	payload: Optional[ Any ]
	timeout: Optional[ int ]
	agents: Optional[ str ]
	
	def __init__( self ) -> None:
		'''
			Purpose:
			--------
			Initialize the NASA FIRMS fetcher.

			Parameters:
			-----------
			None

			Returns:
			--------
			None
		'''
		super( ).__init__( )
		self.base_url = 'https://firms.modaps.eosdis.nasa.gov/api'
		self.map_key = self._resolve_map_key( )
		self.mode = 'area'
		self.params = { }
		self.payload = ''
		self.timeout = 20
		self.agents = cfg.AGENTS
		self.headers = {
				'Accept': 'text/csv',
				'User-Agent': self.agents
		}
	
	def __dir__( self ) -> List[ str ]:
		'''
			Purpose:
			--------
			Provide ordered member visibility.

			Parameters:
			-----------
			None

			Returns:
			--------
			List[str]
		'''
		return [
				'base_url',
				'map_key',
				'mode',
				'params',
				'payload',
				'timeout',
				'_resolve_map_key',
				'request_csv',
				'_csv_to_rows',
				'_summarize_rows',
				'fetch_area',
				'fetch_data_availability',
				'fetch',
				'create_schema'
		]
	
	def _resolve_map_key( self ) -> Optional[ str ]:
		'''
			Purpose:
			--------
			Resolve the NASA FIRMS MAP_KEY from environment variables.

			Parameters:
			-----------
			None

			Returns:
			--------
			Optional[str]
		'''
		try:
			candidates: List[ Optional[ str ] ]=[
					os.getenv( 'FIRMS_MAP_KEY' ),
					os.getenv( 'NASA_FIRMS_MAP_KEY' )
			]
			
			for candidate in candidates:
				if candidate is not None and str( candidate ).strip( ):
					return str( candidate ).strip( )
			
			return None
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Firms'
			exception.method = '_resolve_map_key( self ) -> Optional[ str ]'
			raise exception
	
	def request_csv( self, url: str, time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Issue a GET request to a FIRMS CSV endpoint.

			Parameters:
			-----------
			url (str):
				Fully qualified request URL.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'url', url )
			
			if self.map_key is None or not str( self.map_key ).strip( ):
				raise ValueError(
					'FIRMS MAP_KEY not found. Set FIRMS_MAP_KEY or '
					'NASA_FIRMS_MAP_KEY.'
				)
			
			self.url = str( url ).strip( )
			self.params = { }
			
			self.response = requests.get(
				url=self.url,
				headers=self.headers,
				timeout=int( time )
			)
			self.response.raise_for_status( )
			
			self.payload = self.response.text
			
			return {
					'url': self.url,
					'params': self.params,
					'raw': self.payload
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Firms'
			exception.method = (
					'request_csv( self, url: str, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def _csv_to_rows( self, csv_text: str ) -> List[ Dict[ str, Any ] ]:
		'''
			Purpose:
			--------
			Convert FIRMS CSV text into normalized row dictionaries.

			Parameters:
			-----------
			csv_text (str):
				CSV response text.

			Returns:
			--------
			List[Dict[str, Any]]
		'''
		try:
			if csv_text is None or not str( csv_text ).strip( ):
				return [ ]
			
			df_csv = pd.read_csv( io.StringIO( str( csv_text ) ) )
			rows: List[ Dict[ str, Any ] ]=[ ]
			
			for _, item in df_csv.iterrows( ):
				row: Dict[ str, Any ]={ }
				
				for key in df_csv.columns:
					friendly_key = str( key ).replace( '_', ' ' ).title( )
					row[ friendly_key ]=item[ key ]
				
				rows.append( row )
			
			return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Firms'
			exception.method = (
					'_csv_to_rows( self, csv_text: str ) -> List[ Dict[ str, Any ] ]'
			)
			raise exception
	
	def _summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) -> Dict[ str, Any ]:
		'''
			Purpose:
			--------
			Create a compact summary block from normalized FIRMS rows.

			Parameters:
			-----------
			rows (List[Dict[str, Any]]):
				Normalized row dictionaries.

			Returns:
			--------
			Dict[str, Any]
		'''
		try:
			count = len( rows or [ ] )
			first_date = ''
			first_lat = ''
			first_lon = ''
			
			if rows:
				first_date = str(
					rows[ 0 ].get( 'Acq Date', '' ) or
					rows[ 0 ].get( 'Date', '' ) or ''
				)
				first_lat = str( rows[ 0 ].get( 'Latitude', '' ) or '' )
				first_lon = str( rows[ 0 ].get( 'Longitude', '' ) or '' )
			
			return {
					'count': count,
					'first_date': first_date,
					'first_lat': first_lat,
					'first_lon': first_lon
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Firms'
			exception.method = (
					'_summarize_rows( self, rows: List[ Dict[ str, Any ] ] ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_area( self, source: str, area_coordinates: str='world',
			day_range: int=1, date: str='',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch FIRMS fire detections for an area.

			Parameters:
			-----------
			source (str):
				FIRMS source, such as:
				- LANDSAT_NRT
				- MODIS_NRT
				- MODIS_SP
				- VIIRS_NOAA20_NRT
				- VIIRS_NOAA20_SP
				- VIIRS_NOAA21_NRT
				- VIIRS_SNPP_NRT
				- VIIRS_SNPP_SP

			area_coordinates (str):
				Bounding box as west,south,east,north, or world.

			day_range (int):
				Number of days from 1 to 5.

			date (str):
				Optional YYYY-MM-DD start date. If omitted, most recent data is used.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			throw_if( 'source', source )
			
			self.mode = 'area'
			source_value = str( source ).strip( ).upper( )
			area_value = str( area_coordinates ).strip( )
			range_value = max( 1, min( 5, int( day_range ) ) )
			
			url = (
					f'{self.base_url}/area/csv/{self.map_key}/{source_value}/'
					f'{area_value}/{range_value}'
			)
			
			if str( date ).strip( ):
				url = f'{url}/{str( date ).strip( )}'
			
			base = self.request_csv(
				url=url,
				time=int( time )
			) or { }
			
			rows = self._csv_to_rows( str( base.get( 'raw', '' ) or '' ) )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': {
							'source': source_value,
							'area_coordinates': area_value,
							'day_range': range_value,
							'date': str( date ).strip( )
					},
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', '' )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Firms'
			exception.method = (
					'fetch_area( self, source: str, area_coordinates: str=world, '
					'day_range: int=1, date: str=, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch_data_availability( self, sensor: str='ALL',
			time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Fetch FIRMS data-availability rows for a sensor family.

			Parameters:
			-----------
			sensor (str):
				Sensor family such as ALL, LANDSAT_NRT, MODIS_NRT, MODIS_SP,
				VIIRS_NOAA20_NRT, VIIRS_NOAA20_SP, VIIRS_NOAA21_NRT,
				VIIRS_SNPP_NRT, or VIIRS_SNPP_SP.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			self.mode = 'data-availability'
			sensor_value = str( sensor ).strip( ).upper( )
			
			base = self.request_csv(
				url=f'{self.base_url}/data_availability/csv/{self.map_key}/{sensor_value}',
				time=int( time )
			) or { }
			
			rows = self._csv_to_rows( str( base.get( 'raw', '' ) or '' ) )
			
			return {
					'mode': self.mode,
					'url': base.get( 'url', '' ),
					'params': {
							'sensor': sensor_value
					},
					'summary': self._summarize_rows( rows ),
					'rows': rows,
					'raw': base.get( 'raw', '' )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Firms'
			exception.method = (
					'fetch_data_availability( self, sensor: str=ALL, time: int=20 ) '
					'-> Dict[ str, Any ]'
			)
			raise exception
	
	def fetch( self, mode: str='area', source: str='',
			area_coordinates: str='world', day_range: int=1, date: str='',
			sensor: str='ALL', time: int=20 ) -> Dict[ str, Any ] | None:
		'''
			Purpose:
			--------
			Unified dispatcher for FIRMS area and data-availability retrieval.

			Parameters:
			-----------
			mode (str):
				Supported modes:
				- area
				- data-availability

			source (str):
				FIRMS source for area mode.

			area_coordinates (str):
				Bounding box string or world.

			day_range (int):
				Number of days from 1 to 5.

			date (str):
				Optional start date for area mode.

			sensor (str):
				Sensor family for data-availability mode.

			time (int):
				Request timeout in seconds.

			Returns:
			--------
			Dict[str, Any] | None
		'''
		try:
			active_mode = str( mode or 'area' ).strip( ).lower( )
			
			if active_mode == 'area':
				return self.fetch_area(
					source=source,
					area_coordinates=area_coordinates,
					day_range=day_range,
					date=date,
					time=int( time )
				)
			
			if active_mode == 'data-availability':
				return self.fetch_data_availability(
					sensor=sensor,
					time=int( time )
				)
			
			raise ValueError( "Unsupported mode. Use 'area' or 'data-availability'." )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Firms'
			exception.method = (
					'fetch( self, mode: str=area, source: str=, '
					'area_coordinates: str=world, day_range: int=1, date: str=, '
					'sensor: str=ALL, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict,
			required: list[ str ] ) -> Dict[ str, str ] | None:
		'''
			Purpose:
			--------
			Construct and return a fully dynamic OpenAI Tool API schema definition.

			Parameters:
			-----------
			function (str):
				The function name exposed to the LLM.

			tool (str):
				The underlying system or service the function wraps.

			description (str):
				Precise explanation of what the function does.

			parameters (dict):
				A dictionary defining parameter names and JSON schema descriptors.

			required (list[str]):
				List of required parameter names.

			Returns:
			--------
			Dict[str, str] | None
		'''
		try:
			throw_if( 'function', function )
			throw_if( 'tool', tool )
			throw_if( 'description', description )
			throw_if( 'parameters', parameters )
			
			if required is None:
				required = list( parameters.keys( ) )
			
			return { 'name': function.strip( ),
					'description': (
							f"{description.strip( )} This function uses the "
							f"{tool.strip( )} service."
					),
					'parameters': {
							'type': 'object',
							'properties': parameters,
							'required': required
					}
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'fetchers'
			exception.cause = 'Firms'
			exception.method = (
					'create_schema( self, function: str, tool: str, description: str, '
					'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]'
			)
			raise exception

class OpenSky( Fetcher ):
	'''

		Purpose:
		--------
		Provides access to the OpenSky Network REST API for aircraft state
		vectors, flights, airport arrivals/departures, and aircraft tracks.

	'''
	token_url: Optional[ str ]
	base_url: Optional[ str ]
	client_id: Optional[ str ]
	client_secret: Optional[ str ]
	access_token: Optional[ str ]
	
	def __init__( self ) -> None:
		super( ).__init__( )
		self.timeout = 20
		self.base_url = 'https://opensky-network.org/api'
		self.token_url = (
				'https://auth.opensky-network.org/auth/realms/opensky-network/'
				'protocol/openid-connect/token'
		)
		self.client_id = None
		self.client_secret = None
		self.access_token = None
		self.headers = {
				'Accept': 'application/json',
				'User-Agent': cfg.AGENTS,
		}
	
	def __dir__( self ) -> List[ str ]:
		return [
				'timeout',
				'headers',
				'response',
				'url',
				'result',
				'query',
				'token_url',
				'base_url',
				'client_id',
				'client_secret',
				'access_token',
				'fetch',
				'get_token',
				'request',
				'normalize_states',
				'normalize_flights',
				'normalize_track',
		]
	
	@property
	def mode_options( self ) -> List[ str ]:
		return [
				'states_bbox',
				'flights_aircraft',
				'arrivals_airport',
				'departures_airport',
				'track_aircraft',
		]
	
	def get_token( self, client_id: str, client_secret: str ) -> str:
		'''
	
			Purpose:
			--------
			Request a bearer token from the OpenSky authentication server.
	
			Parameters:
			-----------
			client_id (str):
				OpenSky OAuth client id.
	
			client_secret (str):
				OpenSky OAuth client secret.
	
			Returns:
			--------
			str:
				Bearer access token.
	
		'''
		try:
			throw_if( 'client_id', client_id )
			throw_if( 'client_secret', client_secret )
			self.client_id = client_id.strip( )
			self.client_secret = client_secret.strip( )
			response = requests.post(
				self.token_url,
				headers={ 'Content-Type': 'application/x-www-form-urlencoded' },
				data={
						'grant_type': 'client_credentials',
						'client_id': self.client_id,
						'client_secret': self.client_secret,
				},
				timeout=self.timeout,
			)
			response.raise_for_status( )
			
			payload = response.json( )
			token = payload.get( 'access_token' )
			if not token:
				raise ValueError( 'OpenSky token response did not include access_token.' )
			
			self.access_token = token
			return token
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'OpenSky'
			exception.method = 'get_token( self, client_id: str, client_secret: str ) -> str'
			raise exception
	
	def request( self, endpoint: str, params: Dict[ str, Any ], client_id: str=None,
			client_secret: str=None ) -> Any:
		'''
	
			Purpose:
			--------
			Send a GET request to an OpenSky REST endpoint.
	
			Parameters:
			-----------
			endpoint (str):
				OpenSky endpoint path beginning with '/'.
	
			params (Dict[str, Any]):
				Query-string parameters passed to the endpoint.
	
			client_id (str | None):
				Optional OAuth client id for authenticated requests.
	
			client_secret (str | None):
				Optional OAuth client secret for authenticated requests.
	
			Returns:
			--------
			Any:
				Parsed JSON payload returned by OpenSky.
	
		'''
		try:
			throw_if( 'endpoint', endpoint )
			self.url = f'{self.base_url}{endpoint}'
			
			request_headers = dict( self.headers or { } )
			if client_id and client_secret:
				token = self.get_token( client_id, client_secret )
				request_headers[ 'Authorization' ]=f'Bearer {token}'
			
			clean_params = {
					k: v for k, v in (params or { }).items( )
					if v is not None and v != ''
			}
			
			self.response = requests.get(
				self.url,
				params=clean_params,
				headers=request_headers,
				timeout=self.timeout,
			)
			
			if self.response.status_code == 404:
				return [ ] if '/flights/' in endpoint else { }
			
			self.response.raise_for_status( )
			return self.response.json( )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'OpenSky'
			exception.method = (
					'request( self, endpoint: str, params: Dict[ str, Any ], '
					'client_id: str | None=None, client_secret: str | None=None ) -> Any'
			)
			raise exception
	
	def normalize_states( self, payload: Dict[ str, Any ] | None ) -> Dict[ str, Any ] | None:
		'''
		
			Purpose:
			--------
			Normalize an OpenSky state-vector response into a structured dictionary with
			mode metadata and aircraft state records.
		
			Parameters:
			-----------
			payload (Dict[ str, Any ] | None): Raw OpenSky state-vector response payload.
		
			Returns:
			--------
			Dict[ str, Any ] | None: Normalized state-vector records and metadata, or
			None when normalization fails.
		
		'''
		try:
			if not payload:
				return {
						'mode': 'states_bbox',
						'time': None,
						'count': 0,
						'items': [ ],
				}
			
			rows = payload.get( 'states' ) or [ ]
			items: List[ Dict[ str, Any ] ]=[ ]
			
			for row in rows:
				items.append(
					{
							'icao24': row[ 0 ],
							'callsign': (row[ 1 ] or '').strip( ) if len( row ) > 1 else '',
							'origin_country': row[ 2 ] if len( row ) > 2 else None,
							'time_position': row[ 3 ] if len( row ) > 3 else None,
							'last_contact': row[ 4 ] if len( row ) > 4 else None,
							'longitude': row[ 5 ] if len( row ) > 5 else None,
							'latitude': row[ 6 ] if len( row ) > 6 else None,
							'baro_altitude_m': row[ 7 ] if len( row ) > 7 else None,
							'on_ground': row[ 8 ] if len( row ) > 8 else None,
							'velocity_mps': row[ 9 ] if len( row ) > 9 else None,
							'true_track_deg': row[ 10 ] if len( row ) > 10 else None,
							'vertical_rate_mps': row[ 11 ] if len( row ) > 11 else None,
							'geo_altitude_m': row[ 13 ] if len( row ) > 13 else None,
							'squawk': row[ 14 ] if len( row ) > 14 else None,
							'position_source': row[ 16 ] if len( row ) > 16 else None,
							'category': row[ 17 ] if len( row ) > 17 else None,
					}
				)
			
			return {
					'mode': 'states_bbox',
					'time': payload.get( 'time' ),
					'count': len( items ),
					'items': items,
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'OpenSky'
			exception.method = 'normalize_states( self, payload: Dict[ str, Any ] | None )'
			raise exception
	
	def normalize_flights(
			self,
			payload: List[ Dict[ str, Any ] ] | None,
			mode: str ) -> Dict[ str, Any ] | None:
		try:
			rows = payload or [ ]
			items: List[ Dict[ str, Any ] ]=[ ]
			
			for row in rows:
				items.append(
					{
							'icao24': row.get( 'icao24' ),
							'callsign': (row.get( 'callsign' ) or '').strip( ),
							'first_seen': row.get( 'firstSeen' ),
							'last_seen': row.get( 'lastSeen' ),
							'est_departure_airport': row.get( 'estDepartureAirport' ),
							'est_arrival_airport': row.get( 'estArrivalAirport' ),
							'est_departure_airport_horiz_distance_m':
								row.get( 'estDepartureAirportHorizDistance' ),
							'est_departure_airport_vert_distance_m':
								row.get( 'estDepartureAirportVertDistance' ),
							'est_arrival_airport_horiz_distance_m':
								row.get( 'estArrivalAirportHorizDistance' ),
							'est_arrival_airport_vert_distance_m':
								row.get( 'estArrivalAirportVertDistance' ),
							'departure_airport_candidates_count':
								row.get( 'departureAirportCandidatesCount' ),
							'arrival_airport_candidates_count':
								row.get( 'arrivalAirportCandidatesCount' ),
					}
				)
			
			return {
					'mode': mode,
					'count': len( items ),
					'items': items,
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'OpenSky'
			exception.method = (
					'normalize_flights( self, payload: List[ Dict[ str, Any ] ] | None, '
					'mode: str )'
			)
			raise exception
	
	def normalize_track( self, payload: Dict[ str, Any ] | None ) -> Dict[ str, Any ] | None:
		try:
			if not payload:
				return {
						'mode': 'track_aircraft',
						'icao24': None,
						'callsign': None,
						'start_time': None,
						'end_time': None,
						'count': 0,
						'items': [ ],
				}
			
			path = payload.get( 'path' ) or [ ]
			items: List[ Dict[ str, Any ] ]=[ ]
			for row in path:
				items.append(
					{
							'time': row[ 0 ] if len( row ) > 0 else None,
							'latitude': row[ 1 ] if len( row ) > 1 else None,
							'longitude': row[ 2 ] if len( row ) > 2 else None,
							'baro_altitude_m': row[ 3 ] if len( row ) > 3 else None,
							'true_track_deg': row[ 4 ] if len( row ) > 4 else None,
							'on_ground': row[ 5 ] if len( row ) > 5 else None,
					}
				)
			
			return {
					'mode': 'track_aircraft',
					'icao24': payload.get( 'icao24' ),
					'callsign': payload.get( 'callsign' ) or payload.get( 'calllsign' ),
					'start_time': payload.get( 'startTime' ),
					'end_time': payload.get( 'endTime' ),
					'count': len( items ),
					'items': items,
			}
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'OpenSky'
			exception.method = 'normalize_track( self, payload: Dict[ str, Any ] | None )'
			raise exception
	
	def fetch( self, mode: str='states_bbox', icao24: str='', airport: str='',
			begin: int=None, end: int=None, time_value: int=None,
			lamin: float | None=None, lomin: float | None=None, lamax: float | None=None,
			lomax: float | None=None, extended: bool=False, client_id: str=None,
			client_secret: str=None, time: int=20 ) -> Dict[ str, Any ] | None:
		try:
			self.timeout = int( time )
			active_mode = (mode or 'states_bbox').strip( ).lower( )
			
			if active_mode == 'states_bbox':
				params: Dict[ str, Any ]={ }
				if time_value is not None:
					params[ 'time' ]=int( time_value )
				if icao24 and icao24.strip( ):
					params[ 'icao24' ]=icao24.strip( ).lower( )
				if lamin is not None and lomin is not None and lamax is not None and lomax is not None:
					params[ 'lamin' ]=float( lamin )
					params[ 'lomin' ]=float( lomin )
					params[ 'lamax' ]=float( lamax )
					params[ 'lomax' ]=float( lomax )
				if extended:
					params[ 'extended' ]=1
				
				payload = self.request(
					'/states/all',
					params=params,
					client_id=client_id,
					client_secret=client_secret,
				)
				return self.normalize_states( payload )
			
			if active_mode == 'flights_aircraft':
				throw_if( 'icao24', icao24 )
				throw_if( 'begin', begin )
				throw_if( 'end', end )
				
				payload = self.request(
					'/flights/aircraft',
					params={
							'icao24': icao24.strip( ).lower( ),
							'begin': int( begin ),
							'end': int( end ),
					},
					client_id=client_id,
					client_secret=client_secret,
				)
				return self.normalize_flights( payload, active_mode )
			
			if active_mode == 'arrivals_airport':
				throw_if( 'airport', airport )
				throw_if( 'begin', begin )
				throw_if( 'end', end )
				
				payload = self.request(
					'/flights/arrival',
					params={
							'airport': airport.strip( ).upper( ),
							'begin': int( begin ),
							'end': int( end ),
					},
					client_id=client_id,
					client_secret=client_secret,
				)
				return self.normalize_flights( payload, active_mode )
			
			if active_mode == 'departures_airport':
				throw_if( 'airport', airport )
				throw_if( 'begin', begin )
				throw_if( 'end', end )
				
				payload = self.request(
					'/flights/departure',
					params={
							'airport': airport.strip( ).upper( ),
							'begin': int( begin ),
							'end': int( end ),
					},
					client_id=client_id,
					client_secret=client_secret,
				)
				return self.normalize_flights( payload, active_mode )
			
			if active_mode == 'track_aircraft':
				throw_if( 'icao24', icao24 )
				payload = self.request(
					'/tracks/all',
					params={
							'icao24': icao24.strip( ).lower( ),
							'time': int( time_value or 0 ),
					},
					client_id=client_id,
					client_secret=client_secret,
				)
				return self.normalize_track( payload )
			
			raise ValueError(
				"Unsupported mode. Use 'states_bbox', 'flights_aircraft', "
				"'arrivals_airport', 'departures_airport', or 'track_aircraft'."
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'OpenSky'
			exception.method = (
					'fetch( self, mode: str=states_bbox, icao24: str=, airport: str=, '
					'begin: int | None=None, end: int | None=None, time_value: int | None=None, '
					'lamin: float | None=None, lomin: float | None=None, '
					'lamax: float | None=None, lomax: float | None=None, '
					'extended: bool=False, client_id: str | None=None, '
					'client_secret: str | None=None, time: int=20 ) -> Dict[ str, Any ]'
			)
			raise exception
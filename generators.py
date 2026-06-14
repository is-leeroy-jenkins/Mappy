'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                generators.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="generators.py" company="Terry D. Eppler">

	     generators.py
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
    generators.py
  </summary>
  ******************************************************************************************
'''
from __future__ import annotations

from anthropic import Anthropic as AnthropicClient
import base64
from boogr import Error, Logger
from core import Result
import config as cfg
from google import genai
from google import genai
from google.genai import types
from openai import OpenAI
from pathlib import Path
from typing import Any, Dict, Optional, Pattern, List, Tuple
from requests import Response
from xai_sdk import Client as Xai
from mistralai.client import Mistral as MistralAI
import re
import urllib

def throw_if( name: str, value: Any ) -> None:
	'''
		
		Purpose:
		-----------
		Simple guard which raises ValueError when `value` is falsy (None, empty).
		
		Args:
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
	"""
	
		Purpose:
		_________
		
		Args:
		----------
		
		
		Returns:
		--------
		
		
	"""
	data = Path( path ).read_bytes( )
	return base64.b64encode( data ).decode( "utf-8" )

class Generator:
	'''

		Purpose:
		--------
		Base class for Generator subclasses

		Attributes:
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

			Args:
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
	
	def fetch( self, query: str, url: str, time: int = 10 ) -> Result | None:
		'''

			Purpose:
			--------
			Abstract fetch method to be implemented by subclasses.

			Args:
			-----------
			url (str): Resource URL to fetch.
			time (int): Timeout in seconds.
			show_dialog (bool): If True, show an ErrorDialog on exception.

			Returns:
			---------
			Optional[Result]: Should return Result on success or None on failure.

		'''
		raise NotImplementedError( 'Must be implemented by a subclass.' )

class Grok( Generator ):
	'''

		Purpose:
		--------
		Class providing xAI Grok text generation and web-search functionality through
		the xAI Responses API.

		Attributes:
		-----------
		client (Xai):
			Initialized xAI SDK client.

		model (str):
			Selected Grok model identifier.

		response (Any):
			Last xAI response object.

		api_key (str):
			xAI API key from configuration.

		query (str | None):
			Last user prompt.

		params (Dict[str, Any] | None):
			Last xAI request payload.

		temperature (float):
			Sampling temperature.

		max_tokens (int):
			Maximum output token count.

		top_p (float):
			Nucleus sampling value.

		reasoning_effort (str | None):
			Optional xAI reasoning-effort setting.

		stream (bool):
			Whether streaming is enabled.

		store (bool):
			Whether server-side response storage is enabled.

		messages (List[Dict[str, Any]] | None):
			Message-style compatibility field.

		system_instructions (str | None):
			Final instruction block used for the request.

		web_search (bool):
			Whether xAI web search is enabled.

		search_domains (List[str]):
			Optional allowed domains for xAI web search.

		parallel_tool_calls (bool):
			Whether parallel tool calls are enabled.

		tool_choice (str):
			Tool-choice behavior.

		tools (List[Dict[str, Any]]):
			xAI Responses API tool declarations.

		Methods:
		--------
		fetch( self, query, ... ) -> str | None
		generate_text( self, query, ... ) -> str | None
		search_web( self, query, ... ) -> str | None

	'''
	
	client: Optional[ Xai ]
	model: Optional[ str ]
	response: Optional[ Any ]
	api_key: Optional[ str ]
	query: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	temperature: Optional[ float ]
	max_tokens: Optional[ int ]
	top_p: Optional[ float ]
	reasoning_effort: Optional[ str ]
	stream: Optional[ bool ]
	store: Optional[ bool ]
	messages: Optional[ List[ Dict[ str, Any ] ] ]
	system_instructions: Optional[ str ]
	web_search: Optional[ bool ]
	search_domains: Optional[ List[ str ] ]
	parallel_tool_calls: Optional[ bool ]
	tool_choice: Optional[ str ]
	tools: Optional[ List[ Dict[ str, Any ] ] ]
	
	def __init__( self ) -> None:
		'''
		
			Purpose:
			--------
			Initialize the xAI Grok generator with defaults used by the Foo
			application.

			Args:
			-----------
			None

			Returns:
			--------
			None
			
		'''
		super( ).__init__( )
		self.api_key = cfg.XAI_API_KEY
		self.model = 'grok-4-fast-reasoning'
		self.client = Xai( api_key=self.api_key, base_url='https://api.x.ai/v1' )
		self.messages = None
		self.temperature = 0.7
		self.top_p = 1.0
		self.max_tokens = 2048
		self.reasoning_effort = None
		self.headers = { }
		self.timeout = None
		self.file_path = None
		self.content = None
		self.query = None
		self.params = None
		self.response = None
		self.system_instructions = None
		self.web_search = False
		self.search_domains = [ ]
		self.parallel_tool_calls = True
		self.tool_choice = 'auto'
		self.tools = [ ]
		self.store = True
		self.stream = False
	
	def __dir__( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return a stable ordered member list for introspection.

			Args:
			-----------
			None

			Returns:
			--------
			List[str]:
				Ordered attribute and method names.
			
		'''
		return [
				'client',
				'model',
				'response',
				'api_key',
				'query',
				'params',
				'temperature',
				'max_tokens',
				'top_p',
				'reasoning_effort',
				'stream',
				'store',
				'messages',
				'system_instructions',
				'web_search',
				'search_domains',
				'parallel_tool_calls',
				'tool_choice',
				'tools',
				'normalize_domains',
				'supports_reasoning_effort',
				'is_reasoning_model',
				'build_instructions',
				'build_tools',
				'build_response_format',
				'extract_output_text',
				'fetch',
				'generate_text',
				'search_web'
		]
	
	def normalize_domains( self, domains: Any ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Normalize user-supplied domain input into canonical, de-duplicated xAI
			web-search domains.

			Args:
			-----------
			domains (Any):
				String, list, tuple, set, scalar, or None containing domain values.

			Returns:
			--------
			List[str]:
				Clean domain names without protocol, path, port, or leading www.
			
		'''
		try:
			if domains is None:
				return [ ]
			
			if isinstance( domains, str ):
				parts = re.split( r'[\n,;]+', domains )
			elif isinstance( domains, (list, tuple, set) ):
				parts = [ str( item ) for item in domains if item is not None ]
			else:
				parts = [ str( domains ) ]
			
			values: List[ str ] = [ ]
			
			for entry in parts:
				value = str( entry ).strip( ).lower( )
				
				if not value:
					continue
				
				value = re.sub( r'^https?://', '', value )
				value = value.split( '/' )[ 0 ]
				value = re.sub( r':\d+$', '', value )
				value = value.lstrip( '.' )
				
				if value.startswith( 'www.' ):
					value = value[ 4: ]
				
				if not re.fullmatch( r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', value ):
					raise ValueError( f'Invalid xAI web-search domain: {value}' )
				
				if value not in values:
					values.append( value )
			
			if len( values ) > 5:
				raise ValueError(
					'xAI web-search allowed domains are limited to five domains.'
				)
			
			return values
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = 'normalize_domains( self, domains: Any ) -> List[ str ]'
			Logger( ).write( exception )
			raise exception
	
	def supports_reasoning_effort( self, model: str ) -> bool:
		'''
		
			Purpose:
			--------
			Determine whether the selected Grok model supports explicit
			reasoning_effort.

			Args:
			-----------
			model (str):
				Grok model identifier.

			Returns:
			--------
			bool:
				True when the model supports the reasoning_effort request field.
			
		'''
		try:
			throw_if( 'model', model )
			name = str( model ).strip( ).lower( )
			return name == 'grok-4.3'
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = 'supports_reasoning_effort( self, model: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def supports_reasoning_object( self, model: str ) -> bool:
		'''
		
			Purpose:
			--------
			Determine whether the selected Grok model supports the Responses API
			reasoning object.

			Args:
			-----------
			model (str):
				Grok model identifier.

			Returns:
			--------
			bool:
				True when the model supports a reasoning object in the request.
			
		'''
		try:
			throw_if( 'model', model )
			name = str( model ).strip( ).lower( )
			return name == 'grok-4.20-multi-agent'
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = 'supports_reasoning_object( self, model: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def is_reasoning_model( self, model: str ) -> bool:
		'''
		
			Purpose:
			--------
			Identify models where reasoning is native, automatic, or explicitly
			configurable.

			Args:
			-----------
			model (str):
				Grok model identifier.

			Returns:
			--------
			bool:
				True when the model is a reasoning model.
			
		'''
		try:
			throw_if( 'model', model )
			name = str( model ).strip( ).lower( )
			return (
					'reasoning' in name
					or name.startswith( 'grok-4' )
					or name.startswith( 'grok-4.3' )
					or name.startswith( 'grok-4.20' )
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = 'is_reasoning_model( self, model: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def build_instructions( self, system: str = None,
			response_format: str = None ) -> str | None:
		'''
		
			Purpose:
			--------
			Build the final instruction block sent to xAI.

			Args:
			-----------
			system (str | None):
				Optional system instructions.

			response_format (str | None):
				Optional output mode.

			Returns:
			--------
			str | None:
				Instruction block or None.
			
		'''
		try:
			parts: List[ str ] = [ ]
			
			if system and str( system ).strip( ):
				parts.append( str( system ).strip( ) )
			
			if response_format and str( response_format ).strip( ).lower( ) == 'json':
				parts.append(
					'Return valid JSON only. Do not include markdown fences, prose, '
					'or commentary outside the JSON value.'
				)
			
			if parts:
				return '\n\n'.join( parts )
			
			return None
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = (
					'build_instructions( self, system: str | None=None, '
					'response_format: str | None=None ) -> str | None'
			)
			Logger( ).write( exception )
			raise exception
	
	def build_tools( self, web_search: bool = False, search_domains: Any = None ) -> List[
		Dict[ str, Any ] ]:
		'''
		
			Purpose:
			--------
			Build the xAI Responses API hosted-tool list.

			Args:
			-----------
			web_search (bool):
				Whether to enable the xAI web-search tool.

			search_domains (Any):
				Optional allowed domains for xAI web search.

			Returns:
			--------
			List[Dict[str, Any]]:
				xAI Responses API tool declarations.
			
		'''
		try:
			tools: List[ Dict[ str, Any ] ] = [ ]
			
			if not web_search:
				return tools
			
			domains = self.normalize_domains( search_domains )
			tool: Dict[ str, Any ] = { 'type': 'web_search' }
			
			if domains:
				tool[ 'filters' ] = { 'allowed_domains': domains }
			
			tools.append( tool )
			return tools
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = (
					'build_tools( self, web_search: bool=False, '
					'search_domains: Any=None ) -> List[ Dict[ str, Any ] ]'
			)
			Logger( ).write( exception )
			raise exception
	
	def build_response_format( self, response_format: str = None ) -> Dict[
		                                                                  str, Any ] | None:
		'''
		
			Purpose:
			--------
			Build the xAI/OpenAI-compatible response_format payload.

			Args:
			-----------
			response_format (str | None):
				Response format selector, such as json.

			Returns:
			--------
			Dict[str, Any] | None:
				Response-format object or None.
			
		'''
		try:
			mode = str( response_format or '' ).strip( ).lower( )
			
			if not mode or mode == 'auto':
				return None
			
			if mode in [ 'json', 'json_object' ]:
				return { 'type': 'json_object' }
			
			if mode == 'text':
				return { 'type': 'text' }
			
			return None
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = (
					'build_response_format( self, response_format: str | None=None ) '
					'-> Dict[ str, Any ] | None'
			)
			Logger( ).write( exception )
			raise exception
	
	def extract_output_text( self, response: Any ) -> str:
		'''
		
			Purpose:
			--------
			Extract response text from xAI SDK Responses API results, OpenAI-compatible
			response objects, dictionaries, or streams.

			Args:
			-----------
			response (Any):
				xAI response object, stream, dictionary, or scalar fallback.

			Returns:
			--------
			str:
				Best available output text.
			
		'''
		try:
			if response is None:
				return ''
			
			if hasattr( response, 'output_text' ) and response.output_text:
				return str( response.output_text )
			
			if hasattr( response, 'text' ) and response.text:
				return str( response.text )
			
			if isinstance( response, dict ):
				if response.get( 'output_text' ):
					return str( response.get( 'output_text' ) )
				
				if response.get( 'text' ):
					return str( response.get( 'text' ) )
				
				output = response.get( 'output', [ ] )
				if isinstance( output, list ):
					parts: List[ str ] = [ ]
					
					for item in output:
						if not isinstance( item, dict ):
							continue
						
						content = item.get( 'content', [ ] )
						if isinstance( content, list ):
							for block in content:
								if isinstance( block, dict ) and block.get( 'text' ):
									parts.append( str( block.get( 'text' ) ) )
					
					if parts:
						return '\n'.join( parts ).strip( )
			
			if hasattr( response, '__iter__' ) and not isinstance( response, (str, bytes, dict) ):
				parts: List[ str ] = [ ]
				
				for event in response:
					event_type = getattr( event, 'type', '' )
					
					if event_type == 'response.output_text.delta':
						delta = getattr( event, 'delta', '' )
						if delta:
							parts.append( str( delta ) )
					
					elif event_type == 'response.completed':
						final_response = getattr( event, 'response', None )
						if final_response is not None:
							text = self.extract_output_text( final_response )
							if text:
								return text
				
				if parts:
					return ''.join( parts )
			
			output = getattr( response, 'output', None )
			if output:
				parts: List[ str ] = [ ]
				
				for item in output:
					content = getattr( item, 'content', None )
					
					if content:
						for block in content:
							text = getattr( block, 'text', None )
							
							if text:
								parts.append( str( text ) )
				
				if parts:
					return '\n'.join( parts ).strip( )
			
			return str( response )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = 'extract_output_text( self, response: Any ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def create_response( self, payload: Dict[ str, Any ] ) -> Any:
		'''
		
			Purpose:
			--------
			Call the xAI Responses API using the available SDK surface.

			Args:
			-----------
			payload (Dict[str, Any]):
				Complete Responses API request payload.

			Returns:
			--------
			Any:
				xAI response object.
			
		'''
		try:
			throw_if( 'payload', payload )
			
			if hasattr( self.client, 'responses' ) and hasattr( self.client.responses, 'create' ):
				return self.client.responses.create( **payload )
			
			if hasattr( self.client, 'chat' ) and hasattr( self.client.chat, 'create' ):
				messages = payload.get( 'input', [ ] )
				
				if isinstance( messages, str ):
					messages = [ { 'role': 'user', 'content': messages } ]
				
				chat_payload = {
						'model': payload.get( 'model' ),
						'messages': messages,
						'stream': payload.get( 'stream', False )
				}
				
				if payload.get( 'temperature' ) is not None:
					chat_payload[ 'temperature' ] = payload.get( 'temperature' )
				
				if payload.get( 'top_p' ) is not None:
					chat_payload[ 'top_p' ] = payload.get( 'top_p' )
				
				if payload.get( 'max_output_tokens' ) is not None:
					chat_payload[ 'max_tokens' ] = payload.get( 'max_output_tokens' )
				
				if payload.get( 'tools' ):
					chat_payload[ 'tools' ] = payload.get( 'tools' )
				
				if payload.get( 'tool_choice' ):
					chat_payload[ 'tool_choice' ] = payload.get( 'tool_choice' )
				
				if payload.get( 'stop' ):
					chat_payload[ 'stop' ] = payload.get( 'stop' )
				
				if payload.get( 'response_format' ):
					chat_payload[ 'response_format' ] = payload.get( 'response_format' )
				
				if payload.get( 'reasoning_effort' ):
					chat_payload[ 'reasoning_effort' ] = payload.get( 'reasoning_effort' )
				
				if payload.get( 'reasoning' ):
					chat_payload[ 'reasoning' ] = payload.get( 'reasoning' )
				
				return self.client.chat.create( **chat_payload )
			
			raise RuntimeError( 'The xAI client does not expose responses.create or chat.create.' )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = 'create_response( self, payload: Dict[ str, Any ] ) -> Any'
			Logger( ).write( exception )
			raise exception
	
	def fetch( self, query: str, model: str = 'grok-4-fast-reasoning',
			temperature: float = 0.7, max_tokens: int = 2048, top_p: float = 1.0,
			seed: int | None = None, system: str = None,
			response_format: str = None, reasoning_effort: str = None,
			web_search: bool = False, search_domains: Any = None,
			stop: List[ str ] = None, stream: bool = False, store: bool = True,
			parallel_tool_calls: bool = True, tool_choice: str = 'auto' ) -> str | None:
		'''
		
			Purpose:
			--------
			Send an xAI Responses API request for Grok text generation, optional JSON
			mode, optional reasoning controls, optional web search, and optional stop
			sequences.

			Args:
			-----------
			query (str):
				User prompt.

			model (str):
				Grok model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output-token count.

			top_p (float):
				Nucleus sampling value.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system instructions.

			response_format (str | None):
				Optional output format. Use json for JSON object mode.

			reasoning_effort (str | None):
				Optional reasoning effort, only sent to models that support it.

			web_search (bool):
				Whether to enable xAI web search.

			search_domains (Any):
				Optional allowed domains for xAI web search.

			stop (List[str] | None):
				Optional stop sequences for non-reasoning models.

			stream (bool):
				Whether to stream the response.

			store (bool):
				Whether xAI should store the response server-side.

			parallel_tool_calls (bool):
				Whether parallel tool calls are enabled.

			tool_choice (str):
				Tool-choice behavior.

			Returns:
			--------
			str | None:
				Generated response text.
			
		'''
		try:
			throw_if( 'query', query )
			throw_if( 'model', model )
			
			self.query = str( query )
			self.model = str( model ).strip( )
			self.temperature = float( temperature )
			self.max_tokens = int( max_tokens )
			self.top_p = float( top_p )
			self.reasoning_effort = reasoning_effort if reasoning_effort else None
			self.stream = bool( stream )
			self.store = bool( store )
			self.web_search = bool( web_search )
			self.search_domains = self.normalize_domains( search_domains )
			self.parallel_tool_calls = bool( parallel_tool_calls )
			self.tool_choice = tool_choice or 'auto'
			self.system_instructions = self.build_instructions(
				system=system,
				response_format=response_format
			)
			self.tools = self.build_tools(
				web_search=self.web_search,
				search_domains=self.search_domains
			)
			
			input_messages: List[ Dict[ str, str ] ] = [ ]
			
			if self.system_instructions:
				input_messages.append(
					{
							'role': 'system',
							'content': self.system_instructions
					}
				)
			
			input_messages.append(
				{
						'role': 'user',
						'content': self.query
				}
			)
			
			self.params = {
					'model': self.model,
					'input': input_messages,
					'max_output_tokens': self.max_tokens,
					'stream': self.stream,
					'store': self.store,
					'parallel_tool_calls': self.parallel_tool_calls
			}
			
			if seed is not None:
				self.params[ 'seed' ] = int( seed )
			
			format_payload = self.build_response_format( response_format )
			if format_payload:
				self.params[ 'response_format' ] = format_payload
			
			if self.tools:
				self.params[ 'tools' ] = self.tools
				self.params[ 'tool_choice' ] = self.tool_choice
			
			is_reasoning = self.is_reasoning_model( self.model )
			
			if self.supports_reasoning_effort( self.model ) and self.reasoning_effort:
				self.params[ 'reasoning_effort' ] = self.reasoning_effort
			elif self.supports_reasoning_object( self.model ) and self.reasoning_effort:
				self.params[ 'reasoning' ] = { 'effort': self.reasoning_effort }
			
			if not is_reasoning:
				self.params[ 'temperature' ] = self.temperature
				self.params[ 'top_p' ] = self.top_p
				
				if stop:
					self.params[ 'stop' ] = [
							str( item )
							for item in stop
							if str( item ).strip( )
					]
			
			self.response = self.create_response( self.params )
			return self.extract_output_text( self.response )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = (
					'fetch( self, query: str, model: str="grok-4-fast-reasoning", '
					'temperature: float=0.7, max_tokens: int=2048, top_p: float=1.0, '
					'seed: int | None=None, system: str | None=None, '
					'response_format: str | None=None, reasoning_effort: str | None=None, '
					'web_search: bool=False, search_domains: Any=None, '
					'stop: List[ str ] | None=None, stream: bool=False, '
					'store: bool=True, parallel_tool_calls: bool=True, '
					'tool_choice: str="auto" ) -> str | None'
			)
			Logger( ).write( exception )
			raise exception
	
	def generate_text( self, query: str, model: str = 'grok-4-fast-reasoning',
			temperature: float = 0.7, max_tokens: int = 2048, top_p: float = 1.0,
			seed: int | None = None, system: str = None,
			response_format: str = None, reasoning_effort: str = None,
			web_search: bool = False, search_domains: Any = None,
			stop: List[ str ] = None, stream: bool = False, store: bool = True,
			parallel_tool_calls: bool = True, tool_choice: str = 'auto' ) -> str | None:
		'''
		
			Purpose:
			--------
			Convenience wrapper around fetch for Grok text generation.

			Args:
			-----------
			query (str):
				User prompt.

			model (str):
				Grok model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output-token count.

			top_p (float):
				Nucleus sampling value.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system instructions.

			response_format (str | None):
				Optional output format.

			reasoning_effort (str | None):
				Optional reasoning effort.

			web_search (bool):
				Whether xAI web search is enabled.

			search_domains (Any):
				Optional allowed domains.

			stop (List[str] | None):
				Optional stop sequences.

			stream (bool):
				Whether to stream the response.

			store (bool):
				Whether to store the response server-side.

			parallel_tool_calls (bool):
				Whether parallel tool calls are enabled.

			tool_choice (str):
				Tool-choice behavior.

			Returns:
			--------
			str | None:
				Generated response text.
			
		'''
		try:
			return self.fetch(
				query=query,
				model=model,
				temperature=temperature,
				max_tokens=max_tokens,
				top_p=top_p,
				seed=seed,
				system=system,
				response_format=response_format,
				reasoning_effort=reasoning_effort,
				web_search=web_search,
				search_domains=search_domains,
				stop=stop,
				stream=stream,
				store=store,
				parallel_tool_calls=parallel_tool_calls,
				tool_choice=tool_choice
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = 'generate_text( self, query: str, ... ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def search_web( self, query: str, model: str = 'grok-4-fast-reasoning',
			temperature: float = 0.7, max_tokens: int = 2048, top_p: float = 1.0,
			seed: int | None = None, system: str = None,
			response_format: str = None, reasoning_effort: str = None,
			search_domains: Any = None, stream: bool = False, store: bool = True,
			parallel_tool_calls: bool = True, tool_choice: str = 'auto' ) -> str | None:
		'''
		
			Purpose:
			--------
			Convenience wrapper around fetch with xAI web search enabled.

			Args:
			-----------
			query (str):
				User prompt.

			model (str):
				Grok model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output-token count.

			top_p (float):
				Nucleus sampling value.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system instructions.

			response_format (str | None):
				Optional output format.

			reasoning_effort (str | None):
				Optional reasoning effort.

			search_domains (Any):
				Optional allowed domains.

			stream (bool):
				Whether to stream the response.

			store (bool):
				Whether to store the response server-side.

			parallel_tool_calls (bool):
				Whether parallel tool calls are enabled.

			tool_choice (str):
				Tool-choice behavior.

			Returns:
			--------
			str | None:
				Web-search-augmented response text.
			
		'''
		try:
			return self.fetch(
				query=query,
				model=model,
				temperature=temperature,
				max_tokens=max_tokens,
				top_p=top_p,
				seed=seed,
				system=system,
				response_format=response_format,
				reasoning_effort=reasoning_effort,
				web_search=True,
				search_domains=search_domains,
				stop=None,
				stream=stream,
				store=store,
				parallel_tool_calls=parallel_tool_calls,
				tool_choice=tool_choice
			)
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Grok'
			exception.method = 'search_web( self, query: str, ... ) -> str | None'
			Logger( ).write( exception )
			raise exception

class Gemini( Generator ):
	'''

		Purpose:
		--------
		Class providing Google Gemini text generation, JSON output, Google Search
		grounding, stop sequences, and Gemini thinking controls.

		Attributes:
		-----------
		api_key (str):
			Google Gemini API key from configuration.

		client (Any):
			Initialized Google GenAI client.

		model (str):
			Selected Gemini model identifier.

		response (Any):
			Last Gemini response object.

		query (str | None):
			Last user prompt.

		params (Dict[str, Any] | None):
			Last request payload.

		temperature (float):
			Sampling temperature.

		max_tokens (int):
			Maximum output-token count.

		top_p (float):
			Nucleus sampling parameter.

		top_k (int | None):
			Top-k sampling parameter.

		candidate_count (int):
			Number of candidate responses.

		seed (int | None):
			Optional deterministic seed.

		system_instructions (str | None):
			Optional system prompt.

		response_format (str | None):
			Output response format selector.

		stop_sequences (List[str]):
			Optional stop sequences.

		grounding (bool):
			Whether Google Search grounding is enabled.

		search_domains (List[str]):
			Optional preferred grounding domains used as instruction guidance.

		reasoning (bool):
			Whether Gemini thinking is enabled.

		thinking_level (str | None):
			Gemini 3 thinking level.

		thinking_budget (int | None):
			Gemini 2.5 thinking token budget.

		include_thoughts (bool):
			Whether Gemini should include thought summaries where supported.

		Methods:
		--------
		fetch( self, prompt, ... ) -> str | None
		generate_text( self, prompt, ... ) -> str | None
		search_web( self, prompt, ... ) -> str | None

	'''
	
	api_key: Optional[ str ]
	client: Optional[ Any ]
	model: Optional[ str ]
	response: Optional[ Any ]
	query: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	temperature: Optional[ float ]
	max_tokens: Optional[ int ]
	top_p: Optional[ float ]
	top_k: Optional[ int ]
	candidate_count: Optional[ int ]
	seed: Optional[ int ]
	system_instructions: Optional[ str ]
	response_format: Optional[ str ]
	stop_sequences: Optional[ List[ str ] ]
	grounding: Optional[ bool ]
	search_domains: Optional[ List[ str ] ]
	reasoning: Optional[ bool ]
	thinking_level: Optional[ str ]
	thinking_budget: Optional[ int ]
	include_thoughts: Optional[ bool ]
	tools: Optional[ List[ Any ] ]
	config: Optional[ Any ]
	
	def __init__( self ) -> None:
		'''
		
			Purpose:
			--------
			Initialize the Gemini generator with defaults used by the Foo application.

			Args:
			-----------
			None

			Returns:
			--------
			None
			
		'''
		super( ).__init__( )
		self.api_key = cfg.GOOGLE_API_KEY
		self.client = genai.Client( api_key=self.api_key )
		self.model = 'gemini-2.5-flash'
		self.response = None
		self.query = None
		self.params = None
		self.temperature = 0.7
		self.max_tokens = 2048
		self.top_p = 1.0
		self.top_k = None
		self.candidate_count = 1
		self.seed = None
		self.system_instructions = None
		self.response_format = None
		self.stop_sequences = [ ]
		self.grounding = False
		self.search_domains = [ ]
		self.reasoning = False
		self.thinking_level = None
		self.thinking_budget = None
		self.include_thoughts = False
		self.tools = [ ]
		self.config = None
	
	def __dir__( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return a stable ordered member list for introspection.

			Args:
			-----------
			None

			Returns:
			--------
			List[str]:
				Ordered attribute and method names.
			
		'''
		return [
				'api_key',
				'client',
				'model',
				'response',
				'query',
				'params',
				'temperature',
				'max_tokens',
				'top_p',
				'top_k',
				'candidate_count',
				'seed',
				'system_instructions',
				'response_format',
				'stop_sequences',
				'grounding',
				'search_domains',
				'reasoning',
				'thinking_level',
				'thinking_budget',
				'include_thoughts',
				'tools',
				'config',
				'normalize_domains',
				'normalize_stop_sequences',
				'supports_thinking_level',
				'supports_thinking_budget',
				'build_system_instruction',
				'build_thinking_config',
				'build_tools',
				'build_config',
				'extract_text',
				'fetch',
				'generate_text',
				'search_web'
		]
	
	def normalize_domains( self, domains: Any ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Normalize user-supplied grounding domains into canonical, de-duplicated
			domain names.

			Args:
			-----------
			domains (Any):
				String, list, tuple, set, scalar, or None containing domain values.

			Returns:
			--------
			List[str]:
				Clean domain names without protocol, path, port, or leading www.
			
		'''
		try:
			if domains is None:
				return [ ]
			
			if isinstance( domains, str ):
				parts = re.split( r'[\n,;]+', domains )
			elif isinstance( domains, (list, tuple, set) ):
				parts = [ str( item ) for item in domains if item is not None ]
			else:
				parts = [ str( domains ) ]
			
			values: List[ str ] = [ ]
			
			for entry in parts:
				value = str( entry ).strip( ).lower( )
				
				if not value:
					continue
				
				if not value.startswith( 'http://' ) and not value.startswith( 'https://' ):
					value = f'https://{value}'
				
				parsed = urllib.parse.urlparse( value )
				domain = (parsed.netloc or parsed.path or '').strip( ).lower( )
				domain = re.sub( r':\d+$', '', domain )
				domain = domain.lstrip( '.' )
				
				if domain.startswith( 'www.' ):
					domain = domain[ 4: ]
				
				if not re.fullmatch( r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', domain ):
					raise ValueError( f'Invalid Gemini grounding domain: {domain}' )
				
				if domain not in values:
					values.append( domain )
			
			return values
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = 'normalize_domains( self, domains: Any ) -> List[ str ]'
			Logger( ).write( exception )
			raise exception
	
	def normalize_stop_sequences( self, stop_sequences: Any ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Normalize stop sequences supplied as a string or iterable.

			Args:
			-----------
			stop_sequences (Any):
				String, list, tuple, set, scalar, or None containing stop sequences.

			Returns:
			--------
			List[str]:
				Non-empty stop sequences.
			
		'''
		try:
			if stop_sequences is None:
				return [ ]
			
			if isinstance( stop_sequences, str ):
				parts = stop_sequences.splitlines( )
			elif isinstance( stop_sequences, (list, tuple, set) ):
				parts = [ str( item ) for item in stop_sequences if item is not None ]
			else:
				parts = [ str( stop_sequences ) ]
			
			return [
					str( item ).strip( )
					for item in parts
					if str( item ).strip( )
			]
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = (
					'normalize_stop_sequences( self, stop_sequences: Any ) -> List[ str ]'
			)
			Logger( ).write( exception )
			raise exception
	
	def supports_thinking_level( self, model: str ) -> bool:
		'''
		
			Purpose:
			--------
			Determine whether the selected model supports Gemini 3 thinkingLevel.

			Args:
			-----------
			model (str):
				Gemini model identifier.

			Returns:
			--------
			bool:
				True when the model is a Gemini 3 family model.
			
		'''
		try:
			throw_if( 'model', model )
			return str( model ).strip( ).lower( ).startswith( 'gemini-3' )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = 'supports_thinking_level( self, model: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def supports_thinking_budget( self, model: str ) -> bool:
		'''
		
			Purpose:
			--------
			Determine whether the selected model supports Gemini 2.5 thinkingBudget.

			Args:
			-----------
			model (str):
				Gemini model identifier.

			Returns:
			--------
			bool:
				True when the model is a Gemini 2.5 family model.
			
		'''
		try:
			throw_if( 'model', model )
			return str( model ).strip( ).lower( ).startswith( 'gemini-2.5' )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = 'supports_thinking_budget( self, model: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def build_system_instruction( self, system: str = None, response_format: str = None,
			grounding: bool = False, search_domains: Any = None ) -> str | None:
		'''
		
			Purpose:
			--------
			Build the Gemini system instruction.

			Args:
			-----------
			system (str | None):
				Optional system instruction.

			response_format (str | None):
				Optional response-format selector.

			grounding (bool):
				Whether grounding is enabled.

			search_domains (Any):
				Optional preferred grounding domains.

			Returns:
			--------
			str | None:
				Final system instruction or None.
			
		'''
		try:
			parts: List[ str ] = [ ]
			if system and str( system ).strip( ):
				parts.append( str( system ).strip( ) )
			
			if response_format and str( response_format ).strip( ).lower( ) == 'json':
				parts.append( 'Return valid JSON only. Do not include markdown fences, prose, '
				              'or commentary outside the JSON value.' )
			
			domains = self.normalize_domains( search_domains )
			if grounding and domains:
				parts.append( 'When using Google Search grounding, strongly prefer relevant '
				              f'sources from these domains when available: {", ".join( domains )}.' )
			
			if parts:
				return '\n\n'.join( parts )
			
			return None
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = (
					'build_system_instruction( self, system: str | None=None, '
					'response_format: str | None=None, grounding: bool=False, '
					'search_domains: Any=None ) -> str | None'
			)
			Logger( ).write( exception )
			raise exception
	
	def build_thinking_config( self, model: str, reasoning: bool = False,
			thinking_level: str = None, thinking_budget: int | None = None,
			include_thoughts: bool = False ) -> Any:
		'''
		
			Purpose:
			--------
			Build Gemini thinking configuration for Gemini 3 thinkingLevel or
			Gemini 2.5 thinkingBudget.

			Args:
			-----------
			model (str):
				Gemini model identifier.

			reasoning (bool):
				Whether thinking controls should be enabled.

			thinking_level (str | None):
				Gemini 3 thinking level.

			thinking_budget (int | None):
				Gemini 2.5 thinking budget.

			include_thoughts (bool):
				Whether to include thought summaries where supported.

			Returns:
			--------
			Any:
				Google GenAI ThinkingConfig-compatible object or None.
			
		'''
		try:
			if not reasoning:
				return None
			
			thinking_data: Dict[ str, Any ] = { }
			
			if self.supports_thinking_level( model ):
				level = str( thinking_level or 'low' ).strip( ).lower( )
				
				if level not in [ 'minimal', 'low', 'medium', 'high' ]:
					level = 'low'
				
				thinking_data[ 'thinking_level' ] = level
			
			elif self.supports_thinking_budget( model ):
				if thinking_budget is not None:
					thinking_data[ 'thinking_budget' ] = int( thinking_budget )
				else:
					thinking_data[ 'thinking_budget' ] = -1
			
			else:
				return None
			
			if include_thoughts:
				thinking_data[ 'include_thoughts' ] = True
			
			if hasattr( types, 'ThinkingConfig' ):
				return types.ThinkingConfig( **thinking_data )
			
			return thinking_data
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = (
					'build_thinking_config( self, model: str, reasoning: bool=False, '
					'thinking_level: str | None=None, thinking_budget: int | None=None, '
					'include_thoughts: bool=False ) -> Any'
			)
			Logger( ).write( exception )
			raise exception
	
	def build_tools( self, grounding: bool = False ) -> List[ Any ]:
		'''
		
			Purpose:
			--------
			Build Gemini tool configuration for Google Search grounding.

			Args:
			-----------
			grounding (bool):
				Whether to enable Google Search grounding.

			Returns:
			--------
			List[Any]:
				Google GenAI tool definitions.
			
		'''
		try:
			if not grounding:
				return [ ]
			
			if hasattr( types, 'Tool' ) and hasattr( types, 'GoogleSearch' ):
				return [ types.Tool( google_search=types.GoogleSearch( ) ) ]
			
			return [ { 'google_search': { } } ]
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = 'build_tools( self, grounding: bool=False ) -> List[ Any ]'
			Logger( ).write( exception )
			raise exception
	
	def build_config( self, model: str, temperature: float = 0.7,
			max_tokens: int = 2048, top_p: float = 1.0, top_k: int | None = None,
			candidate_count: int = 1, seed: int | None = None,
			system: str = None, response_format: str = None,
			stop_sequences: Any = None, grounding: bool = False, search_domains: Any = None,
			reasoning: bool = False, thinking_level: str = None,
			thinking_budget: int | None = None, include_thoughts: bool = False,
			response_json_schema: Dict[ str, Any ] = None ) -> Any:
		'''
		
			Purpose:
			--------
			Build a Google GenAI GenerateContentConfig-compatible configuration.

			Args:
			-----------
			model (str):
				Gemini model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output-token count.

			top_p (float):
				Nucleus sampling parameter.

			top_k (int | None):
				Top-k sampling parameter.

			candidate_count (int):
				Number of candidates to generate.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system instruction.

			response_format (str | None):
				Optional output format selector.

			stop_sequences (Any):
				Optional stop sequences.

			grounding (bool):
				Whether Google Search grounding is enabled.

			search_domains (Any):
				Optional preferred grounding domains.

			reasoning (bool):
				Whether thinking is enabled.

			thinking_level (str | None):
				Gemini 3 thinking level.

			thinking_budget (int | None):
				Gemini 2.5 thinking budget.

			include_thoughts (bool):
				Whether thought summaries are requested.

			response_json_schema (Dict[str, Any] | None):
				Optional JSON schema for structured output.

			Returns:
			--------
			Any:
				GenerateContentConfig object or dictionary fallback.
			
		'''
		try:
			config_data: Dict[ str, Any ] = {
					'temperature': float( temperature ),
					'max_output_tokens': int( max_tokens ),
					'top_p': float( top_p ),
					'candidate_count': int( candidate_count )
			}
			
			if top_k is not None and int( top_k ) > 0:
				config_data[ 'top_k' ] = int( top_k )
			
			if seed is not None:
				config_data[ 'seed' ] = int( seed )
			
			system_instruction = self.build_system_instruction(
				system=system,
				response_format=response_format,
				grounding=grounding,
				search_domains=search_domains
			)
			
			if system_instruction:
				config_data[ 'system_instruction' ] = system_instruction
			
			clean_stop = self.normalize_stop_sequences( stop_sequences )
			if clean_stop:
				config_data[ 'stop_sequences' ] = clean_stop
			
			if response_format and str( response_format ).strip( ).lower( ) == 'json':
				config_data[ 'response_mime_type' ] = 'application/json'
			
			if response_json_schema:
				config_data[ 'response_mime_type' ] = 'application/json'
				config_data[ 'response_json_schema' ] = response_json_schema
			
			tools_value = self.build_tools( grounding=grounding )
			if tools_value:
				config_data[ 'tools' ] = tools_value
			
			thinking_config = self.build_thinking_config(
				model=model,
				reasoning=reasoning,
				thinking_level=thinking_level,
				thinking_budget=thinking_budget,
				include_thoughts=include_thoughts
			)
			
			if thinking_config:
				config_data[ 'thinking_config' ] = thinking_config
			
			if hasattr( types, 'GenerateContentConfig' ):
				return types.GenerateContentConfig( **config_data )
			
			return config_data
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = (
					'build_config( self, model: str, temperature: float=0.7, '
					'max_tokens: int=2048, top_p: float=1.0, top_k: int | None=None, '
					'candidate_count: int=1, seed: int | None=None, '
					'system: str | None=None, response_format: str | None=None, '
					'stop_sequences: Any=None, grounding: bool=False, '
					'search_domains: Any=None, reasoning: bool=False, '
					'thinking_level: str | None=None, thinking_budget: int | None=None, '
					'include_thoughts: bool=False, '
					'response_json_schema: Dict[ str, Any ] | None=None ) -> Any'
			)
			Logger( ).write( exception )
			raise exception
	
	def extract_text( self, response: Any ) -> str:
		'''
		
			Purpose:
			--------
			Extract final text from a Gemini response object, dictionary, or fallback
			value.

			Args:
			-----------
			response (Any):
				Gemini response object.

			Returns:
			--------
			str:
				Best available response text.
			
		'''
		try:
			if response is None:
				return ''
			
			if hasattr( response, 'text' ) and response.text:
				return str( response.text )
			
			if isinstance( response, dict ):
				if response.get( 'text' ):
					return str( response.get( 'text' ) )
			
			candidates = getattr( response, 'candidates', None )
			if candidates:
				parts: List[ str ] = [ ]
				
				for candidate in candidates:
					content = getattr( candidate, 'content', None )
					candidate_parts = getattr( content, 'parts', None ) if content else None
					
					if not candidate_parts:
						continue
					
					for part in candidate_parts:
						text = getattr( part, 'text', None )
						
						if text:
							parts.append( str( text ) )
				
				if parts:
					return '\n'.join( parts ).strip( )
			
			return str( response )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = 'extract_text( self, response: Any ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def fetch( self, prompt: str, model: str = 'gemini-2.5-flash',
			temperature: float = 0.7, max_tokens: int = 2048, top_p: float = 1.0,
			top_k: int | None = None, candidate_count: int = 1,
			seed: int | None = None, system: str = None,
			response_format: str = None, stop_sequences: Any = None,
			grounding: bool = False, search_domains: Any = None,
			reasoning: bool = False, thinking_level: str = None,
			thinking_budget: int | None = None, include_thoughts: bool = False,
			response_json_schema: Dict[ str, Any ] = None ) -> str | None:
		'''
		
			Purpose:
			--------
			Send a Gemini generate_content request for text generation, JSON output,
			Google Search grounding, stop sequences, and model-appropriate thinking
			configuration.

			Args:
			-----------
			prompt (str):
				User prompt.

			model (str):
				Gemini model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output-token count.

			top_p (float):
				Nucleus sampling parameter.

			top_k (int | None):
				Top-k sampling parameter.

			candidate_count (int):
				Number of candidates to generate.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system instruction.

			response_format (str | None):
				Optional output format selector. Use json for JSON mode.

			stop_sequences (Any):
				Optional stop sequences.

			grounding (bool):
				Whether Google Search grounding is enabled.

			search_domains (Any):
				Optional preferred grounding domains.

			reasoning (bool):
				Whether Gemini thinking is enabled.

			thinking_level (str | None):
				Gemini 3 thinking level.

			thinking_budget (int | None):
				Gemini 2.5 thinking budget.

			include_thoughts (bool):
				Whether thought summaries are requested.

			response_json_schema (Dict[str, Any] | None):
				Optional JSON schema for structured output.

			Returns:
			--------
			str | None:
				Generated response text.
			
		'''
		try:
			throw_if( 'prompt', prompt )
			throw_if( 'model', model )
			
			self.query = str( prompt )
			self.model = str( model ).strip( )
			self.temperature = float( temperature )
			self.max_tokens = int( max_tokens )
			self.top_p = float( top_p )
			self.top_k = int( top_k ) if top_k is not None else None
			self.candidate_count = int( candidate_count )
			self.seed = int( seed ) if seed is not None else None
			self.system_instructions = (str( system ).strip( )
			                            if system and str( system ).strip( )
			                            else None)
			self.response_format = response_format
			self.stop_sequences = self.normalize_stop_sequences( stop_sequences )
			self.grounding = bool( grounding )
			self.search_domains = self.normalize_domains( search_domains )
			self.reasoning = bool( reasoning )
			self.thinking_level = thinking_level
			self.thinking_budget = thinking_budget
			self.include_thoughts = bool( include_thoughts )
			self.config = self.build_config( model=self.model, temperature=self.temperature,
				max_tokens=self.max_tokens, top_p=self.top_p, top_k=self.top_k,
				candidate_count=self.candidate_count, seed=self.seed,
				system=self.system_instructions, response_format=self.response_format,
				stop_sequences=self.stop_sequences, grounding=self.grounding,
				search_domains=self.search_domains, reasoning=self.reasoning,
				thinking_level=self.thinking_level, thinking_budget=self.thinking_budget,
				include_thoughts=self.include_thoughts, response_json_schema=response_json_schema )
			self.params = {
					'model': self.model,
					'contents': self.query,
					'config': self.config
			}
			
			self.response = self.client.models.generate_content( **self.params )
			return self.extract_text( self.response )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = 'fetch( self, *args ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def generate_text( self, prompt: str, model: str = 'gemini-2.5-flash',
			temperature: float = 0.7, max_tokens: int = 2048, top_p: float = 1.0,
			top_k: int | None = None, candidate_count: int = 1,
			seed: int | None = None, system: str = None,
			response_format: str = None, stop_sequences: Any = None,
			grounding: bool = False, search_domains: Any = None,
			reasoning: bool = False, thinking_level: str = None,
			thinking_budget: int | None = None, include_thoughts: bool = False,
			response_json_schema: Dict[ str, Any ] = None ) -> str | None:
		'''
		
			Purpose:
			--------
			Convenience wrapper around fetch for Gemini text generation.

			Args:
			-----------
			prompt (str):
				User prompt.

			model (str):
				Gemini model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output-token count.

			top_p (float):
				Nucleus sampling parameter.

			top_k (int | None):
				Top-k sampling parameter.

			candidate_count (int):
				Number of candidates to generate.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system instruction.

			response_format (str | None):
				Optional output format selector.

			stop_sequences (Any):
				Optional stop sequences.

			grounding (bool):
				Whether Google Search grounding is enabled.

			search_domains (Any):
				Optional preferred grounding domains.

			reasoning (bool):
				Whether Gemini thinking is enabled.

			thinking_level (str | None):
				Gemini 3 thinking level.

			thinking_budget (int | None):
				Gemini 2.5 thinking budget.

			include_thoughts (bool):
				Whether thought summaries are requested.

			response_json_schema (Dict[str, Any] | None):
				Optional JSON schema for structured output.

			Returns:
			--------
			str | None:
				Generated response text.
			
		'''
		try:
			return self.fetch( prompt=prompt, model=model, temperature=temperature,
				max_tokens=max_tokens, top_p=top_p, top_k=top_k,
				candidate_count=candidate_count, seed=seed, system=system,
				response_format=response_format, stop_sequences=stop_sequences,
				grounding=grounding, search_domains=search_domains, reasoning=reasoning,
				thinking_level=thinking_level, thinking_budget=thinking_budget,
				include_thoughts=include_thoughts, response_json_schema=response_json_schema )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = 'generate_text( self, prompt: str, ... ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def search_web( self, prompt: str, model: str = 'gemini-2.5-flash',
			temperature: float = 0.7, max_tokens: int = 2048, top_p: float = 1.0,
			top_k: int | None = None, candidate_count: int = 1,
			seed: int | None = None, system: str = None,
			response_format: str = None, stop_sequences: Any = None,
			search_domains: Any = None, reasoning: bool = False,
			thinking_level: str = None, thinking_budget: int | None = None,
			include_thoughts: bool = False,
			response_json_schema: Dict[ str, Any ] = None ) -> str | None:
		'''
		
			Purpose:
			--------
			Convenience wrapper around fetch with Google Search grounding enabled.

			Args:
			-----------
			prompt (str):
				User prompt.

			model (str):
				Gemini model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output-token count.

			top_p (float):
				Nucleus sampling parameter.

			top_k (int | None):
				Top-k sampling parameter.

			candidate_count (int):
				Number of candidates to generate.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system instruction.

			response_format (str | None):
				Optional output format selector.

			stop_sequences (Any):
				Optional stop sequences.

			search_domains (Any):
				Optional preferred grounding domains.

			reasoning (bool):
				Whether Gemini thinking is enabled.

			thinking_level (str | None):
				Gemini 3 thinking level.

			thinking_budget (int | None):
				Gemini 2.5 thinking budget.

			include_thoughts (bool):
				Whether thought summaries are requested.

			response_json_schema (Dict[str, Any] | None):
				Optional JSON schema for structured output.

			Returns:
			--------
			str | None:
				Web-grounded Gemini response text.
			
		'''
		try:
			return self.fetch( prompt=prompt, model=model, temperature=temperature,
				max_tokens=max_tokens, top_p=top_p, top_k=top_k, candidate_count=candidate_count,
				seed=seed, system=system, response_format=response_format,
				stop_sequences=stop_sequences, grounding=True, search_domains=search_domains,
				reasoning=reasoning, thinking_level=thinking_level, thinking_budget=thinking_budget,
				include_thoughts=include_thoughts, response_json_schema=response_json_schema )
		
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'generators'
			exception.cause = 'Gemini'
			exception.method = 'search_web( self, prompt: str, ... ) -> str | None'
			Logger( ).write( exception )
			raise exception

class Claude( Generator ):
	'''
	
		Purpose:
		---------
		Class providing Anthropic Claude text-generation, extended thinking,
		and optional web search support through the Messages API.
	
		Attributes:
		-----------
		client - Anthropic
		model - str
		response - Any
		api_key - str
		messages - List[ Dict[ str, Any ] ]
		params - Dict[ str, Any ]
		temperature - float
		max_tokens - int
		top_p - float
		top_k - int | None
		thinking_budget - int | None
		system_instructions - str | None
		web_search - bool
		search_domains - List[ str ]
		blocked_domains - List[ str ]
	
		Methods:
		-----------
		fetch( ) -> str | None
		generate_text( ) -> str | None
		search_web( ) -> str | None
		
	'''
	client: Optional[ AnthropicClient ]
	model: Optional[ str ]
	response: Optional[ Any ]
	api_key: Optional[ str ]
	messages: Optional[ List[ Dict[ str, Any ] ] ]
	params: Optional[ Dict[ str, Any ] ]
	temperature: Optional[ float ]
	max_tokens: Optional[ int ]
	top_p: Optional[ float ]
	top_k: Optional[ int ]
	thinking_budget: Optional[ int ]
	system_instructions: Optional[ str ]
	web_search: Optional[ bool ]
	search_domains: Optional[ List[ str ] ]
	blocked_domains: Optional[ List[ str ] ]
	
	def __init__( self ) -> None:
		'''
		
			Purpose:
			-----------
			Initialize Anthropic Claude API client.
			
			Args:
			-----------
			None
			
			Returns:
			-----------
			None
			
		'''
		super( ).__init__( )
		self.api_key = cfg.CLAUDE_API_KEY
		self.url = r'https://api.anthropic.com'
		self.client = None
		self.messages = None
		self.model = 'claude-sonnet-4-6'
		self.max_tokens = 2048
		self.temperature = 0.7
		self.top_p = 1.0
		self.top_k = None
		self.thinking_budget = None
		self.headers = { }
		self.timeout = None
		self.content = None
		self.params = None
		self.response = None
		self.system_instructions = None
		self.web_search = False
		self.search_domains = [ ]
		self.blocked_domains = [ ]
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ] = self.agents
	
	def __dir__( self ) -> List[ str ]:
		'''
		
			Purpose:
			-----------
			Claude list of members.
			
			Args:
			-----------
			None
			
			Returns:
			-----------
			list[str]: Ordered attribute/method names.
			
		'''
		return [ 'content',
		         'url',
		         'client',
		         'timeout',
		         'headers',
		         'fetch',
		         'api_key',
		         'response',
		         'params',
		         'agents',
		         'messages',
		         'temperature',
		         'top_p',
		         'top_k',
		         'thinking_budget',
		         'system_instructions',
		         'web_search',
		         'search_domains',
		         'blocked_domains' ]
	
	def _normalize_domains( self, domains: Any ) -> List[ str ]:
		'''
		
			Purpose:
			-----------
			Normalize domain input into a canonical, de-duplicated list.
			
			Args:
			-----------
			domains (Any): String, list, tuple, set, or None.
			
			Returns:
			-----------
			List[str]
			
		'''
		try:
			if domains is None:
				return [ ]
			
			if isinstance( domains, str ):
				_parts = re.split( r'[\n,;]+', domains )
			elif isinstance( domains, (list, tuple, set) ):
				_parts = [ str( x ) for x in domains if x is not None ]
			else:
				_parts = [ str( domains ) ]
			
			_values = [ ]
			for _entry in _parts:
				_value = str( _entry ).strip( ).lower( )
				if not _value:
					continue
				
				if not _value.startswith( 'http://' ) and not _value.startswith( 'https://' ):
					_value = f'https://{_value}'
				
				_parsed = urllib.parse.urlparse( _value )
				_domain = (_parsed.netloc or _parsed.path or '').strip( ).lower( )
				_domain = re.sub( r':\d+$', '', _domain )
				_domain = _domain.lstrip( '.' )
				
				if _domain.startswith( 'www.' ):
					_domain = _domain[ 4: ]
				
				if _domain and _domain not in _values:
					_values.append( _domain )
			
			return _values
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Claude'
			exception.method = '_normalize_domains( self, domains: Any ) -> List[ str ]'
			Logger( ).write( exception )
			raise exception
	
	def _supports_thinking( self, model: str ) -> bool:
		'''
		
			Purpose:
			-----------
			Determine whether the selected Claude model supports extended thinking.
			
			Args:
			-----------
			model (str): Model name.
			
			Returns:
			-----------
			bool
			
		'''
		try:
			throw_if( 'model', model )
			_name = str( model ).strip( ).lower( )
			return _name.startswith( 'claude-' )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Claude'
			exception.method = '_supports_thinking( self, model: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def _extract_text( self, response: Any ) -> str:
		'''
		
			Purpose:
			-----------
			Extract plain text from an Anthropic Messages API response.
			
			Args:
			-----------
			response (Any): Anthropic response object.
			
			Returns:
			-----------
			str
			
		'''
		try:
			if response is None:
				return ''
			
			if hasattr( response, 'content' ) and response.content:
				_parts = [ ]
				for _block in response.content:
					_type = getattr( _block, 'type', None )
					if _type == 'text':
						_text = getattr( _block, 'text', '' )
						if _text:
							_parts.append( _text )
				if _parts:
					return '\n'.join( _parts ).strip( )
			
			return str( response )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Claude'
			exception.method = '_extract_text( self, response: Any ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def fetch( self, query: str, model: str = 'claude-sonnet-4-6', temperature: float = 0.7,
			max_tokens: int = 2048, top_p: float = 1.0, top_k: int | None = None,
			system: str = None, stop_sequences: List[ str ] = None,
			thinking: bool = False, thinking_budget: int | None = None, web_search: bool = False,
			search_domains: Any = None, blocked_domains: Any = None ) -> str | None:
		'''
		
			Purpose:
			-------
			Send an Anthropic Messages API request for Claude text generation,
			optional extended thinking, and optional server-side web search.
			
			Args:
			-----------
			query (str): User prompt.
			model (str): Claude model name.
			temperature (float): Sampling temperature.
			max_tokens (int): Max output tokens.
			top_p (float): Top-p nucleus sampling parameter.
			top_k (int | None): Top-k sampling parameter.
			system (str | None): Optional system prompt.
			stop_sequences (List[str] | None): Optional stop sequences.
			thinking (bool): Enable extended thinking when supported.
			thinking_budget (int | None): Claude thinking budget in tokens.
			web_search (bool): Enable Claude web search tool.
			search_domains (Any): Optional allowlist domain input.
			blocked_domains (Any): Optional blocklist domain input.
			
			Returns:
			---------
			str | None
			
		'''
		try:
			throw_if( 'query', query )
			throw_if( 'model', model )
			
			self.query = query
			self.model = str( model ).strip( )
			self.temperature = float( temperature )
			self.max_tokens = int( max_tokens )
			self.top_p = float( top_p )
			self.top_k = int( top_k ) if top_k is not None else None
			self.system_instructions = system if system and str( system ).strip( ) else None
			self.web_search = bool( web_search )
			self.client = AnthropicClient( api_key=self.api_key )
			self.search_domains = self._normalize_domains( search_domains )
			self.blocked_domains = self._normalize_domains( blocked_domains )
			self.thinking_budget = int( thinking_budget ) if thinking_budget is not None else None
			self.messages = [ { 'role': 'user', 'content': self.query } ]
			self.params = {
					'model': self.model,
					'max_tokens': self.max_tokens,
					'messages': self.messages,
			}
			
			if self.system_instructions:
				self.params[ 'system' ] = self.system_instructions
			
			if stop_sequences:
				self.params[ 'stop_sequences' ] = stop_sequences
			
			if thinking and self._supports_thinking( self.model ):
				_budget = self.thinking_budget if self.thinking_budget is not None else 1024
				if _budget < 1024:
					_budget = 1024
				
				self.params[ 'thinking' ] = {
						'type': 'enabled',
						'budget_tokens': _budget,
				}
				
				if self.top_p is not None:
					self.params[ 'top_p' ] = min( 1.0, max( 0.95, self.top_p ) )
			else:
				self.params[ 'temperature' ] = self.temperature
				self.params[ 'top_p' ] = self.top_p
				
				if self.top_k is not None and self.top_k > 0:
					self.params[ 'top_k' ] = self.top_k
			
			if self.web_search:
				self.tools = [ ]
				self.web_tool = {
						'type': 'web_search_20250305',
						'name': 'web_search',
				}
				
				if self.search_domains:
					self.web_tool[ 'allowed_domains' ] = self.search_domains
				
				if self.blocked_domains:
					self.web_tool[ 'blocked_domains' ] = self.blocked_domains
				
				self.tools.append( self.web_tool )
				self.params[ 'tools' ] = self.tools
			
			self.response = self.client.messages.create( **self.params )
			return self._extract_text( self.response )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Claude'
			exception.method = 'fetch( self, *args ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def generate_text( self, query: str, model: str = 'claude-sonnet-4-6', temperature: float = 0.7,
			max_tokens: int = 2048, top_p: float = 1.0, top_k: int | None = None,
			system: str = None, stop_sequences: List[ str ] = None,
			thinking: bool = False, thinking_budget: int | None = None, web_search: bool = False,
			search_domains: Any = None, blocked_domains: Any = None ) -> str | None:
		'''
		
			Purpose:
			-----------
			Convenience wrapper around fetch for text generation.
			
			Args:
			-----------
			query (str): User prompt.
			
			Returns:
			-----------
			str | None
			
		'''
		try:
			return self.fetch( query=query, model=model, temperature=temperature,
				max_tokens=max_tokens, top_p=top_p, top_k=top_k, system=system,
				stop_sequences=stop_sequences, thinking=thinking, thinking_budget=thinking_budget,
				web_search=web_search, search_domains=search_domains,
				blocked_domains=blocked_domains, )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Claude'
			exception.method = 'generate_text( self, query: str, ... ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def search_web( self, query: str, model: str = 'claude-sonnet-4-6', temperature: float = 0.7,
			max_tokens: int = 2048, top_p: float = 1.0, top_k: int | None = None,
			system: str = None, stop_sequences: List[ str ] = None,
			thinking: bool = False, thinking_budget: int | None = None,
			search_domains: Any = None, blocked_domains: Any = None ) -> str | None:
		'''
		
			Purpose:
			-----------
			Convenience wrapper around fetch with web search enabled.
			
			Args:
			-----------
			query (str): User prompt.
			
			Returns:
			-----------
			str | None
			
		'''
		try:
			return self.fetch( query=query, model=model, temperature=temperature,
				max_tokens=max_tokens,
				top_p=top_p, top_k=top_k, system=system, stop_sequences=stop_sequences,
				thinking=thinking, thinking_budget=thinking_budget, web_search=True,
				search_domains=search_domains, blocked_domains=blocked_domains, )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Claude'
			exception.method = 'search_web( self, query: str, ... ) -> str | None'
			Logger( ).write( exception )
			raise exception

class Mistral( Generator ):
	'''

		Purpose:
		---------
		Class providing access to the Mistral chat-completions API.

		Attributes:
		-----------
		client - Optional[ MistralAI ]
		model - Optional[ str ]
		response - Optional[ Any ]
		api_key - Optional[ str ]
		query - Optional[ str ]
		params - Optional[ Dict[ str, Any ] ]
		temperature - Optional[ float ]
		max_tokens - Optional[ int ]
		top_p - Optional[ float ]
		messages - Optional[ List[ Dict[ str, Any ] ] ]
		system_instructions - Optional[ str ]
		seed - Optional[ int ]
		safe_prompt - Optional[ bool ]

		Methods:
		-----------
		_extract_text( self, response: Any ) -> str
		fetch( self, query: str, model: str='mistral-large-latest',
		       temperature: float=0.7, max_tokens: int=1024, top_p: float=1.0,
		       seed: int | None=None, safe_mode: bool=False,
		       system: str | None=None ) -> str | None
		create_schema( ... ) -> Dict[ str, str ] | None

	'''
	client: Optional[ MistralAI ]
	model: Optional[ str ]
	response: Optional[ Any ]
	api_key: Optional[ str ]
	query: Optional[ str ]
	params: Optional[ Dict[ str, Any ] ]
	temperature: Optional[ float ]
	max_tokens: Optional[ int ]
	top_p: Optional[ float ]
	messages: Optional[ List[ Dict[ str, Any ] ] ]
	system_instructions: Optional[ str ]
	seed: Optional[ int ]
	safe_prompt: Optional[ bool ]
	
	def __init__( self ) -> None:
		'''

			Purpose:
			-----------
			Initialize the Mistral API wrapper.

			Args:
			-----------
			None

			Returns:
			-----------
			None

		'''
		super( ).__init__( )
		self.api_key = cfg.MISTRAL_API_KEY
		self.model = 'mistral-large-latest'
		self.headers = { }
		self.client = None
		self.timeout = None
		self.content = None
		self.params = None
		self.response = None
		self.query = None
		self.temperature = None
		self.max_tokens = None
		self.top_p = None
		self.messages = [ ]
		self.system_instructions = None
		self.seed = None
		self.safe_prompt = False
		self.agents = cfg.AGENTS
		
		if 'User-Agent' not in self.headers:
			self.headers[ 'User-Agent' ] = self.agents
	
	def __dir__( self ) -> List[ str ]:
		'''

			Purpose:
			-----------
			Return the ordered list of members exposed by this wrapper.

			Args:
			-----------
			None

			Returns:
			-----------
			list[str]

		'''
		return [
				'content',
				'client',
				'timeout',
				'headers',
				'fetch',
				'api_key',
				'response',
				'params',
				'agents',
				'model',
				'temperature',
				'max_tokens',
				'top_p',
				'messages',
				'system_instructions',
				'seed',
				'safe_prompt',
				'_extract_text',
				'create_schema',
		]
	
	def _extract_text( self, response: Any ) -> str:
		'''

			Purpose:
			-----------
			Extract plain text from a Mistral chat completion response.

			Args:
			-----------
			response (Any): Raw SDK response object.

			Returns:
			-----------
			str

		'''
		try:
			if response is None:
				return ''
			
			if hasattr( response, 'choices' ) and response.choices:
				choice = response.choices[ 0 ]
				
				if hasattr( choice, 'message' ) and choice.message is not None:
					message = choice.message
					
					if hasattr( message, 'content' ):
						content = message.content
						
						if isinstance( content, str ):
							return content.strip( )
						
						if isinstance( content, list ):
							parts: List[ str ] = [ ]
							for item in content:
								if isinstance( item, str ) and item.strip( ):
									parts.append( item.strip( ) )
								elif hasattr( item, 'text' ):
									text_value = getattr( item, 'text', '' )
									if text_value:
										parts.append( str( text_value ).strip( ) )
							
							if parts:
								return '\n'.join( parts ).strip( )
						
						return str( content ).strip( )
			return str( response )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Mistral'
			exception.method = '_extract_text( self, response: Any ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def fetch( self, query: str, model: str = 'mistral-large-latest', temperature: float = 0.7,
			max_tokens: int = 1024, top_p: float = 1.0, seed: int | None = None,
			safe_mode: bool = False, system: str = None ) -> str | None:
		'''

			Purpose:
			-------
			Send a Mistral chat-completions request for text generation.

			Args:
			-----------
			query (str): User prompt.
			model (str): Mistral model name.
			temperature (float): Sampling temperature.
			max_tokens (int): Maximum output tokens.
			top_p (float): Top-p nucleus sampling parameter.
			seed (int | None): Deterministic random seed when provided.
			safe_mode (bool): If True, enable Mistral safe prompt injection.
			system (str | None): Optional system instructions.

			Returns:
			---------
			str | None

		'''
		try:
			throw_if( 'query', query )
			throw_if( 'model', model )
			self.query = str( query ).strip( )
			self.model = str( model ).strip( )
			self.temperature = float( temperature )
			self.max_tokens = int( max_tokens )
			self.top_p = float( top_p )
			self.seed = int( seed ) if seed is not None else None
			self.safe_prompt = bool( safe_mode )
			self.system_instructions = system if system and str( system ).strip( ) else None
			self.client = MistralAI( api_key=self.api_key )
			self.messages = [ ]
			if self.system_instructions:
				self.messages.append( {
						'role': 'system',
						'content': self.system_instructions,
				} )
			
			self.messages.append( {
					'role': 'user',
					'content': self.query,
			} )
			self.params = {
					'model': self.model,
					'messages': self.messages,
					'temperature': self.temperature,
					'max_tokens': self.max_tokens,
					'top_p': self.top_p,
					'stream': False,
					'response_format': { 'type': 'text' },
					'safe_prompt': self.safe_prompt,
			}
			
			if self.seed is not None and self.seed > 0:
				self.params[ 'random_seed' ] = self.seed
			
			self.response = self.client.chat.complete( **self.params )
			return self._extract_text( self.response )
		except Exception as exc:
			exception = Error( exc )
			exception.module = 'fetchers'
			exception.cause = 'Mistral'
			exception.method = 'fetch( self, *args ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def create_schema( self, function: str, tool: str,
			description: str, parameters: dict, required: list[ str ] ) -> Dict[ str, str ] | None:
		"""

			Purpose:
			________
			Construct and return a fully dynamic OpenAI Tool API schema definition.
			Supports arbitrary parameters, types, nested objects, and required fields.

			Args:
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
			_schema = \
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
			exception.cause = 'Mistral'
			exception.method = ('create_schema( self, function: str, tool: str, description: str, '
			                    'parameters: dict, required: list[ str ] ) -> Dict[ str, str ]')
			Logger( ).write( exception )
			raise exception

class Chat( Generator ):
	'''

		Purpose:
		--------
		Class used for interacting with OpenAI text-generation, reasoning, image,
		vision, file-search, and web-search capabilities through the Responses API.

		Attributes:
		-----------
		api_key (str):
			OpenAI API key from configuration.

		client (OpenAI):
			Initialized OpenAI SDK client.

		system_instructions (str | None):
			Final instruction block supplied to the Responses API.

		model (str):
			Selected OpenAI model identifier.

		number (int):
			Default response count retained for compatibility.

		temperature (float):
			Default sampling temperature.

		top_percent (float):
			Default nucleus sampling value.

		frequency_penalty (float):
			Compatibility member retained for older UI paths.

		presence_penalty (float):
			Compatibility member retained for older UI paths.

		max_completion_tokens (int):
			Default output-token limit.

		store (bool):
			Whether Responses API results should be stored server-side.

		stream (bool):
			Whether the Responses API request should stream.

		response_format (str):
			Current response-format mode.

		reasoning_effort (str | None):
			Optional reasoning-effort setting for reasoning-capable models.

		web_search (bool):
			Whether built-in web search is enabled.

		search_domains (List[str]):
			Optional preferred web-search domains.

		vector_store_ids (List[str]):
			Configured OpenAI vector store identifiers for file search.

		request (Dict[str, Any] | None):
			Last Responses API request payload.

		response (Any):
			Last OpenAI SDK response object.

		Methods:
		--------
		fetch( self, prompt, ... ) -> str
		generate_text( self, prompt, ... ) -> str
		generate_image( self, prompt ) -> str
		analyze_image( self, prompt, url ) -> str
		summarize_document( self, prompt, path ) -> str
		search_web( self, prompt, ... ) -> str
		search_files( self, prompt ) -> str
		translate( self, text ) -> str
		transcribe( self, text ) -> str
		get_format_options( self ) -> List[str]
		get_model_options( self ) -> List[str]
		get_effort_options( self ) -> List[str]
		get_data( self ) -> Dict[str, Any]
		dump( self ) -> str

	'''
	
	api_key: Optional[ str ]
	client: Optional[ OpenAI ]
	system_instructions: Optional[ str ]
	model: Optional[ str ]
	number: Optional[ int ]
	temperature: Optional[ float ]
	top_percent: Optional[ float ]
	frequency_penalty: Optional[ float ]
	presence_penalty: Optional[ float ]
	max_completion_tokens: Optional[ int ]
	store: Optional[ bool ]
	stream: Optional[ bool ]
	modalities: Optional[ List[ str ] ]
	stops: Optional[ List[ str ] ]
	response_format: Optional[ str ]
	reasoning_effort: Optional[ str ]
	input_text: Optional[ str ]
	id: Optional[ str ]
	vector_store_ids: Optional[ List[ str ] ]
	metadata: Optional[ Dict[ str, Any ] ]
	tools: Optional[ List[ Dict[ str, Any ] ] ]
	vector_stores: Optional[ Dict[ str, str ] ]
	web_search: Optional[ bool ]
	search_domains: Optional[ List[ str ] ]
	parallel_tool_calls: Optional[ bool ]
	tool_choice: Optional[ str ]
	request: Optional[ Dict[ str, Any ] ]
	response: Optional[ Any ]
	query: Optional[ str ]
	image_url: Optional[ str ]
	input: Optional[ Any ]
	messages: Optional[ Any ]
	
	def __init__( self, num: int = 1, temp: float = 0.8, top: float = 0.9,
			freq: float = 0.0, pres: float = 0.0, iters: int = 10000,
			store: bool = True, stream: bool = True ) -> None:
		'''
		
			Purpose:
			--------
			Initialize the OpenAI Chat generator with defaults used by the Foo
			application.

			Args:
			-----------
			num (int):
				Default response count retained for compatibility.

			temp (float):
				Default sampling temperature.

			top (float):
				Default top-p value.

			freq (float):
				Default frequency-penalty value retained for compatibility.

			pres (float):
				Default presence-penalty value retained for compatibility.

			iters (int):
				Default maximum completion/output token count.

			store (bool):
				Default Responses API store setting.

			stream (bool):
				Default Responses API stream setting.

			Returns:
			--------
			None
			
		'''
		super( ).__init__( )
		self.api_key = cfg.OPENAI_API_KEY
		self.client = OpenAI( api_key=self.api_key )
		self.client.api_key = cfg.OPENAI_API_KEY
		self.system_instructions = None
		self.model = 'gpt-5-mini'
		self.number = num
		self.temperature = temp
		self.top_percent = top
		self.frequency_penalty = freq
		self.presence_penalty = pres
		self.max_completion_tokens = iters
		self.store = store
		self.stream = stream
		self.modalities = [ 'text', 'audio' ]
		self.stops = [ '#', ';' ]
		self.response_format = 'auto'
		self.reasoning_effort = None
		self.input_text = None
		self.id = 'asst_2Yu2yfINGD5en4e0aUXAKxyu'
		self.vector_store_ids = [ 'vs_67e83bdf8abc81918bda0d6b39a19372' ]
		self.metadata = { }
		self.tools = [ ]
		self.vector_stores = { 'Code': 'vs_67e83bdf8abc81918bda0d6b39a19372' }
		self.web_search = False
		self.search_domains = [ ]
		self.parallel_tool_calls = True
		self.tool_choice = 'auto'
		self.request = None
		self.response = None
		self.query = None
		self.image_url = None
		self.input = None
		self.messages = None
	
	def __dir__( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return a stable ordered member list for introspection.

			Args:
			-----------
			None

			Returns:
			--------
			List[str]:
				Ordered attribute and method names.
			
		'''
		return [
				'api_key',
				'client',
				'system_instructions',
				'model',
				'number',
				'temperature',
				'top_percent',
				'frequency_penalty',
				'presence_penalty',
				'max_completion_tokens',
				'store',
				'stream',
				'response_format',
				'reasoning_effort',
				'web_search',
				'search_domains',
				'parallel_tool_calls',
				'tool_choice',
				'tools',
				'vector_store_ids',
				'request',
				'response',
				'fetch',
				'generate_text',
				'generate_image',
				'analyze_image',
				'summarize_document',
				'search_web',
				'search_files',
				'translate',
				'transcribe',
				'get_format_options',
				'get_model_options',
				'get_effort_options',
				'get_data',
				'dump'
		]
	
	def normalize_domains( self, domains: Any ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Normalize user-supplied domain input into canonical, de-duplicated
			domain names.

			Args:
			-----------
			domains (Any):
				String, list, tuple, set, scalar, or None containing domain values.

			Returns:
			--------
			List[str]:
				Clean domain names without protocol, path, port, or leading www.
			
		'''
		try:
			if domains is None:
				return [ ]
			
			if isinstance( domains, str ):
				parts = re.split( r'[\n,;]+', domains )
			elif isinstance( domains, (list, tuple, set) ):
				parts = [ str( item ) for item in domains if item is not None ]
			else:
				parts = [ str( domains ) ]
			
			values: List[ str ] = [ ]
			
			for entry in parts:
				value = str( entry ).strip( ).lower( )
				
				if not value:
					continue
				
				if not value.startswith( 'http://' ) and not value.startswith( 'https://' ):
					value = f'https://{value}'
				
				parsed = urllib.parse.urlparse( value )
				domain = (parsed.netloc or parsed.path or '').strip( ).lower( )
				domain = re.sub( r':\d+$', '', domain )
				domain = domain.lstrip( '.' )
				
				if domain.startswith( 'www.' ):
					domain = domain[ 4: ]
				
				if not domain:
					continue
				
				if not re.fullmatch( r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', domain ):
					raise ValueError( f'Invalid domain: {domain}' )
				
				if domain not in values:
					values.append( domain )
			
			return values
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'normalize_domains( self, domains: Any ) -> List[ str ]'
			Logger( ).write( exception )
			raise exception
	
	def supports_reasoning( self, model: str ) -> bool:
		'''
		
			Purpose:
			--------
			Determine whether the selected OpenAI model should receive a reasoning
			configuration.

			Args:
			-----------
			model (str):
				OpenAI model identifier.

			Returns:
			--------
			bool:
				True when the model name indicates a reasoning-capable family.
			
		'''
		try:
			throw_if( 'model', model )
			name = str( model ).strip( ).lower( )
			return name.startswith( 'gpt-5' ) or name.startswith( 'o' )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'supports_reasoning( self, model: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def build_instructions( self, system: str = None,
			response_format: str = None, web_search: bool = False,
			search_domains: Any = None ) -> str | None:
		'''
		
			Purpose:
			--------
			Build the final instruction block sent to the OpenAI Responses API.

			Args:
			-----------
			system (str | None):
				Optional user-provided system/developer instructions.

			response_format (str | None):
				Optional response-format mode, such as json.

			web_search (bool):
				Whether web search is enabled for this request.

			search_domains (Any):
				Optional preferred source domains.

			Returns:
			--------
			str | None:
				Instruction block or None when no instructions are required.
			
		'''
		try:
			parts: List[ str ] = [ ]
			
			if system and str( system ).strip( ):
				parts.append( str( system ).strip( ) )
			
			if response_format and str( response_format ).strip( ).lower( ) == 'json':
				parts.append(
					'Return valid JSON only. Do not include markdown fences, prose, '
					'or commentary outside the JSON value.'
				)
			
			domains = self.normalize_domains( search_domains )
			if web_search and domains:
				parts.append(
					'When using web search, strongly prefer sources from the following '
					f'domains when they are relevant and available: {", ".join( domains )}.'
				)
			
			if parts:
				return '\n\n'.join( parts )
			
			return None
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = (
					'build_instructions( self, system: str | None=None, '
					'response_format: str | None=None, web_search: bool=False, '
					'search_domains: Any=None ) -> str | None'
			)
			Logger( ).write( exception )
			raise exception
	
	def build_text_format( self, response_format: str | Dict[ str, Any ] = None,
			json_schema: Dict[ str, Any ] = None, schema_name: str = 'structured_response',
			schema_description: str = 'Structured JSON response.' ) -> Dict[ str, Any ] | None:
		'''
		
			Purpose:
			--------
			Build the Responses API text.format payload for text, JSON object mode,
			or JSON schema structured output.

			Args:
			-----------
			response_format (str | Dict[str, Any] | None):
				Output format selector. Accepted strings are auto, text, json,
				json_object, json_schema, and schema.

			json_schema (Dict[str, Any] | None):
				Optional JSON Schema object for structured outputs.

			schema_name (str):
				Response-format name used when json_schema is supplied.

			schema_description (str):
				Description used when json_schema is supplied.

			Returns:
			--------
			Dict[str, Any] | None:
				Responses API text-format object or None to omit the field.
			
		'''
		try:
			if isinstance( response_format, dict ):
				return response_format
			
			mode = str( response_format or '' ).strip( ).lower( )
			
			if not mode or mode == 'auto':
				return None
			
			if mode == 'text':
				return { 'type': 'text' }
			
			if mode in [ 'json', 'json_object' ]:
				return { 'type': 'json_object' }
			
			if mode in [ 'json_schema', 'schema' ]:
				throw_if( 'json_schema', json_schema )
				return {
						'type': 'json_schema',
						'name': schema_name,
						'description': schema_description,
						'strict': True,
						'schema': json_schema
				}
			
			return None
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = (
					'build_text_format( self, response_format: str | Dict[ str, Any ] | None=None, '
					'json_schema: Dict[ str, Any ] | None=None, schema_name: str=structured_response, '
					'schema_description: str=Structured JSON response. ) -> Dict[ str, Any ] | None'
			)
			Logger( ).write( exception )
			raise exception
	
	def build_tools( self, web_search: bool = False, search_domains: Any = None,
			file_search: bool = False, vector_store_ids: List[ str ] = None,
			max_file_results: int = 20 ) -> List[ Dict[ str, Any ] ]:
		'''
		
			Purpose:
			--------
			Build the Responses API hosted-tool list for web search and file search.

			Args:
			-----------
			web_search (bool):
				Whether to enable the built-in web-search tool.

			search_domains (Any):
				Optional preferred domains. Current behavior keeps these domains in
				instructions for compatibility and does not force unsupported filters.

			file_search (bool):
				Whether to enable the built-in file-search tool.

			vector_store_ids (List[str] | None):
				Vector store identifiers for file search.

			max_file_results (int):
				Maximum number of file-search results.

			Returns:
			--------
			List[Dict[str, Any]]:
				Responses API tool definitions.
			
		'''
		try:
			tools: List[ Dict[ str, Any ] ] = [ ]
			
			if web_search:
				tools.append( { 'type': 'web_search' } )
			
			if file_search:
				store_ids = vector_store_ids or self.vector_store_ids
				throw_if( 'vector_store_ids', store_ids )
				tools.append(
					{
							'type': 'file_search',
							'vector_store_ids': store_ids,
							'max_num_results': int( max_file_results )
					}
				)
			
			return tools
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = (
					'build_tools( self, web_search: bool=False, search_domains: Any=None, '
					'file_search: bool=False, vector_store_ids: List[ str ] | None=None, '
					'max_file_results: int=20 ) -> List[ Dict[ str, Any ] ]'
			)
			Logger( ).write( exception )
			raise exception
	
	def extract_output_text( self, response: Any ) -> str:
		'''
		
			Purpose:
			--------
			Extract text from an OpenAI SDK response or streaming response.

			Args:
			-----------
			response (Any):
				OpenAI response object, stream, dictionary, or scalar fallback.

			Returns:
			--------
			str:
				Best available output text.
			
		'''
		try:
			if response is None:
				return ''
			
			if hasattr( response, 'output_text' ) and response.output_text:
				return str( response.output_text )
			
			if isinstance( response, dict ):
				if response.get( 'output_text' ):
					return str( response.get( 'output_text' ) )
				if response.get( 'text' ):
					return str( response.get( 'text' ) )
			
			if hasattr( response, '__iter__' ) and not isinstance( response, (str, bytes, dict) ):
				parts: List[ str ] = [ ]
				
				for event in response:
					event_type = getattr( event, 'type', '' )
					
					if event_type == 'response.output_text.delta':
						delta = getattr( event, 'delta', '' )
						if delta:
							parts.append( str( delta ) )
					
					elif event_type == 'response.completed':
						final_response = getattr( event, 'response', None )
						if final_response is not None and hasattr( final_response, 'output_text' ):
							text = str( final_response.output_text or '' )
							if text:
								return text
				
				if parts:
					return ''.join( parts )
			
			output = getattr( response, 'output', None )
			if output:
				parts: List[ str ] = [ ]
				for item in output:
					content = getattr( item, 'content', None )
					if content:
						for block in content:
							text = getattr( block, 'text', None )
							if text:
								parts.append( str( text ) )
				
				if parts:
					return '\n'.join( parts ).strip( )
			
			return str( response )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'extract_output_text( self, response: Any ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def fetch( self, prompt: str, model: str = 'gpt-5-mini', temperature: float = 0.7,
			max_tokens: int = 1024, top_p: float = 1.0, seed: int | None = None,
			system: str = None, response_format: str | Dict[ str, Any ] = None,
			reasoning_effort: str = None, web_search: bool = False,
			search_domains: Any = None, store: bool = True, stream: bool = False,
			parallel_tool_calls: bool = True, tool_choice: str = 'auto',
			json_schema: Dict[ str, Any ] = None,
			schema_name: str = 'structured_response',
			schema_description: str = 'Structured JSON response.' ) -> str:
		'''
		
			Purpose:
			--------
			Send an OpenAI Responses API request for text generation, optional JSON
			mode, optional structured output, optional reasoning, and optional web
			search.

			Args:
			-----------
			prompt (str):
				User prompt.

			model (str):
				OpenAI model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output tokens.

			top_p (float):
				Nucleus sampling parameter.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system/developer instructions.

			response_format (str | Dict[str, Any] | None):
				Output format. Use json for JSON object mode, or json_schema/schema
				with json_schema for structured output.

			reasoning_effort (str | None):
				Optional reasoning effort for reasoning-capable models.

			web_search (bool):
				Whether to enable OpenAI built-in web search.

			search_domains (Any):
				Optional preferred domains used in instruction guidance.

			store (bool):
				Whether to store the response server-side.

			stream (bool):
				Whether to stream the response.

			parallel_tool_calls (bool):
				Whether parallel tool calls are allowed.

			tool_choice (str):
				Tool-choice behavior, normally auto.

			json_schema (Dict[str, Any] | None):
				Optional JSON Schema object for structured output.

			schema_name (str):
				Schema response-format name.

			schema_description (str):
				Schema response-format description.

			Returns:
			--------
			str:
				Generated response text.
			
		'''
		try:
			throw_if( 'prompt', prompt )
			throw_if( 'model', model )
			
			self.query = prompt
			self.model = str( model ).strip( )
			self.temperature = float( temperature )
			self.max_completion_tokens = int( max_tokens )
			self.top_percent = float( top_p )
			self.store = bool( store )
			self.stream = bool( stream )
			self.web_search = bool( web_search )
			self.search_domains = self.normalize_domains( search_domains )
			self.parallel_tool_calls = bool( parallel_tool_calls )
			self.tool_choice = tool_choice or 'auto'
			self.response_format = (
					str( response_format ).strip( ).lower( )
					if isinstance( response_format, str )
					else response_format
			)
			self.reasoning_effort = reasoning_effort if reasoning_effort else None
			self.system_instructions = self.build_instructions(
				system=system,
				response_format=(
						response_format
						if isinstance( response_format, str )
						else None
				),
				web_search=self.web_search,
				search_domains=self.search_domains
			)
			self.tools = self.build_tools(
				web_search=self.web_search,
				search_domains=self.search_domains,
				file_search=False
			)
			
			self.request = {
					'model': self.model,
					'input': self.query,
					'max_output_tokens': self.max_completion_tokens,
					'store': self.store,
					'stream': self.stream,
					'parallel_tool_calls': self.parallel_tool_calls
			}
			
			text_format = self.build_text_format( response_format=response_format,
				json_schema=json_schema, schema_name=schema_name,
				schema_description=schema_description )
			
			if text_format:
				self.request[ 'text' ] = { 'format': text_format }
			
			if self.system_instructions:
				self.request[ 'instructions' ] = self.system_instructions
			
			if seed is not None:
				self.request[ 'seed' ] = int( seed )
			
			if self.tools:
				self.request[ 'tools' ] = self.tools
				self.request[ 'tool_choice' ] = self.tool_choice
			
			if self.supports_reasoning( self.model ) and self.reasoning_effort:
				self.request[ 'reasoning' ] = { 'effort': self.reasoning_effort }
			else:
				self.request[ 'temperature' ] = self.temperature
				self.request[ 'top_p' ] = self.top_percent
			
			self.response = self.client.responses.create( **self.request )
			return self.extract_output_text( self.response )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = (
					'fetch( self, prompt: str, model: str="gpt-5-mini", '
					'temperature: float=0.7, max_tokens: int=1024, top_p: float=1.0, '
					'seed: int | None=None, system: str | None=None, '
					'response_format: str | Dict[ str, Any ] | None=None, '
					'reasoning_effort: str | None=None, web_search: bool=False, '
					'search_domains: Any=None, store: bool=True, stream: bool=False, '
					'parallel_tool_calls: bool=True, tool_choice: str="auto", '
					'json_schema: Dict[ str, Any ] | None=None, '
					'schema_name: str="structured_response", '
					'schema_description: str="Structured JSON response." ) -> str'
			)
			Logger( ).write( exception )
			raise exception
	
	def generate_text( self, prompt: str, model: str = 'gpt-5-mini',
			temperature: float = 0.7, max_tokens: int = 1024, top_p: float = 1.0,
			seed: int | None = None, system: str = None,
			response_format: str | Dict[ str, Any ] = None,
			reasoning_effort: str = None, web_search: bool = False,
			search_domains: Any = None, store: bool = True, stream: bool = False,
			parallel_tool_calls: bool = True, tool_choice: str = 'auto',
			json_schema: Dict[ str, Any ] = None ) -> str:
		'''
		
			Purpose:
			--------
			Convenience wrapper around fetch for text generation.

			Args:
			-----------
			prompt (str):
				User prompt.

			model (str):
				OpenAI model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output tokens.

			top_p (float):
				Nucleus sampling parameter.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system/developer instructions.

			response_format (str | Dict[str, Any] | None):
				Output format selector or complete text.format object.

			reasoning_effort (str | None):
				Optional reasoning effort.

			web_search (bool):
				Whether to enable web search.

			search_domains (Any):
				Optional preferred source domains.

			store (bool):
				Whether to store the response.

			stream (bool):
				Whether to stream the response.

			parallel_tool_calls (bool):
				Whether parallel tool calls are enabled.

			tool_choice (str):
				Tool-choice behavior.

			json_schema (Dict[str, Any] | None):
				Optional JSON Schema for structured output.

			Returns:
			--------
			str:
				Generated response text.
			
		'''
		try:
			return self.fetch( prompt=prompt, model=model, temperature=temperature,
				max_tokens=max_tokens, top_p=top_p, seed=seed, system=system,
				response_format=response_format, reasoning_effort=reasoning_effort,
				web_search=web_search, search_domains=search_domains, store=store,
				stream=stream, parallel_tool_calls=parallel_tool_calls,
				tool_choice=tool_choice, json_schema=json_schema )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'generate_text( self, prompt: str, ... ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def generate_image( self, prompt: str ) -> str:
		'''
		
			Purpose:
			--------
			Generate an image using the OpenAI image API.

			Args:
			-----------
			prompt (str):
				Image-generation prompt.

			Returns:
			--------
			str:
				Image URL or serialized response fallback.
			
		'''
		try:
			throw_if( 'prompt', prompt )
			self.input_text = prompt
			self.response = self.client.images.generate(
				model='gpt-image-1',
				prompt=self.input_text,
				size='1024x1024'
			)
			
			if hasattr( self.response, 'data' ) and self.response.data:
				image = self.response.data[ 0 ]
				
				if hasattr( image, 'url' ) and image.url:
					return image.url
			
			return str( self.response )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'generate_image( self, prompt: str ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def analyze_image( self, prompt: str, url: str ) -> str:
		'''
		
			Purpose:
			--------
			Analyze an image using a multimodal OpenAI model.

			Args:
			-----------
			prompt (str):
				User analysis prompt.

			url (str):
				Image URL or data URL.

			Returns:
			--------
			str:
				Image analysis result text.
			
		'''
		try:
			throw_if( 'prompt', prompt )
			throw_if( 'url', url )
			self.input_text = prompt
			self.image_url = url
			self.input = [
					{
							'role': 'user',
							'content': [
									{
											'type': 'input_text',
											'text': self.input_text
									},
									{
											'type': 'input_image',
											'image_url': self.image_url
									}
							]
					}
			]
			self.response = self.client.responses.create(
				model=self.model,
				input=self.input
			)
			return self.extract_output_text( self.response )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'analyze_image( self, prompt: str, url: str ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def summarize_document( self, prompt: str, path: str ) -> str:
		'''
		
			Purpose:
			--------
			Upload or reference a document path and summarize it through the Responses
			API.

			Args:
			-----------
			prompt (str):
				Summarization prompt.

			path (str):
				Local path to the document.

			Returns:
			--------
			str:
				Summary text.
			
		'''
		try:
			throw_if( 'prompt', prompt )
			throw_if( 'path', path )
			file_path = Path( path )
			
			if not file_path.exists( ):
				raise FileNotFoundError( str( file_path ) )
			
			with file_path.open( 'rb' ) as stream:
				uploaded = self.client.files.create(
					file=stream,
					purpose='assistants'
				)
			
			self.messages = [
					{
							'role': 'user',
							'content': [
									{
											'type': 'input_text',
											'text': prompt
									},
									{
											'type': 'input_file',
											'file_id': uploaded.id
									}
							]
					}
			]
			self.response = self.client.responses.create( model=self.model, input=self.messages )
			return self.extract_output_text( self.response )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'summarize_document( self, prompt: str, path: str ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def search_web( self, prompt: str, model: str = 'gpt-5-mini',
			temperature: float = 0.7, max_tokens: int = 1024, top_p: float = 1.0,
			seed: int | None = None, system: str = None,
			response_format: str | Dict[ str, Any ] = None,
			reasoning_effort: str = None, search_domains: Any = None,
			store: bool = True, stream: bool = False, parallel_tool_calls: bool = True,
			tool_choice: str = 'auto' ) -> str:
		'''
		
			Purpose:
			--------
			Execute a Responses API request with the built-in web-search tool enabled.

			Args:
			-----------
			prompt (str):
				User prompt.

			model (str):
				OpenAI model identifier.

			temperature (float):
				Sampling temperature.

			max_tokens (int):
				Maximum output tokens.

			top_p (float):
				Nucleus sampling value.

			seed (int | None):
				Optional deterministic seed.

			system (str | None):
				Optional system/developer instructions.

			response_format (str | Dict[str, Any] | None):
				Optional output format.

			reasoning_effort (str | None):
				Optional reasoning effort.

			search_domains (Any):
				Optional preferred source domains.

			store (bool):
				Whether to store the response.

			stream (bool):
				Whether to stream the response.

			parallel_tool_calls (bool):
				Whether parallel tool calls are enabled.

			tool_choice (str):
				Tool-choice behavior.

			Returns:
			--------
			str:
				Web-search-augmented response text.
			
		'''
		try:
			return self.fetch( prompt=prompt, model=model, temperature=temperature,
				max_tokens=max_tokens,
				top_p=top_p,
				seed=seed,
				system=system,
				response_format=response_format,
				reasoning_effort=reasoning_effort,
				web_search=True,
				search_domains=search_domains,
				store=store,
				stream=stream,
				parallel_tool_calls=parallel_tool_calls,
				tool_choice=tool_choice
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'search_web( self, prompt: str, ... ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def search_files( self, prompt: str ) -> str:
		'''
		
			Purpose:
			--------
			Run a file-search tool call against configured vector stores using the
			Responses API.

			Args:
			-----------
			prompt (str):
				User query for file search.

			Returns:
			--------
			str:
				File-search-grounded response text.
			
		'''
		try:
			throw_if( 'prompt', prompt )
			self.query = prompt
			self.tools = self.build_tools(
				web_search=False,
				file_search=True,
				vector_store_ids=self.vector_store_ids,
				max_file_results=20
			)
			self.request = {
					'model': self.model,
					'tools': self.tools,
					'input': prompt
			}
			self.response = self.client.responses.create( **self.request )
			return self.extract_output_text( self.response )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'search_files( self, prompt: str ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def translate( self, text: str ) -> str:
		'''
		
			Purpose:
			--------
			Translate text using the currently selected OpenAI text model.

			Args:
			-----------
			text (str):
				Source text to translate.

			Returns:
			--------
			str:
				Translated text.
			
		'''
		try:
			throw_if( 'text', text )
			return self.fetch(
				prompt=f'Translate the following text faithfully and preserve meaning:\n\n{text}',
				model=self.model,
				temperature=0.2,
				max_tokens=self.max_completion_tokens,
				top_p=self.top_percent,
				system=self.system_instructions
			)
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'translate( self, text: str ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def transcribe( self, text: str ) -> str:
		'''
		
			Purpose:
			--------
			Compatibility passthrough until audio transcription is split into its own
			provider path.

			Args:
			-----------
			text (str):
				Text value to pass through.

			Returns:
			--------
			str:
				The original text value.
			
		'''
		try:
			throw_if( 'text', text )
			return text
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'transcribe( self, text: str ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def get_format_options( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return supported formatting options for UI selectors.

			Args:
			-----------
			None

			Returns:
			--------
			List[str]:
				Available response-format labels.
			
		'''
		return [ 'auto', 'text', 'json', 'json_schema' ]
	
	def get_model_options( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return available OpenAI model options from configuration or fallback
			defaults.

			Args:
			-----------
			None

			Returns:
			--------
			List[str]:
				Available model identifiers.
			
		'''
		if hasattr( cfg, 'GPT_MODELS' ) and cfg.GPT_MODELS:
			return list( cfg.GPT_MODELS )
		
		return [
				'gpt-5.4',
				'gpt-5',
				'gpt-5-mini',
				'gpt-5-nano',
				'gpt-5.1',
				'gpt-5.2',
				'gpt-4.1'
		]
	
	def get_effort_options( self ) -> List[ str ]:
		'''
		
			Purpose:
			--------
			Return available reasoning-effort options.

			Args:
			-----------
			None

			Returns:
			--------
			List[str]:
				Available reasoning-effort labels.
			
		'''
		return [ 'minimal', 'low', 'medium', 'high' ]
	
	def get_data( self ) -> Dict[ str, Any ]:
		'''
		
			Purpose:
			--------
			Return the current Chat generator state as a dictionary.

			Args:
			-----------
			None

			Returns:
			--------
			Dict[str, Any]:
				Serializable state dictionary.
			
		'''
		return {
				'num': self.number,
				'model': self.model,
				'temperature': self.temperature,
				'top_percent': self.top_percent,
				'frequency_penalty': self.frequency_penalty,
				'presence_penalty': self.presence_penalty,
				'max_completion_tokens': self.max_completion_tokens,
				'store': self.store,
				'stream': self.stream,
				'response_format': self.response_format,
				'reasoning_effort': self.reasoning_effort,
				'web_search': self.web_search,
				'search_domains': self.search_domains,
				'parallel_tool_calls': self.parallel_tool_calls,
				'tool_choice': self.tool_choice,
				'vector_store_ids': self.vector_store_ids,
				'request': self.request
		}
	
	def dump( self ) -> str:
		'''
		
			Purpose:
			--------
			Return a string representation of the current Chat generator state.

			Args:
			-----------
			None

			Returns:
			--------
			str:
				String representation of get_data().
			
		'''
		try:
			return str( self.get_data( ) )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'generators'
			exception.cause = 'Chat'
			exception.method = 'dump( self ) -> str'
			Logger( ).write( exception )
			raise exception


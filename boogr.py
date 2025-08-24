'''
  ******************************************************************************************
      Assembly:                Mathy
      Filename:                booger.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="booger.py" company="Terry D. Eppler">

	     Mathy Booger

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
    booger.py
  </summary>
  ******************************************************************************************
  '''
from __future__ import annotations
import traceback
from sys import exc_info
from typing import List, Optional, Tuple
import FreeSimpleGUI as sg

class Dark( ):
	'''

        Constructor:
		-----------
        Dark( )

        Pupose:
		-------
		Class representing the theme

    '''
	theme_background: Optional[ str ]
	theme_textcolor: Optional[ str ]
	element_forecolor: Optional[ str ]
	text_backcolor: Optional[ str ]
	text_forecolor: Optional[ str ]
	input_forecolor: Optional[ str ]
	input_backcolor: Optional[ str ]
	button_backcolor: Optional[ str ]
	button_forecolor: Optional[ str ]
	button_color: Optional[ Tuple[ str, str ] ]
	icon_path: Optional[ str ]
	theme_font: Optional[ Tuple[ str, int ] ]
	scrollbar_color: Optional[ str ]
	form_size: Optional[ Tuple[ int, int ] ]

	def __init__( self ):
		sg.theme( 'DarkGrey15' )
		sg.theme_input_text_color( '#FFFFFF' )
		sg.theme_element_text_color( '#69B1EF' )
		sg.theme_text_color( '#69B1EF' )
		self.theme_background = sg.theme_background_color( )
		self.theme_textcolor = sg.theme_text_color( )
		self.element_forecolor = sg.theme_element_text_color( )
		self.element_backcolor = sg.theme_background_color( )
		self.text_backcolor = sg.theme_text_element_background_color( )
		self.text_forecolor = sg.theme_element_text_color( )
		self.input_forecolor = sg.theme_input_text_color( )
		self.input_backcolor = sg.theme_input_background_color( )
		self.button_backcolor = sg.theme_button_color_background( )
		self.button_forecolor = sg.theme_button_color_text( )
		self.button_color = sg.theme_button_color( )
		self.icon_path = r'/\resources\ico\ninja.ico'
		self.theme_font = ('Roboto', 11)
		self.scrollbar_color = '#755600'
		self.form_size = (400, 200)
		sg.set_global_icon( icon = self.icon_path )
		sg.set_options( font = self.theme_font )
		sg.user_settings_save( 'Boo', r'/\resources\theme' )

	def __dir__( self ) -> List[ str ] | None:
		'''

		    Purpose:
		    --------
		    Creates a List[ str ] of type members

		    Parameters:
		    ----------
			self

		    Returns:
		    ---------
			List[ str ] | None

		'''
		return [ 'form_size', 'theme_background',
		         'theme_textcolor', 'element_backcolor', 'element_forecolor',
		         'text_forecolor', 'text_backcolor', 'input_backcolor',
		         'input_forecolor', 'button_color', 'button_backcolor',
		         'button_forecolor', 'icon_path', 'theme_font',
		         'scrollbar_color' ]

class Error( Exception ):
	'''

        Purpose:
        ---------
		Class wrapping error used as the path argument for ErrorDialog class

        Constructor:
		----------
        Error( error: Exception, heading: str=None, cause: str=None,
                method: str=None, module: str=None )

    '''
	error: Optional[ Exception ]
	heading: Optional[ str ]
	module: Optional[ str ]
	info: Optional[ str ]
	cause: Optional[ str ]
	method: Optional[ str ]

	def __init__( self, error: Exception, heading: str = None, cause: str = None,
	              method: str = None, module: str = None ):
		super( ).__init__( )
		self.exception = error
		self.heading = heading
		self.cause = cause
		self.method = method
		self.module = module
		self.type = exc_info( )[ 0 ]
		self.trace = traceback.format_exc( )
		self.info = str( exc_info( )[ 0 ] ) + ': \r\n \r\n' + traceback.format_exc( )

	def __str__( self ) -> str | None:
		'''

            Purpose:
            --------
			returns a string reprentation of the object

            Parameters:
            ----------
			self

            Returns:
            ---------
			str | None

		'''
		if self.info is not None:
			return self.info

	def __dir__( self ) -> List[ str ] | None:
		'''

		    Purpose:
		    --------
		    Creates a List[ str ] of type members

		    Parameters:
		    ----------
			self

		    Returns:
		    ---------
			List[ str ] | None

		'''
		return [ 'message', 'cause', 'method', 'module', 'scaler', 'stack_trace', 'info' ]

class ErrorDialog( Dark ):
	'''

	    Construcotr:  ErrorDialog( error )

	    Purpose:  Class that displays excetption target_names that accepts
            a single, optional argument 'error' of scaler Error

    '''
	error: Optional[ Exception ]
	heading: Optional[ str ]
	module: Optional[ str ]
	info: Optional[ str ]
	cause: Optional[ str ]
	method: Optional[ str ]

	def __init__( self, error: Error ):
		super( ).__init__( )
		sg.theme( 'DarkGrey15' )
		sg.theme_input_text_color( '#FFFFFF' )
		sg.theme_element_text_color( '#69B1EF' )
		sg.theme_text_color( '#69B1EF' )
		self.theme_background = sg.theme_background_color( )
		self.theme_textcolor = sg.theme_text_color( )
		self.element_forecolor = sg.theme_element_text_color( )
		self.element_backcolor = sg.theme_background_color( )
		self.text_backcolor = sg.theme_text_element_background_color( )
		self.text_forecolor = sg.theme_element_text_color( )
		self.input_forecolor = sg.theme_input_text_color( )
		self.input_backcolor = sg.theme_input_background_color( )
		self.button_backcolor = sg.theme_button_color_background( )
		self.button_forecolor = sg.theme_button_color_text( )
		self.button_color = sg.theme_button_color( )
		self.icon_path = r'\resources\ico\ninja.ico'
		self.theme_font = ('Roboto', 11)
		self.scrollbar_color = '#755600'
		sg.set_global_icon( icon = self.icon_path )
		sg.set_options( font = self.theme_font )
		sg.user_settings_save( 'Mathy', r'\resources\theme' )
		self.form_size = (500, 300)
		self.error = error
		self.heading = error.heading
		self.module = error.module
		self.info = error.trace
		self.cause = error.cause
		self.method = error.method

	def __str__( self ) -> str | None:
		'''

            Purpose:
            --------
			returns a string reprentation of the object

            Parameters:
            ----------
			self

            Returns:
            ---------
			str | None

		'''
		return self.info

	def __dir__( self ) -> List[ str ] | None:
		'''

		    Purpose:
		    --------
		    Creates a List[ str ] of type members

		    Parameters:
		    ----------
			self

		    Returns:
		    ---------
			List[ str ] | None

		'''
		return [ 'size', 'settings_path', 'theme_background',
		         'theme_textcolor', 'element_backcolor', 'element_forecolor',
		         'text_forecolor', 'text_backcolor', 'input_backcolor',
		         'input_forecolor', 'button_color', 'button_backcolor',
		         'button_forecolor', 'icon_path', 'theme_font',
		         'scrollbar_color', 'progressbar_color',
		         'info', 'cause', 'method', 'error', 'heading',
		         'module', 'scaler', 'message' 'show' ]

	def show( self ) -> object:
		'''

            Purpose:
            --------


            Parameters:
            ----------


            Returns:
            ---------


		'''
		_msg = self.heading if isinstance( self.heading, str ) else None
		_info = f'Module:\t{self.module}\r\nClass:\t{self.cause}\r\n' \
		        f'Method:\t{self.method}\r\n \r\n{self.info}'
		_red = '#F70202'
		_font = ('Roboto', 10)
		_padsz = (3, 3)
		_layout = [ [ sg.Text( ) ],
		            [ sg.Text( f'{_msg}', size = (100, 1), key = '-MSG-', text_color = _red,
			            font = _font ) ],
		            [ sg.Text( size = (150, 1) ) ],
		            [ sg.Multiline( f'{_info}', key = '-INFO-', size = (80, 7), pad = _padsz ) ],
		            [ sg.Text( ) ],
		            [ sg.Text( size = (20, 1) ), sg.Cancel( size = (15, 1), key = '-CANCEL-' ),
		              sg.Text( size = (10, 1) ), sg.Ok( size = (15, 1), key = '-OK-' ) ] ]

		_window = sg.Window( r' Mathy', _layout,
			icon = self.icon_path,
			font = self.theme_font,
			size = self.form_size,
			keep_on_top = True )

		while True:
			_event, _values = _window.read( )
			if _event in (sg.WIN_CLOSED, sg.WIN_X_EVENT, 'Canel', '-OK-'):
				break

		_window.close( )


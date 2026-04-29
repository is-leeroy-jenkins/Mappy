'''
  ******************************************************************************************
      Assembly:                Mappy
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


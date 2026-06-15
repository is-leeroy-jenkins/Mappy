/*
  ******************************************************************************************
      Assembly:                Mappy Documentation
      Filename:                extra.js
      Author:                  Terry D. Eppler
      Created:                 06-14-2026

      Purpose:
        Provides small progressive enhancements for the Mappy Material for MkDocs site.
        The script labels external links, makes generated tables easier to scroll on
        narrow screens, and adds copy-friendly anchors to API headings without changing
        page content, routing, navigation, or mkdocstrings behavior.

      Usage:
        Add this file to docs/assets/js/extra.js and reference it from mkdocs.yml:

            extra_javascript:
              - assets/js/extra.js
  ******************************************************************************************
*/
( function()
{
	'use strict';
	
	/**
	 * Determine whether a link points outside the current site.
	 *
	 * Purpose:
	 *   Normalizes an anchor href against the current page and returns true when the
	 *   destination uses an HTTP(S) origin different from the current documentation
	 *   origin.
	 *
	 * @param {HTMLAnchorElement} anchor - Anchor element to inspect.
	 * @returns {boolean} True when the anchor points to an external HTTP(S) origin.
	 */
	function isExternalLink( anchor )
	{
		if( !anchor || !anchor.href )
		{
			return false;
		}
		try
		{
			var url = new URL( anchor.href, window.location.href );
			return /^https?:$/.test( url.protocol ) && url.origin !== window.location.origin;
		}
		catch( error )
		{
			return false;
		}
	}
	
	/**
	 * Mark external links with safe browser behavior.
	 *
	 * Purpose:
	 *   Adds target and rel attributes to external links so documentation readers can
	 *   open outside references without losing their current documentation page.
	 *
	 * @returns {void}
	 */
	function enhanceExternalLinks()
	{
		document.querySelectorAll( 'a[href]' ).forEach( function( anchor )
		{
			if( !isExternalLink( anchor ) )
			{
				return;
			}
			anchor.setAttribute( 'target', '_blank' );
			anchor.setAttribute( 'rel', 'noopener noreferrer' );
			anchor.classList.add( 'mappy-external-link' );
		} );
	}
	
	/**
	 * Wrap plain markdown tables for horizontal scrolling.
	 *
	 * Purpose:
	 *   Ensures wide API and reference tables remain usable on smaller screens while
	 *   avoiding duplicate wrappers if Material for MkDocs already handled the table.
	 *
	 * @returns {void}
	 */
	function wrapTables()
	{
		document.querySelectorAll( '.md-typeset table:not([class])' ).forEach( function( table )
		{
			if( table.parentElement &&
					table.parentElement.classList.contains( 'mappy-table-wrap' ) )
			{
				return;
			}
			var wrapper = document.createElement( 'div' );
			wrapper.className = 'mappy-table-wrap';
			wrapper.style.overflowX = 'auto';
			wrapper.style.margin = '1em 0';
			table.parentNode.insertBefore( wrapper, table );
			wrapper.appendChild( table );
		} );
	}
	
	/**
	 * Add copyable fragment links to documentation headings.
	 *
	 * Purpose:
	 *   Adds a lightweight visual affordance to generated headings that already have
	 *   an id. The function does not create ids or rewrite existing Material anchors.
	 *
	 * @returns {void}
	 */
	function enhanceHeadingAnchors()
	{
		document.querySelectorAll( '.md-typeset h2[id], .md-typeset h3[id], .md-typeset h4[id]' )
				.forEach( function( heading )
				{
					if( heading.querySelector( '.mappy-heading-anchor' ) )
					{
						return;
					}
					var anchor = document.createElement( 'a' );
					anchor.className = 'mappy-heading-anchor';
					anchor.href = '#' + heading.id;
					anchor.setAttribute( 'aria-label', 'Link to this section' );
					anchor.textContent = ' #';
					anchor.style.textDecoration = 'none';
					anchor.style.opacity = '0.55';
					heading.appendChild( anchor );
				} );
	}
	
	/**
	 * Run all documentation enhancements.
	 *
	 * Purpose:
	 *   Applies safe, idempotent enhancements after the initial page load and after
	 *   Material for MkDocs instant-navigation updates.
	 *
	 * @returns {void}
	 */
	function applyMappyEnhancements()
	{
		enhanceExternalLinks();
		wrapTables();
		enhanceHeadingAnchors();
	}
	
	if( document.readyState === 'loading' )
	{
		document.addEventListener( 'DOMContentLoaded', applyMappyEnhancements );
	}
	else
	{
		applyMappyEnhancements();
	}
	if( typeof document$ !== 'undefined' && document$.subscribe )
	{
		document$.subscribe( applyMappyEnhancements );
	}
}() );
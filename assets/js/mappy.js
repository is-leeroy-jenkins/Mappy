/*
 * ======================================================================================
 * Mappy Documentation JavaScript
 * ======================================================================================
 * Purpose:
 *     Adds high-value usability enhancements to the Mappy MkDocs site without requiring
 *     external JavaScript dependencies. The script is defensive by design: every feature
 *     checks for required DOM elements before execution so the same file can be loaded on
 *     all documentation pages, including API reference pages, user-guide pages, and landing
 *     pages.
 *
 * Features:
 *     - Back-to-top button.
 *     - Active heading tracking.
 *     - External link hardening.
 *     - Code block language badges.
 *     - Copy import path buttons for API headings.
 *     - API object filter.
 *     - Expand/collapse controls for API details blocks.
 *     - Responsive table wrappers.
 *     - Image zoom/lightbox support.
 *     - Anchor-link copy helper.
 *     - Keyboard-accessible behavior.
 *
 * Notes:
 *     This file is intended for Material for MkDocs and mkdocstrings-generated API pages.
 *     It does not change source content, route navigation, or MkDocs build behavior.
 * ======================================================================================
 */
( function()
{
	'use strict';
	const MAPPY = {
		backToTopId: 'mappy-back-to-top',
		apiToolsId: 'mappy-api-tools',
		apiFilterId: 'mappy-api-filter',
		imageOverlayId: 'mappy-image-overlay',
		activeHeadingClass: 'mappy-heading-active',
		tableWrapperClass: 'mappy-table-wrapper',
		codeBlockClass: 'mappy-code-block',
		codeBadgeClass: 'mappy-code-badge',
		apiHiddenClass: 'mappy-api-object-hidden',
		backToTopVisibleClass: 'mappy-back-to-top--visible',
		copyButtonClass: 'mappy-copy-import',
		apiButtonClass: 'mappy-api-button',
		lightboxImageClass: 'mappy-lightbox-image',
		anchorCopyClass: 'mappy-anchor-copy',
		storageKey: 'mappy-api-filter'
	};
	
	function ready( callback )
	{
		if( document.readyState === 'loading' )
		{
			document.addEventListener( 'DOMContentLoaded', callback );
			return;
		}
		callback();
	}
	
	function getMainContent()
	{
		return document.querySelector( '.md-content__inner' ) ||
				document.querySelector( '.md-main__inner' ) ||
				document.body;
	}
	
	function getTypesetRoot()
	{
		return document.querySelector( '.md-typeset' ) || getMainContent();
	}
	
	function normalizeText( value )
	{
		return String( value || '' )
				.replace( /\s+/g, ' ' )
				.trim()
				.toLowerCase();
	}
	
	function debounce( callback, wait )
	{
		let timeoutId = null;
		return function debouncedCallback()
		{
			const args = arguments;
			const context = this;
			window.clearTimeout( timeoutId );
			timeoutId = window.setTimeout( function()
			{
				callback.apply( context, args );
			}, wait );
		};
	}
	
	function createElement( tagName, className, text )
	{
		const element = document.createElement( tagName );
		if( className )
		{
			element.className = className;
		}
		if( typeof text === 'string' )
		{
			element.textContent = text;
		}
		return element;
	}
	
	function safeClipboardWrite( text, successCallback )
	{
		const value = String( text || '' ).trim();
		if( !value )
		{
			return;
		}
		if( navigator.clipboard && navigator.clipboard.writeText )
		{
			navigator.clipboard.writeText( value )
					.then( function()
					{
						if( typeof successCallback === 'function' )
						{
							successCallback();
						}
					} )
					.catch( function()
					{
						fallbackClipboardWrite( value, successCallback );
					} );
			return;
		}
		fallbackClipboardWrite( value, successCallback );
	}
	
	function fallbackClipboardWrite( text, successCallback )
	{
		const textarea = document.createElement( 'textarea' );
		textarea.value = text;
		textarea.setAttribute( 'readonly', 'readonly' );
		textarea.style.position = 'fixed';
		textarea.style.left = '-9999px';
		textarea.style.top = '-9999px';
		document.body.appendChild( textarea );
		textarea.select();
		try
		{
			document.execCommand( 'copy' );
			if( typeof successCallback === 'function' )
			{
				successCallback();
			}
		}
		catch( error )
		{
			console.warn( 'Mappy documentation: clipboard copy failed.', error );
		}
		finally
		{
			document.body.removeChild( textarea );
		}
	}
	
	function temporaryButtonText( button, message )
	{
		const originalText = button.textContent;
		button.textContent = message;
		window.setTimeout( function()
		{
			button.textContent = originalText;
		}, 1500 );
	}
	
	function initBackToTop()
	{
		if( document.getElementById( MAPPY.backToTopId ) )
		{
			return;
		}
		const button = createElement( 'button', 'mappy-back-to-top', '↑ Top' );
		button.id = MAPPY.backToTopId;
		button.type = 'button';
		button.setAttribute( 'aria-label', 'Back to top' );
		button.addEventListener( 'click', function()
		{
			window.scrollTo( {
				top: 0,
				behavior: 'smooth'
			} );
		} );
		document.body.appendChild( button );
		
		function updateVisibility()
		{
			if( window.scrollY > 500 )
			{
				button.classList.add( MAPPY.backToTopVisibleClass );
				return;
			}
			button.classList.remove( MAPPY.backToTopVisibleClass );
		}
		
		window.addEventListener( 'scroll', updateVisibility, { passive: true } );
		updateVisibility();
	}
	
	function initExternalLinks()
	{
		const links = document.querySelectorAll( '.md-typeset a[href]' );
		links.forEach( function( link )
		{
			const href = link.getAttribute( 'href' ) || '';
			if( !href || href.startsWith( '#' ) || href.startsWith( '/' ) ||
					href.startsWith( 'mailto:' ) )
			{
				return;
			}
			if( href.startsWith( 'http://' ) || href.startsWith( 'https://' ) )
			{
				link.setAttribute( 'target', '_blank' );
				link.setAttribute( 'rel', 'noopener noreferrer' );
				if( !link.getAttribute( 'aria-label' ) )
				{
					link.setAttribute( 'aria-label',
							`${ link.textContent.trim() } opens in a new tab` );
				}
			}
		} );
	}
	
	function initResponsiveTables()
	{
		const root = getTypesetRoot();
		const tables = root.querySelectorAll( 'table:not([data-mappy-wrapped])' );
		tables.forEach( function( table )
		{
			if( table.closest( `.${ MAPPY.tableWrapperClass }` ) )
			{
				table.setAttribute( 'data-mappy-wrapped', 'true' );
				return;
			}
			const wrapper = createElement( 'div', MAPPY.tableWrapperClass );
			table.parentNode.insertBefore( wrapper, table );
			wrapper.appendChild( table );
			table.setAttribute( 'data-mappy-wrapped', 'true' );
		} );
	}
	
	function inferLanguageFromCodeBlock( block )
	{
		const code = block.querySelector( 'code' );
		if( !code )
		{
			return '';
		}
		const classes = Array.from( code.classList || [] );
		const languageClass = classes.find( function( name )
		{
			return name.indexOf( 'language-' ) === 0;
		} );
		if( !languageClass )
		{
			return '';
		}
		return languageClass.replace( 'language-', '' ).trim();
	}
	
	function initCodeBadges()
	{
		const root = getTypesetRoot();
		const blocks = root.querySelectorAll( 'pre:not([data-mappy-code-badge])' );
		blocks.forEach( function( block )
		{
			const language = inferLanguageFromCodeBlock( block );
			block.classList.add( MAPPY.codeBlockClass );
			block.setAttribute( 'data-mappy-code-badge', 'true' );
			if( !language )
			{
				return;
			}
			const badge = createElement( 'span', MAPPY.codeBadgeClass, language );
			block.appendChild( badge );
		} );
	}
	
	function getHeadingImportPath( heading )
	{
		const text = heading.textContent || '';
		const code = heading.querySelector( 'code' );
		if( code && code.textContent.trim() )
		{
			return code.textContent.trim();
		}
		const match = text.match( /([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)/ );
		if( match && match[ 1 ] )
		{
			return match[ 1 ].trim();
		}
		return '';
	}
	
	function initCopyImportButtons()
	{
		const root = getTypesetRoot();
		const headings = root.querySelectorAll(
				'.doc-heading:not([data-mappy-copy]), .doc-object h2:not([data-mappy-copy]), .doc-object h3:not([data-mappy-copy])'
		);
		headings.forEach( function( heading )
		{
			const importPath = getHeadingImportPath( heading );
			heading.setAttribute( 'data-mappy-copy', 'true' );
			if( !importPath )
			{
				return;
			}
			const button = createElement( 'button', MAPPY.copyButtonClass, 'Copy' );
			button.type = 'button';
			button.setAttribute( 'aria-label', `Copy ${ importPath }` );
			button.addEventListener( 'click', function( event )
			{
				event.preventDefault();
				event.stopPropagation();
				safeClipboardWrite( importPath, function()
				{
					temporaryButtonText( button, 'Copied' );
				} );
			} );
			heading.appendChild( button );
		} );
	}
	
	function getApiObjects()
	{
		const root = getTypesetRoot();
		return Array.from( root.querySelectorAll( '.doc-object' ) ).filter( function( object )
		{
			return !object.classList.contains( 'doc-module' );
		} );
	}
	
	function createApiTools()
	{
		if( document.getElementById( MAPPY.apiToolsId ) )
		{
			return document.getElementById( MAPPY.apiToolsId );
		}
		const apiObjects = getApiObjects();
		if( apiObjects.length < 4 )
		{
			return null;
		}
		const root = getTypesetRoot();
		const firstApiObject = apiObjects[ 0 ];
		const wrapper = createElement( 'section', 'mappy-api-tools' );
		const label = createElement( 'label', 'mappy-api-filter-label', 'Filter API members' );
		const input = createElement( 'input', 'mappy-api-filter' );
		const buttonRow = createElement( 'div', 'mappy-api-actions' );
		const expandButton = createElement( 'button', MAPPY.apiButtonClass, 'Expand all' );
		const collapseButton = createElement( 'button', MAPPY.apiButtonClass, 'Collapse all' );
		const clearButton = createElement( 'button', MAPPY.apiButtonClass, 'Clear filter' );
		wrapper.id = MAPPY.apiToolsId;
		input.id = MAPPY.apiFilterId;
		input.type = 'search';
		input.placeholder = 'Filter classes, functions, methods, and attributes...';
		input.setAttribute( 'aria-label', 'Filter API members' );
		expandButton.type = 'button';
		collapseButton.type = 'button';
		clearButton.type = 'button';
		buttonRow.appendChild( expandButton );
		buttonRow.appendChild( collapseButton );
		buttonRow.appendChild( clearButton );
		wrapper.appendChild( label );
		wrapper.appendChild( input );
		wrapper.appendChild( buttonRow );
		root.insertBefore( wrapper, firstApiObject );
		expandButton.addEventListener( 'click', function()
		{
			setAllDetailsOpen( true );
		} );
		collapseButton.addEventListener( 'click', function()
		{
			setAllDetailsOpen( false );
		} );
		clearButton.addEventListener( 'click', function()
		{
			input.value = '';
			window.sessionStorage.removeItem( MAPPY.storageKey );
			filterApiObjects( '' );
			input.focus();
		} );
		const storedFilter = window.sessionStorage.getItem( MAPPY.storageKey );
		if( storedFilter )
		{
			input.value = storedFilter;
			filterApiObjects( storedFilter );
		}
		input.addEventListener( 'input', debounce( function()
		{
			window.sessionStorage.setItem( MAPPY.storageKey, input.value );
			filterApiObjects( input.value );
		}, 120 ) );
		return wrapper;
	}
	
	function setAllDetailsOpen( isOpen )
	{
		const root = getTypesetRoot();
		const details = root.querySelectorAll( 'details' );
		details.forEach( function( item )
		{
			item.open = isOpen;
		} );
	}
	
	function filterApiObjects( query )
	{
		const value = normalizeText( query );
		const apiObjects = getApiObjects();
		apiObjects.forEach( function( object )
		{
			if( !value )
			{
				object.classList.remove( MAPPY.apiHiddenClass );
				return;
			}
			const text = normalizeText( object.textContent );
			if( text.indexOf( value ) >= 0 )
			{
				object.classList.remove( MAPPY.apiHiddenClass );
				return;
			}
			object.classList.add( MAPPY.apiHiddenClass );
		} );
	}
	
	function initApiTools()
	{
		createApiTools();
		initCopyImportButtons();
	}
	
	function initAnchorCopyButtons()
	{
		const root = getTypesetRoot();
		const headings = root.querySelectorAll( 'h1[id], h2[id], h3[id], h4[id]' );
		headings.forEach( function( heading )
		{
			if( heading.getAttribute( 'data-mappy-anchor-copy' ) === 'true' )
			{
				return;
			}
			heading.setAttribute( 'data-mappy-anchor-copy', 'true' );
			const button = createElement( 'button', MAPPY.anchorCopyClass, '#' );
			button.type = 'button';
			button.setAttribute( 'aria-label', `Copy link to ${ heading.textContent.trim() }` );
			button.addEventListener( 'click', function( event )
			{
				event.preventDefault();
				event.stopPropagation();
				const url = `${ window.location.origin }${ window.location.pathname }#${ heading.id }`;
				safeClipboardWrite( url, function()
				{
					temporaryButtonText( button, '✓' );
				} );
			} );
			heading.appendChild( button );
		} );
	}
	
	function initActiveHeadingTracking()
	{
		const root = getTypesetRoot();
		const headings = Array.from( root.querySelectorAll( 'h2[id], h3[id]' ) );
		if( !headings.length || !( 'IntersectionObserver' in window ) )
		{
			return;
		}
		let activeHeading = null;
		const observer = new IntersectionObserver( function( entries )
		{
			const visible = entries
					.filter( function( entry )
					{
						return entry.isIntersecting;
					} )
					.sort( function( a, b )
					{
						return a.boundingClientRect.top - b.boundingClientRect.top;
					} );
			if( !visible.length )
			{
				return;
			}
			if( activeHeading )
			{
				activeHeading.classList.remove( MAPPY.activeHeadingClass );
			}
			activeHeading = visible[ 0 ].target;
			activeHeading.classList.add( MAPPY.activeHeadingClass );
		}, {
			rootMargin: '-15% 0px -70% 0px',
			threshold: 0.1
		} );
		headings.forEach( function( heading )
		{
			observer.observe( heading );
		} );
	}
	
	function createImageOverlay()
	{
		let overlay = document.getElementById( MAPPY.imageOverlayId );
		if( overlay )
		{
			return overlay;
		}
		overlay = createElement( 'div', 'mappy-image-overlay' );
		overlay.id = MAPPY.imageOverlayId;
		overlay.setAttribute( 'role', 'dialog' );
		overlay.setAttribute( 'aria-modal', 'true' );
		overlay.setAttribute( 'aria-label', 'Image preview' );
		overlay.tabIndex = -1;
		const closeButton = createElement( 'button', 'mappy-image-overlay-close', '×' );
		const image = document.createElement( 'img' );
		closeButton.type = 'button';
		closeButton.setAttribute( 'aria-label', 'Close image preview' );
		image.className = MAPPY.lightboxImageClass;
		image.alt = '';
		overlay.appendChild( closeButton );
		overlay.appendChild( image );
		
		function closeOverlay()
		{
			overlay.classList.remove( 'mappy-image-overlay--visible' );
			image.removeAttribute( 'src' );
		}
		
		closeButton.addEventListener( 'click', closeOverlay );
		overlay.addEventListener( 'click', function( event )
		{
			if( event.target === overlay )
			{
				closeOverlay();
			}
		} );
		document.addEventListener( 'keydown', function( event )
		{
			if( event.key === 'Escape' )
			{
				closeOverlay();
			}
		} );
		document.body.appendChild( overlay );
		return overlay;
	}
	
	function initImageLightbox()
	{
		const root = getTypesetRoot();
		const images = root.querySelectorAll( 'img:not([data-mappy-lightbox])' );
		if( !images.length )
		{
			return;
		}
		const overlay = createImageOverlay();
		const overlayImage = overlay.querySelector( `.${ MAPPY.lightboxImageClass }` );
		images.forEach( function( image )
		{
			if( !image.src || image.closest( 'a' ) )
			{
				image.setAttribute( 'data-mappy-lightbox', 'true' );
				return;
			}
			image.setAttribute( 'data-mappy-lightbox', 'true' );
			image.classList.add( 'mappy-clickable-image' );
			image.tabIndex = 0;
			image.setAttribute( 'role', 'button' );
			image.setAttribute( 'aria-label', image.alt
			                                  ? `Preview image: ${ image.alt }`
			                                  : 'Preview image' );
			
			function openOverlay()
			{
				overlayImage.src = image.src;
				overlayImage.alt = image.alt || '';
				overlay.classList.add( 'mappy-image-overlay--visible' );
				overlay.focus();
			}
			
			image.addEventListener( 'click', openOverlay );
			image.addEventListener( 'keydown', function( event )
			{
				if( event.key === 'Enter' || event.key === ' ' )
				{
					event.preventDefault();
					openOverlay();
				}
			} );
		} );
	}
	
	function initSearchKeyboardShortcut()
	{
		document.addEventListener( 'keydown', function( event )
		{
			const target = event.target;
			const isTyping = target &&
					( target.tagName === 'INPUT' ||
							target.tagName === 'TEXTAREA' ||
							target.isContentEditable );
			if( isTyping )
			{
				return;
			}
			if( event.key !== '/' )
			{
				return;
			}
			const searchInput = document.querySelector( '.md-search__input' );
			if( !searchInput )
			{
				return;
			}
			event.preventDefault();
			searchInput.focus();
		} );
	}
	
	function initDetailsPersistence()
	{
		const root = getTypesetRoot();
		const detailsBlocks = root.querySelectorAll( 'details[id]' );
		detailsBlocks.forEach( function( details )
		{
			const key = `mappy-details-${ window.location.pathname }-${ details.id }`;
			const stored = window.sessionStorage.getItem( key );
			if( stored === 'open' )
			{
				details.open = true;
			}
			if( stored === 'closed' )
			{
				details.open = false;
			}
			details.addEventListener( 'toggle', function()
			{
				window.sessionStorage.setItem( key, details.open
				                                    ? 'open'
				                                    : 'closed' );
			} );
		} );
	}
	
	function initPrintHelper()
	{
		const root = getTypesetRoot();
		if( root.getAttribute( 'data-mappy-print-helper' ) === 'true' )
		{
			return;
		}
		root.setAttribute( 'data-mappy-print-helper', 'true' );
		window.addEventListener( 'beforeprint', function()
		{
			const detailsBlocks = root.querySelectorAll( 'details' );
			detailsBlocks.forEach( function( details )
			{
				details.setAttribute( 'data-mappy-print-open', details.open
				                                               ? 'true'
				                                               : 'false' );
				details.open = true;
			} );
		} );
		window.addEventListener( 'afterprint', function()
		{
			const detailsBlocks = root.querySelectorAll( 'details[data-mappy-print-open]' );
			detailsBlocks.forEach( function( details )
			{
				details.open = details.getAttribute( 'data-mappy-print-open' ) === 'true';
				details.removeAttribute( 'data-mappy-print-open' );
			} );
		} );
	}
	
	function initMaterialNavigationCompatibility()
	{
		if( typeof document$ !== 'undefined' && document$.subscribe )
		{
			document$.subscribe( function()
			{
				initializePageEnhancements();
			} );
		}
	}
	
	function initializePageEnhancements()
	{
		initExternalLinks();
		initResponsiveTables();
		initCodeBadges();
		initApiTools();
		initAnchorCopyButtons();
		initActiveHeadingTracking();
		initImageLightbox();
		initDetailsPersistence();
		initPrintHelper();
	}
	
	ready( function()
	{
		initBackToTop();
		initSearchKeyboardShortcut();
		initializePageEnhancements();
		initMaterialNavigationCompatibility();
	} );
} )();
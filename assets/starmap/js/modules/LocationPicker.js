( function()
{
	window.StarMapApp = window.StarMapApp || {};
	
	class LocationPicker
	{
		constructor( containerId, options = {} )
		{
			this.containerId      = containerId;
			this.onLocationChange = options.onLocationChange || ( () =>
			{
			} );
			this.initialLat = Number.isFinite( Number( options.initialLat ) )
			                  ? Number( options.initialLat )
			                  : 20;
			this.initialLon = Number.isFinite( Number( options.initialLon ) )
			                  ? Number( options.initialLon )
			                  : 0;
			this.initialZoom = Number.isFinite( Number( options.initialZoom ) )
			                   ? Number( options.initialZoom )
			                   : 8;
			this.tileUrl = options.tileUrl || 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
			this.tileAttribution = options.tileAttribution || '&copy; OpenStreetMap contributors &copy; CARTO';
			this.tileSubdomains = options.tileSubdomains || 'abcd';
			this.marker = null;
			this.map = L.map( this.containerId ).setView( [ this.initialLat, this.initialLon ], this.initialZoom );
			this.init();
		}
		
		init()
		{
			L.tileLayer( this.tileUrl, {
				attribution: this.tileAttribution,
				subdomains: this.tileSubdomains,
				maxZoom: 20
			} ).addTo( this.map );
			L.Control.geocoder( { defaultMarkGeocode: false } ).on( 'markgeocode', ( e ) =>
			{
				const {
					      lat,
					      lng
				      } = e.geocode.center;
				this.setView( lat, lng, 8, true );
			} ).addTo( this.map );
			this.map.on( 'click', ( e ) =>
			{
				const {
					      lat,
					      lng
				      } = e.latlng;
				this.setView( lat, lng, this.map.getZoom(), true );
			} );
			this.setView( this.initialLat, this.initialLon, this.initialZoom, false );
		}
		
		updateMarker( lat, lng )
		{
			if( this.marker )
			{
				this.map.removeLayer( this.marker );
			}
			this.marker = L.marker( [ lat, lng ] ).addTo( this.map );
		}
		
		setView( lat, lng, zoom = 8, notify = false )
		{
			const latitude  = Number( lat );
			const longitude = Number( lng );
			const zoomLevel = Number.isFinite( Number( zoom ) )
			                  ? Number( zoom )
			                  : 8;
			if( !Number.isFinite( latitude ) || !Number.isFinite( longitude ) )
			{
				return;
			}
			this.map.setView( [ latitude, longitude ], zoomLevel );
			this.updateMarker( latitude, longitude );
			if( notify )
			{
				this.onLocationChange( latitude, longitude );
			}
		}
		
		getCurrentPosition()
		{
			return new Promise( ( resolve, reject ) =>
			{
				if( !navigator.geolocation )
				{
					reject( new Error( 'Geolocation is not supported by your browser.' ) );
				}
				else
				{
					navigator.geolocation.getCurrentPosition( ( position ) =>
						resolve( position.coords ), ( error ) => reject( error ) );
				}
			} );
		}
	}
	
	window.StarMapApp.LocationPicker = LocationPicker;
} )();
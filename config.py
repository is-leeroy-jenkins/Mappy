'''
  ******************************************************************************************
      Assembly:                Name
      Filename:                name.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="guro.py" company="Terry D. Eppler">

	     name.py
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
    name.py
  </summary>
  ******************************************************************************************
  '''
import os
from typing import Optional, List, Dict
from pathlib import Path

# ------------ CONSTANT

BLUE_DIVIDER = "<div style='height:1.5px;align:left;background:#0078FC;margin:20px 0px 30px 0px;'></div>"
APP_TITLE = 'Mappy'
APP_SUBTITLE = 'Geospatial Toolkit'
DB_PATH = 'stores/sqlite/data.db'
DEFAULT_DATA = r'Reports'
BASE_DIR = Path( __file__ ).resolve( ).parent
FAVICON = r'resources/images/favicon.ico'
LOGO = r'resources/images/mappy_logo.png'
MAP_ID = r'16b56ad08af295ded24d8eb2'
MAP_NAME = r'uap-static'
DATASET_ID = r'5adda1cd-f412-4ed5-874d-e97664f229b4'
DATASET_NAME = r'UAP'
STYLE_ID = r'86d00019936c16f936cc936c'
STYLE_NAME = r'uap-dark'

# ----------- API KEYS
CLAUDE_API_KEY = os.getenv( 'CLAUDE_API_KEY' )
GEOCODING_API_KEY = os.getenv( 'GEOCODING_API_KEY' )
GOOGLE_API_KEY = os.getenv( 'GOOGLE_API_KEY' )
GOOGLE_CSE_ID = os.getenv( 'GOOGLE_CSE_ID' )
GOOGLE_CLOUD_LOCATION = os.getenv( 'GOOGLE_CLOUD_LOCATION' )
GOOGLE_CLOUD_PROJECT_ID = os.getenv( 'GOOGLE_CLOUD_PROJECT_ID' )
GOOGLEMAPS_API_KEY = os.getenv( 'GOOGLEMAPS_API_KEY' )
GOOGLE_WEATHER_API_KEY = os.getenv( 'GOOGLE_WEATHER_API_KEY' )
MISTRAL_API_KEY = os.getenv( 'MISTRAL_API_KEY' )
NASA_API_KEY = os.getenv( 'NASA_API_KEY' )
NASA_EARTHDATA_TOKEN = os.getenv( 'NASA_EARTHDATA_TOKEN' )
OPENAI_API_KEY = os.getenv( 'OPENAI_API_KEY' )
AIRNOW_API_KEY = os.getenv( 'AIRNOW_API_KEY' )
OPENAQ_API_KEY = os.getenv( 'OPENAQ_API_KEY' )
WEATHERAPI_API_KEY = os.getenv( 'WEATHERAPI_API_KEY' )
OPENSKY_API_CLIENT_ID = os.getenv( 'OPENSKY_API_CLIENT_ID' )
OPENSKY_API_CREDENTIALS = os.getenv( 'OPENSKY_API_CREDENTIALS' )
GOVINFO_API_KEY = os.getenv( 'GOVINFO_API_KEY' )
FIRMS_MAP_KEY = os.getenv( 'FIRMS_MAP_KEY' )
PURPLEAIR_API_KEY = os.getenv( 'PURPLEAIR_API_KEY' )
XAI_API_KEY = os.getenv( 'XAI_API_KEY' )

# -------------- SETTINGS

MODES = [ 'Geocoding', 'Interactive Map', 'Distances', 'Static Maps', 'Time Zones', 'Web Scraper',
          'Weather', 'Environmental', 'Geological', 'Astronomical', 'Celestial Map', 'Generative',
          'Data Upload', 'Data Management' ]

AGENTS = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
          'AppleWebKit/537.36 (KHTML, like Gecko) '
          'Chrome/147.0.0.0 Safari/537.36')

# --------------- API

AIR_NOW = r'''AirNow is the official U.S. government website and app providing real-time,
		local air quality data and forecasts using the color-coded Air Quality Index (AQI).
		It covers ozone and particle pollution ( and  ) via a partnership of the EPA, NOAA, and
		local agencies, offering a "Fire and Smoke Map" to monitor smoke impacts. https://docs.airnowapi.org/
'''

PURPLE_AIR = r'''PurpleAir provides low-cost, real-time air quality monitoring through public and
		private sensor networks. The API supports sensor lookup, sensor data retrieval, field
		selection, and geographic filtering such as bounding-box requests. API requests require a
		valid PurpleAir API key and commonly use fields such as pm2.5, temperature, humidity,
		pressure, and related sensor metadata. https://api.purpleair.com/
'''

OPEN_AQ = r'''OpenAQ provides open air-quality data through a resource-oriented API. Version 3
		exposes resources such as locations, latest measurements, parameters, providers, sensors,
		licenses, owners, manufacturers, countries, and measurements. Location resources describe
		monitoring stations, geographic coordinates, providers, sensors, and the parameters measured
		at each location. https://docs.openaq.org/
'''

NOAA_CLIMATE_DATA = r'''NOAA climate data is provided primarily through the National Centers for
		Environmental Information (NCEI), serving as the world's largest archive of atmospheric,
		coastal, and geophysical data. It offers free access to historical weather records, 30-year
		Climate Normals, and datasets on temperature, precipitation, and storms. Data is accessible
		via the NCEI Climate Data Online (CDO) portal and https://www.ncdc.noaa.gov/cdo-web/
'''

USGS_NATIONAL_MAP = r'''The USGS National Map is a premier collaborative program providing free,
		accurate, and public domain geospatial data for the United States and its territories.
		It offers topographic maps, 3D elevation data, and 8+ data layers (transportation,
		hydrography, structures) via an online viewer, data downloads, and web services for public,
		academic, and government use. https://tnmaccess.nationalmap.gov/api/v1/docs
'''

USGS_EARTHQUAKES = r'''The USGS Earthquake Hazards Program monitors, reports, and researches global
		seismic activity to reduce losses and save lives. It operates the National Earthquake
		Information Center (NEIC) and Advanced National Seismic System (ANSS) to detect magnitude,
		location, and impacts, providing data for public safety, engineering, and hazard assessments
		https://earthquake.usgs.gov/fdsnws/event/1/
'''

USGS_WATER = r'''The USGS Water Resources Mission Area monitors, assesses, and conducts research on
		the nation's water, providing data on streamflow, groundwater, water quality, and water use.
		https://api.waterdata.usgs.gov/
'''

NOAA_TIDES_CURRENTS = r'''NOAA Tides & Currents, managed by the Center for Operational Oceanographic
		Products and Services (CO-OPS), is the authoritative U.S. source for water level, tidal, and
		oceanographic data. It offers real-time monitoring and predictions for over 3,000 stations,
		crucial for navigation, safety, and coastal resilience. https://tidesandcurrents.noaa.gov/web_services_info.html
'''

STAR_MAP = r'''Provides static and link-based star chart generation using the SKY-MAP.ORG
		XML API, Site Linker, and Image Generator interfaces. https://starmap360.com/blog/starmap-api-for-developers-and-sellers/
'''

NASA_OPEN_SCIENCE = r'''NASA’s Open Science Data Repository (OSDR) enables the reuse of comprehensive,
		multi-modal space life science data—including omics, physiological, phenotypic, behavioral,
		and environmental telemetry—to advance basic and applied research as well as operational
		outcomes for human space exploration.
'''

OPEN_SKY = r'''The OpenSky Network consists of a multitude of sensors connected to the Internet by
		volunteers, industrial supporters, and academic/governmental organizations. All collected
		raw data is archived in a large historical database. The database is primarily used by
		researchers from different areas to analyze and improve air traffic control technologies
		and processes. The main technologies behind the OpenSky Network are the Automatic Dependent
		Surveillance-Broadcast (ADS-B) and Mode S. These technologies provide detailed (live) aircraft
		information over the publicly accessible 1090 MHz radio frequency channel.
'''

EPA_ENVIROFACTS = r'''The EPA Envirofacts Data Warehouse contains information from selected EPA
		environmental program databases and provides REST access to environmental activities that
		may affect air, water, and land in the United States. The Envirofacts API supports table-based
		queries, filter paths, row limits, and output formats such as JSON.
		https://www.epa.gov/enviro/envirofacts-data-service-api
'''

EPA_UV_INDEX = r'''The EPA UV Index web services provide daily and hourly UV Index forecast data.
		The UV Index estimates solar ultraviolet radiation intensity on a 1-11+ scale and supports
		location-based forecast queries for sun-exposure planning.
		https://www.epa.gov/enviro/web-services#uvindex
'''

NASA_EONET = r'''NASA Earth Observatory's Natural Event Tracker (EONET) is a metadata service
		for natural events such as wildfires, severe storms, volcanoes, sea and lake ice, dust and haze,
		and other hazards. Version 3.0 is the current stable API. It supports events, categories,
		sources, and layers. Event requests support filters such as source, category, status, limit,
		days, start, end, magnitude, and bounding box. https://eonet.gsfc.nasa.gov/docs/v3
'''

NASA_FIRMS = r'''NASA's Fire Information for Resource Management System (FIRMS) provides near
		real-time and standard active fire / thermal anomaly detections from sensors such as MODIS
		and VIIRS. The area API returns fire detections by source, bounding area, date, and day range
		and requires a FIRMS MAP_KEY for most data requests. https://firms.modaps.eosdis.nasa.gov/api/
'''

OPEN_WEATHER = r'''Open-Meteo provides weather forecasts using global and mesoscale weather models.
		The API supports latitude/longitude forecast requests, hourly and daily variables, forecast
		ranges, units, and related weather-model options. This Mappy wrapper is named OpenWeather
		but currently targets Open-Meteo, not the OpenWeatherMap API. https://open-meteo.com/en/docs
'''

HISTORICAL_WEATHER = r'''Provides historical weather retrieval by resolving a user-facing location name
		through the Open-Meteo Geocoding API and then querying the Open-Meteo Historical Weather
		API for the selected date or date range. https://open-meteo.com/en/docs/historical-weather-api
'''

ASTRONOMY_CATALOG = r'''The Open Astronomy Catalog (OAC) API is a RESTful interface designed for
		programmatic access to open-access astronomical data, specifically focusing on transient events.
		https://astrocats.space/
		
'''

ASTRO_QUERY = r'''Access to the astropy package that contains key functionality and common tools needed for
		performing astronomy and astrophysics with Python. It is at the core of the Astropy Project,
		which aims to enable the community to develop a robust ecosystem of affiliated packages
		covering a broad range of needs for astronomical research, data processing, and data analysis.
		https://docs.astropy.org/en/stable/
'''

US_NAVAL_OBSERVATORY = r'''Provides access to APIs from the US Naval Observatory's Celestial Navigation Data for
		Assumed Position and Time:  this data service provides all the astronomical information
		necessary to plot navigational lines of position from observations of the altitudes of
		celestial bodies. https://aa.usno.navy.mil/data/api
'''

GOOGLE_CSE = r'''The Cse Service is the endpoint that returns the requested searches.
		You must identify a particular search engine to use in your request
		(using the cx query parameter) as well as the search query (using the q query parameter).
		In addition, you should provide a developer key (using the key query parameter).
'''

GOOGLE_WEATHER = r'''The Google Weather API provides hyperlocal weather data by latitude and longitude.
		Supported products include current conditions, hourly forecasts, daily forecasts, hourly
		history, and weather alerts. Requests require a Google Maps Platform API key with Weather API
		access enabled. https://developers.google.com/maps/documentation/weather/overview
'''

NASA_GLOBAL_IMAGERY = r'''NASA Global Imagery Browse Services (GIBS) provides full-resolution Earth
		science imagery through standard web services including WMS, WMTS, TWMS, and related
		capabilities documents. GIBS imagery is layer, projection, time, format, and bounding-box
		or tile oriented. https://nasa-gibs.github.io/gibs-api-docs/
'''

CDC_WONDER = r'''Wide-ranging ONline Data for Epidemiologic Research -- an easy-to-use, menu-driven
		system that makes the information resources of the Centers for Disease Control and
		Prevention (CDC) available to public health professionals and the public at large. It provides
		access to a wide array of public health information.
'''

SPACE_WEATHER = r'''The Space Weather Database Of Notifications, Knowledge, Information (DONKI) is
		a comprehensive on-line tool for space weather forecasters, scientists, and the general
		space science community. DONKI chronicles the daily interpretations of space weather
		observations, analysis, models, forecasts, and notifications provided by the Space Weather
		Research Center (SWRC), comprehensive knowledge-base search functionality to support anomaly
		resolution and space science research, intelligent linkages, relationships, cause-and-effects
		between space weather activities and comprehensive webservice API access to information
		stored in DONKI. https://ccmc.gsfc.nasa.gov/tools/DONKI/
'''

STAR_CHART = r'''Provides static and link-based star chart generation using the SKY-MAP.ORG
		XML API, Site Linker, and Image Generator interfaces. https://sky-map.org/?locale=EN
'''

SATELLITE_CENTER = r'''The Satellite Situation Center Web (SSCWeb) Service is operated by NASA's
		Space Physics Data Facility (SPDF). It was developed jointly by SPDF and the National Space
		Science Data Center (NSSDC) to support a range of NASA science programs and to fulfill key
		international NASA responsibilities including those of NSSDC and the World Data Center-A
		for Rockets and Satellites. https://sscweb.gsfc.nasa.gov/
'''
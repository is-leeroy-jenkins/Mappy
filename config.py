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
DEFAULT_DATA = r'stores/excel/Reports.xlsx'
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
GEOCODING_API_KEY = os.getenv( 'GEOCODING_API_KEY' )
GOOGLE_API_KEY = os.getenv( 'GOOGLE_API_KEY' )
GOOGLE_CSE_ID = os.getenv( 'GOOGLE_CSE_ID' )
GOOGLE_CLOUD_LOCATION = os.getenv( 'GOOGLE_CLOUD_LOCATION' )
GOOGLE_CLOUD_PROJECT_ID = os.getenv( 'GOOGLE_CLOUD_PROJECT_ID' )
GOOGLEMAPS_API_KEY = os.getenv( 'GOOGLEMAPS_API_KEY' )
GOOGLE_WEATHER_API_KEY = os.getenv( 'GOOGLE_WEATHER_API_KEY' )
NASA_API_KEY = os.getenv( 'NASA_API_KEY' )
NASA_EARTHDATA_TOKEN = os.getenv( 'NASA_EARTHDATA_TOKEN' )
AIRNOW_API_KEY = os.getenv( 'AIRNOW_API_KEY' )
OPENAQ_API_KEY = os.getenv( 'OPENAQ_API_KEY' )
WEATHERAPI_API_KEY = os.getenv( 'WEATHERAPI_API_KEY' )
OPENSKY_API_CLIENT_ID = os.getenv( 'OPENSKY_API_CLIENT_ID' )
OPENSKY_API_CREDENTIALS = os.getenv( 'OPENSKY_API_CREDENTIALS' )
GOVINFO_API_KEY = os.getenv( 'GOVINFO_API_KEY' )
FIRMS_MAP_KEY = os.getenv( 'FIRMS_MAP_KEY' )
PURPLEAIR_API_KEY = os.getenv( 'PURPLEAIR_API_KEY' )

# -------------- SETTINGS

MODES = [ 'Geocoding', 'Map', 'Weather', 'Environmental', 'Geological', 'Astronomical',
          'Distances', 'Static Maps', 'Time Zones', 'Data Upload', 'Data Management' ]

AGENTS = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
          'AppleWebKit/537.36 (KHTML, like Gecko) '
          'Chrome/147.0.0.0 Safari/537.36')

# --------------- API
AIR_NOW = r'''AirNow is the official U.S. government website and app providing real-time,
		local air quality data and forecasts using the color-coded Air Quality Index (AQI).
		It covers ozone and particle pollution ( and  ) via a partnership of the EPA, NOAA, and
		local agencies, offering a "Fire and Smoke Map" to monitor smoke impacts
'''

PURPLE_AIR = r'''PurpleAir provides low-cost, real-time air quality monitors and a public,
		crowdsourced map to measure, visualize, and share hyper-local,, particulate matter data.
		Using laser counters, these sensors empower communities to track pollution, particularly
		during wildfire events. Data is accessible via the PurpleAir Map and is used by researchers,
		public agencies, and individuals worldwide.
'''

OPEN_AQ = r'''OpenAQ is a non-profit organization that aggregates, harmonizes, and shares open-source,
		global air quality data to fight "air inequality". It provides real-time and historical
		data—primarily on PM2.5, PM10, and other pollutants—from over 48,000 locations across 150 c
		ountries. The platform empowers researchers, journalists, and communities to access, analyze,
		and use air quality data through an open API, fostering collaboration to improve public
		health and policy
'''

NOAA_CLIMATE_DATA = r'''NOAA climate data is provided primarily through the National Centers for
		Environmental Information (NCEI), serving as the world's largest archive of atmospheric,
		coastal, and geophysical data. It offers free access to historical weather records, 30-year
		Climate Normals, and datasets on temperature, precipitation, and storms. Data is accessible
		via the NCEI Climate Data Online (CDO) portal and NOAA Climate.gov maps and tools
'''

USGS_NATIONAL_MAP = r'''The USGS National Map is a premier collaborative program providing free,
		accurate, and public domain geospatial data for the United States and its territories.
		It offers topographic maps, 3D elevation data, and 8+ data layers (transportation,
		hydrography, structures) via an online viewer, data downloads, and web services for public,
		academic, and government use
'''

USGS_EARTHQUAKES = r'''The USGS Earthquake Hazards Program monitors, reports, and researches global
		seismic activity to reduce losses and save lives. It operates the National Earthquake
		Information Center (NEIC) and Advanced National Seismic System (ANSS) to detect magnitude,
		location, and impacts, providing data for public safety, engineering, and hazard assessments
'''

USGS_WATER = r'''The USGS Water Resources Mission Area monitors, assesses, and conducts research on
		the nation's water, providing data on streamflow, groundwater, water quality, and water use.
		With over 1.9 million sites across all 50 states, they provide real-time information crucial
		for water management, safety, and economic, environmental, and recreational decisions
'''

NOAA_TIDES_CURRENTS = r'''NOAA Tides & Currents, managed by the Center for Operational Oceanographic
		Products and Services (CO-OPS), is the authoritative U.S. source for water level, tidal, and
		oceanographic data. It offers real-time monitoring and predictions for over 3,000 stations,
		crucial for navigation, safety, and coastal resilience.
'''

SKY_MAP = r'''Provides static and link-based star chart generation using the SKY-MAP.ORG
		XML API, Site Linker, and Image Generator interfaces.
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

EPA_ENVIROFACTS = r'''The Envirofacts Data Warehouse contains information from select EPA Environmental
		program office databases and provides access about environmental activities that may affect air,
		water, and land anywhere in the United States.
'''

EPA_UV_INDEX = r'''The EPA UV Index predicts daily solar UV radiation intensity on a 1–11+ scale,
		helping to gauge sun-safe precautions. Developed with the National Weather Service, it factors
		in ozone, clouds, and elevation to forecast noon intensity. A UV Alert is issued if the
		index is 6+ and unusually high.
'''

NASA_EONET = r'''NASA Earth Observatory's Natural Event Tracker (EONET) allows users to access imagery,
		often in near real-time (NRT), of natural events such as dust storms, forest fires, and tropical
		cyclones—empowering people all across the planet to locate, track, and potentially prepare for
		and manage events that affect communities in their paths. The EONET application programming
		interface (API) provides customization of features including curation and direct links to
		image sources.
'''

NASA_FIRMS = r'''ASA’s Fire Information for Resource Management System (FIRMS) provides near
		real-time, satellite-derived active fire and hotspot data (within 3 hours of observation)
		to monitor wildfires. Using sensors from MODIS and VIIRS, it offers global coverage through
		an interactive map, email alerts, and GIS data. It is designed for firefighters, scientists,
		and natural resource managers
'''

OPEN_WEATHER = r'''
		Provides forecast weather retrieval by location name using the Open-Meteo
		Geocoding API and Open-Meteo Forecast API. This class is forecast-only by design and
		intentionally excludes archive / historical date-based retrieval so it does not overlap
		with the separate Historical Weather class.
'''

HISTORICAL_WEATHER = r'''Provides historical weather retrieval by location name and date using the
		Open-Meteo Geocoding API and Open-Meteo Historical Weather API. This class is intentionally
		designed around the actual user-facing need in the Foo fetcher expander: enter a location
		and a date, resolve that location to coordinates, then retrieve historical weather for that date.
'''

ASTRONOMY_CATALOG = r'''The Open Astronomy Catalog (OAC) API is a RESTful interface designed for
		programmatic access to open-access astronomical data, specifically focusing on transient events.
'''

ASTRO_QUERY = r'''Access to the astropy package that contains key functionality and common tools needed for
		performing astronomy and astrophysics with Python. It is at the core of the Astropy Project,
		which aims to enable the community to develop a robust ecosystem of affiliated packages
		covering a broad range of needs for astronomical research, data processing, and data analysis.
'''

US_NAVAL_OBSERVATORY = r'''Provides access to APIs from the US Naval Observatory's Celestial Navigation Data for
		Assumed Position and Time:  this data service provides all the astronomical information
		necessary to plot navigational lines of position from observations of the altitudes of
		celestial bodies.
'''

GOOGLE_CSE = r'''The Cse Service is the endpoint that returns the requested searches.
		You must identify a particular search engine to use in your request
		(using the cx query parameter) as well as the search query (using the q query parameter).
		In addition, you should provide a developer key (using the key query parameter).
'''

GOOGLE_WEATHER = r'''The Weather API lets you request real-time, hyperlocal weather data for
		locations around the world. Weather information includes temperature, precipitation,
		humidity, and more.
'''
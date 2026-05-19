###### mappy
![](https://github.com/is-leeroy-jenkins/Mappy/blob/master/resources/images/project_mappy.png)

- `mappy` is a lightweight Python framework that wraps various mapping fucntionality 
for use in data pipelines and agentic tooling. It is designed to be simplify the integration of geospatial 
capabilities into ML/AI workflows and applications.

- With `mappy`, you can enrich spreadsheets with latitude/longitude, calculate travel distances,  
generate static map previews, and use caching/rate limiting to control API usage — all from Python.

- `mappy` plays well with `cosmo`, mappy's galactic cousin.
## 🎥 Demo 

![](https://github.com/is-leeroy-jenkins/Mappy/blob/master/resources/images/mappy-demo.gif)

## ✨ Features

- 🔎 **Geocoding** – Convert free-form addresses or (City, State, Country) triples into coordinates.  
- 📏 **Distance Matrix** – Compute distance and travel time between origins and destinations.  
- 🗺 **Static Maps** – Generate map image URLs for embedding or reporting.  
- ⏱ **Time Zones** – Look up IANA time zones for coordinates.  
- ⚡ **Rate Limiting & Caching** – Stay under API quotas with built-in QPS limiter and caching backends.  
- 📊 **Excel Integration** – Enrich spreadsheets with geocoded results in a single call.  
- 🛠 **Error Handling** – Explicit exceptions for not found, gateway failures, and more.  
- 🧩 **Extensible** – Drop-in services for Places, Directions, or any other Maps endpoint.  



## 📦 Installation

Clone the repository and install dependencies:
```
  pip install -r requirements.txt
  
```



## 🚀 Quick Start

### 1. Initialize Maps
```
    from mappy import Maps

    maps = Maps(api_key="YOUR_API_KEY")
```

### 2. Geocode an address

```    
    from mappy import Geocoder

    geo = Geocoder(maps)
    result = geo.freeform("Paris, France")
    print(result["lat"], result["lng"], result["formatted_address"])
```

### 3. Calculate distance

```    
    from mappy import DistanceMatrix

    dist = DistanceMatrix(maps)
    d = dist.summary("New York, USA", "Los Angeles, USA", mode="driving")
    print(d["distance_text"], d["duration_text"])
 ```

### 4. Get a static map URL

```    
    from mappy import StaticMapURL

    sm = StaticMapURL(api_key="YOUR_API_KEY")
    url = sm.pin(lat=48.8584, lng=2.2945, zoom=14)
    print(url)
```

### 5. Process Excel locations

```    
    from mappy import Excel

    excel = Excel(api_key="YOUR_API_KEY")
    excel.enrich(
        input_path="locations.xlsx",
        output_path="locations_with_coords.xlsx",
        city_col="City",
        state_col="State",
        country_col="Country"
    )
```


## 📂 Project Structure

    mappy/
     ├── __init__.py        # Public interface
     ├── maps.py            # Maps (API gateway)
     ├── geocode.py         # Address → coordinates
     ├── places.py          # Places text search fallback
     ├── distance.py        # Distance Matrix API
     ├── timezone.py        # Time zone resolution
     ├── staticmaps.py      # Static map URL generator
     ├── excel.py           # Excel integration helpers
     ├── caching.py         # InMemoryCache & SQLiteCache
     ├── rate.py            # Rate limiter
     └── exceptions.py      # Custom errors



## ⚠️ Error Handling

- **NotFound** – Raised when a location cannot be resolved.  
- **GatewayError** – Raised when HTTP/API communication fails.  
- **MappyError** – Base class for all framework exceptions.  

###### By catching these explicitly, you can gracefully handle errors in bulk geocoding or API calls.



## 💡 Design Philosophy

- **Simplicity first**: Every class has a single clear responsibility.  
- **Composable**: Services like `Geocoder`, `DistanceMatrix`, `StaticMapURL` can be used alone or together.  
- **Cache-friendly**: Optional `InMemoryCache` or `SQLiteCache` save API calls and reduce cost.  
- **Rate-aware**: Built-in `RateLimiter` keeps calls under quota.  
- **Spreadsheet-ready**: The `Excel` service directly reads/writes `.csv` or `.xlsx`.  



## 🧪 Example Use Cases

- Enriching a customer database with GPS coordinates.  
- Calculating commute distances for IMT relocation analysis.  
- Creating static map thumbnails for property listings.  
- Validating and normalizing international addresses.  
- Auditing time zone coverage for scheduling software.  



## 🔑 AI API Key

- [OpenAI API Key](https://github.com/is-leeroy-jenkins/Buddy/blob/main/resources/setup/openai.md)
- [Grok API Key](https://github.com/is-leeroy-jenkins/Buddy/blob/main/resources/setup/xai.md)
- [Gemini API Key](https://github.com/is-leeroy-jenkins/Buddy/blob/main/resources/setup/gemini.md)


#### Data Services 

- [Claude](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve) 
- [Mistral](https://chat.mistral.ai/1) 
- [NASA](https://api.nasa.gov/) 
- [Geolocation](https://developers.google.com/maps/documentation/geolocation/get-api-key) 
- [Google Maps](https://developers.google.com/maps/documentation/embed/get-api-key) 
- [Gov Data](https://api.govinfo.gov/docs/) 
- [The News API](https://www.thenewsapi.com/register) 
- [Google Weather](https://developers.google.com/maps/documentation/weather/get-api-key) 
- [Grokipedia](https://pypi.org/project/grokipedia-api/) 
- [CDC](https://data.cdc.gov/login) 
- [Purple Air](https://develop.purpleair.com/) 
- [FIRMS](https://firms.modaps.eosdis.nasa.gov/usfs/api/map_key/) 
- [CENSUS](https://api.census.gov/data/key_signup.html) 
- [Wikipedia](https://www.mediawiki.org/wiki/Wikimedia_APIs/Get_started)


#### **Dependencies**:
- `requests` – robust HTTP client  
- `pandas` – spreadsheet data processing  
- `openpyxl` – Excel I/O (.xlsx files)  



## 📜 License

Mappy is available via the MIT License [here](https://github.com/is-leeroy-jenkins/mappy/blob/master/LICENSE.txt).  







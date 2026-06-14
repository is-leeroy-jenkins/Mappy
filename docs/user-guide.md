# User Guide

Mappy is a Python geospatial toolkit and Streamlit application for Google Maps workflows, route
analysis, static map URL generation, time-zone lookup, spreadsheet enrichment, external data
fetching, and generated-content workflows.

## 🧭 Overview

Mappy can be used in two ways:

| Use Case               | Entry Point            | Description                                                                                     |
| ---------------------- | ---------------------- | ----------------------------------------------------------------------------------------------- |
| Interactive workflows  | `streamlit run app.py` | Use the Streamlit interface for guided geospatial, enrichment, fetch, and generation workflows. |
| Programmatic workflows | Python modules         | Import service classes directly in scripts, notebooks, or other applications.                   |

The main capabilities are organized by module.

| Capability             | Module          | Purpose                                                         |
| ---------------------- | --------------- | --------------------------------------------------------------- |
| Streamlit application  | `app.py`        | Interactive UI for Mappy workflows.                             |
| Google Maps gateway    | `maps.py`       | Shared Google Maps Web Services request layer.                  |
| Geocoding              | `geocode.py`    | Forward, reverse, structured, and batch geocoding.              |
| Places fallback        | `places.py`     | Text Search and Place Details lookup.                           |
| Distance Matrix        | `distances.py`  | Route distance, duration, and mode comparison.                  |
| Static Maps            | `staticmaps.py` | Google Static Maps URL generation.                              |
| Time Zones             | `timezones.py`  | Time-zone metadata and local-time conversion.                   |
| Spreadsheet enrichment | `excel.py`      | CSV/XLSX geospatial enrichment workflows.                       |
| Caching                | `caches.py`     | In-memory and SQLite-backed cache implementations.              |
| External fetchers      | `fetchers.py`   | Web, document, scientific, search, and external data retrieval. |
| Generators             | `generators.py` | Generated-content and provider-oriented workflows.              |

## ⚙️ Installation

Create and activate a virtual environment from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Confirm the project compiles.

```powershell
python -m compileall .
```

## 🔑 API Key Setup

Google-backed workflows require a Google Maps Platform API key.

Set the key for the current PowerShell session:

```powershell
$env:GOOGLEMAPS_API_KEY = "your-google-maps-api-key"
```

For permanent local use, add the key through Windows Environment Variables or your shell profile.

Do not commit API keys to source files, documentation, screenshots, notebooks, or examples.

## ▶️ Running the Streamlit Application

Run the app from the repository root.

```powershell
streamlit run app.py
```

The application provides guided workflows for geocoding, place lookup, route analysis, static map
URL generation, time-zone lookup, spreadsheet enrichment, external data retrieval, and generation
utilities.

## 🗺️ Google Maps Gateway

The `Maps` class centralizes outbound Google Maps Web Services calls. Service wrappers use it
instead of building their own request logic.

```python
from maps import Maps

maps = Maps()

payload = maps.request(
    "geocode/json",
    {
        "address": "1600 Pennsylvania Avenue NW, Washington, DC"
    }
)

print(payload.get("status"))
```

The gateway handles the common request path:

1. Validate the endpoint and parameters.
2. Apply rate limiting.
3. Add the configured API key.
4. Send the HTTP request.
5. Record diagnostics.
6. Retry transient failures.
7. Return the parsed JSON payload.

For normal application work, use the higher-level service wrappers instead of calling
`Maps.request(...)` directly.

## 📍 Forward Geocoding

Use `Geocoder.freeform(...)` to resolve a free-form address into a structured geospatial record.

```python
from maps import Maps
from geocode import Geocoder
from caches import InMemoryCache

maps = Maps()
cache = InMemoryCache()
geocoder = Geocoder(maps, cache=cache)

result = geocoder.freeform(
    address="1600 Pennsylvania Avenue NW, Washington, DC",
    country="US"
)

print(result["formatted_address"])
print(result["lat"], result["lng"])
```

Typical fields returned by geocoding workflows include:

| Field               | Description                              |
| ------------------- | ---------------------------------------- |
| `formatted_address` | Canonical formatted address.             |
| `lat`               | Latitude.                                |
| `lng`               | Longitude.                               |
| `place_id`          | Google place identifier.                 |
| `types`             | Google result type values.               |
| `country_code`      | Short country code.                      |
| `country_name`      | Full country name.                       |
| `admin_level_1`     | State, province, region, or equivalent.  |
| `admin_level_2`     | County or secondary administrative area. |
| `locality`          | City or locality.                        |
| `postal_code`       | Postal code.                             |
| `source`            | Mappy workflow source.                   |
| `query`             | Original query value.                    |

## 🔁 Reverse Geocoding

Use `Geocoder.reverse(...)` to resolve latitude and longitude into an address.

```python
from maps import Maps
from geocode import Geocoder

geocoder = Geocoder(Maps())

result = geocoder.reverse(
    latitude=38.8977,
    longitude=-77.0365
)

print(result["formatted_address"])
```

## 🏙️ City, State, and Country Lookup

Use `Geocoder.city_state_country(...)` when your source data is split into separate locality fields.

```python
from maps import Maps
from geocode import Geocoder

geocoder = Geocoder(Maps())

result = geocoder.city_state_country(
    city="Dallas",
    state="TX",
    country="US"
)

print(result["formatted_address"])
print(result["lat"], result["lng"])
```

## 📦 Batch Geocoding

Use `Geocoder.batch_freeform(...)` to process multiple addresses while preserving row-level status.

```python
from maps import Maps
from geocode import Geocoder

geocoder = Geocoder(Maps())

rows = geocoder.batch_freeform(
    addresses=[
        "1600 Pennsylvania Avenue NW, Washington, DC",
        "1200 Pennsylvania Avenue NW, Washington, DC",
        ""
    ],
    country="US"
)

for row in rows:
    print(row["query"], row["geocode_status"], row["formatted_address"])
```

Batch output includes `geocode_status` and `geocode_error` fields so individual failures do not stop
the full batch.

## 🏢 Places Lookup

Use the `Place` wrapper when a query is better represented as a named place, business, landmark, or
institution.

```python
from maps import Maps
from places import Place

places = Place(Maps())

result = places.text_to_location(
    query="EPA Headquarters Washington DC",
    country="US"
)

print(result["name"])
print(result["formatted_address"])
print(result["lat"], result["lng"])
```

Places output includes standard geospatial fields and additional place metadata.

| Field                    | Description                            |
| ------------------------ | -------------------------------------- |
| `name`                   | Place name.                            |
| `business_status`        | Google business status when available. |
| `rating`                 | Google rating when available.          |
| `user_ratings_total`     | Number of ratings when available.      |
| `website`                | Website URL when available.            |
| `formatted_phone_number` | Phone number when available.           |

## 🔎 Places Candidate Search

Use `search_candidates(...)` when a query may return multiple possible matches.

```python
from maps import Maps
from places import Place

places = Place(Maps())

candidates = places.search_candidates(
    query="Springfield",
    country="US",
    lmt=5
)

for item in candidates:
    print(item.get("name"), item.get("formatted_address"))
```

## 🛣️ Distance Matrix

Use `DistanceMatrix.summary(...)` to calculate a compact route summary.

```python
from maps import Maps
from distances import DistanceMatrix

distance = DistanceMatrix(Maps())

summary = distance.summary(
    origin="Dallas, TX",
    destination="Austin, TX",
    mode="driving"
)

print(summary["distance_text"])
print(summary["duration_text"])
```

Supported travel modes:

| Mode        | Description                                         |
| ----------- | --------------------------------------------------- |
| `driving`   | Driving route distance and duration.                |
| `walking`   | Walking route distance and duration.                |
| `bicycling` | Bicycling route distance and duration.              |
| `transit`   | Transit route distance and duration when available. |

## 🔀 Compare Travel Modes

Use `compare_modes(...)` to compare route results across multiple travel modes.

```python
from maps import Maps
from distances import DistanceMatrix

distance = DistanceMatrix(Maps())

rows = distance.compare_modes(
    origin="Washington, DC",
    destination="Baltimore, MD",
    modes=["driving", "transit", "walking"]
)

for row in rows:
    print(row["mode"], row["distance_text"], row["duration_text"])
```

## 📋 Matrix Results as a DataFrame

Use `to_dataframe(...)` to convert route rows into a pandas DataFrame.

```python
from maps import Maps
from distances import DistanceMatrix

distance = DistanceMatrix(Maps())

rows = distance.matrix(
    origins=["Washington, DC", "Baltimore, MD"],
    destinations=["Philadelphia, PA"],
    mode="driving"
)

df = distance.to_dataframe(rows)
print(df.head())
```

## 🖼️ Static Map URLs

Use `StaticMap` to build Google Static Maps URLs.

### Single Pin

```python
from staticmaps import StaticMap

static_map = StaticMap()

url = static_map.pin(
    lat=38.8977,
    lng=-77.0365,
    zoom=14,
    size="600x400"
)

print(url)
```

### Multiple Pins

```python
from staticmaps import StaticMap

static_map = StaticMap()

url = static_map.pins(
    points=[
        {"lat": 38.8977, "lng": -77.0365},
        {"lat": 38.8895, "lng": -77.0353}
    ],
    size="600x400",
    maptype="roadmap",
    color="red"
)

print(url)
```

### Path Map

```python
from staticmaps import StaticMap

static_map = StaticMap()

url = static_map.path(
    points=[
        (38.8977, -77.0365),
        (38.8895, -77.0353),
        (38.8814, -77.0365)
    ],
    size="600x400",
    maptype="roadmap"
)

print(url)
```

### Bounding Box

```python
from staticmaps import StaticMap

static_map = StaticMap()

url = static_map.bbox(
    west=-77.05,
    south=38.88,
    east=-77.02,
    north=38.91,
    size="600x400"
)

print(url)
```

Static map methods return URLs. They do not download image files.

## 🕒 Time Zone Lookup

Use `Timezone.lookup(...)` to retrieve Google Time Zone API metadata for coordinates.

```python
from maps import Maps
from timezones import Timezone

timezone = Timezone(Maps())

data = timezone.lookup(
    lat=38.8977,
    lng=-77.0365
)

print(data.get("timeZoneId"))
print(data.get("timeZoneName"))
```

## 🌐 Time Zone ID

Use `get_id(...)` when you only need the IANA time-zone identifier.

```python
from maps import Maps
from timezones import Timezone

timezone = Timezone(Maps())

zone_id = timezone.get_id(
    lat=38.8977,
    lng=-77.0365
)

print(zone_id)
```

## ⏰ UTC Offset

Use `offset_hours(...)` to calculate the total offset from UTC.

```python
from maps import Maps
from timezones import Timezone

timezone = Timezone(Maps())

offset = timezone.offset_hours(
    lat=38.8977,
    lng=-77.0365
)

print(offset)
```

## 🕓 Local Time Conversion

Use `local_time(...)` to convert UTC datetime values to the local time at a coordinate.

```python
import datetime as dt
from maps import Maps
from timezones import Timezone

timezone = Timezone(Maps())

result = timezone.local_time(
    lat=38.8977,
    lng=-77.0365,
    utc_datetime=dt.datetime.now(dt.timezone.utc)
)

print(result["local_time"])
```

## 📊 Spreadsheet Enrichment

Mappy includes an `Excel` helper for CSV/XLSX enrichment workflows.

The enrichment pattern is:

```text
Input CSV/XLSX
   |
   v
Read DataFrame
   |
   v
Resolve each row with Geocoder
   |
   +-- fallback to Places when needed
   |
   v
Append canonical output columns
   |
   v
Write enriched CSV/XLSX
```

Typical output columns include:

| Column              | Description                              |
| ------------------- | ---------------------------------------- |
| `formatted_address` | Resolved address.                        |
| `lat`               | Latitude.                                |
| `lng`               | Longitude.                               |
| `place_id`          | Google place identifier.                 |
| `types`             | Google result types.                     |
| `country_code`      | Country code.                            |
| `country_name`      | Country name.                            |
| `admin_level_1`     | State, province, or region.              |
| `admin_level_2`     | County or secondary administrative area. |
| `locality`          | City or locality.                        |
| `postal_code`       | Postal code.                             |
| `geocode_status`    | Row-level status.                        |
| `geocode_error`     | Row-level error text when applicable.    |

Common status values:

| Status          | Meaning                           |
| --------------- | --------------------------------- |
| `ok`            | Resolved through geocoding.       |
| `ok_places`     | Resolved through Places fallback. |
| `not_found`     | No usable result was found.       |
| `skipped_empty` | Source row had no usable input.   |
| `error`         | Row-level processing error.       |

## 🧠 Caching

Use `InMemoryCache` for temporary process-local caching.

```python
from caches import InMemoryCache

cache = InMemoryCache()

cache.set("example", {"value": 1})
print(cache.get("example"))
print(cache.stats())
```

Use `SQLiteCache` for durable local caching.

```python
from caches import SQLiteCache

cache = SQLiteCache("mappy_cache.sqlite")

cache.set("example", {"value": 1})
print(cache.get("example"))
print(cache.stats())

cache.close()
```

Caching is especially useful for repeated geocoding, Places, distance, time-zone, and enrichment
workflows.

## ⏱️ Rate Limiting

`Maps` uses `RateLimiter` to reduce avoidable burst-rate and quota issues.

```python
from rates import RateLimiter

limiter = RateLimiter(max=5)

for _ in range(10):
    limiter.wait()
    print("Request allowed")
```

## ⚠️ Error Handling

Mappy uses project-specific exceptions and wrapped logging in operational service modules.

Common exceptions include:

| Exception      | Purpose                                                      |
| -------------- | ------------------------------------------------------------ |
| `MappyError`   | Base framework exception.                                    |
| `GatewayError` | External gateway, transport, retry, or API response failure. |
| `NotFound`     | Lookup completed but did not produce a usable result.        |

Common validation failures include:

| Failure            | Cause                                                      |
| ------------------ | ---------------------------------------------------------- |
| Missing value      | Required argument was `None`.                              |
| Blank string       | Required text value was empty.                             |
| Invalid coordinate | Latitude or longitude was outside valid ranges.            |
| Unsupported mode   | Distance Matrix mode was not supported.                    |
| Missing column     | Spreadsheet enrichment referenced a missing column.        |
| Not found          | External lookup produced no usable result.                 |
| Gateway error      | External request failed or returned a hard failure status. |

## 🔐 Sensitive Data Practices

Do not log or commit sensitive values.

Avoid logging:

| Value                   | Reason                                        |
| ----------------------- | --------------------------------------------- |
| API keys                | Secret credential.                            |
| Raw request payloads    | May contain user input.                       |
| Full provider responses | May contain provider or user data.            |
| Addresses               | Location data may be sensitive.               |
| Coordinates             | Location data may be sensitive.               |
| File contents           | Uploaded files may contain sensitive data.    |
| DataFrame rows          | Uploaded records may contain sensitive data.  |
| Cache keys              | Cache keys may include normalized user input. |

## 📚 API Reference

Use the API reference pages for class and method documentation generated from source docstrings.

| API Page           | Module          |
| ------------------ | --------------- |
| Application        | `app.py`        |
| Caching            | `caches.py`     |
| Configuration      | `config.py`     |
| Core Models        | `core.py`       |
| Distance Matrix    | `distances.py`  |
| Excel Enrichment   | `excel.py`      |
| Exceptions         | `exceptions.py` |
| External Fetchers  | `fetchers.py`   |
| Content Generators | `generators.py` |
| Geocoding          | `geocode.py`    |
| Maps Gateway       | `maps.py`       |
| Places             | `places.py`     |
| Rates              | `rates.py`      |
| Static Maps        | `staticmaps.py` |
| Time Zones         | `timezones.py`  |

## ✅ Recommended Workflow

For most users:

1. Start with the Streamlit app.
2. Use direct Python imports when automating repeatable workflows.
3. Add caching when repeating external lookups.
4. Validate inputs before long-running enrichment jobs.
5. Review row-level statuses after batch processing.
6. Build the documentation with `mkdocs build` after source docstring changes.

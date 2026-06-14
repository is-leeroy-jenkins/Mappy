# Architecture

Mappy is a Python geospatial toolkit and Streamlit application for Google Maps workflows, location
enrichment, route analysis, static map generation, external data retrieval, and generated-content
workflows. The architecture is intentionally flat and service-oriented: each major capability lives
in a standalone Python module that can be used directly from code or orchestrated through the
Streamlit interface.

## 🧭 Architectural Overview

Mappy is organized around a reusable service layer with a Streamlit application on top. The
application layer handles user interaction, while the service modules handle validation, external
requests, normalization, caching, enrichment, and output generation.

```text
+----------------------------------------------------------------------------------+
|                                  Streamlit UI                                     |
|                                    app.py                                         |
|----------------------------------------------------------------------------------|
|  Inputs | Uploads | Geocoding | Places | Routes | Static Maps | Fetch | Generate |
+---------------------------------------+------------------------------------------+
                                        |
                                        v
+----------------------------------------------------------------------------------+
|                              Application Services                                |
|----------------------------------------------------------------------------------|
|  Geocoding          Places Fallback       Distance Matrix      Spreadsheet        |
|  geocode.py         places.py             distances.py         excel.py           |
|                                                                                  |
|  Static Maps        Time Zones            External Fetchers    Generators         |
|  staticmaps.py      timezones.py          fetchers.py          generators.py      |
+---------------------------+----------------------+-------------------------------+
                            |                      |
                            v                      v
+----------------------------------------------------------------------------------+
|                              Shared Infrastructure                               |
|----------------------------------------------------------------------------------|
|  Google Maps Gateway      Rate Limiter        Cache Backends       Result Model   |
|  maps.py                  rates.py            caches.py            core.py        |
|                                                                                  |
|  Configuration            Exceptions          Logging Integration                 |
|  config.py                exceptions.py       boogr.Error / boogr.Logger          |
+---------------------------------------+------------------------------------------+
                                        |
                                        v
+----------------------------------------------------------------------------------+
|                              External Systems                                    |
|----------------------------------------------------------------------------------|
|  Google Maps APIs | Places API | Distance Matrix | Static Maps | Time Zone API    |
|  Web Sources      | Scientific APIs | Search Sources | Provider APIs | Local Files    |
+----------------------------------------------------------------------------------+
```

## 🧱 Design Principles

Mappy follows a few practical design principles.

| Principle                  | Description                                                                                                                       |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Flat source layout         | Modules sit at the repository root so the app and documentation can import them directly.                                         |
| Thin UI layer              | `app.py` should orchestrate workflows, not bury service logic inside Streamlit callbacks.                                         |
| Reusable services          | Geocoding, Places, Distance Matrix, Static Maps, Time Zone, Excel enrichment, fetchers, and generators can be used independently. |
| Canonical output shapes    | Service wrappers normalize external payloads into predictable dictionaries, lists, dataframes, or URLs.                           |
| Cache-aware workflows      | Repeated lookups can use in-memory or SQLite cache backends.                                                                      |
| Documentation-ready source | Public classes, functions, and methods use Google-style docstrings for MkDocs and mkdocstrings.                                   |
| Stable exception logging   | Wrapped exceptions record module, cause, method, message, and traceback without logging sensitive runtime values.                 |

## 🗂️ Repository Layout

Mappy uses a flat application layout with documentation under `docs/`.

```text
Mappy/
  app.py
  caches.py
  config.py
  core.py
  distances.py
  excel.py
  exceptions.py
  fetchers.py
  generators.py
  geocode.py
  maps.py
  places.py
  rates.py
  staticmaps.py
  timezones.py
  requirements.txt
  README.md
  mkdocs.yml
  docs/
    index.md
    architecture.md
    user-guide.md
    development.md
    github-pages.md
    api/
      index.md
      app.md
      caches.md
      config.md
      core.md
      distances.md
      excel.md
      exceptions.md
      fetchers.md
      generators.md
      geocode.md
      maps.md
      places.md
      rates.md
      staticmaps.md
      timezones.md
    assets/
      css/
        extra.css
      js/
        extra.js
```

## 🖥️ Application Layer

The application layer is implemented in `app.py`.

`app.py` provides the Streamlit interface for interactive workflows. It should remain focused on
page layout, controls, state management, service orchestration, and display logic.

Primary responsibilities include:

| Responsibility        | Description                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------- |
| Page configuration    | Configures the Streamlit page, title, icons, and layout.                                     |
| Sidebar controls      | Collects mode selections, configuration values, and workflow options.                        |
| Input capture         | Accepts addresses, coordinates, files, prompts, provider options, and user settings.         |
| Service orchestration | Calls geocoding, Places, distance, static map, time-zone, fetcher, and generator modules.    |
| Result rendering      | Displays dictionaries, tables, dataframes, maps, generated text, URLs, and status summaries. |
| Session state         | Maintains state across Streamlit reruns without moving business logic into the UI.           |

The UI layer depends on the service layer. The service layer should not depend on Streamlit.

```text
app.py
  |
  +-- geocode.py
  +-- places.py
  +-- distances.py
  +-- staticmaps.py
  +-- timezones.py
  +-- excel.py
  +-- fetchers.py
  +-- generators.py
```

## 🗺️ Google Maps Gateway Layer

The Google Maps gateway is implemented in `maps.py`.

The `Maps` class centralizes outbound Google Maps Web Services requests. Instead of having every
service wrapper construct its own HTTP logic, service classes call `Maps.request(...)`.

```text
Service Wrapper
      |
      v
Maps.request(endpoint, params)
      |
      +-- validate endpoint and parameter inputs
      +-- apply request rate limiting
      +-- inject configured Google Maps API key
      +-- issue HTTP GET request
      +-- record diagnostics
      +-- retry transient failures
      +-- raise gateway errors for hard failures
      |
      v
Parsed JSON payload
```

The gateway layer supports these service wrappers:

| Wrapper          | Module         | Google API Family                    |
| ---------------- | -------------- | ------------------------------------ |
| `Geocoder`       | `geocode.py`   | Geocoding API                        |
| `Place`          | `places.py`    | Places Text Search and Place Details |
| `DistanceMatrix` | `distances.py` | Distance Matrix API                  |
| `Timezone`       | `timezones.py` | Time Zone API                        |

## 📍 Geocoding Layer

The geocoding layer is implemented in `geocode.py`.

The `Geocoder` class resolves free-form addresses, reverse-geocodes coordinates, resolves structured
city/state/country values, and supports batch geocoding.

| Component                          | Purpose                                                                    |
| ---------------------------------- | -------------------------------------------------------------------------- |
| `flatten_geocode(...)`             | Converts raw Google Geocoding results into Mappy’s canonical output shape. |
| `Geocoder.freeform(...)`           | Resolves one free-form address.                                            |
| `Geocoder.reverse(...)`            | Resolves one coordinate pair into an address.                              |
| `Geocoder.city_state_country(...)` | Resolves structured locality fields.                                       |
| `Geocoder.batch_freeform(...)`     | Processes multiple addresses with row-level status handling.               |

Typical output fields include:

| Field               | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `formatted_address` | Canonical formatted address.                             |
| `lat`               | Latitude.                                                |
| `lng`               | Longitude.                                               |
| `place_id`          | Google place identifier.                                 |
| `types`             | Google result types.                                     |
| `country_code`      | Short country code.                                      |
| `country_name`      | Full country name.                                       |
| `admin_level_1`     | State, province, region, or equivalent.                  |
| `admin_level_2`     | County or secondary administrative area.                 |
| `locality`          | City or locality.                                        |
| `postal_code`       | Postal code.                                             |
| `source`            | Workflow source, such as `geocode` or `reverse_geocode`. |
| `query`             | Original query value.                                    |

## 🏢 Places Layer

The Places layer is implemented in `places.py`.

The `Place` class provides a fallback and enrichment path for named locations, businesses,
landmarks, institutions, and ambiguous user queries. It uses Places Text Search to find candidates
and Place Details to retrieve structured metadata.

| Component                          | Purpose                                                        |
| ---------------------------------- | -------------------------------------------------------------- |
| `Place.text_to_location(...)`      | Resolves free text into a canonical location record.           |
| `Place.place_details(...)`         | Resolves a known `place_id` into detailed metadata.            |
| `Place.search_candidates(...)`     | Returns candidate Places results for review or disambiguation. |
| `Place.flatten_place_details(...)` | Converts Place Details into Mappy’s canonical output shape.    |
| `Place.component_value(...)`       | Extracts address components from Google payloads.              |

Places output intentionally overlaps with geocoding output. It also includes additional fields such
as:

| Field                    | Description                            |
| ------------------------ | -------------------------------------- |
| `name`                   | Place name.                            |
| `business_status`        | Google business status when available. |
| `rating`                 | Google rating when available.          |
| `user_ratings_total`     | Number of user ratings when available. |
| `website`                | Place website when available.          |
| `formatted_phone_number` | Place phone number when available.     |

## 🛣️ Distance Matrix Layer

The distance layer is implemented in `distances.py`.

The `DistanceMatrix` class wraps route-distance and duration workflows.

| Component                              | Purpose                                                 |
| -------------------------------------- | ------------------------------------------------------- |
| `DistanceMatrix.matrix(...)`           | Executes one-to-many or many-to-many distance requests. |
| `DistanceMatrix.summary(...)`          | Returns a compact one-route summary.                    |
| `DistanceMatrix.compare_modes(...)`    | Compares travel modes for the same route.               |
| `DistanceMatrix.to_dataframe(...)`     | Converts route rows into a pandas DataFrame.            |
| `DistanceMatrix.normalize_mode(...)`   | Validates travel mode values.                           |
| `DistanceMatrix.normalize_inputs(...)` | Normalizes address and coordinate inputs.               |
| `DistanceMatrix.flatten_element(...)`  | Converts one Google response element into a row.        |

Supported modes are:

| Mode        | Description                                   |
| ----------- | --------------------------------------------- |
| `driving`   | Driving distance and duration.                |
| `walking`   | Walking distance and duration.                |
| `bicycling` | Bicycling distance and duration.              |
| `transit`   | Transit distance and duration when available. |

## 🖼️ Static Maps Layer

The static map layer is implemented in `staticmaps.py`.

The `StaticMap` class builds Google Static Maps URLs. It does not download images directly. It
returns URLs that can be displayed in Streamlit, used in documentation, opened in a browser, or
embedded in reports.

| Component                            | Purpose                                                 |
| ------------------------------------ | ------------------------------------------------------- |
| `StaticMap.pin(...)`                 | Builds a single-marker map URL.                         |
| `StaticMap.pins(...)`                | Builds a multi-marker map URL.                          |
| `StaticMap.path(...)`                | Builds a map URL with a visible path.                   |
| `StaticMap.bbox(...)`                | Builds a map URL with a bounding box outline.           |
| `StaticMap.build_url(...)`           | Assembles the final Google Static Maps URL.             |
| `StaticMap.normalize_points(...)`    | Converts supported point shapes into coordinate tuples. |
| `StaticMap.validate_coordinate(...)` | Validates latitude and longitude ranges.                |

## 🕒 Time Zone Layer

The time-zone layer is implemented in `timezones.py`.

The `Timezone` class wraps the Google Time Zone API.

| Component                            | Purpose                                             |
| ------------------------------------ | --------------------------------------------------- |
| `Timezone.lookup(...)`               | Retrieves the full Google Time Zone API payload.    |
| `Timezone.get_id(...)`               | Extracts the IANA time-zone identifier.             |
| `Timezone.offset_hours(...)`         | Calculates total UTC offset in hours.               |
| `Timezone.local_time(...)`           | Converts UTC time into local time for a coordinate. |
| `Timezone.batch_lookup(...)`         | Enriches row dictionaries with time-zone fields.    |
| `Timezone.validate_coordinates(...)` | Validates latitude and longitude ranges.            |

## 📊 Spreadsheet Enrichment Layer

The spreadsheet layer is implemented in `excel.py`.

The `Excel` class reads CSV/XLSX files, resolves location data, appends canonical geospatial output
columns, summarizes enrichment results, and writes enriched files.

```text
CSV/XLSX Input
      |
      v
Excel.read(...)
      |
      v
Row iteration
      |
      +-- Geocoder.freeform(...)
      |       |
      |       +-- fallback to Place.text_to_location(...)
      |
      +-- Geocoder.city_state_country(...)
              |
              +-- fallback to Place.text_to_location(...)
      |
      v
Canonical enrichment columns
      |
      v
Excel.write(...)
      |
      v
CSV/XLSX Output
```

The enrichment layer preserves row alignment. Every input row receives output values, even when the
row is skipped, not found, or fails with an error.

Common row-level status values include:

| Status          | Meaning                                               |
| --------------- | ----------------------------------------------------- |
| `ok`            | Resolved through geocoding.                           |
| `ok_places`     | Resolved through Places fallback.                     |
| `not_found`     | No usable result was found.                           |
| `skipped_empty` | The source row did not contain usable location input. |
| `error`         | A row-level error occurred.                           |

## 🧠 Cache Layer

The cache layer is implemented in `caches.py`.

Caching reduces duplicate lookups and allows repeated workflows to reuse previous results.

| Class           | Storage           | Purpose                                                 |
| --------------- | ----------------- | ------------------------------------------------------- |
| `BaseCache`     | Interface         | Defines the common cache contract.                      |
| `InMemoryCache` | Python dictionary | Provides fast process-local caching.                    |
| `SQLiteCache`   | SQLite database   | Provides durable local caching across application runs. |

Cache implementations support:

| Method          | Purpose                                     |
| --------------- | ------------------------------------------- |
| `get(...)`      | Read a cached dictionary payload.           |
| `set(...)`      | Store a cached dictionary payload.          |
| `delete(...)`   | Remove one cached key.                      |
| `clear(...)`    | Clear all records or a namespace.           |
| `contains(...)` | Check whether a usable cached value exists. |
| `stats(...)`    | Return backend diagnostics.                 |

## ⏱️ Rate Limiting Layer

The rate-limiting layer is implemented in `rates.py`.

The `RateLimiter` class enforces a minimum interval between requests. The `Maps` gateway calls it
before outbound API requests.

```text
Maps.request(...)
      |
      v
RateLimiter.wait()
      |
      +-- count request
      +-- compare elapsed time with configured interval
      +-- sleep when necessary
      +-- update diagnostics
```

## 📦 Core Model Layer

The core layer is implemented in `core.py`.

The `Result` class wraps an HTTP response into a lightweight result object.

| Field         | Description                          |
| ------------- | ------------------------------------ |
| `url`         | Response URL.                        |
| `status_code` | HTTP response status code.           |
| `text`        | Response text body.                  |
| `encoding`    | Response encoding.                   |
| `headers`     | Response headers.                    |
| `response`    | Original `requests.Response` object. |

## 🌐 Fetcher Layer

The fetcher layer is implemented in `fetchers.py`.

Fetchers isolate retrieval logic for web pages, documents, search results, scientific sources,
environmental sources, geospatial services, and other external data sources.

```text
User or App Request
      |
      v
Fetcher Class
      |
      +-- validate inputs
      +-- call external source
      +-- parse or normalize result
      +-- return text, data, document, table, image, or result object
```

The architectural role of `fetchers.py` is to keep external retrieval logic out of the Streamlit UI
and out of generator classes.

## ✍️ Generator Layer

The generator layer is implemented in `generators.py`.

Generators transform prompts, retrieved context, user inputs, files, or structured data into
generated responses or structured outputs.

```text
Prompt / Context / Data
      |
      v
Generator Class
      |
      +-- validate inputs
      +-- prepare provider payload
      +-- call provider or local model
      +-- normalize output
      |
      v
Generated response or structured result
```

The architectural role of `generators.py` is to keep provider-specific generation logic separate
from the UI and retrieval layers.

## ⚠️ Exception Layer

Project-specific exceptions are defined in `exceptions.py`.

| Exception      | Purpose                                                       |
| -------------- | ------------------------------------------------------------- |
| `MappyError`   | Base exception for known Mappy errors.                        |
| `GatewayError` | External gateway, API, response, retry, or transport failure. |
| `NotFound`     | Lookup completed without producing a usable result.           |

Operational modules that wrap errors use the project logging pattern:

```text
boogr.Error
boogr.Logger
```

The logging pattern records stable diagnostic metadata, such as module, cause, method, message, and
traceback. Runtime-sensitive values should not be written to logs.

Do not log:

| Sensitive Value    | Reason                                                |
| ------------------ | ----------------------------------------------------- |
| API keys           | Secret credential.                                    |
| Raw payloads       | May contain user input or provider data.              |
| Full API responses | May contain user or service data.                     |
| Addresses          | User-provided location data.                          |
| Coordinates        | User-provided location data.                          |
| File contents      | Uploaded data may be sensitive.                       |
| DataFrame rows     | Uploaded spreadsheet rows may contain sensitive data. |
| Cache keys         | Cache keys may include normalized user input.         |

## 🔐 Configuration Layer

Configuration is centralized in `config.py`.

Typical configuration responsibilities include:

| Area             | Purpose                                                    |
| ---------------- | ---------------------------------------------------------- |
| Paths            | Root, log, database, image, and documentation paths.       |
| API keys         | External provider keys read from environment variables.    |
| App labels       | Application title, subtitle, and UI constants.             |
| Helper functions | Typed environment-variable readers and validation helpers. |

The configuration layer should not perform external network work. It should remain safe to import.

## 🔄 Primary Data Flow

Most workflows follow the same pattern.

```text
User Input
   |
   v
Streamlit UI or Python Caller
   |
   v
Service Wrapper
   |
   +-- validate inputs
   +-- check cache when configured
   +-- call gateway, fetcher, or provider
   +-- normalize result
   +-- write cache when configured
   |
   v
Dictionary / DataFrame / URL / Generated Output
   |
   v
Display, export, documentation, or downstream use
```

## 🧩 Extension Points

Mappy is designed so additional workflows can be added without rewriting the whole application.

| Extension                  | Where to Add It                                                                    |
| -------------------------- | ---------------------------------------------------------------------------------- |
| New Google Maps service    | Add a service wrapper that uses `Maps.request(...)`.                               |
| New external data source   | Add a fetcher class in `fetchers.py`.                                              |
| New generation provider    | Add a generator class in `generators.py`.                                          |
| New enrichment column      | Extend `Excel.create_outputs(...)`, `append_empty(...)`, and `append_result(...)`. |
| New cache backend          | Implement the `BaseCache` interface.                                               |
| New Streamlit workflow     | Add UI orchestration in `app.py` that calls an existing service class.             |
| New API documentation page | Add `docs/api/<module>.md` with a mkdocstrings directive.                          |

## 📚 Documentation Integration

Mappy documentation is built with MkDocs, Material for MkDocs, and mkdocstrings.

Source modules are documented with Google-style docstrings. API pages under `docs/api/` should use
mkdocstrings directives such as:

```markdown
# Geocoding API

::: geocode
```

The documentation system depends on:

| File                        | Purpose                                                     |
| --------------------------- | ----------------------------------------------------------- |
| `mkdocs.yml`                | Site configuration, navigation, theme, and plugin settings. |
| `docs/index.md`             | Documentation landing page.                                 |
| `docs/architecture.md`      | Architecture explanation.                                   |
| `docs/user-guide.md`        | Usage guide and examples.                                   |
| `docs/development.md`       | Contributor and validation guide.                           |
| `docs/api/*.md`             | API reference pages generated from source docstrings.       |
| `docs/assets/css/extra.css` | Documentation styling overrides.                            |
| `docs/assets/js/extra.js`   | Small documentation UI enhancements.                        |

## ✅ Architecture Summary

Mappy’s architecture is organized around clear separation of responsibilities:

| Layer            | Main Files                                                                             | Responsibility                                             |
| ---------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| UI               | `app.py`                                                                               | User interaction and workflow orchestration.               |
| Service wrappers | `geocode.py`, `places.py`, `distances.py`, `staticmaps.py`, `timezones.py`, `excel.py` | Domain workflows and normalized outputs.                   |
| Gateway          | `maps.py`                                                                              | Shared Google Maps request execution.                      |
| Infrastructure   | `caches.py`, `rates.py`, `core.py`, `config.py`, `exceptions.py`                       | Caching, rate limiting, configuration, models, and errors. |
| Retrieval        | `fetchers.py`                                                                          | External data retrieval.                                   |
| Generation       | `generators.py`                                                                        | Generated content and provider workflows.                  |
| Documentation    | `docs/`, `mkdocs.yml`                                                                  | MkDocs site and API reference.                             |

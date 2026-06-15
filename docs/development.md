# Development

This guide explains how to set up Mappy for local development, validate source changes, maintain
Google-style documentation comments, and build the MkDocs documentation site.

## 🧰 Development Environment

Mappy is a Python project with a Streamlit application and MkDocs documentation.

Recommended local setup:

```powershell
git clone https://github.com/is-leeroy-jenkins/Mappy.git
cd Mappy

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Confirm Python can import the project modules from the repository root.

```powershell
python -m compileall .
```

## 🔑 Environment Variables

Set required API keys before running workflows that call external providers.

```powershell
$env:GOOGLEMAPS_API_KEY = "your-google-maps-api-key"
```

Other provider-specific keys should also be set as environment variables if the related fetcher or
generator workflows are used.

Do not hard-code secrets in source files, documentation files, notebooks, screenshots, or examples.

## ▶️ Running the App

Run the Streamlit app from the repository root.

```powershell
streamlit run app.py
```

The app should be run from the same directory that contains the flat source modules so imports such
as `from maps import Maps` and `from geocode import Geocoder` resolve correctly.

## 🧪 Validation Workflow

Run validation after modifying Python files.

```powershell
python -m compileall .
```

For documentation work, build the MkDocs site.

```powershell
mkdocs build
```

For local preview:

```powershell
mkdocs serve
```

Then open the local documentation URL shown by MkDocs.

## 📚 Documentation Standards

Mappy source files use Google-style docstrings so `mkdocstrings` can generate API documentation.

Every public class, function, and method should have a docstring.

Use this structure:

```python
def example_method(self, name: str, count: int = 1) -> dict:
    """Summarize what the method does.

    Purpose:
        Explain why the method exists, what workflow it supports, and what
        side effects or output shape callers should expect.

    Args:
        name: Human-readable name to process.
        count: Number of times to process the name.

    Returns:
        dict: Result dictionary returned to the caller.

    Raises:
        Error: Raised after logging when validation or processing fails.
    """
```

## 🧾 Docstring Rules

Follow these rules consistently.

| Rule               | Required Practice                                                                  |
| ------------------ | ---------------------------------------------------------------------------------- |
| Summary line       | Start with a one-line summary. Do not start the docstring with `Purpose:`.         |
| Purpose section    | Include `Purpose:` for meaningful classes, functions, and methods.                 |
| Args section       | Use `Args:` only when the function has parameters other than `self` or `cls`.      |
| Returns section    | Use `Returns:` only when the method returns a meaningful value.                    |
| Constructors       | Do not include `Returns:` in `__init__` docstrings.                                |
| Attributes section | Use `Attributes:` for classes with meaningful instance state.                      |
| Raises section     | Use `Raises:` when the method raises or wraps exceptions.                          |
| No `self`          | Do not document `self`.                                                            |
| No `cls`           | Do not document `cls`.                                                             |
| Google-style args  | Use `name: Description.` not `name (str): Description.`                            |
| No legacy headers  | Do not use `Parameters:`, `Parametes:`, `Attribues:`, or underline-style sections. |

## ✅ Good Docstring Example

```python
class Geocoder:
    """Provide forward, reverse, structured, and batch geocoding.

    Purpose:
        Coordinates Google Geocoding API requests through the shared Maps gateway
        and optional cache backend. The class resolves free-form addresses,
        latitude/longitude pairs, and city/state/country triples into a consistent
        flattened output shape used by application, enrichment, and reporting
        workflows.

    Attributes:
        maps: Google Maps gateway used for Geocoding API requests.
        cache: Optional cache backend used to store and retrieve lookup results.
        output: Last flattened geocoding result.
    """
```

## ❌ Docstring Patterns to Avoid

Do not use this pattern:

```python
def bad_method(self, value: str) -> None:
    """Purpose:
    Does something.

    Parameters:
        self: The class instance.
        value (str): Value to process.

    Returns:
        None.
    """
```

Problems:

| Problem                | Why It Fails                                                                  |
| ---------------------- | ----------------------------------------------------------------------------- |
| Starts with `Purpose:` | The first line should be a summary.                                           |
| Uses `Parameters:`     | MkDocs/mkdocstrings expects configured Google-style sections.                 |
| Documents `self`       | `self` is implicit and should not be documented.                              |
| Uses `value (str):`    | This is not the preferred Google-style format for this project.               |
| Returns `None`         | Avoid noisy `Returns:` sections for methods that do not return useful values. |

## 🪵 Logging Pattern

Operational modules that already wrap exceptions should use `boogr.Error` and `boogr.Logger`.

Required pattern:

```python
from boogr import Error, Logger

try:
    # operational logic
    pass
except Exception as e:
    exception = Error(e)
    exception.module = "mappy"
    exception.cause = "ClassOrWorkflowName"
    exception.method = "method_name( self, value: str ) -> ReturnType"
    Logger().write(exception)
    raise exception
```

Use stable method signatures in `exception.method`.

Do not log:

| Do Not Log               | Reason                              |
| ------------------------ | ----------------------------------- |
| API keys                 | Secret value.                       |
| Raw request payloads     | May contain sensitive user input.   |
| Full response payloads   | May contain user or provider data.  |
| Addresses or coordinates | User-provided location data.        |
| DataFrame rows           | May contain uploaded file contents. |
| File contents            | May contain sensitive source data.  |
| Cache keys               | May contain normalized user input.  |

## 🧱 Source File Responsibilities

| File            | Development Responsibility                                        |
| --------------- | ----------------------------------------------------------------- |
| `app.py`        | Streamlit UI and workflow orchestration.                          |
| `caches.py`     | Cache interfaces and implementations.                             |
| `config.py`     | Paths, environment readers, constants, and configuration helpers. |
| `core.py`       | Lightweight result containers and core helpers.                   |
| `distances.py`  | Distance Matrix wrapper and route normalization.                  |
| `excel.py`      | CSV/XLSX read, write, and geospatial enrichment workflows.        |
| `exceptions.py` | Project-specific exception hierarchy.                             |
| `fetchers.py`   | External retrieval classes and fetch utilities.                   |
| `generators.py` | Content-generation classes and provider wrappers.                 |
| `geocode.py`    | Forward, reverse, structured, and batch geocoding.                |
| `maps.py`       | Google Maps request gateway.                                      |
| `places.py`     | Places Text Search and Place Details fallback workflows.          |
| `rates.py`      | Request-rate limiting.                                            |
| `staticmaps.py` | Google Static Maps URL generation.                                |
| `timezones.py`  | Google Time Zone API workflows.                                   |

## 🧭 Adding a New Google Maps Service Wrapper

Use the existing service structure.

1. Add a new module or class.
2. Accept a `Maps` instance in the constructor.
3. Validate required inputs with `throw_if(...)`.
4. Build a small request parameter dictionary.
5. Call `self.maps.request(...)`.
6. Normalize the provider payload into a stable dictionary.
7. Add cache support if repeated calls are likely.
8. Add Google-style docstrings.
9. Add wrapped logging only where the module already uses the project exception pattern.
10. Add an API reference page under `docs/api/`.

Example pattern:

```python
class NewService:
    """Provide a concise service summary.

    Purpose:
        Explain the external workflow this service wraps and the normalized output
        shape it returns.
    """

    def __init__(self, maps: Maps) -> None:
        """Initialize the service wrapper.

        Purpose:
            Store the shared Maps gateway and initialize runtime state.

        Args:
            maps: Google Maps gateway used for service requests.
        """
        self.maps = maps
        self.data = None

    def lookup(self, value: str) -> dict:
        """Resolve one service lookup.

        Purpose:
            Validate the lookup value, call the shared gateway, and normalize the
            provider response into a dictionary.

        Args:
            value: Lookup value to resolve.

        Returns:
            dict: Normalized lookup result.

        Raises:
            Error: Raised after logging when validation or lookup fails.
        """
```

## 📦 Adding a New Cache Backend

New cache backends should follow the `BaseCache` contract.

Required methods:

| Method                      | Expected Behavior                                 |
| --------------------------- | ------------------------------------------------- |
| `get(key)`                  | Return cached dictionary or `None`.               |
| `set(key, value, ttl=None)` | Store dictionary payload.                         |
| `delete(key)`               | Remove one key.                                   |
| `clear(namespace=None)`     | Remove all records or namespace-prefixed records. |
| `contains(key)`             | Return whether a usable record exists.            |
| `stats()`                   | Return backend diagnostics.                       |

## 📊 Adding New Spreadsheet Output Columns

When extending enrichment output:

1. Add the new key to `Excel.create_outputs(...)`.
2. Append a value in `Excel.append_empty(...)`.
3. Append a resolved value in `Excel.append_result(...)`.
4. Confirm row alignment is preserved for every source row.
5. Update `user-guide.md` and API examples if the output is user-facing.

## 🖥️ Streamlit Development Rules

When updating `app.py`:

| Rule                        | Required Practice                                               |
| --------------------------- | --------------------------------------------------------------- |
| Preserve session keys       | Avoid renaming existing keys unless all call sites are updated. |
| Keep UI thin                | Put business logic in service modules.                          |
| Avoid duplicate widget keys | Every repeated widget should have a stable unique key.          |
| Avoid hidden side effects   | Button handlers should clearly update session state.            |
| Keep expensive work gated   | External calls should happen only after explicit user action.   |
| Validate inputs             | Show user-facing warnings before service calls when possible.   |
| Preserve layout             | Avoid broad UI rewrites when only a service change is needed.   |

## 📘 MkDocs Structure

Expected documentation structure:

```text
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

## 🔌 API Reference Page Pattern

Each API reference page should use `mkdocstrings`.

Example for `docs/api/geocode.md`:

```markdown
# Geocoding API

::: geocode
```

Example for `docs/api/maps.md`:

```markdown
# Maps Gateway API

::: maps
```

Example for `docs/api/app.md`:

```markdown
# Application API

::: app
```

## 🧪 Documentation Build

Build documentation locally.

```powershell
mkdocs build
```

Serve documentation locally.

```powershell
mkdocs serve
```

Common issues:

| Error or Warning              | Likely Cause                                                            | Fix                                                        |
| ----------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------- |
| Page exists but is not in nav | A Markdown file exists under `docs/` but is not listed in `mkdocs.yml`. | Add it to `nav` or remove the file.                        |
| Nav page not found            | `mkdocs.yml` references a Markdown file that does not exist.            | Create the file or remove the nav entry.                   |
| Import error in mkdocstrings  | Source module cannot be imported.                                       | Run from repo root and confirm dependencies are installed. |
| API docs missing members      | Docstrings are missing or filters hide members.                         | Check docstrings and `mkdocstrings` options.               |
| Favicon warning               | Config references missing `docs/img/favicon.ico`.                       | Add the file or remove the favicon/logo lines.             |

## 🚀 GitHub Pages Deployment

Build and deploy the site with MkDocs.

```powershell
mkdocs gh-deploy --force
```

Then configure the repository Pages settings to serve from the `gh-pages` branch.

Expected public URL format:

```text
https://is-leeroy-jenkins.github.io/Mappy/
```

If the repository uses a different owner, branch, or name, update `site_url`, `repo_url`, and
`repo_name` in `mkdocs.yml`.

## ✅ Pre-Commit Checklist

Before committing documentation or source updates:

```powershell
python -m compileall .
mkdocs build
```

Review these items:

| Check                                            | Status   |
| ------------------------------------------------ | -------- |
| Source compiles without syntax errors.           | Required |
| No API keys or secrets are committed.            | Required |
| New public methods have Google-style docstrings. | Required |
| `__init__` docstrings do not include `Returns:`. | Required |
| Args sections do not document `self` or `cls`.   | Required |
| Logger writes match wrapped exception paths.     | Required |
| Markdown files referenced in `mkdocs.yml` exist. | Required |
| MkDocs build completes successfully.             | Required |

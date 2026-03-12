# Disaster Event Intelligence API

## Overview

This project is a FastAPI backend for storing, querying, and analysing disaster events.
It provides a local SQL-backed API with full CRUD support, analytics endpoints, and optional ingestion from external public data sources.

The current implementation focuses on:

- wildfire events from NASA EONET
- earthquake events from the USGS Earthquake Catalog
- local analytics over stored records

This project was developed for `COMP3011 Coursework 1`.

## Main Features

- Full CRUD API for the `disaster_events` core data model
- SQLite database persistence
- HTTP Basic Authentication for protected endpoints
- Input validation with Pydantic
- Filtering by source, type, severity, time, and location
- Analytics endpoints for summaries, daily trends, and hotspots
- External ingestion endpoints for NASA EONET and USGS earthquake data
- Source metadata and ingestion history tracking
- Automatic interactive API documentation through FastAPI Swagger UI

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy 2.x
- Pydantic 2.x
- SQLite
- HTTPX
- Pytest

## Project Structure

```text
project/
|-- app/
|   |-- api/routes/
|   |-- crud/
|   |-- db/
|   |-- models/
|   |-- schemas/
|   `-- main.py
|-- test/
|-- app.db
|-- README.md
`-- requirements.txt
```

## Deployment

The API is deployed on Render.

- Base URL: `https://comp3011haoji.onrender.com`
- Swagger UI: `https://comp3011haoji.onrender.com/docs`

## Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If your environment already has a virtual environment, activate that instead.

Optional authentication environment variables:

```powershell
$env:BASIC_AUTH_USERNAME="admin"
$env:BASIC_AUTH_PASSWORD="admin123"
```

You can also create a local `.env` file based on `.env.example`.

## Run The API

```powershell
uvicorn app.main:app --reload
```

If `uvicorn` is not available on your path:

```powershell
python -m uvicorn app.main:app --reload
```

The API will usually be available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Data Model

The main database table is `disaster_events`.
The domain model now uses three main tables:

- `disaster_events` for the core event records
- `source_metadata` for registered upstream sources
- `ingest_runs` for synchronization history and auditability

`disaster_events` fields:

- `id`
- `title`
- `event_type`
- `latitude`
- `longitude`
- `severity`
- `source_id`
- `external_id`
- `event_time`
- `created_at`

## API Endpoints

### CRUD Endpoints

- `POST /events`
- `GET /events`
- `GET /events/{event_id}`
- `PUT /events/{event_id}`
- `PATCH /events/{event_id}`
- `DELETE /events/{event_id}`

### Ingestion Endpoints

- `GET /ingest/eonet/wildfires/preview`
- `POST /ingest/eonet/wildfires/sync`
- `POST /ingest/usgs/earthquakes/sync`
- `GET /ingest/runs`

### Metadata Endpoints

- `GET /sources`

### Analytics Endpoints

- `GET /analytics/summary`
- `GET /analytics/timeseries/daily`
- `GET /analytics/hotspots`

### Health Endpoints

- `GET /health`
- `GET /health/db`

## Authentication

This project uses HTTP Basic Authentication for protected endpoints.

Protected endpoint groups:

- `/events`
- `/ingest`
- `/analytics`

Public endpoints:

- `/health`
- `/health/db`

Default credentials:

- username: `admin`
- password: `admin123`

These default credentials are provided for coursework demonstration only and should be overridden in a real deployment.

Environment variables:

- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`

In Swagger UI:

- open `http://127.0.0.1:8000/docs`
- click `Authorize`
- enter the username and password for Basic Auth

## Example Requests

Create a local event:

```json
POST /events
{
  "title": "Test Wildfire",
  "type": "wildfire",
  "latitude": 34.05,
  "longitude": -118.25,
  "severity": 3,
  "source": "manual",
  "event_time": "2026-03-12T10:00:00"
}
```

Query filtered events:

```text
GET /events?type=wildfire&source=InciWeb&severity_min=2&limit=20
```

Sync wildfire data from NASA EONET:

```text
POST /ingest/eonet/wildfires/sync?days=30&limit=100&status_filter=open
```

Sync earthquake data from USGS:

```text
POST /ingest/usgs/earthquakes/sync?days=30&min_magnitude=4.5&limit=200
```

Get analytics summary:

```text
GET /analytics/summary
```

Check service health:

```text
GET /health
```

## Status Codes

Common status codes used by the API:

- `200 OK` for successful reads, analytics, sync operations, and health checks
- `201 Created` for successful record creation
- `204 No Content` for successful deletion
- `401 Unauthorized` for missing or invalid Basic Authentication credentials
- `404 Not Found` when a record does not exist
- `422 Unprocessable Entity` for validation failures
- `502 Bad Gateway` when an external upstream API request fails
- `503 Service Unavailable` when the database health check fails

## Testing

Run the test suite with:

```powershell
pytest -q
```

Current tests cover:

- CRUD creation and filtered reads
- protected endpoint authentication
- invalid Basic Auth rejection
- public health endpoint access
- database health failure handling
- invalid payload validation
- boundary value validation
- NASA EONET ingestion with mocked upstream data
- duplicate EONET ingestion handling
- external API failure handling for EONET and USGS
- USGS earthquake ingestion with mocked upstream data
- source metadata and ingestion history persistence
- analytics summary, timeseries, and hotspot endpoints
- analytics correctness with controlled fixtures and date filters

## API Documentation

Interactive documentation is available at runtime through FastAPI:

- `http://127.0.0.1:8000/docs`

A PDF copy of the API documentation should be included for submission:

- `docs/api_documentation.pdf`

## Coursework Mapping

This project addresses the coursework requirements in the following ways:

- at least one SQL-backed data model with full CRUD support
- clearer domain modelling with source and ingestion audit tables
- more than four HTTP endpoints
- JSON request and response handling
- appropriate HTTP status and error handling
- local execution for demonstration
- automated tests
- documented authentication process
- API documentation through OpenAPI / Swagger UI

## Notes And Limitations

- The database currently uses SQLite for simplicity and local demonstration.
- External ingestion depends on the availability of NASA EONET and USGS services.
- Basic Authentication uses fixed credentials unless overridden with environment variables.

## Submission Notes

For the coursework submission, this repository should be accompanied by:

- API documentation PDF
- technical report
- GenAI declaration
- presentation slides

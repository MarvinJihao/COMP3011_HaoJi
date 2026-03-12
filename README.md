# Disaster Event Intelligence API

## Overview

This project is a FastAPI-based backend for storing, querying, and analysing disaster events.  
It provides a local SQL-backed API with full CRUD support for disaster records and optional ingestion from external public data sources.

The current implementation focuses on:

- wildfire events from NASA EONET
- earthquake events from the USGS Earthquake Catalog
- local analytics over the stored dataset

This project was developed for COMP3011 Coursework 1.

---

## Main Features

- Full CRUD API for the `fire_events` data model
- SQLite database persistence
- Input validation with Pydantic
- Filtering by source, type, severity, time, and location
- Analytics endpoints for summaries, daily trends, and hotspots
- External ingestion endpoints for NASA EONET and USGS earthquake data
- Automatic interactive API documentation through FastAPI Swagger UI

---

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy 2.x
- Pydantic 2.x
- SQLite
- Pytest
- HTTPX

---

## Project Structure

```
project/
├── app/
│   ├── api/routes/
│   ├── crud/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   └── main.py
├── test/
├── app.db
├── README.md
└── requirements.txt
```

---
## Deployment

The API is deployed on Render and can be accessed publicly.

Base URL:
https://comp3011haoji.onrender.com

Interactive documentation (Swagger UI):
https://comp3011haoji.onrender.com/docs

---

## Setup
From the project root:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If your environment already has a virtual environment, activate that instead.


---

## Run the API
```
uvicorn app.main:app --reload
```
If uvicorn is not available on your path:
```
python -m uvicorn app.main:app --reload
```
The API will usually be available at:
Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

---

## Data Model
The main database table is fire_events.
Fields:
- id
- title
- type
- latitude
- longitude
- severity
- source
- event_time
- created_at

Although the table name is fire_events, it currently stores both wildfire and earthquake records.



---

## API Endpoints
### CRUD Endpoints
- POST /fire-events
- GET /fire-events
- GET /fire-events/{event_id}
- PUT /fire-events/{event_id}
- PATCH /fire-events/{event_id}
- DELETE /fire-events/{event_id}

### Ingestion Endpoints
- GET /ingest/eonet/wildfires/preview
- POST /ingest/eonet/wildfires/sync
- POST /ingest/usgs/earthquakes/sync

### Analytics Endpoints
- GET /analytics/summary
- GET /analytics/timeseries/daily
- GET /analytics/hotspots


---
## Example Request
Create a local event:
```
POST /fire-events

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
```
GET /fire-events?type=wildfire&source=InciWeb&severity_min=2&limit=20
```
Sync wildfire data from NASA EONET:
```
POST /ingest/eonet/wildfires/sync?days=30&limit=100&status_filter=open
```
Sync earthquake data from USGS:
```
POST /ingest/usgs/earthquakes/sync?days=30&min_magnitude=4.5&limit=200
```
Get analytics summary:
```
GET /analytics/summary
```

---

## Status Codes
Common status codes used by the API:
- 200 OK for successful reads, analytics, and sync operations
- 201 Created for successful record creation
- 204 No Content for successful deletion
- 404 Not Found when a record does not exist
- 422 Unprocessable Entity for validation failures
- 502 Bad Gateway when an external upstream API request fails

---
## Testing
Run the test suite with:
```
pytest -q
```
Current tests cover:
- CRUD creation and filtered reads
- NASA EONET ingestion with mocked upstream data
- USGS earthquake ingestion with mocked upstream data
- analytics summary, timeseries, and hotspot endpoints

---
## API Documentation
Interactive documentation is available at runtime through FastAPI:
http://127.0.0.1:8000/docs
A PDF copy of the API documentation should be included for submission:
docs/api_documentation.pdf


---
## Coursework Mapping
This project addresses the coursework requirements in the following ways:
- At least one SQL-backed data model with full CRUD support
- More than four HTTP endpoints
- JSON request and response handling
- Appropriate HTTP status and error handling
- Local execution for demonstration
- Automated tests
- API documentation through OpenAPI / Swagger UI

---
## Notes and Limitations
- The database currently uses SQLite for simplicity and local demonstration.
- External ingestion depends on the availability of NASA EONET and USGS services.
- The table name fire_events is broader in use than its name suggests, because it also stores earthquake records.
- Authentication is not implemented in the current version.


---
## Submission Notes
For the coursework submission, this repository should be accompanied by:
- API documentation PDF
- technical report
- GenAI declaration
- presentation slides


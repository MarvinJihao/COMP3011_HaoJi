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

- Python 3.9+
- FastAPI
- SQLAlchemy 2.x
- Pydantic 2.x
- SQLite
- Pytest
- HTTPX

---

## Project Structure

```text
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

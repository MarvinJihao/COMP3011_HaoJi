# Technical Report

## Disaster Event Intelligence API

Module: COMP3011  
Assessment: Coursework 1  
Author: Jihao Marvin  
Project Title: Disaster Event Intelligence API

## 1. Introduction

This project is a backend API for storing, querying, and analysing disaster events.
The system was designed as a SQL-backed FastAPI application that supports local event management, external data ingestion, metadata tracking, and analytical queries.

This report should be read alongside the supporting repository materials, especially `README.md`, `docs/api_documentation.md`, and `docs/system_design.md`.

The project goes beyond a minimal CRUD implementation by:

- supporting multiple disaster event types rather than a single narrow entity
- integrating external public data sources
- storing source metadata and ingestion history
- providing analytics and risk assessment endpoints over locally stored data

The resulting system is not only able to ingest data, but also to treat that data as part of an independent local application domain.

## 2. Problem Definition

The coursework requires at least one SQL-backed data model with full CRUD support, multiple HTTP endpoints, correct status handling, documentation, and local or hosted execution.

A straightforward solution would have been a simple CRUD API over a single table.
However, this would not have demonstrated a strong level of architectural reasoning.
For that reason, the project was designed around the idea of a disaster event intelligence service, where the API is responsible for:

- persisting event records
- ingesting data from external providers
- tracking data source metadata
- logging ingestion runs
- providing analytics over the local dataset

## 3. Technology Stack and Justification

### 3.1 Python

Python was chosen because it has strong support for web development, data handling, testing, and API integrations.
It also makes rapid prototyping practical while still allowing clear structure and maintainability.

### 3.2 FastAPI

FastAPI was selected as the primary framework because:

- it is lightweight and well suited for API-first systems
- it provides automatic OpenAPI documentation
- it integrates naturally with Pydantic for validation
- it supports dependency injection cleanly

This made it especially suitable for a coursework project where both implementation quality and documentation quality are assessed.

### 3.3 SQLAlchemy

SQLAlchemy was used as the ORM because it provides a robust mapping between Python objects and SQL tables.
It also made it easier to keep database logic separate from the route layer through CRUD modules.

### 3.4 SQLite

SQLite was chosen because the project needed to be easy to run locally and easy to demonstrate.
For coursework scale, SQLite is a pragmatic choice:

- no separate database server is needed
- local setup is simple
- the data model remains relational and SQL-backed

The trade-off is that SQLite is less suitable than PostgreSQL or MySQL for high concurrency and production-scale workloads.

### 3.5 HTTPX

HTTPX was used for external API ingestion because it offers a clean interface for outbound HTTP requests and integrates well into Python web applications.

### 3.6 Pytest

Pytest was used to verify functional correctness across authentication, CRUD behaviour, upstream failures, and analytics logic.

## 4. System Design

The architecture follows a layered approach:

- route layer for HTTP request handling
- dependency layer for authentication
- CRUD layer for data access and persistence logic
- model layer for SQLAlchemy entities
- schema layer for request and response validation
- database session layer for connection management

This structure makes the code easier to reason about and supports clearer explanation during assessment.

### 4.1 Domain Model

The system uses three main entities:

- `disaster_events`
- `source_metadata`
- `ingest_runs`

This is an important improvement over the earlier single-table design.
Initially, the project concept was closer to `fire_events`, but once earthquake ingestion was introduced, that name no longer matched the problem domain.
Refactoring to `disaster_events` created a cleaner and more extensible model.

### 4.2 Disaster Events

The `disaster_events` table stores the main event records used by the API.

It includes:

- title
- event type
- coordinates
- severity
- source reference
- external identifier
- event time

This table is the system of record for the application.

### 4.3 Source Metadata

The `source_metadata` table stores information about registered event sources.

This was added to avoid repeating source information directly on every event row and to make the architecture more expressive.
It also allows the project to distinguish between event data and source identity.

### 4.4 Ingest Runs

The `ingest_runs` table records synchronization attempts.

Each run stores:

- provider
- dataset
- status
- inserted / skipped / failed counts
- serialized filter parameters
- timestamps

This provides observability and auditability, which gives the project a more mature architecture than a minimal CRUD-only API.

## 5. API Design

The API is grouped into four areas:

Full endpoint definitions, example requests, and response formats are documented separately in `docs/api_documentation.md`.

### 5.1 Events

The Events module provides the core CRUD functionality:

- create events
- list events
- retrieve by ID
- replace records
- patch records
- delete records

This is the centre of the application and satisfies the coursework CRUD requirement.

### 5.2 Ingest

The Ingest module imports data from:

- NASA EONET for wildfires
- USGS Earthquake Catalog for earthquakes

These external APIs are treated as data suppliers rather than as the system's live backing store.
The ingested data is transformed and persisted locally.

### 5.3 Analytics

The Analytics module provides:

- summary statistics
- daily timeseries
- spatial hotspots
- risk assessment

This elevates the project beyond basic CRUD by providing interpretation and intelligence over the dataset.

### 5.4 Health

The Health module provides:

- service health status
- database connectivity checks

These endpoints are intentionally public so that deployment verification and monitoring can happen without authentication barriers.

## 6. Authentication Design

The system implements HTTP Basic Authentication on the backend.

This is enforced via a FastAPI dependency that:

- reads the `Authorization` header
- extracts Basic Auth credentials
- validates them against configured values
- returns `401 Unauthorized` if validation fails

Protected route groups are:

- `/events`
- `/ingest`
- `/analytics`

Public route groups are:

- `/health`
- `/health/db`

Basic Authentication was chosen because it is simple, standards-based, easy to document, and sufficient for coursework demonstration.

If this system were extended further, a more production-ready choice would be token-based authentication or role-based access control.

## 7. External Data Integration

Two public external APIs are integrated:

### 7.1 NASA EONET

Used for wildfire event ingestion.

The API data is:

- previewed through a non-persistent endpoint
- synchronized through a persistent ingestion endpoint

### 7.2 USGS Earthquake Catalog

Used for earthquake event ingestion.

The API data is transformed into the local disaster event format and then stored.

### 7.3 Why Local Persistence Matters

The project does not merely proxy upstream APIs.
Instead, it persists the data in a local SQL database and performs analytics on local records.
This design is more aligned with the coursework requirement to build a real API system rather than a thin wrapper over third-party services.

## 8. Error Handling

The API uses conventional HTTP status codes:

- `200 OK`
- `201 Created`
- `204 No Content`
- `401 Unauthorized`
- `404 Not Found`
- `422 Unprocessable Entity`
- `502 Bad Gateway`
- `503 Service Unavailable`

Examples:

- invalid credentials produce `401`
- invalid payloads produce `422`
- missing event IDs produce `404`
- upstream provider failures produce `502`
- database health failures produce `503`

This supports both correctness and clarity in documentation and testing.

## 9. Testing Approach

The test suite was designed to cover both success and failure scenarios.

Covered areas include:

- CRUD creation and filtered reads
- authentication failures
- invalid payloads
- boundary values
- duplicate ingestion handling
- upstream provider failures
- public health checks
- database failure handling
- analytics correctness under controlled fixtures
- risk assessment ranking logic

This test coverage is important because it demonstrates not just that the endpoints exist, but that the application behaves predictably under realistic scenarios.

## 10. Deployment

The application is deployable locally and has also been hosted remotely.

The deployment model uses:

- FastAPI as an ASGI application
- `uvicorn` as the application server
- PythonAnywhere hosting for remote availability

This allows both local testing and live demonstration through `/docs`.
Practical setup, execution, and deployment notes are also summarised in `README.md`.

## 11. Challenges Encountered

Several practical challenges arose during development:

### 11.1 Domain Refactoring

The original model naming was too narrow once earthquake support was added.
Renaming the conceptual model to `disaster_events` improved the architecture, but required cleanup of routes, schemas, and documentation.

### 11.2 External API Variability

External APIs do not always return uniform records.
Some events may have missing fields, unusual geometry formats, or values that need transformation.
This required careful ingestion logic and duplicate detection.

### 11.3 Documentation Quality

FastAPI generates useful API documentation automatically, but a submission-ready coursework package still requires more curated documentation.
This led to the creation of additional written documents such as API documentation and system design notes.

### 11.4 Deployment Practicalities

Deploying an ASGI app to PythonAnywhere introduced platform-specific steps, including environment setup, command configuration, and reload workflow.

## 12. Limitations

The current system has several limitations:

- SQLite is suitable for coursework but not ideal for larger-scale production systems
- authentication is intentionally basic and does not support roles or tokens
- external ingestion depends on the availability and structure of third-party APIs
- ingest runs and events are logically related, but not linked through a direct foreign key
- risk scoring is heuristic rather than scientifically validated

These limitations are acceptable for the coursework scope, but they also identify clear opportunities for future work.

## 13. Future Improvements

Potential future extensions include:

- replacing SQLite with PostgreSQL
- adding background scheduled sync jobs
- introducing anomaly detection in addition to risk scoring
- implementing role-based or token-based authentication
- improving source metadata richness
- adding pagination metadata and more advanced filtering
- introducing geospatial indexing for location-heavy analytics

## 14. Reflection on Design Choices

The final design reflects a conscious shift from a minimal CRUD API to a more complete backend application.
The introduction of source metadata, ingestion history, analytics, and risk assessment makes the project easier to justify as a cohesive system rather than a collection of independent endpoints.

In particular, the strongest design improvements were:

- generalising the domain model to `disaster_events`
- separating source metadata from event records
- introducing audit-style ingestion tracking
- adding analytical value beyond data storage

These changes made the project more aligned with the higher marking bands in the assessment criteria.

## 15. Generative AI Declaration

Generative AI tools were used during the development of this coursework in a declared and methodical way.

AI was used for:

- planning implementation steps
- discussing design alternatives
- explaining external API documentation
- suggesting test scenarios
- refining written documentation

AI was not used as an unquestioned source of truth.
All generated suggestions were reviewed, adapted, and integrated manually into the final implementation.

The main benefit of AI use in this project was acceleration of exploration and structured reasoning, especially when comparing architectural options and improving testing scope.

This use aligns more closely with a methodological and design-support role rather than arbitrary code generation.

## 16. Conclusion

This project satisfies the coursework's core technical requirements while also demonstrating a more developed system design than a minimal CRUD submission.

The final application provides:

- SQL-backed CRUD functionality
- external data ingestion
- source metadata management
- ingestion audit history
- analytics and risk assessment
- authentication
- testing
- deployment support

Overall, the project represents a structured and extensible disaster event intelligence API that is suitable for coursework demonstration and discussion.

## 17. References

- FastAPI. Available at: https://fastapi.tiangolo.com/ [Accessed 19 March 2026].
- SQLAlchemy. Available at: https://docs.sqlalchemy.org/ [Accessed 19 March 2026].
- Pydantic. Available at: https://docs.pydantic.dev/ [Accessed 19 March 2026].
- HTTPX. Available at: https://www.python-httpx.org/ [Accessed 19 March 2026].
- NASA EONET Version 3 Documentation. Available at: https://eonet.gsfc.nasa.gov/docs/v3 [Accessed 19 March 2026].
- USGS Earthquake Catalog API Documentation. Available at: https://earthquake.usgs.gov/fdsnws/event/1/ [Accessed 19 March 2026].
- PythonAnywhere Help. Available at: https://help.pythonanywhere.com/ [Accessed 19 March 2026].

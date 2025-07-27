# Active Context

## Current Goals

- Scraper module requirements and integration points: 1) All job deduplication, insertion, and status updates must use the data access layer (job_database.py/data_service.py). 2) Scraper orchestration should use async worker pools. 3) Deduplicate jobs using a unique job ID (hash of URL + title). 4) Push new jobs to Redis queue. 5) Insert/update job metadata in SQLite with status 'queued'. 6) Log errors to SQLite and optionally to a dead-letter queue. 7) No direct DB schema changes in pipeline code.

## Current Blockers

- None yet
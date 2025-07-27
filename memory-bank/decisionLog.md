# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-07-26 | Use sqlite-utils for schema creation and management in the job scraper pipeline. | sqlite-utils provides a robust, Pythonic API for explicit schema definition, index management, and type safety. It supports best practices for index creation, foreign keys, and strict mode, which aligns with the pipeline's requirements for deduplication, error logging, and dashboard integration. |
| 2025-07-26 | Define jobs table schema with explicit types and indexes for the job scraper pipeline. | Explicitly defining the schema ensures data integrity, deduplication, and efficient querying. Indexes on id, status, and frequently queried fields will optimize performance for dashboard and pipeline operations. |
| 2025-07-26 | Scraper module will be implemented to use only the data access layer for all database operations, orchestrated via async worker pools, with deduplication, Redis queueing, and error logging as per the overhaul plan. | This ensures compatibility with the existing system, prevents direct DB access, and supports scalability, observability, and maintainability. |

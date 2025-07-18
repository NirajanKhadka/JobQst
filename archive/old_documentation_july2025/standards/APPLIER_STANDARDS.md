---
post_title: "Application Applier Module Standards"
author1: "Nirajan Khadka"
post_slug: "applier-standards"
microsoft_alias: "nirajank"
featured_image: ""
categories: ["standards", "applier"]
tags: ["applier", "automation", "quality"]
ai_note: "Module-specific standards for the application applier/orchestration code."
summary: "Rules and best practices for the application applier/orchestration system in AutoJobAgent."
post_date: "2025-07-04"
---

> **Under any circumstances, the user should ask the AI to edit these standards.**

# 🤖 Application Applier Module Standards

## Purpose
This document defines all coding, documentation, and quality standards for the application applier/orchestration system in AutoJobAgent. All applier code must comply with these rules in addition to the overall project quality gates.

## Python Rules
- Use descriptive, intent-revealing names for all classes, functions, and variables.
- All applier services must implement clear interfaces for queuing, processing, and status tracking.
- No global variables; use dependency injection for configuration and state.
- Use type hints for all functions and method signatures.
- All public functions/classes must have docstrings.
- Limit orchestration and worker functions to 30 lines or less.
- Handle all network, file, and API errors with retries, logging, and user feedback.
- Never hardcode credentials or API keys.
- All retry logic must be idempotent and safe for repeated execution.
- All concurrency (threads, async, processes) must be safe and avoid race conditions.
- All configuration (API keys, endpoints, limits) must be managed via environment variables or config files.

## Observability & Logging
- All applier operations must log key events (queue, start, complete, fail, retry) with timestamps.
- Expose metrics for queue length, processing rate, error rate, and retries.
- All logs must avoid sensitive data.

## Documentation & Comments
- Every applier class/function must have a docstring explaining its workflow and logic.
- Inline comments for any non-obvious orchestration or retry logic.
- Document all required environment variables or config options.

## Testing & Quality
- All applier logic must be covered by unit and integration tests.
- No placeholder/fake data in production workflows.
- All changes must be reviewed for concurrency, error handling, and idempotency.

## Performance
- Use async, batching, or worker pools for high-throughput processing.
- Minimize memory and CPU usage (avoid unbounded queues or threads).
- Profile applier performance with cProfile or Py-Spy.

## Security
- Validate and sanitize all job and profile data before processing.
- Never expose sensitive data in logs or status messages.

---

> For project-wide quality gates, see DEVELOPMENT_STANDARDS.md.

---
post_title: "Document Generation Module Standards"
author1: "Nirajan Khadka"
post_slug: "docgen-standards"
microsoft_alias: "nirajank"
featured_image: ""
categories: ["standards", "docgen"]
tags: ["document generation", "resume", "cover letter", "quality"]
ai_note: "Module-specific standards for document generation code and documentation."
summary: "Rules and best practices for document generation in AutoJobAgent."
post_date: "2025-07-04"
---

> **Under any circumstances, the user should ask the AI to edit these standards.**

# 📄 Document Generation Module Standards

## Purpose
This document defines all coding, documentation, and quality standards for document generation (resume, cover letter, PDF, etc.) in AutoJobAgent. All docgen code must comply with these rules in addition to the overall project quality gates.

## Python Rules
- Use descriptive, intent-revealing names for all classes, functions, and variables.
- All document generators must use real profile data (no placeholders).
- Use type hints for all functions and method signatures.
- All public functions/classes must have docstrings.
- Limit document generation functions to 30 lines or less.
- Handle all file I/O and API errors with clear messages and logging.
- Never hardcode credentials or API keys.
- All templates must be managed in a modular, extensible way (supporting new formats easily).
- All output must be validated for ATS compatibility and professional formatting.
- All generated files must follow a consistent naming/versioning convention (e.g., `Name_Role_YYYYMMDD.pdf`).

## Documentation & Comments
- Every generator class/function must have a docstring explaining its output and logic.
- Inline comments for any non-obvious formatting or template logic.
- Document all required environment variables or config options.

## Testing & Quality
- All document generation logic must be covered by unit or integration tests.
- No placeholder/fake data in generated documents.
- All output must be reviewed for ATS compatibility and professional formatting.

## Performance
- Optimize for fast document creation (profile with cProfile or Py-Spy).
- Minimize memory usage (avoid loading large templates into memory if not needed).

## Security
- Never include sensitive data in generated documents unless explicitly required.
- Validate and sanitize all input data used in document generation.

---

> For project-wide quality gates, see DEVELOPMENT_STANDARDS.md.

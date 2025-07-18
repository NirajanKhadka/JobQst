---
post_title: "Dashboard Module Standards"
author1: "Nirajan Khadka"
post_slug: "dashboard-standards"
microsoft_alias: "nirajank"
featured_image: ""
categories: ["standards", "dashboard"]
tags: ["dashboard", "streamlit", "ui", "quality"]
ai_note: "Module-specific standards for dashboard code and documentation."
summary: "Rules and best practices for dashboard/UI code in AutoJobAgent."
post_date: "2025-07-04"
---

> **Under any circumstances, the user should ask the AI to edit these standards.**

# 🖥️ Dashboard Module Standards

## Purpose
This document defines all coding, documentation, and quality standards for the dashboard (UI) components of AutoJobAgent. All dashboard code must comply with these rules in addition to the overall project quality gates.

## Python & Streamlit Rules
- Use descriptive, intent-revealing names for all UI elements and callbacks.
- All Streamlit widgets must have unique keys.
- Avoid global state; use session state or dependency injection.
- UI logic and business logic must be separated (no data processing in UI callbacks).
- Use type hints for all functions.
- All public functions/classes must have docstrings.
- Limit UI callback functions to 30 lines or less.
- Use early returns to reduce nesting in callbacks.
- Handle all user input validation and error display gracefully.
- All UI must be responsive and work across major browsers and devices.
- State management must be explicit and predictable (use Streamlit session state or equivalent).

## Documentation & Comments
- Every dashboard component must have a docstring explaining its purpose.
- Inline comments for any non-obvious UI logic.
- Document all custom Streamlit components or wrappers.

## Testing & Quality
- All dashboard logic must be covered by integration or UI tests where feasible.
- No placeholder/fake data in production UI.
- All UI changes must be reviewed for accessibility, responsiveness, and cross-browser compatibility.
- All UI must handle errors gracefully and provide clear user feedback (error boundaries, notifications, etc.).

## Performance
- Minimize unnecessary re-renders (use st.session_state, memoization, etc.).
- Avoid blocking the main thread with heavy computation.
- Profile UI performance with Streamlit profiler or browser dev tools.

## Security
- Never expose sensitive data in the UI.
- Validate and sanitize all user inputs.

---

> For project-wide quality gates, see DEVELOPMENT_STANDARDS.md.

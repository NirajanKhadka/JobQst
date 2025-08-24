# JobLens Dashboard - Incremental Implementation Plan

This document outlines the phased implementation plan for the new JobLens dashboard, built with FastAPI and React, leveraging the existing PostgreSQL database and backend logic.

---

## 🚀 **Phase 1: Core Foundation & API**

**Goal:** Establish the backend API and a basic frontend to display jobs from the existing PostgreSQL database. This phase focuses on creating a solid, working foundation.

### **1. Project Structure Setup**

First, we'll create the new directory structure for the dashboard to keep the backend and frontend code separate and organized.

```
automate_job/
├── dashboard/
│   ├── backend/         # FastAPI application
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── v1/
│   │   │   │       ├── endpoints/
│   │   │   │       │   ├── jobs.py
│   │   │   │       │   └── profiles.py
│   │   │   │       └── api.py
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   └── db.py      # PostgreSQL connection
│   │   │   ├── schemas/
│   │   │   │   └── job.py
│   │   │   └── main.py
│   │   ├── .env
│   │   └── requirements.txt
│   └── frontend/        # React application
│       ├── public/
│       ├── src/
│       │   ├── components/
│       │   │   └── JobTable.tsx
│       │   ├── hooks/
│       │   │   └── useJobs.ts
│       │   ├── services/
│       │   │   └── api.ts
│       │   ├── App.tsx
│       │   └── main.tsx
│       ├── index.html
│       ├── package.json
│       └── tsconfig.json
└── src/
    └── ... (existing core logic)
```

### **2. Backend Development (FastAPI)**

The backend will serve as the bridge between the frontend and your existing system logic.

#### **Key Tasks:**

1.  **Initialize FastAPI App:**
    *   Set up `dashboard/backend/app/main.py`.
    *   Configure CORS (Cross-Origin Resource Sharing) to allow requests from the React frontend.

2.  **Database Connection:**
    *   Create `dashboard/backend/app/core/db.py`.
    *   This module will **import and reuse your existing `PostgreSQLJobDatabase` class** from `src.core.postgresql_database`.
    *   It will manage the connection lifecycle for the API.

3.  **API Endpoints:**
    *   **/api/v1/profiles**:
        *   **Action:** Fetches the list of available user profiles.
        *   **Integration:** Calls the existing `UserProfileManager` to get profile names.
        *   **Response:** `["Nirajan", "Nirmala", "default"]`
    *   **/api/v1/jobs/{profile_name}**:
        *   **Action:** Fetches all jobs for a given profile.
        *   **Integration:** Uses `PostgreSQLJobDatabase(profile_name).get_all_jobs()`.
        *   **Response:** A JSON array of job objects.

4.  **Dependencies:**
    *   Create `dashboard/backend/requirements.txt`:
        ```
        fastapi
        uvicorn[standard]
        psycopg2-binary
        pydantic
        python-dotenv
        ```

### **3. Frontend Development (React)**

The frontend will provide a clean, modern interface to view the data served by the FastAPI backend.

#### **Key Tasks:**

1.  **Initialize React App:**
    *   Use Vite with the TypeScript template to set up the project in `dashboard/frontend/`.
    *   Install necessary packages: `axios` (for API calls) and `@mui/material`, `@mui/x-data-grid` (for UI components).

2.  **API Service:**
    *   Create `dashboard/frontend/src/services/api.ts` to manage all communication with the backend.
    *   Define functions like `getProfiles()` and `getJobs(profileName)`.

3.  **UI Components:**
    *   **Profile Selector:** A simple dropdown/select component to list and choose a user profile.
    *   **Job Table:**
        *   Use the Material-UI `DataGrid` component for a powerful, Excel-like table out of the box.
        *   Display key job information: `title`, `company`, `location`, `status`, `match_score`.
        *   The table will be read-only in this phase.

4.  **Application State:**
    *   Use React's built-in state management (`useState`, `useEffect`) for this phase.
    *   Fetch profiles on initial load.
    *   When a profile is selected, fetch the corresponding jobs and update the `DataGrid`.

### **5. Phase 1 Deliverables**

At the end of Phase 1, we will have:

-   ✅ A running FastAPI server that serves profiles and job data from your PostgreSQL database.
-   ✅ A running React application that displays a list of profiles.
-   ✅ A functional jobs table that shows all jobs for the selected profile.
-   ✅ A solid and scalable foundation for adding more complex features in the next phases.

---

This incremental approach ensures we have a working, valuable piece of the application at the end of each phase, minimizing risk and allowing for continuous feedback.

---

## 🎭 **Phase 2: Interactive Job & Application Tracking**

**Goal:** Transform the read-only dashboard into an interactive tool for managing jobs and tracking applications manually.

### **1. Backend Development (FastAPI)**

We'll expand the API to handle job creation, status updates, and application tracking.

#### **New API Endpoints:**

*   **`POST /api/v1/jobs/{profile_name}`**:
    *   **Action:** Adds a new job manually to a specific profile.
    *   **Payload:** `{ "title": "...", "company": "...", "url": "...", ... }`
    *   **Integration:** Calls `PostgreSQLJobDatabase(profile_name).add_job(job_data)`.
*   **`PATCH /api/v1/jobs/{job_id}/status`**:
    *   **Action:** Updates the status of a single job (`status` field).
    *   **Payload:** `{ "status": "Interested" }`
    *   **Integration:** Calls `PostgreSQLJobDatabase.update_job_status(job_id, new_status)`.
*   **`PATCH /api/v1/applications/{job_id}/status`**:
    *   **Action:** Updates the application tracking status (`application_status` field).
    *   **Payload:** `{ "application_status": "Applied", "notes": "Applied via company website." }`
    *   **Integration:** Calls `PostgreSQLJobDatabase.update_application_status(job_id, new_status, notes)`.
*   **`POST /api/v1/jobs/bulk-update`**:
    *   **Action:** Performs a bulk action on multiple jobs (e.g., update status).
    *   **Payload:** `{ "job_ids": [1, 2, 3], "action": "archive" }`

### **2. Frontend Development (React)**

The frontend will be enhanced with forms, modals, and interactive elements to use the new API endpoints.

#### **Key UI/UX Enhancements:**

1.  **"Add Job" Functionality:**
    *   An "Add Job" button that opens a modal form.
    *   The form will capture all necessary job details and post to the new `/jobs` endpoint.

2.  **Interactive Job Table:**
    *   **Status Dropdown:** Each row will have a dropdown to quickly change the job's `status` (e.g., New, Interested, Archived).
    *   **Checkbox Selection:** Add checkboxes to each row to enable bulk actions.
    *   **Bulk Action Bar:** A toolbar that appears when jobs are selected, offering options like "Archive Selected" or "Mark as Interested".

3.  **Job Details View & Application Tracker:**
    *   Clicking a job row will open a detailed view (either a modal or a side panel).
    *   This view will display all job information.
    *   It will feature a dedicated **Application Tracker** section.
    *   The tracker will have a dropdown to update the `application_status` (e.g., Not Applied, Applied, Interviewing, Offer, Rejected).
    *   A text area will allow adding notes for each application step.

### **3. Phase 2 Deliverables**

-   ✅ Users can manually add new jobs to their profile through the dashboard.
-   ✅ Users can change the status of individual jobs directly from the table.
-   ✅ Users can select multiple jobs and perform bulk actions.
-   ✅ A detailed view for each job allows for comprehensive application tracking with status and notes.

---

## 🎮 **Phase 3: Scraper & Processor Control**

**Goal:** Integrate control and monitoring of your powerful backend scrapers and processors directly into the dashboard.

### **1. Backend Development (FastAPI)**

This involves creating endpoints to trigger and monitor your existing Python scripts and services. We'll use background tasks to prevent blocking the API.

#### **New API Endpoints:**

*   **`POST /api/v1/scrapers/start`**:
    *   **Action:** Starts a scraping process.
    *   **Payload:** `{ "profile_name": "...", "keywords": [...], "sites": [...] }`
    *   **Integration:** Uses `asyncio.create_subprocess_exec` or a similar method to run your `multi_site_jobspy_workers.py` script as a background process.
*   **`POST /api/v1/processors/start`**:
    *   **Action:** Starts the job processing pipeline for new jobs.
    *   **Payload:** `{ "profile_name": "..." }`
    *   **Integration:** Triggers your `enhanced_fast_job_pipeline.py` as a background task.
*   **`GET /api/v1/system/status`**:
    *   **Action:** Provides a real-time status of ongoing backend processes.
    *   **Integration:** This will require a mechanism to share state between the main API and the background tasks. A simple file-based status flag or a lightweight in-memory cache (like `cachetools`) can work since you're avoiding Redis.
    *   **Response:** `{ "scraper_active": true, "processor_active": false, "last_scrape": "..." }`

### **2. Frontend Development (React)**

A new "Control Panel" or "System" tab will be added to house these new features.

#### **Key UI/UX Enhancements:**

1.  **Scraper Control Form:**
    *   A simple form to input keywords, select job sites, and choose a profile.
    *   A "Start Scraping" button that calls the `/scrapers/start` endpoint.
    *   The button will be disabled if a scraping process is already active.

2.  **Processor Control:**
    *   A "Process New Jobs" button that calls the `/processors/start` endpoint.
    *   This button will be disabled if a processing task is running.

3.  **Live Status Dashboard:**
    *   A dedicated section that polls the `/system/status` endpoint every few seconds.
    *   Displays visual indicators (e.g., spinning icons, status text) for active scrapers and processors.
    *   Shows key information like "Last scraped: 5 minutes ago" or "Processor: Analyzing 50 jobs".
    *   The main jobs table will have an auto-refresh mechanism (or a manual refresh button) to show newly scraped jobs.

### **3. Phase 3 Deliverables**

-   ✅ Users can initiate job scraping directly from the dashboard.
-   ✅ Users can start the job processing pipeline from the dashboard.
-   ✅ The dashboard provides clear, real-time feedback on whether backend tasks are running.
-   ✅ The jobs list updates to reflect the results of scraping and processing tasks.

---

## 📊 **Phase 4: Analytics & Visualization**

**Goal:** Provide users with valuable insights into their job search through data visualization.

### **1. Backend Development (FastAPI)**

Create new endpoints specifically for aggregated analytics data. These endpoints will perform efficient queries on your PostgreSQL database.

#### **New API Endpoints:**

*   **`GET /api/v1/analytics/{profile_name}/summary`**:
    *   **Action:** Returns key metrics like total jobs, application count, interview rate, etc.
    *   **Integration:** Runs aggregate SQL queries (`COUNT`, `AVG`) on the `jobs` table.
*   **`GET /api/v1/analytics/{profile_name}/status-distribution`**:
    *   **Action:** Returns the number of jobs in each application status category.
    *   **Integration:** Uses a `GROUP BY application_status` query.
*   **`GET /api/v1/analytics/{profile_name}/jobs-over-time`**:
    *   **Action:** Returns the number of jobs added per day/week over a period.
    *   **Integration:** Uses date functions and `GROUP BY` on the `created_at` field.

### **2. Frontend Development (React)**

A new "Analytics" tab will be created to display the charts and stats.

#### **Key UI/UX Enhancements:**

1.  **Install Charting Library:**
    *   Add a library like `Recharts` or `Chart.js` to the React project.

2.  **Analytics Dashboard Components:**
    *   **Key Metrics Cards:** Display the summary stats in a clear, prominent way (e.g., "89 Applications", "12 Interviews").
    *   **Application Funnel Chart:** A bar or funnel chart showing the `status-distribution` data.
    *   **Jobs Over Time Line Chart:** A line chart visualizing the `jobs-over-time` data.
    *   **Filters:** Allow users to filter the analytics by date range.

### **4. Phase 4 Deliverables**

-   ✅ A dedicated Analytics tab in the dashboard.
-   ✅ Key performance indicators (KPIs) for the user's job search.
-   ✅ Visual charts to help users understand their progress and identify trends.
-   ✅ A more engaging and insightful user experience that goes beyond simple data display.

---

## 🏁 **Phase 5: Benchmarks & Performance Monitoring**

**Goal:** Provide real-time and historical benchmarking of system performance, including job processing speed, database throughput, and scraper efficiency.

### **1. Backend Development (FastAPI)**

Create new endpoints to collect and serve benchmark data:

- **`GET /api/v1/benchmarks/processing`**:
    - **Action:** Returns metrics on job processing speed (jobs/sec, avg. time per job, max batch size).
    - **Integration:** Collects timing and throughput data from the processor pipeline and stores in PostgreSQL.
- **`GET /api/v1/benchmarks/database`**:
    - **Action:** Returns database performance metrics (query latency, write speed, connection pool usage).
    - **Integration:** Uses periodic test queries and logs to measure DB performance.
- **`GET /api/v1/benchmarks/scrapers`**:
    - **Action:** Returns scraper throughput (jobs/min per site, error rates, success rates).
    - **Integration:** Aggregates stats from scraper runs and logs.

### **2. Frontend Development (React)**

Add a new "Benchmarks" tab to the dashboard:

- **Processing Speed Panel:**
    - Real-time chart of jobs processed per second/minute.
    - Historical trends (last hour, day, week).
    - Display max, min, and average batch sizes.
- **Database Performance Panel:**
    - Show query latency, write speed, and connection pool usage.
    - Visualize spikes or slowdowns over time.
- **Scraper Throughput Panel:**
    - Per-site jobs/min, error rates, and success rates.
    - Compare performance across sites and time periods.
- **Benchmark History:**
    - Table or chart of previous benchmark runs for reference.

### **5. Phase 5 Deliverables**

-   ✅ A "Benchmarks" tab in the dashboard for real-time and historical performance monitoring.
-   ✅ API endpoints and backend logic to collect, store, and serve benchmark data.
-   ✅ Visual charts and tables showing job processing speed, database performance, and scraper throughput.
-   ✅ Actionable insights to help optimize and scale the system.


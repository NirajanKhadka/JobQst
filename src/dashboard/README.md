## Worker Pool & Orchestration Controls

The dashboard now includes a Worker Pool section for real-time management of all job processing workers:

- **Worker Pool Table:**
  - Lists all workers with name, description, status, CPU/memory usage, and uptime.
  - Start/Stop buttons for each worker.
  - Total, running, and stopped worker counts.

- **Orchestration Controls:**
  - Start All, Stop All, and Restart All buttons for bulk management.
  - Buttons are disabled while actions are in progress.

- **Real-Time Updates:**
  - WebSocket connection to `/ws` keeps the UI in sync with backend changes.

### API Endpoints
- `POST /api/system/start_worker` — Start a worker
- `POST /api/system/stop_worker` — Stop a worker
- `GET /api/system/worker_status` — Get all worker statuses
- `POST /api/system/start_all_workers` — Start all workers
- `POST /api/system/stop_all_workers` — Stop all workers
- `POST /api/system/restart_all_workers` — Restart all workers

### Usage
- Use the Worker Pool section to view and control workers individually or in bulk.
- All changes are reflected in real time via WebSocket.

For detailed architecture and integration, see [../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) and [components/README.md](components/README.md). 
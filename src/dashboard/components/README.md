## Worker Pool & Orchestration Controls Component

This component provides real-time management of all job processing workers:

- Lists all workers with name, description, status, CPU/memory usage, and uptime.
- Start/Stop buttons for each worker.
- Start All, Stop All, and Restart All buttons for bulk management.
- UI updates in real time via WebSocket messages from the backend.

### Integration
- Uses `/api/system/worker_status` for initial data.
- Sends POST requests to `/api/system/start_worker`, `/stop_worker`, `/start_all_workers`, `/stop_all_workers`, `/restart_all_workers` for control actions.
- Listens to `/ws` WebSocket for live updates.

### Extensibility
- New worker types or controls can be added by updating the backend worker descriptions and script mappings, and extending the UI table. 
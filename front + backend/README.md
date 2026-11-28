# Designing-an-AI-Assisted-Security-Operations-Center
The intended approach to this problem is an MCP server scanner that can cover most bases: MCP server code, permissions, and runtime behavior to name a few. This scanner will look for vulnerabilities, patterns in behavior, and changes in expected behavior to report on them. Vulnerabilities will be sorted by threat levels.


## Running the front end and back end together

1. Start the backend (from `backend/`): `uvicorn app.main:app --port 8000`
2. Start the UI (from `scanner frontend/`): `python main.py`

The UI has no built-in data. Everything it shows comes from the backend:

| UI action | Backend endpoint | Where the data comes from |
|---|---|---|
| Load the dashboard | `GET /api/v1/servers/` | Stored security events, grouped by `raw_event["server"]` |
| "New scan" button | `POST /api/v1/scans/` | Saved as a `queued` row in `scan_requests` |

Scanner results get into the database through `POST /api/v1/events/` (or `/api/v1/alerts/wazuh`).
Put the scanner's details in `raw_event`: `server`, `tool`, `category`, `evidence` (`static`, `runtime`, `ai`), `recommendation`.
An empty database shows an empty dashboard. To use another backend address, set `SCANNER_API_URL`.

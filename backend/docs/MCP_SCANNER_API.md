# MCP Scanner → AI-Assisted SOC API Contract

**Project:** Designing an AI-Assisted Security Operations Center  
**Scope:** Existing MCP scanner endpoints on `LLM-branch`  
**Integration status:** Backend verified with synthetic scanner findings and a live Gemini analysis. Integration with the team's actual MCP scanner remains to be tested.

## Overview

The MCP scanner sends a finding to the SOC backend. The backend saves the original finding in SQLite. A separate request triggers Gemini analysis: the adapter makes a sanitized copy of the finding, sends that copy to Gemini, validates the structured response, and stores the resulting analysis or a failure status.

```text
MCP scanner → POST finding → SQLite
                              ↓
                   POST finding/{id}/analyze
                              ↓
                    sanitize → Gemini
                              ↓
                  save completed/failed result
                              ↓
                   GET finding/{id}/analyses
```

**Important:** Posting a finding does **not** automatically run Gemini analysis. The scanner/integrator must call the separate analysis endpoint.

## Base URL and authentication

Local development base URL: `http://127.0.0.1:8000/api/v1/scanner`

All endpoints in this document require the HTTP request header:

```http
X-API-Key: <SOC_API_KEY>
```

The backend reads `SOC_API_KEY` from the local project-root `.env` file. Do not commit this key, put it in source code, or share it in logs/screenshots. Use HTTPS if the service is exposed beyond localhost. The `GEMINI_API_KEY` is a different secret used only by the backend to contact Gemini.

## 1. Submit a finding

`POST /findings` → `201 Created` on success.

Request body (synthetic example):

```json
{
  "finding_id": "MCP-E2E-002",
  "source": "mcp_runtime",
  "target": "test-mcp-server",
  "tool_name": "read_configuration",
  "category": "unauthorized_access",
  "title": "MCP tool attempted unauthorized file access",
  "description": "A tool attempted to read configuration files outside its permitted directory.",
  "scanner_severity": "high",
  "evidence": [
    "Sandbox detected an attempted read of a restricted directory.",
    "The tool declaration did not authorize the access."
  ]
}
```

### Input fields and validation

| Field | Required | Format / constraint |
| --- | --- | --- |
| `finding_id` | Yes | Nonempty string, max 100 characters; scanner-defined identifier |
| `source` | Yes | Nonempty string, max 100 characters |
| `target` | Yes | Nonempty string, max 200 characters |
| `tool_name` | No | String up to 200 characters, or `null` |
| `category` | Yes | Nonempty string, max 100 characters |
| `title` | Yes | Nonempty string, max 200 characters |
| `description` | Yes | Nonempty string, max 4,000 characters |
| `scanner_severity` | No | String, integer, or `null`; not yet normalized to a shared severity scale |
| `evidence` | No | Up to 20 nonempty strings; each at most 1,000 characters; defaults to `[]` |

The response includes a database-generated integer `id` and `created_at`, alongside the submitted fields. **Keep the returned integer `id`**: subsequent API paths use this value as `finding_db_id`, not the scanner's text `finding_id`.

Invalid submissions receive `422 Unprocessable Entity` and are not stored.

## 2. Request Gemini analysis

`POST /findings/{finding_db_id}/analyze`

Example: `POST /findings/2/analyze`

The backend reads the saved finding, sanitizes recognized secret patterns in a copy, calls Gemini, and saves a result. This request is synchronous, so it can take time; the original finding remains stored if analysis fails.

A successful **analysis** response resembles:

```json
{
  "id": 3,
  "finding_db_id": 2,
  "status": "completed",
  "event_description": "The MCP tool attempted to read files outside its permitted directory.",
  "threat_type": "unauthorized_access",
  "ai_severity": "high",
  "summary": "Possible unauthorized access to configuration files.",
  "recommended_actions": [
    "Investigate the tool implementation and logs.",
    "Review tool permissions and least-privilege controls."
  ],
  "created_at": "2026-11-28T02:56:10.457746"
}
```

The `status` may instead be `failed`, even when the HTTP status is `200 OK`. **Always check the JSON `status`**, not only the HTTP code. A failed result may have `null` analysis fields. Scanner severity and AI severity are separate values and need not match. An AI conclusion is an assessment of supplied evidence, not independent verification that the event occurred.

## 3. Retrieve saved records

| Method and endpoint | Purpose | Typical success |
| --- | --- | --- |
| `GET /findings` | List saved scanner findings | `200 OK` |
| `GET /findings/{finding_db_id}` | Retrieve one original finding | `200 OK` |
| `GET /findings/{finding_db_id}/analyses` | List saved analysis attempts, newest first; no Gemini call | `200 OK` |

Unknown finding database IDs return `404 Not Found` on the single-finding, analysis, and analysis-history endpoints.

## Error handling

| Condition | Behavior |
| --- | --- |
| Missing or incorrect `X-API-Key` | `401 Unauthorized` |
| Server-side `SOC_API_KEY` unset | `503 Service Unavailable` |
| Invalid finding JSON / field limits | `422 Unprocessable Entity` |
| Unknown `finding_db_id` | `404 Not Found` |
| Database failure while saving | `500 Internal Server Error` |
| Gemini call/validation failure | A saved analysis attempt marked `failed`, typically with HTTP `200` |

## Integration checklist for the scanner team

1. Produce the JSON fields listed above using **synthetic test evidence** initially.
2. Send `POST /findings` with `X-API-Key`, and capture the returned integer `id`.
3. Call `POST /findings/{id}/analyze` using that database ID.
4. Check `status` (`completed` or `failed`), and treat `ai_severity` as the LLM assessment rather than the scanner's original severity.
5. Retrieve results using `GET /findings/{id}/analyses` and confirm they persist across a server restart.
6. Agree on common values for `category`, `source`, and `scanner_severity` before real scanner integration.

## Known limitations and security notes

- These endpoints have been demonstrated with **simulated findings**, not the team's actual MCP scanner output.
- Current credential sanitization uses pattern matching and **does not guarantee all secrets or sensitive data are removed**. The unredacted original is stored locally and must be protected; do not submit real confidential data without an approved data-handling policy.
- API-key authentication currently protects `/api/v1/scanner` routes; other API routes require a separate security review.
- Analysis currently runs synchronously; production integration may need background jobs, rate limiting, timeouts, and operational monitoring.
- The database file `backend/data/soc_events.db` should not be accidentally staged/committed with local test data.

## Verification to date

The team member implementing this backend reported **38 passing backend tests**. Manual Swagger checks confirmed authenticated ingestion (`201`), retrieval (`200`), live Gemini analysis (`status: completed`), persistence after restart, and unauthorized access rejection (`401`). Automated tests also cover failed-analysis persistence. These checks do not replace testing against the actual scanner.

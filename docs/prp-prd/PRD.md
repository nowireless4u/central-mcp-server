# Product Requirements Document (PRD)

## Central MCP Server — Containerized Deployment

**Version:** 1.0
**Date:** 2026-03-27
**Status:** Active

---

## 1. Overview

Central MCP Server is a community MCP (Model Context Protocol) server that wraps HPE Aruba Networking Central REST APIs and exposes them as tools for AI assistants. The server runs as a Docker container, providing a portable, reproducible, and isolated deployment model that eliminates host-level dependency management.

## 2. Problem Statement

Network engineers and operations teams need a way to query HPE Aruba Networking Central data through AI assistants (Claude Desktop, Claude Code, GitHub Copilot). Running MCP servers directly on host machines introduces dependency conflicts, credential management challenges, and inconsistent environments across team members. A containerized deployment solves these problems by packaging the server with all dependencies and providing a consistent runtime regardless of the host OS.

## 3. Goals

| Goal | Description |
|------|-------------|
| **Portable deployment** | Single `docker compose up` command to start the server on any machine with Docker installed. |
| **Zero host dependencies** | No Python, uv, or other tooling required on the host — everything is inside the container. |
| **Consistent environments** | Every deployment uses the same Python 3.12 runtime, locked dependencies, and server configuration. |
| **Credential isolation** | Credentials are passed via environment variables or `.env` file, never baked into the image. |
| **MCP client compatibility** | Works with Claude Desktop, Claude Code, GitHub Copilot, and any MCP client that supports HTTP/SSE transport. |
| **Read-only operations** | All exposed tools are read-only — no mutations to the Central environment. |

## 4. Non-Goals

- Write/mutation operations against Central (device provisioning, config changes, firmware upgrades).
- Multi-tenant or multi-org support within a single container instance.
- Built-in authentication or authorization for the MCP endpoint itself (assumed to run on a trusted network or behind a reverse proxy).
- A web UI or dashboard — the server is a headless MCP endpoint only.

## 5. Target Users

| Persona | Description |
|---------|-------------|
| **Network Engineer** | Queries site health, device status, client connectivity, and alerts through AI assistants. |
| **NOC Operator** | Uses guided prompts to run common troubleshooting workflows during incidents. |
| **Platform/DevOps Engineer** | Deploys and maintains the containerized server for their team. |

## 6. Functional Requirements

### 6.1 Container Runtime

| ID | Requirement |
|----|-------------|
| CR-1 | The server MUST run inside a Docker container using the provided Dockerfile. |
| CR-2 | The container MUST expose the MCP server on port 8001 via SSE (Server-Sent Events) transport. |
| CR-3 | The container MUST accept credentials via environment variables: `CENTRAL_BASE_URL`, `CENTRAL_CLIENT_ID`, `CENTRAL_CLIENT_SECRET`. |
| CR-4 | The container MUST support configuration via a `.env` file mounted or passed through `docker compose`. |
| CR-5 | The container MUST start with `docker compose up` using the provided `docker-compose.yml`. |
| CR-6 | The container MUST verify API connectivity at startup and log a warning if credentials are invalid or the API is unreachable. |

### 6.2 MCP Tools

| ID | Requirement |
|----|-------------|
| MT-1 | The server MUST expose site health tools: `central_get_sites`, `central_get_site_name_id_mapping`. |
| MT-2 | The server MUST expose device tools: `central_get_devices`, `central_find_device`. |
| MT-3 | The server MUST expose client tools: `central_get_clients`, `central_find_client`. |
| MT-4 | The server MUST expose alert tools: `central_get_alerts`. |
| MT-5 | The server MUST expose event tools: `central_get_events`, `central_get_events_count`. |
| MT-6 | All tools MUST be annotated as read-only (`readOnlyHint=true`, `destructiveHint=false`). |
| MT-7 | All tools MUST support OData v4.0 filtering where applicable. |
| MT-8 | Tools returning large datasets MUST support cursor-based pagination. |

### 6.3 Guided Prompts

| ID | Requirement |
|----|-------------|
| GP-1 | The server MUST include built-in prompts for common workflows (network health overview, site troubleshooting, client connectivity check, etc.). |
| GP-2 | Prompts MUST guide AI assistants through multi-step tool call sequences. |

### 6.4 MCP Client Integration

| ID | Requirement |
|----|-------------|
| CI-1 | The server MUST work with Claude Desktop via HTTP MCP configuration. |
| CI-2 | The server MUST work with Claude Code via `claude mcp add` with a URL endpoint. |
| CI-3 | The server MUST work with GitHub Copilot via `.vscode/mcp.json` HTTP configuration. |
| CI-4 | The MCP endpoint URL MUST be `http://<host>:8001/mcp`. |

## 7. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NF-1 | The container image MUST be based on `python:3.12-slim` for minimal size. |
| NF-2 | Dependencies MUST be installed from a locked `uv.lock` file for reproducibility. |
| NF-3 | The server MUST retry transient API errors (5xx, 429) up to 5 times before failing. |
| NF-4 | The server MUST handle paginated Central API responses transparently (both cursor and offset modes). |
| NF-5 | Credentials MUST NOT be baked into the Docker image. |
| NF-6 | The container SHOULD start and become ready within 30 seconds under normal conditions. |

## 8. Architecture

```
┌──────────────────────┐       ┌──────────────────────────┐       ┌─────────────────────┐
│   MCP Client         │       │   Docker Container       │       │  HPE Aruba Central  │
│  (Claude, Copilot)   │──────▶│   central-mcp-server     │──────▶│    REST APIs         │
│                      │ HTTP  │   FastMCP (SSE :8001)    │ HTTPS │                     │
│                      │◀──────│                          │◀──────│                     │
└──────────────────────┘  SSE  └──────────────────────────┘       └─────────────────────┘
```

- **Transport:** SSE over HTTP on port 8001.
- **API Client:** `pycentral` SDK with OAuth2 client credentials flow.
- **Data Layer:** All data is fetched live from Central APIs — no local caching or database.

## 9. Security Considerations

| Area | Approach |
|------|----------|
| **Credentials** | Passed via environment variables, never stored in the image. Use Docker secrets or a vault in production. |
| **Network** | The MCP endpoint has no built-in auth. Run on a trusted network or behind a reverse proxy with authentication. |
| **Data** | All operations are read-only. No ability to modify Central configuration. |
| **Image** | Based on official Python slim image. No unnecessary packages installed. |
| **Corporate Policy** | Users must review their organization's device and data policies before connecting to any AI assistant. |

## 10. Tools Reference

### Sites
| Tool | Description |
|------|-------------|
| `central_get_sites` | Detailed health metrics for one or more sites |
| `central_get_site_name_id_mapping` | Lightweight mapping of all site names to IDs and health scores |

### Devices
| Tool | Description |
|------|-------------|
| `central_get_devices` | Filtered list of devices by type, site, model, serial, etc. |
| `central_find_device` | Look up a single device by serial number or name |

### Clients
| Tool | Description |
|------|-------------|
| `central_get_clients` | Filtered list of clients by connection type, status, VLAN, WLAN, etc. |
| `central_find_client` | Look up a single client by MAC address |

### Alerts
| Tool | Description |
|------|-------------|
| `central_get_alerts` | Active, cleared, or deferred alerts for a site |

### Events
| Tool | Description |
|------|-------------|
| `central_get_events` | Events for a site, device, or client within a time window |
| `central_get_events_count` | Event count breakdown by type |

## 11. Success Metrics

| Metric | Target |
|--------|--------|
| Time to first query | < 5 minutes from `git clone` to a successful MCP tool call |
| Container startup | < 30 seconds to healthy state |
| API reliability | Transparent retry handles transient Central API errors without user intervention |
| Client compatibility | Works with Claude Desktop, Claude Code, and GitHub Copilot without custom configuration beyond the documented examples |

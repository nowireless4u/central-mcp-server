# Product Requirements Plan (PRP)

## Central MCP Server — Containerized Deployment

**Version:** 1.0
**Date:** 2026-03-27
**Status:** Active

---

## 1. Project Summary

Deliver a Docker-containerized MCP server that exposes HPE Aruba Networking Central data as tools for AI assistants. The container runs the server over SSE transport on port 8001, requiring zero host dependencies beyond Docker.

## 2. Implementation Phases

### Phase 1: Core Container Infrastructure (Complete)

| Task | Status | Details |
|------|--------|---------|
| Dockerfile | Done | Python 3.12-slim base, uv for dependency management, SSE transport on port 8001 |
| docker-compose.yml | Done | Single-service compose with env var passthrough |
| .dockerignore | Done | Excludes .venv, .env, .git, and non-essential files from build context |
| SSE transport support | Done | `server.py` detects `MCP_TRANSPORT=sse` and binds to `0.0.0.0:8001` |
| Credential passthrough | Done | Environment variables flow from host → compose → container → `config.py` |

### Phase 2: MCP Tools & Data Layer (Complete)

| Task | Status | Details |
|------|--------|---------|
| Site tools | Done | `central_get_sites`, `central_get_site_name_id_mapping` |
| Device tools | Done | `central_get_devices`, `central_find_device` with OData filtering |
| Client tools | Done | `central_get_clients`, `central_find_client` with connection-type-aware field pruning |
| Alert tools | Done | `central_get_alerts` with pagination, severity sorting, OData filtering |
| Event tools | Done | `central_get_events`, `central_get_events_count` with time range presets |
| Guided prompts | Done | 10 multi-step workflow prompts |
| Retry logic | Done | 5-retry with immediate retry on 5xx/429, immediate raise on 4xx |
| Pagination | Done | Cursor-based (primary) and offset-based (fallback) pagination |
| Data models | Done | Pydantic models for all entities with field descriptions |

### Phase 3: Documentation & Client Configuration (Current)

| Task | Status | Details |
|------|--------|---------|
| README update | In Progress | Rewrite to focus on Docker container deployment |
| PRD | In Progress | Document product requirements and architecture |
| PRP | In Progress | Document implementation plan and phases |
| MCP client configs | Done | `mcp.json` for HTTP transport, documented for Claude Desktop/Code/Copilot |

### Phase 4: Hardening & Production Readiness (Planned)

| Task | Status | Details |
|------|--------|---------|
| Health check endpoint | Planned | Add Docker HEALTHCHECK and `/health` route for orchestrator probes |
| Graceful shutdown | Planned | Handle SIGTERM for clean container stop |
| Structured logging | Planned | JSON log output for container log aggregation |
| Image size optimization | Planned | Multi-stage build to reduce final image size |
| CI/CD pipeline | Planned | Automated image build and publish on tag |
| Rate limiting | Planned | Protect the MCP endpoint from excessive requests |
| Reverse proxy guidance | Planned | Document nginx/traefik setup for TLS and auth |

## 3. Architecture Decisions

### 3.1 SSE Transport for Containers

**Decision:** Use SSE (Server-Sent Events) transport instead of stdio when running in a container.

**Rationale:** stdio transport requires direct process attachment, which is not possible when the MCP server runs inside a container. SSE over HTTP allows MCP clients to connect to the container over the network, which is the standard approach for containerized MCP servers.

### 3.2 Single Container, No Database

**Decision:** The server runs as a single stateless container with no database or caching layer.

**Rationale:** All data is fetched live from Central APIs. There is no local state to persist. This keeps the deployment simple — one container, one port, three environment variables.

### 3.3 uv for Dependency Management

**Decision:** Use `uv` inside the container for dependency installation.

**Rationale:** uv is significantly faster than pip for dependency resolution and installation, reducing container build time. The `uv.lock` file ensures reproducible builds across environments.

### 3.4 Credential Handling via Environment Variables

**Decision:** Credentials are passed exclusively through environment variables, never baked into the image.

**Rationale:** This follows the twelve-factor app methodology. Docker Compose reads from a `.env` file on the host, and environment variables can be sourced from secrets managers in production.

### 3.5 Read-Only Tool Annotations

**Decision:** All MCP tools are annotated as read-only and non-destructive.

**Rationale:** This signals to MCP clients and AI assistants that the tools cannot modify the Central environment, enabling auto-approval workflows in clients that support tool annotations.

## 4. Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| `fastmcp[code-mode]` | >=3.1.1 | MCP server framework |
| `pycentral` | 2.0a17 (pre-release) | HPE Aruba Central SDK |
| `python-dotenv` | >=1.0.0 | Environment variable loading |
| `platformdirs` | (transitive) | Config directory resolution |
| Docker | >=20.10 | Container runtime |
| Docker Compose | >=2.0 | Container orchestration |

## 5. Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| `pycentral` pre-release breaking changes | High | Medium | Pin exact version (2.0a17), test before upgrading |
| Central API rate limiting under heavy use | Medium | Medium | Built-in retry logic handles 429 responses; consider adding request queuing |
| No auth on MCP endpoint | High | Low (trusted network) | Document reverse proxy setup; plan auth middleware for Phase 4 |
| Container image size | Low | Low | Python slim base keeps it reasonable; multi-stage build planned for Phase 4 |
| Credential leakage via container inspection | Medium | Low | Credentials are env vars, not in image layers; recommend Docker secrets for production |

## 6. Testing Strategy

| Level | Approach |
|-------|----------|
| Unit | pytest + pytest-asyncio for tool logic, data transformers, and utility functions |
| Integration | Run container against a lab/non-production Central instance |
| Client compatibility | Manual verification with Claude Desktop, Claude Code, and GitHub Copilot |
| Container | Verify build, startup, health check, and graceful shutdown |

## 7. File Inventory

| File | Role |
|------|------|
| `server.py` | FastMCP app, lifespan, tool registration, transport selection |
| `config.py` | Credential loading (env → .env → user config dir) |
| `models.py` | Pydantic data models for all entities |
| `utils.py` | Pagination, retry, OData filter builder, data cleaning |
| `services/central_service.py` | Central API connection singleton |
| `tools/sites.py` | Site health tools |
| `tools/devices.py` | Device inventory tools |
| `tools/clients.py` | Client connectivity tools |
| `tools/alerts.py` | Alert monitoring tools |
| `tools/events.py` | Event investigation tools |
| `tools/prompts.py` | 10 guided workflow prompts |
| `tools/__init__.py` | Shared read-only tool annotations |
| `INSTRUCTIONS.md` | LLM system instructions |
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Compose service definition |
| `mcp.json` | MCP client HTTP configuration example |
| `pyproject.toml` | Package metadata and dependencies |

# mindbody-connector

An MCP (Model Context Protocol) server that lets consumers' AI assistants **discover services, check availability, and book or cancel appointments** at wellness businesses running on Mindbody.

**Status:** prototype, validated against the Mindbody sandbox (`SiteId = -99`).

## Why it exists

Consumers increasingly talk to AI assistants instead of opening booking apps. This connector gives those assistants a safe, merchant-controlled way to complete a real booking on the consumer's behalf.

## Safety design (merchant stays in control)

- Read operations (search services, check availability) work out of the box
- Write operations (book / cancel) are **disabled by default** and gated behind two **separate** server-side switches (`MINDBODY_ALLOW_BOOKINGS`, `MINDBODY_ALLOW_CANCEL`)
- Per-site merchant opt-in: a business activates the integration explicitly before any write can touch its data
- All credentials live in server-side environment variables only — never in code, never client-side

## Tools

| Tool | Type | Description |
|---|---|---|
| `search_services` | read | List services offered by a site |
| `check_availability` | read | Get bookable time slots for a service |
| `book_appointment` | write (gated) | Create an appointment |
| `cancel_appointment` | write (gated) | Cancel an appointment |

## Quick start

```bash
pip install "mcp[cli]" httpx
MINDBODY_MOCK=1 python smoke_test.py   # offline self-check, no credentials needed
```

Expected output: `7 passed / 0 failed`.

The code is compatible with both `mcp` 1.x and 2.x (the `FastMCP` → `MCPServer` rename is handled automatically).

## Files

| File | Purpose |
|---|---|
| `mindbody_mcp_server.py` | MCP server with the 4 tools above |
| `smoke_test.py` | Offline self-check (mock mode, no credentials) |
| `demo_walkthrough.py` | Scripted 55-second demo for screen recording (`--fast` for a quick check) |

## Roadmap

- [ ] Live sandbox integration tests with a real API key
- [ ] Class booking (in addition to appointments)
- [ ] Multi-tenant merchant activation flow

## License

MIT

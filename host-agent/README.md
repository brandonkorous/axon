# Axon Host Agent

Lightweight service that provides Axon agents with host filesystem and executable access.

## Quick Start

```bash
node server.js --id "my-project" --path "/path/to/project" --executables "git,node,python"
```

## Options

| Flag | Env Var | Description |
|------|---------|-------------|
| --id | HOST_AGENT_ID | Unique identifier for this host agent |
| --path | HOST_AGENT_PATH | Root directory for file operations |
| --port | HOST_AGENT_PORT | Port to listen on (default: 9100) |
| --executables | HOST_AGENT_EXECUTABLES | Comma-separated allowed executables |
| --key | HOST_AGENT_KEY | Optional API key for authentication |

## Manager

The manager process handles multiple host agents from a single process:

```bash
# Start the manager (manages all host agents)
node manager.js

# Or with a custom port
HOST_AGENT_MANAGER_PORT=9099 node manager.js
```

The Axon backend controls agents through the manager API on port 9099.

### Manager API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | List all managed agents and their status |
| `/start` | POST | Start a new host agent (body: `{ id, path, port, executables }`) |
| `/stop` | POST | Stop a running agent (body: `{ id }`) |
| `/restart` | POST | Restart with new config (body: `{ id, path, port, executables }`) |
| `/logs?id=X` | GET | Retrieve last 100 log lines for an agent |

## API

- `GET /health` — Status check
- `POST /exec` — Execute an allowlisted command
- `GET /list?path=.` — List directory contents
- `GET /read?path=file.txt` — Read a file
- `POST /write` — Write a file

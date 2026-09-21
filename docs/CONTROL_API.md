# Local DevRoom Control API

The control API exposes the existing Python orchestrator to the DevRoom Commander UI.

## Mock smoke test

From the repository root:

```powershell
python -m devroom.control_server `
  --goal "Test the DevRoom human-gated workflow" `
  --workspace "D:\DEV_ROOM_TEST" `
  --provider mock
```

The API listens on `http://127.0.0.1:8765` by default.

Configure the Lovable/Vite frontend with:

```
VITE_DEVROOM_API_URL=http://127.0.0.1:8765
```

Without that variable, the frontend remains in mock mode.

## Codex-backed run

After the Codex CLI is installed and authenticated:

```powershell
python -m devroom.control_server `
  --goal "Your approved development goal" `
  --workspace "D:\YOUR_WORKSPACE" `
  --provider codex
```

The bootstrap uses the provider router with Codex for all currently configured roles. The Implementer receives workspace-write; Lead, Architect, Reviewer, and QA remain read-only.

## API surface

Only these endpoints are exposed:

- `GET /api/health`
- `GET /api/workflow`
- `POST /api/workflow/decision`

The browser does not contain orchestration logic. It only reads workflow state and submits human gate decisions.

State snapshots are persisted under `.devroom/workflow.json` in the selected workspace by default.
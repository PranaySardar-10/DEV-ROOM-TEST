# Local DevRoom Control API

The control API exposes the Python production orchestrator to the DevRoom Commander UI.

## Production run

Create a local configuration from the example configuration if needed:

```powershell
python -c "from devroom.config import write_example_config; write_example_config('devroom.json')"
```

Run the configured local workforce:

```powershell
python -m devroom.control_server \
  --goal "Your approved development goal" \
  --workspace "D:\YOUR_WORKSPACE" \
  --config "D:\DEV-ROOM-TEST\devroom.json" \
  --allowed-path "Assets/Scripts/VehicleOwnership.cs"
```

The active production workforce is local Ollama only:
- Lead → local read-only model
- Architect → local read-only model
- Coder → local proposal-only model
- Implementer → controlled workspace-write local model
- QA → local read-only model

Human/ChatGPT review is a workflow gate, not an autonomous provider role. The browser does not contain orchestration logic; it only reads workflow state and submits human decisions.

The `--allowed-path` scope is mandatory for a real Implementer run. Repeat the option for each approved production file.

## Mock smoke test

For deterministic orchestration/control-API tests:

```powershell
python -m devroom.control_server \
  --goal "Test the DevRoom human-gated workflow" \
  --workspace "D:\DEV_ROOM_TEST" \
  --config "devroom.json" \
  --provider mock
```

The API listens on `http://127.0.0.1:8765` by default.

Configure the Lovable/Vite frontend with:

```
VITE_DEVROOM_API_URL=http://127.0.0.1:8765
```

Without that variable, the frontend remains in mock mode.

## API surface

Only these endpoints are exposed:
- `GET /api/health`
- `GET /api/workflow`
- `POST /api/workflow/decision`

State snapshots are persisted under `.devroom/workflow.json` in the selected workspace by default.

## Safety boundary

The control API does not grant the UI filesystem write access. Only the Implementer provider receives workspace-write, and it receives only the explicit `allowed_paths` scope passed to the workflow.

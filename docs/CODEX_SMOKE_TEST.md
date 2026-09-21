# DevRoom Codex smoke test

The provider adapter is ready, but live Codex execution is deliberately not part of CI yet.

## Local smoke test

From a checked-out DevRoom repository:

```powershell
codex --version
codex exec --ephemeral --sandbox read-only --json "Reply with exactly: DEVROOM_CODEX_SMOKE_OK"
```

Expected behavior:
- `codex` is installed and authenticated.
- stdout is JSONL because `--json` is enabled.
- the final `agent_message` contains `DEVROOM_CODEX_SMOKE_OK`.

The DevRoom provider uses `workspace-write` only when an agent is actually authorized to modify its assigned workspace. Review-only runs should remain read-only.

Do not place Codex authentication tokens or API keys in the repository. OpenAI documents `codex exec` as the non-interactive interface for scripts/CI and recommends explicit sandbox permissions. 

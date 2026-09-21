# DevRoom Codex smoke test

The provider adapter is ready, and live Codex execution has been verified locally.

## Local smoke test

From the checked-out DevRoom repository:

```powershell
codex --version
codex exec --ephemeral --sandbox read-only --json "Reply with exactly: DEVROOM_CODEX_SMOKE_OK"
```

Expected behavior:
- `codex` is installed and authenticated.
- `stdout` is JSONL because `--json` is enabled.
- the final `agent_message` contains `DEVROOM_CODEX_SMOKE_OK`.

## Workspace targeting

DevRoom passes the task workspace explicitly to Codex with `--cd` and also sets the subprocess working directory to the same path. This is deliberate: an agent must have an explicit target workspace rather than inheriting whatever directory launched the orchestrator.

Role-specific sandboxing remains part of the provider configuration:
- Review-only tasks should use `read-only`.
- Implementation tasks may use `workspace-write` only after Human Gate 1 and only inside an isolated task workspace.
- `danger-full-access` is not part of the normal DevRoom workflow.

OpenAI documents `codex exec` as the non-interactive interface for scripts/CI, recommends explicit sandbox permissions, and documents `--cd`/workspace targeting for Codex execution. citeturn0search5turn0search1

Do not place Codex authentication tokens or API keys in the repository.

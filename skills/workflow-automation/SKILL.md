---
name: workflow-automation
description: >
  This skill MUST be invoked when building automation scripts, CI/CD pipelines, or orchestration workflows.
  SHOULD also invoke when user says "automate", "pipeline", "workflow", "cron", "scheduled".
  Do NOT use for simple one-off bash commands.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Workflow Automation

Patterns for reliable, maintainable automation scripts.

## Idempotency

Scripts must be safe to re-run without side effects:
- Check before create: `if not exists → create`
- Use upsert over insert
- Avoid appending to files without checking for duplicates
- Temp files: use unique names or clean up at start

## Error handling

```bash
set -euo pipefail          # fail fast on any error
trap 'cleanup' EXIT        # always clean up

cleanup() {
  rm -f "$LOCKFILE"
  # release resources
}
```

- Exit codes: 0=success, 1=general error, 2=usage error, 3+=domain-specific
- Never swallow errors silently
- Log the error before exiting

## Logging

```bash
log()  { echo "[$(date -u +%H:%M:%S)] $*"; }
warn() { echo "[WARN] $*" >&2; }
die()  { echo "[ERROR] $*" >&2; exit 1; }
```

- Structured: timestamp + level + message
- Progress indicators for long steps: `log "Step 2/5: building image..."`
- Log inputs at start, outcome at end

## Parallelism

```bash
# Independent tasks in parallel
task_a & task_b & wait

# Dependent tasks sequential
result_a=$(task_a)
task_b "$result_a"
```

Rule: parallel = no shared state. If tasks share state → sequential.

## Signal / lock coordination

```bash
LOCKFILE="/tmp/deploy.lock"
[ -f "$LOCKFILE" ] && die "Another instance running"
touch "$LOCKFILE"
```

For agent coordination: write status to RLM, not shared files.

## Retry pattern

```bash
retry() {
  local n=3
  until "$@"; do
    (( n-- )) || die "Command failed after retries: $*"
    sleep 2
  done
}
```

Use for: network calls, health checks. Never retry: file writes, DB mutations.

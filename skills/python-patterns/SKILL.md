---
name: python-patterns
description: >
  This skill MUST be invoked when writing Python scripts for infrastructure, tooling, or automation.
  SHOULD also invoke when user says "python", "script", "pip", "pytest".
  Do NOT use for 1C BSL code.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Python Patterns

Best practices for infrastructure Python scripts.

## Paths — always pathlib

```python
from pathlib import Path

base = Path(__file__).parent
config = base / "config.yaml"
config.read_text(encoding="utf-8")
```

Never use `os.path.join`, `os.getcwd()`, or string concatenation for paths.

## Type hints

```python
def process(items: list[str], limit: int = 10) -> dict[str, int]:
    ...
```

All function signatures get type hints. Use `from __future__ import annotations` for forward refs.

## CLI scripts — argparse

```python
import argparse

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Tool description")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()
```

## HTTP — httpx or requests

```python
import httpx

resp = httpx.get(url, timeout=10)
resp.raise_for_status()
data = resp.json()
```

Always set timeout. Always call `raise_for_status()` before reading body.

## Error handling

```python
# Specific exceptions only
try:
    result = risky_call()
except FileNotFoundError as e:
    log.error("Config missing: %s", e)
    sys.exit(1)
except httpx.HTTPStatusError as e:
    log.error("HTTP %d: %s", e.response.status_code, e.response.text)
    raise
```

Never: `except Exception`, never `except:`.

## Logging over print

```python
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

log.info("Processing %d items", len(items))
log.error("Failed: %s", err)
```

## YAML/JSON

```python
import json, yaml

data = json.loads(Path("file.json").read_text())
cfg = yaml.safe_load(Path("config.yaml").read_text())  # safe_load always
```

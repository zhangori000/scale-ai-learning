from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class LocalJSONStore:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_json_atomic(self, filename: str, payload: Any) -> Path:
        target = self.base_dir / filename
        fd, temp_path = tempfile.mkstemp(
            prefix=target.name + ".",
            suffix=".tmp",
            dir=str(self.base_dir),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(payload, tmp, ensure_ascii=False, indent=2)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(temp_path, target)
        finally:
            # Clean temp file if replace failed.
            if os.path.exists(temp_path):
                os.remove(temp_path)
        return target

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
            prefix=target.stem + "_",
            suffix=".tmp",
            dir=str(self.base_dir),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=True, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, target)
            return target
        except Exception:
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise

    def read_json(self, path_or_name: str | Path) -> Any:
        path = Path(path_or_name)
        if not path.is_absolute():
            path = self.base_dir / path
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

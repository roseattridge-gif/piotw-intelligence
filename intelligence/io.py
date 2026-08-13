from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def read_jsonl(path: str | Path, model: type[T]) -> list[T]:
    rows: list[T] = []
    for line in Path(path).read_text().splitlines():
        if line.strip():
            rows.append(model.model_validate_json(line))
    return rows


def write_jsonl(path: str | Path, rows: list[BaseModel]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(row.model_dump_json() + "\n" for row in rows))

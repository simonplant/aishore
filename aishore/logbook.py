"""Append-only task log: tasks/log.csv. One row per merged, rejected, or abandoned task."""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

FIELDS = ["date", "id", "tier", "kind", "outcome", "human_minutes", "net_loc",
          "review_real", "review_discarded", "gate_caught", "missing_gate", "note"]


def append(root: Path, **row) -> None:
    path = root / "tasks" / "log.csv"
    new = not path.exists()
    with path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({"date": dt.date.today().isoformat(), **{k: row.get(k, "") for k in FIELDS[1:]}})

"""Append-only outreach audit log."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from src.models import ContactRecord, EmailDraft

LOG_HEADERS = [
    "timestamp",
    "recipient_email",
    "company",
    "role",
    "subject",
    "status",
    "error_message",
]


def log_outreach(
    record: ContactRecord,
    draft: EmailDraft,
    status: str,
    log_path: str | Path = "outreach_log.csv",
    error_message: str | None = None,
) -> None:
    path = Path(log_path)
    write_header = not path.exists() or path.stat().st_size == 0

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_HEADERS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "recipient_email": record.recipient_email,
                "company": record.company,
                "role": record.role,
                "subject": draft.subject,
                "status": status,
                "error_message": error_message or "",
            }
        )

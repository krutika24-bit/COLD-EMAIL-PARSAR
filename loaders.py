"""Load and validate outreach targets (FR1)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.config import project_root
from src.models import REQUIRED_FIELDS, ContactRecord

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def validate_record(data: dict[str, Any]) -> tuple[ContactRecord | None, str | None]:
    missing = [f for f in REQUIRED_FIELDS if not str(data.get(f, "")).strip()]
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"

    record = ContactRecord.from_dict(data)
    if not _is_valid_email(record.recipient_email):
        return None, f"Invalid email: {record.recipient_email!r}"

    return record, None


def default_contacts_path() -> Path:
    phase_path = (
        project_root()
        / "phases"
        / "phase_01_load_targets"
        / "data"
        / "contacts.json"
    )
    if phase_path.exists():
        return phase_path
    return project_root() / "data" / "contacts.json"


def load_targets_from_json(path: str | Path) -> list[ContactRecord]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Contacts file not found: {path}")

    with path.open(encoding="utf-8-sig") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError(f"{path}: expected a JSON array of contacts")

    records: list[ContactRecord] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            print(f"  Skip row {i}: not an object")
            continue
        record, err = validate_record(item)
        if err:
            print(f"  Skip row {i} ({item.get('recipient_email', '?')}): {err}")
            continue
        records.append(record)

    return records


def load_targets_from_csv(path: str | Path) -> list[ContactRecord]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Contacts file not found: {path}")

    records: list[ContactRecord] = []
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Clean keys and values, removing spaces and None
            cleaned_row = {
                str(k).strip(): str(v).strip() if v else ""
                for k, v in row.items()
                if k is not None
            }
            record, err = validate_record(cleaned_row)
            if err:
                print(f"  Skip CSV row {i} ({cleaned_row.get('recipient_email', '?')}): {err}")
                continue
            records.append(record)

    return records


SAMPLE_CONTACTS: list[dict[str, Any]] = [
    {
        "recipient_name": "Priya Sharma",
        "recipient_email": "priya@example.com",
        "company": "Acme AI",
        "role": "Backend Engineering Intern",
        "personalization_note": "Company recently launched an AI workflow automation product",
        "candidate_name": "Your Name",
        "candidate_background": "Python developer interested in automation and AI agents",
        "portfolio_url": "https://github.com/yourname",
    },
    {
        "recipient_email": "hiring@nexustech.io",
        "company": "Nexus Tech",
        "role": "Junior Software Engineer",
        "candidate_name": "Your Name",
        "candidate_background": "building small agents and API integrations in Python",
        "portfolio_url": "https://github.com/yourname",
    },
    {
        "recipient_name": "Alex Kim",
        "recipient_email": "alex@startupco.dev",
        "company": "StartupCo",
        "role": "Founding Engineer Intern",
        "personalization_note": "Your post about shipping MVPs quickly resonated with me",
        "candidate_name": "Your Name",
        "candidate_background": "full-stack prototypes and developer tooling",
    },
]


def load_hardcoded_targets() -> list[ContactRecord]:
    records: list[ContactRecord] = []
    for i, item in enumerate(SAMPLE_CONTACTS):
        record, err = validate_record(item)
        if err:
            raise ValueError(f"Invalid SAMPLE_CONTACTS[{i}]: {err}")
        records.append(record)
    return records


def load_targets(source: str | Path | None = None) -> list[ContactRecord]:
    if source is None:
        env_path = project_root() / ".env"
        input_path = None
        if env_path.exists():
            from dotenv import load_dotenv
            import os

            load_dotenv(env_path)
            input_path = os.getenv("INPUT_PATH")
        
        p = None
        if input_path:
            p = Path(input_path)
            if not p.is_absolute():
                p = project_root() / p
        else:
            p = default_contacts_path()

        if p and p.exists():
            if p.suffix.lower() == ".csv":
                return load_targets_from_csv(p)
            return load_targets_from_json(p)
        return load_targets_from_json(default_contacts_path())

    if isinstance(source, str) and source.strip().lower() == "hardcoded":
        return load_hardcoded_targets()

    path = Path(source)
    if path.exists():
        if path.suffix.lower() == ".csv":
            return load_targets_from_csv(path)
        return load_targets_from_json(path)

    raise FileNotFoundError(f"Contacts source not found: {source}")

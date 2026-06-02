"""Terminal preview and confirmation."""

from __future__ import annotations

from src.models import ContactRecord, EmailDraft


def preview_email(draft: EmailDraft, record: ContactRecord) -> None:
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"Generated email for: {record.company} — {record.role}")
    print(f"Recipient: {record.recipient_email}")
    print(f"Subject: {draft.subject}")
    print(bar)
    print(draft.body)
    print(f"{bar}\n")


def prompt_action() -> str:
    while True:
        raw = input("Send this email? (yes/no/skip): ").strip().lower()
        if raw in ("y", "yes"):
            return "send"
        if raw in ("n", "no", "skip", "s"):
            return "skip"
        print("  Please enter yes, no, or skip.")

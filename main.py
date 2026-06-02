"""Orchestrator: load → generate → preview → confirm → send → log."""

from __future__ import annotations

import sys
from pathlib import Path

from src.cli import preview_email, prompt_action
from src.config import load_config, project_root
from src.email_generator import generate_email
from src.email_sender import reset_send_count, send_or_draft
from src.loaders import load_targets
from src.logger import log_outreach
from src.models import EmailDraft


def run() -> None:
    root = project_root()
    config = load_config(root / ".env")
    input_path = root / config.input_path
    targets = load_targets(input_path if input_path.exists() else None)

    if not targets:
        print("No valid outreach targets loaded.")
        sys.exit(1)

    reset_send_count()
    log_file = root / config.log_path
    processed = 0

    print(f"\nThe Closer — {len(targets)} target(s) | DRY_RUN={config.dry_run}\n")

    for record in targets:
        processed += 1
        try:
            draft = generate_email(record, config)
            preview_email(draft, record)
            action = prompt_action()

            if action == "send":
                result = send_or_draft(draft, record, config)
                log_outreach(
                    record,
                    draft,
                    result.status,
                    log_path=log_file,
                    error_message=result.error_message,
                )
                if result.error_message:
                    print(f"  Failed: {result.error_message}")
            else:
                log_outreach(record, draft, "skipped", log_path=log_file)
                print("  Skipped.")

        except Exception as exc:
            print(f"  Error: {exc}")
            empty = EmailDraft(subject="", body="")
            log_outreach(
                record,
                empty,
                "failed",
                log_path=log_file,
                error_message=str(exc),
            )

    print(f"\nDone. Processed {processed} target(s). Log: {log_file}\n")


if __name__ == "__main__":
    run()

"""Email transport: dry-run and SMTP."""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

from src.models import AppConfig, ContactRecord, EmailDraft, SendResult

_send_count = 0


def reset_send_count() -> None:
    global _send_count
    _send_count = 0


def send_or_draft(
    draft: EmailDraft,
    record: ContactRecord,
    config: AppConfig,
) -> SendResult:
    global _send_count

    if not draft.subject.strip() or not draft.body.strip():
        return SendResult(status="failed", error_message="Empty subject or body")

    if _send_count >= config.max_sends_per_run:
        return SendResult(
            status="failed",
            error_message=f"MAX_SENDS_PER_RUN ({config.max_sends_per_run}) reached",
        )

    if config.dry_run:
        print(
            f"  [DRY RUN] Would {config.email_mode} to {record.recipient_email}\n"
            f"  Subject: {draft.subject}"
        )
        status = "drafted" if config.email_mode == "draft" else "sent"
        return SendResult(status=status)

    try:
        _send_smtp(draft, record, config)
        _send_count += 1
        status = "drafted" if config.email_mode == "draft" else "sent"
        return SendResult(status=status)
    except smtplib.SMTPException as exc:
        return SendResult(status="failed", error_message=str(exc))


def _send_smtp(draft: EmailDraft, record: ContactRecord, config: AppConfig) -> None:
    msg = MIMEText(draft.body, "plain", "utf-8")
    msg["Subject"] = draft.subject.replace("\n", " ")
    msg["From"] = f"{config.sender_name} <{config.smtp_user}>"
    msg["To"] = record.recipient_email

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(config.smtp_user, config.smtp_password)
        server.sendmail(config.smtp_user, [record.recipient_email], msg.as_string())

    print(f"  Email sent to {record.recipient_email}")

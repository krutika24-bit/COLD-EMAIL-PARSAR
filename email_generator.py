"""Generate personalized cold emails from contact records."""

from __future__ import annotations

from src.models import AppConfig, ContactRecord, EmailDraft

MAX_BODY_WORDS = 150


def count_words(text: str) -> int:
    return len(text.split())


def _personalization_hook(record: ContactRecord) -> str:
    if record.personalization_note:
        return record.personalization_note.strip()
    return f"I noticed {record.company} is hiring for the {record.role} role."


def _sign_off(record: ContactRecord) -> str:
    lines = [record.candidate_name]
    for url in (record.portfolio_url, record.linkedin_url, record.resume_link):
        if url:
            lines.append(url)
    return "\n".join(lines)


def _warn_if_too_long(draft: EmailDraft) -> None:
    words = count_words(draft.body)
    if words > MAX_BODY_WORDS:
        print(f"  Warning: email body is {words} words (target: under {MAX_BODY_WORDS})")


def generate_email(record: ContactRecord, config: AppConfig | None = None) -> EmailDraft:
    hook = _personalization_hook(record)
    subject = f"Quick note on the {record.role} role at {record.company}"

    body = f"""Hi {record.display_name()},

{hook}

I'm {record.candidate_name}, and I've been working on projects around {record.candidate_background}. The {record.role} position at {record.company} stood out because it aligns with how I like to build practical, product-focused software.

Would you be open to a quick look at my profile or pointing me to the right person on your team?

Best,
{_sign_off(record)}
"""

    draft = EmailDraft(subject=subject.strip(), body=body.strip())

    if config and config.use_llm:
        draft = llm_enhance(draft, record, config)

    _warn_if_too_long(draft)
    return draft


def print_email(draft: EmailDraft, record: ContactRecord) -> None:
    """Pretty-print for terminal preview demos."""
    bar = "-" * 60
    print(bar)
    print(f"To: {record.recipient_email}")
    print(f"Company: {record.company} | Role: {record.role}")
    print(f"Subject: {draft.subject}")
    print(f"Words: {count_words(draft.body)}")
    print(bar)
    print(draft.body)
    print(bar)


def llm_enhance(draft: EmailDraft, record: ContactRecord, config: AppConfig) -> EmailDraft:
    """Stretch: rewrite via Groq (Phase 9d). Falls back to template on error."""
    try:
        from src.llm_groq import enhance_email

        return enhance_email(draft, record, config)
    except Exception as exc:
        print(f"  Groq enhance failed, using template: {exc}")
        return draft

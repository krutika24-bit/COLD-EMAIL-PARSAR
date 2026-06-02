"""Groq Chat Completions wrapper (Phase 9d stretch)."""

from __future__ import annotations

from src.models import AppConfig, ContactRecord, EmailDraft


def enhance_email(
    draft: EmailDraft,
    record: ContactRecord,
    config: AppConfig,
) -> EmailDraft:
    from groq import Groq

    client = Groq(api_key=config.groq_api_key)
    system = (
        "You polish cold outreach emails for job seekers. "
        "Keep under 150 words, one clear ask, professional tone. "
        "Do NOT invent experience, referrals, or relationships. "
        "Return subject on first line as 'Subject: ...' then blank line then body."
    )
    user = (
        f"Company: {record.company}\nRole: {record.role}\n"
        f"Candidate: {record.candidate_name}\nBackground: {record.candidate_background}\n"
        f"Note: {record.personalization_note or ''}\n\n"
        f"Current subject: {draft.subject}\n\n{draft.body}"
    )

    response = client.chat.completions.create(
        model=config.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
        max_tokens=512,
    )
    text = (response.choices[0].message.content or "").strip()
    return _parse_subject_body(text, draft)


def _parse_subject_body(text: str, fallback: EmailDraft) -> EmailDraft:
    if text.lower().startswith("subject:"):
        lines = text.split("\n", 1)
        subject = lines[0].split(":", 1)[1].strip()
        body = lines[1].strip() if len(lines) > 1 else fallback.body
        return EmailDraft(subject=subject, body=body)
    return EmailDraft(subject=fallback.subject, body=text)

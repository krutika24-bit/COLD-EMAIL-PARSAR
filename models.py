"""Shared domain types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

REQUIRED_FIELDS = (
    "recipient_email",
    "company",
    "role",
    "candidate_name",
    "candidate_background",
)


@dataclass
class ContactRecord:
    recipient_email: str
    company: str
    role: str
    candidate_name: str
    candidate_background: str
    recipient_name: Optional[str] = None
    job_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    personalization_note: Optional[str] = None
    linkedin_url: Optional[str] = None
    resume_link: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContactRecord:
        return cls(
            recipient_email=_req_str(data, "recipient_email"),
            company=_req_str(data, "company"),
            role=_req_str(data, "role"),
            candidate_name=_req_str(data, "candidate_name"),
            candidate_background=_req_str(data, "candidate_background"),
            recipient_name=_opt_str(data, "recipient_name"),
            job_url=_opt_str(data, "job_url"),
            portfolio_url=_opt_str(data, "portfolio_url"),
            personalization_note=_opt_str(data, "personalization_note"),
            linkedin_url=_opt_str(data, "linkedin_url"),
            resume_link=_opt_str(data, "resume_link"),
        )

    def display_name(self) -> str:
        return self.recipient_name or "there"


def _req_str(data: dict[str, Any], key: str) -> str:
    return str(data.get(key, "")).strip()


def _opt_str(data: dict[str, Any], key: str) -> Optional[str]:
    val = data.get(key)
    if val is None:
        return None
    s = str(val).strip()
    return s or None


@dataclass
class EmailDraft:
    subject: str
    body: str


@dataclass
class AppConfig:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    sender_name: str
    dry_run: bool
    email_mode: str
    max_sends_per_run: int
    input_path: str
    use_llm: bool
    groq_api_key: str
    groq_model: str
    log_path: str = "outreach_log.csv"


@dataclass
class SendResult:
    status: str
    error_message: Optional[str] = None
    provider_id: Optional[str] = None

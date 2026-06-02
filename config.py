"""Load application configuration from environment."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.models import AppConfig


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).strip().lower()
    return val in ("1", "true", "yes", "on")


def load_config(env_file: str | None = None) -> AppConfig:
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    dry_run = _env_bool("DRY_RUN", True)
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_user = os.getenv("SMTP_USER", "")

    if not dry_run and (not smtp_user or not smtp_password):
        print(
            "Error: DRY_RUN=false requires SMTP_USER and SMTP_PASSWORD in .env\n"
            "Use a Gmail App Password: https://support.google.com/accounts/answer/185833",
            file=sys.stderr,
        )
        sys.exit(1)

    use_llm = _env_bool("USE_LLM", False)
    groq_key = os.getenv("GROQ_API_KEY", "")
    if use_llm and not groq_key:
        print(
            "Error: USE_LLM=true requires GROQ_API_KEY in .env\n"
            "Get a key: https://console.groq.com/keys",
            file=sys.stderr,
        )
        sys.exit(1)

    return AppConfig(
        smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        sender_name=os.getenv("SENDER_NAME", "Your Name"),
        dry_run=dry_run,
        email_mode=os.getenv("EMAIL_MODE", "send").lower(),
        max_sends_per_run=int(os.getenv("MAX_SENDS_PER_RUN", "5")),
        input_path=os.getenv("INPUT_PATH", "data/contacts.json"),
        use_llm=use_llm,
        groq_api_key=groq_key,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    )


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent

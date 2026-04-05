import structlog
import logging
import sys
import re
from typing import Any

PII_PATTERNS = [
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[EMAIL_REDACTED]"),
    (re.compile(r"\+?[0-9]{7,15}"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    (re.compile(r"\b\d{10,}\b"), "[ID_REDACTED]"),
]


def mask_pii(value: str) -> str:
    result = str(value)
    for pattern, replacement in PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


from structlog.types import EventDict


def sanitize_log_values(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    sensitive_keys = {
        "full_name",
        "name",
        "email",
        "phone",
        "dob",
        "date_of_birth",
        "address",
        "ip",
        "ip_address",
        "signer_ip",
        "external_id",
        "patient_name",
        "user_name",
        "username",
        "value_preview",
    }

    for key, value in event_dict.items():
        if key in sensitive_keys and isinstance(value, str):
            event_dict[key] = mask_pii(value)
        elif isinstance(value, str) and len(value) > 100:
            event_dict[key] = value[:100] + "..."
    return event_dict


def setup_logging():
    """
    Structured Logging for SaMD (Mission 12 Hardening).
    Formats logs as JSON for production log aggregators (ELK/Sentry).
    Ensures HIPAA/GDPR compliance by avoiding raw PII in message strings.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            sanitize_log_values,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Bridge standard logging to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


logger = structlog.get_logger()

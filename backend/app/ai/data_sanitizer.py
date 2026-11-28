import re

from .finding_schemas import ScannerFinding

PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?"
    r"-----END [A-Z ]*PRIVATE KEY-----",
    re.IGNORECASE | re.DOTALL,
)

BEARER_PATTERN = re.compile(
    r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}=*",
    re.IGNORECASE,
)

TOKEN_PATTERN = re.compile(
    r"\b(?:"
    r"AKIA[0-9A-Z]{16}|"
    r"AIza[0-9A-Za-z_-]{35}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,}"
    r")\b"
)

SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"""(?i)(["']?\b(?:api[_-]?key|access[_-]?token|password|passwd|client[_-]?secret)["']?\s*[:=]\s*)("[^"]*"|'[^']*'|[^\s,;]+)"""
)

def redact_text(text: str) -> str:
    """Remove common credential patterns from text."""

    text = PRIVATE_KEY_PATTERN.sub(
        "[REDACTED PRIVATE KEY]", text
    )

    text = BEARER_PATTERN.sub(
        "Bearer [REDACTED]", text
    )

    text = TOKEN_PATTERN.sub(
        "[REDACTED TOKEN]", text
    )

    def replace_assignment(match):
        value = match.group(2)
        quote = value[0] if value.startswith(
            ("'", '"')
        ) else ""

        return (
            match.group(1)
            + quote
            + "[REDACTED]"
            + quote
        )

    return SECRET_ASSIGNMENT_PATTERN.sub(
        replace_assignment, text
    )

def sanitize_finding(finding: ScannerFinding) -> dict:
    """Create a sanitized copy without changing the original."""

    data = finding.model_dump(exclude_none=True)

    for key, value in data.items():
        if isinstance(value, str):
            data[key] = redact_text(value)

        elif isinstance(value, list):
            data[key] = [
                redact_text(item) if isinstance(item, str)
                else item
                for item in value
            ]

    return data


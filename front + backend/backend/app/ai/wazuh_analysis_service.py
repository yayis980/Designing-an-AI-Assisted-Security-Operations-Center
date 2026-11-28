import logging
from dataclasses import dataclass
from typing import Any, Literal

from app.services.wazuh import parse_wazuh_alert
from app.schemas.event import SecurityEventCreate

from .wazuh_adapter import analyze_wazuh_event
from .llm_schemas import SecurityAnalysis


logger = logging.getLogger(__name__)


@dataclass
class WazuhAnalysisResult:
    event: SecurityEventCreate
    ai_status: Literal["completed", "failed"]
    ai_analysis: SecurityAnalysis | None = None


def analyze_wazuh_alert(
    alert: dict[str, Any]
) -> WazuhAnalysisResult:

    # Step 1: Parse incoming Wazuh alert
    event = parse_wazuh_alert(alert)

    # Step 2: Attempt Gemini analysis
    try:
        analysis = analyze_wazuh_event(event)

        return WazuhAnalysisResult(
            event=event,
            ai_status="completed",
            ai_analysis=analysis,
        )

    except Exception as error:

        # Log failure without exposing alert contents
        logger.warning(
            "Gemini analysis failed: %s",
            type(error).__name__,
        )

        # Preserve the event even when Gemini fails
        return WazuhAnalysisResult(
            event=event,
            ai_status="failed",
            ai_analysis=None,
        )
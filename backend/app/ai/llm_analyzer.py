import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .llm_schemas import SecurityAnalysis
from .llm_prompts import SOC_ANALYST_SYSTEM_PROMPT


# Load API key from project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def analyze_finding(finding: str) -> SecurityAnalysis:

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    # Send security finding to Gemini
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",

        contents=f"Analyze this security finding:\n{finding}",

        config=types.GenerateContentConfig(
            system_instruction=SOC_ANALYST_SYSTEM_PROMPT,
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=SecurityAnalysis,
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    # Validate JSON against our Pydantic schema
    return SecurityAnalysis.model_validate_json(response.text)


if __name__ == "__main__":

    sample = "Simulated event: 5 failed SSH logins in one minute."

    analysis = analyze_finding(sample)

    # Display structured JSON
    print(analysis.model_dump_json(indent=2))
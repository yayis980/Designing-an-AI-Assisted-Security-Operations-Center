import argparse
import time

from backend.app.ai.finding_schemas import ScannerFinding
from backend.app.ai.scanner_adapter import analyze_scanner_finding
from google.genai import errors 


TEST_CASES = [
    {
        "name": "Tool Poisoning",
        "category": "tool_poisoning",
        "description": (
            "An MCP tool description contains instructions "
            "telling an AI assistant to ignore its original "
            "instructions and perform additional actions "
            "without notifying the user."
        ),
        "evidence": [
            "Static analysis identified instruction-like text "
            "inside the tool description."
        ],
        "expected": "medium",
    },
    {
        "name": "Prompt Injection",
        "category": "prompt_injection",
        "description": (
            "An MCP tool response contains embedded instructions "
            "attempting to redirect the AI assistant away from "
            "the user's authorized request."
        ),
        "evidence": [
            "The returned data includes instructions directed "
            "at the AI assistant rather than ordinary task data."
        ],
        "expected": "medium",
    },
    {
        "name": "Excessive Permissions",
        "category": "excessive_permissions",
        "description": (
            "An MCP weather lookup tool requests unrestricted "
            "filesystem read and write permissions despite "
            "only requiring access to weather information."
        ),
        "evidence": [
            "Permission inspection identified filesystem "
            "privileges unrelated to the tool's declared purpose."
        ],
        "expected": "medium",
    },
    {
        "name": "Unauthorized Data Transmission",
        "category": "network_egress",
        "description": (
            "An MCP tool transmitted contents of a synthetic "
            "configuration file to an unauthorized external "
            "endpoint during sandbox testing."
        ),
        "evidence": [
            "Sandbox network monitoring confirmed outbound "
            "transmission of planted test data."
        ],
        "expected": "high",
    },
    {
        "name": "Unexpected Filesystem Access",
        "category": "behavioral_mismatch",
        "description": (
            "An MCP tool declared as read-only attempted "
            "to access configuration files outside its "
            "authorized directory."
        ),
        "evidence": [
            "Sandbox monitoring recorded an attempted access "
            "outside the permitted filesystem scope."
        ],
        "expected": "medium",
    },
    {
        "name": "Normal MCP Activity",
        "category": "normal_behavior",
        "description": (
            "An MCP weather tool received a valid city name, "
            "queried its authorized weather service, and "
            "returned the requested forecast."
        ),
        "evidence": [
            "Runtime monitoring confirmed that the tool "
            "accessed only its authorized API endpoint. "
            "No suspicious behavior was observed."
        ],
        "expected": "informational",
    },
]


def evaluate_model(run_all=False, case_number=None):

    if case_number is not None:
        cases = [(case_number, TEST_CASES[case_number - 1])]
    elif run_all:
        cases = list(enumerate(TEST_CASES, start=1))
    else:
        cases = [(1, TEST_CASES[0])]

    correct = 0
    completed = 0
    failed = 0

    results = []

    for index, case in cases:

        print(f"\nTesting {index}: {case['name']}")

        finding = ScannerFinding(
            finding_id=f"MCP-{index:03d}",
            source="synthetic_mcp_evaluation",
            target="test-mcp-server",
            tool_name="test_tool",
            category=case["category"],
            title=case["name"],
            description=case["description"],
            scanner_severity=None,
            evidence=case["evidence"],
        )

        try:
            # Retry temporary Gemini server errors
            max_attempts = 3

            for attempt in range(max_attempts):
                try:
                    analysis = analyze_scanner_finding(finding)
                    break

                except errors.APIError as error:

                    # Retry only temporary server unavailability
                    if error.code != 503 or attempt == max_attempts - 1:
                        raise

                    delay = 2 ** (attempt + 1)

                    print(
                        f"Gemini unavailable (503). "
                        f"Retrying in {delay} seconds..."
                    )

                    time.sleep(delay)



            predicted = analysis.severity
            expected = case["expected"]

            completed += 1

            match = predicted == expected

            if match:
                correct += 1

            print(f"Expected:  {expected}")
            print(f"Predicted: {predicted}")
            print(f"Result: {'MATCH' if match else 'MISMATCH'}")
            print(f"Summary: {analysis.summary}")

            results.append({
                "scenario": case["name"],
                "expected": expected,
                "predicted": predicted,
                "match": match,
            })

        except Exception as error:
            failed += 1
            print(
                f"Evaluation failed: "
                f"{type(error).__name__}: {error}"
            )

    print("\n========== MCP EVALUATION RESULTS ==========")

    print(f"Total scenarios: {len(cases)}")
    print(f"Completed: {completed}")
    print(f"Failed requests: {failed}")
    print(f"Matching classifications: {correct}")

    if completed:
        agreement = (correct / completed) * 100
        print(f"Reference label agreement: {agreement:.2f}%")

    return results


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all six MCP security scenarios",
    )
    parser.add_argument(
        "--case",
        type=int,
        choices=range(1, 7),
        help="Evaluate a specific MCP scenario (1-6)",
    )

    args = parser.parse_args()

    evaluate_model(
    run_all=args.all,
    case_number=args.case
)
    

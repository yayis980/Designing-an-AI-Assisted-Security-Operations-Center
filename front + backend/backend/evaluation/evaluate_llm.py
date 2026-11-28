import argparse

from backend.app.ai.llm_analyzer import analyze_finding


# Synthetic security scenarios and expected classifications
TEST_CASES = [
    {
        "name": "Normal Login",
        "finding": (
            "An employee successfully logged into their assigned "
            "workstation during normal business hours using MFA. "
            "The login was authorized, and no suspicious activity "
            "was detected."
        ),
        "expected": "informational"
    },
    {
        "name": "Failed SSH Logins",
        "finding": (
            "Five failed SSH login attempts occurred within "
            "one minute. No successful login was observed."
        ),
        "expected": "low"
    },
    {
        "name": "Repeated Authentication Failures",
        "finding": (
            "120 failed SSH authentication attempts originated "
            "from six different IP addresses within five minutes. "
            "Two administrator accounts were targeted. "
            "No successful login was observed."
        ),
        "expected": "medium"
    },
    {
        "name": "Unauthorized Administrator Access",
        "finding": (
            "Incident responders confirmed that an unauthorized "
            "individual successfully accessed a privileged "
            "administrator account. No further actions have "
            "yet been confirmed."
        ),
        "expected": "high"
    },
    {
        "name": "Confirmed Ransomware",
        "finding": (
            "Security investigators confirmed ransomware "
            "encrypted files across multiple critical servers. "
            "Essential business services are currently disrupted."
        ),
        "expected": "critical"
    }
]


def evaluate_model(run_all=False):

    correct = 0
    completed = 0

    cases = TEST_CASES if run_all else TEST_CASES[:1]

    for case in cases:

        print(f"\nTesting: {case['name']}")

        try:
            analysis = analyze_finding(case["finding"])

            predicted = analysis.severity
            expected = case["expected"]

            completed += 1

            print(f"Expected:  {expected}")
            print(f"Predicted: {predicted}")

            if predicted == expected:
                correct += 1
                print("Result: MATCH")
            else:
                print("Result: MISMATCH")

            print(f"Summary: {analysis.summary}")

        except Exception as error:
            print(f"Evaluation error: {type(error).__name__}: {error}")

    print("\n--- Evaluation Results ---")

    print(f"Completed: {completed}/{len(cases)}")
    print(f"Matches: {correct}")

    if completed:
        agreement = (correct / completed) * 100
        print(f"Agreement with expected labels: {agreement:.2f}%")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all five security scenarios"
    )

    args = parser.parse_args()

    evaluate_model(run_all=args.all)
    
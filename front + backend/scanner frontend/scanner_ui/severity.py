"""One place for severity names, colors, and the score -> level mapping."""

SEVERITIES = ["Critical", "High", "Medium", "Low"]

# fg = text color, bg = badge background, bar = solid color for the chart
SEVERITY_STYLES = {
    "Critical": {"fg": "#8F1D1D", "bg": "#FCE4E4", "bar": "#B42318"},
    "High": {"fg": "#9A3E0A", "bg": "#FDEBD6", "bar": "#E8590C"},
    "Medium": {"fg": "#6B5200", "bg": "#F9F0C2", "bar": "#D4A017"},
    "Low": {"fg": "#1B8F4F", "bg": "#E1ECF8", "bar": "#1B8F4F"},
}


def level_for_score(score: int) -> str:
    if score >= 90:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def count_by_severity(findings: list) -> dict:
    return {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITIES}

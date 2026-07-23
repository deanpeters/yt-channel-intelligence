"""Domain-intelligence status (Phase 7).

Aggregates per-case corroboration results across the whole corpus into a single
trust picture: how many cases have been checked against an independent source,
how their claims held up, and — critically — any contradictions where an
independent source disagrees with the corpus. The "domain intelligence" label
is gated on this data, not asserted: until enough of the corpus is corroborated
and contradictions are resolved, the corpus stays a single-channel topical
corpus.
"""
import json
from pathlib import Path

from phases.topic_enrich import load_topic_config

# The corpus earns the "domain intelligence" label only when at least this
# share of cases are corroborated against an independent source and no
# unresolved contradictions remain. One channel alone never clears this bar.
DOMAIN_COVERAGE_THRESHOLD = 0.5


def load_corroboration_results(config: dict) -> list[dict]:
    results_dir = Path(config["workspace"]) / "corroboration"
    if not results_dir.exists():
        return []
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(results_dir.glob("*.json"))
    ]


def assess_domain(total_cases: int, results: list[dict]) -> dict:
    corroborated_cases = len(results)
    totals = {"corroborated": 0, "uncorroborated": 0, "contradicted": 0}
    contradictions = []
    for result in results:
        for check in result.get("claim_checks", []):
            status = check.get("status", "uncorroborated")
            totals[status] = totals.get(status, 0) + 1
            if status == "contradicted":
                contradictions.append({
                    "subject": result["subject"],
                    "mechanism": check.get("mechanism", ""),
                    "rationale": check.get("rationale", ""),
                })

    coverage = corroborated_cases / total_cases if total_cases else 0.0
    is_domain = (
        coverage >= DOMAIN_COVERAGE_THRESHOLD and not contradictions
    )
    return {
        "total_cases": total_cases,
        "corroborated_cases": corroborated_cases,
        "coverage": round(coverage, 3),
        "claim_totals": totals,
        "contradictions": contradictions,
        "is_domain_intelligence": is_domain,
    }


def _verdict_line(assessment: dict) -> str:
    if assessment["is_domain_intelligence"]:
        return (
            "VERDICT: corroboration is broad and contradiction-free enough to "
            "treat this as domain intelligence."
        )
    reasons = []
    if assessment["coverage"] < DOMAIN_COVERAGE_THRESHOLD:
        reasons.append(
            f"coverage {assessment['coverage']:.0%} is below the "
            f"{DOMAIN_COVERAGE_THRESHOLD:.0%} bar"
        )
    if assessment["contradictions"]:
        reasons.append(
            f"{len(assessment['contradictions'])} unresolved contradiction(s)"
        )
    return (
        "VERDICT: NOT domain intelligence yet — "
        + "; ".join(reasons)
        + ". This remains a single-channel topical corpus."
    )


def render_report(assessment: dict, results: list[dict]) -> str:
    lines = [
        "# Domain Intelligence Status",
        "",
        _verdict_line(assessment),
        "",
        f"- Cases corroborated against an independent source: "
        f"{assessment['corroborated_cases']}/{assessment['total_cases']} "
        f"({assessment['coverage']:.0%})",
        f"- Claim checks: {assessment['claim_totals']}",
        f"- Contradictions: {len(assessment['contradictions'])}",
        "",
    ]
    if assessment["contradictions"]:
        lines += ["## Contradictions (independent source disagrees)", ""]
        for c in assessment["contradictions"]:
            lines.append(
                f"- **{c['subject']}** / {c['mechanism']}: {c['rationale']}"
            )
        lines.append("")
    lines += ["## Corroborated cases", ""]
    for result in results:
        s = result.get("summary", {})
        lines.append(
            f"- **{result['subject']}** — "
            f"{s.get('corroborated', 0)} corroborated, "
            f"{s.get('uncorroborated', 0)} uncorroborated, "
            f"{s.get('contradicted', 0)} contradicted "
            f"(source: {result.get('source', 'n/a')})"
        )
    lines.append("")
    return "\n".join(lines)


def domain_status(config_path: str, output_path: str) -> tuple[str, dict]:
    config = load_topic_config(config_path)
    results = load_corroboration_results(config)
    assessment = assess_domain(len(config["cases"]), results)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        render_report(assessment, results), encoding="utf-8"
    )
    return output_path, assessment

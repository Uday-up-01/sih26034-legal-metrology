import json
from pathlib import Path
from app.schemas.inspection import ExtractedField, ComplianceResult

RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "rules_v1.json"
LOW_CONFIDENCE = 0.65


def load_rules():
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(fields: list[ExtractedField]) -> tuple[str, list[ComplianceResult], str]:
    ruleset = load_rules()
    by_name = {f.field_name: f for f in fields}
    results: list[ComplianceResult] = []

    for rule in ruleset["rules"]:
        field = by_name.get(rule["field"])
        if field is None:
            results.append(ComplianceResult(
                rule_id=rule["rule_id"], field=rule["field"], label=rule["label"],
                status="FAIL", reason="Required declaration was not detected in the submitted content."
            ))
        elif field.confidence < LOW_CONFIDENCE:
            results.append(ComplianceResult(
                rule_id=rule["rule_id"], field=rule["field"], label=rule["label"],
                status="REVIEW", reason="Declaration may be present, but extraction confidence is low.", evidence=field
            ))
        elif not field.normalized_value:
            results.append(ComplianceResult(
                rule_id=rule["rule_id"], field=rule["field"], label=rule["label"],
                status="REVIEW", reason="Declaration was detected but its value could not be parsed reliably.", evidence=field
            ))
        else:
            results.append(ComplianceResult(
                rule_id=rule["rule_id"], field=rule["field"], label=rule["label"],
                status="PASS", reason="Declaration detected and parsed by the prototype rule.", evidence=field
            ))

    statuses = {r.status for r in results}
    overall = "POSSIBLE_NON_COMPLIANCE" if "FAIL" in statuses else "MANUAL_REVIEW" if "REVIEW" in statuses else "COMPLIANT_FOR_PROTOTYPE_RULESET"
    return ruleset["ruleset_id"], results, overall

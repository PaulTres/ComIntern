"""Rule engine deciding which regulations apply to a company profile.

Each regulation YAML has an ``applicability.triggers`` list. A trigger has a
``when`` condition and a human-readable ``reason``. The regulation applies if
at least one trigger matches; all matching reasons are returned.

Conditions are either a leaf ``{field, op, value}`` or a combinator
``{all: [...]}``, ``{any: [...]}``, ``{not: {...}}``.
"""

from typing import Any

# NIS2 Annex I (sectors of high criticality) and Annex II (other critical sectors),
# mapped to the questionnaire's sector values.
NIS2_ANNEX_I = {
    "energy", "transport", "banking", "financial_market", "health", "water",
    "digital_infrastructure", "ict_services",
}
NIS2_ANNEX_II = {
    "postal", "waste", "chemicals", "food", "manufacturing", "digital_providers", "research",
}
EU_COUNTRIES = {"DE", "RO", "OTHER_EU"}


def size_class(employees: float, turnover_m: float, balance_sheet_m: float) -> str:
    """EU SME definition (Recommendation 2003/361/EC)."""
    if employees < 10 and (turnover_m <= 2 or balance_sheet_m <= 2):
        return "micro"
    if employees < 50 and (turnover_m <= 10 or balance_sheet_m <= 10):
        return "small"
    if employees < 250 and (turnover_m <= 50 or balance_sheet_m <= 43):
        return "medium"
    return "large"


def derive(profile: dict[str, Any]) -> dict[str, Any]:
    """Return the profile enriched with derived fields usable in rules."""
    p = dict(profile)
    p.setdefault("countries", [])
    for key in ("employees", "employees_de", "turnover_m", "balance_sheet_m", "dp_staff_count"):
        p[key] = float(p.get(key) or 0)
    if "DE" in p["countries"] and not profile.get("employees_de"):
        # Without a German headcount, assume everyone could be based there.
        p["employees_de"] = p["employees"] if p["countries"] == ["DE"] else 0
    p["in_eu"] = bool(EU_COUNTRIES & set(p["countries"]))
    p["size_class"] = size_class(p["employees"], p["turnover_m"], p["balance_sheet_m"])
    p["medium_or_larger"] = p["size_class"] in ("medium", "large")
    sector = p.get("sector")
    p["nis2_annex"] = "I" if sector in NIS2_ANNEX_I else "II" if sector in NIS2_ANNEX_II else None
    return p


def _leaf(cond: dict[str, Any], p: dict[str, Any]) -> bool:
    actual = p.get(cond["field"])
    op, value = cond.get("op", "eq"), cond.get("value")
    match op:
        case "eq":
            return actual == value
        case "ne":
            return actual != value
        case "truthy":
            return bool(actual)
        case "gte":
            return actual is not None and actual >= value
        case "gt":
            return actual is not None and actual > value
        case "lte":
            return actual is not None and actual <= value
        case "lt":
            return actual is not None and actual < value
        case "in":
            return actual in value
        case "contains":
            return value in (actual or [])
        case "contains_any":
            return bool(set(value) & set(actual or []))
    raise ValueError(f"Unknown operator: {op}")


def evaluate(cond: dict[str, Any], p: dict[str, Any]) -> bool:
    if "all" in cond:
        return all(evaluate(c, p) for c in cond["all"])
    if "any" in cond:
        return any(evaluate(c, p) for c in cond["any"])
    if "not" in cond:
        return not evaluate(cond["not"], p)
    return _leaf(cond, p)


def _format(reason: str, p: dict[str, Any]) -> str:
    values = {k: (int(v) if isinstance(v, float) and v.is_integer() else v) for k, v in p.items()}
    try:
        return reason.format(**values)
    except (KeyError, IndexError, ValueError):
        return reason


def assess(applicability: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    """Return the reasons why a regulation applies (empty list = not applicable)."""
    p = derive(profile)
    return [
        _format(t["reason"], p)
        for t in applicability.get("triggers", [])
        if evaluate(t["when"], p)
    ]


def visible(question: dict[str, Any], answers: dict[str, Any]) -> bool:
    """Whether a questionnaire question is shown, given its ``show_if``."""
    cond = question.get("show_if")
    return True if cond is None else evaluate(cond, answers)

"""Compliance scores.

Per regulation: sum(weight * status value) / sum(weight) over all requirements that
are not marked "not applicable". Overall: average of regulation scores weighted by
their total requirement weight.
"""

from dataclasses import dataclass

from comintern.models.compliance import ComplianceStatus

STATUS_VALUE = {
    ComplianceStatus.COMPLIANT: 1.0,
    ComplianceStatus.IN_PROGRESS: 0.5,
    ComplianceStatus.NOT_STARTED: 0.0,
}


@dataclass
class Item:
    weight: int
    status: str
    has_evidence: bool = False


@dataclass
class Score:
    score: int | None  # 0–100, None when nothing is applicable
    weight: int
    total: int
    compliant: int
    in_progress: int
    not_started: int
    not_applicable: int
    evidenced: int

    @property
    def level(self) -> str:
        return level(self.score)


def score_items(items: list[Item]) -> Score:
    applicable = [i for i in items if i.status != ComplianceStatus.NOT_APPLICABLE]
    weight = sum(i.weight for i in applicable)
    achieved = sum(i.weight * STATUS_VALUE.get(i.status, 0.0) for i in applicable)
    return Score(
        score=round(100 * achieved / weight) if weight else None,
        weight=weight,
        total=len(items),
        compliant=sum(i.status == ComplianceStatus.COMPLIANT for i in items),
        in_progress=sum(i.status == ComplianceStatus.IN_PROGRESS for i in items),
        not_started=sum(i.status == ComplianceStatus.NOT_STARTED for i in items),
        not_applicable=sum(i.status == ComplianceStatus.NOT_APPLICABLE for i in items),
        evidenced=sum(i.has_evidence for i in applicable),
    )


def overall(scores: list[Score]) -> int | None:
    scored = [s for s in scores if s.score is not None]
    weight = sum(s.weight for s in scored)
    if not weight:
        return None
    return round(sum(s.score * s.weight for s in scored) / weight)


def level(score: int | None) -> str:
    if score is None:
        return "none"
    return "green" if score >= 80 else "amber" if score >= 50 else "red"

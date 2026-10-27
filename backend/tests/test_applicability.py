import pytest

from app import catalog
from app.services.applicability import assess, size_class

REGS = {r["code"]: r for r in catalog.regulation_entries()}


def applicable(profile):
    return {code for code, r in REGS.items() if assess(r["applicability"], profile)}


GERMAN_SME = {
    "countries": ["DE"], "employees": 80, "turnover_m": 12, "balance_sheet_m": 8, "sector": "manufacturing",
    "processes_personal_data": True, "ai_usage": "uses", "financial_entity": False, "aml_obliged": False,
}
ROMANIAN_BANK = {
    "countries": ["RO"], "employees": 2500, "turnover_m": 600, "balance_sheet_m": 9000, "sector": "banking",
    "processes_personal_data": True, "ai_usage": "none", "financial_entity": True, "aml_obliged": True,
}
AI_STARTUP = {
    "countries": ["OTHER_EU"], "employees": 12, "turnover_m": 1.5, "balance_sheet_m": 1, "sector": "software",
    "processes_personal_data": True, "ai_usage": "provides", "financial_entity": False, "aml_obliged": False,
}


def test_german_sme():
    assert applicable(GERMAN_SME) == {
        "EU_GDPR", "DE_BDSG", "EU_NIS2", "DE_NIS2_BSIG", "EU_AI_ACT", "DE_HINSCHG",
    }


def test_romanian_bank():
    assert applicable(ROMANIAN_BANK) == {
        "EU_GDPR", "RO_LAW_190_2018", "EU_NIS2", "RO_NIS2", "EU_DORA", "EU_CSRD",
        "RO_LAW_361_2022", "RO_LAW_129_2019", "RO_EFACTURA",
    }


def test_ai_startup():
    assert applicable(AI_STARTUP) == {"EU_GDPR", "EU_AI_ACT"}


def test_reason_is_formatted():
    reasons = assess(REGS["DE_HINSCHG"]["applicability"], GERMAN_SME)
    assert reasons == ["You employ 80 people and operate in Germany (threshold 50)."]


def test_lksg_uses_german_headcount():
    profile = {**GERMAN_SME, "countries": ["DE", "RO"], "employees": 3000, "employees_de": 400}
    assert "DE_LKSG" not in applicable(profile)
    assert "DE_LKSG" in applicable({**profile, "employees_de": 1200})


@pytest.mark.parametrize(
    "employees,turnover,balance,expected",
    [(5, 1, 1, "micro"), (40, 8, 20, "small"), (40, 20, 20, "medium"), (200, 60, 40, "medium"), (300, 10, 10, "large")],
)
def test_size_class(employees, turnover, balance, expected):
    assert size_class(employees, turnover, balance) == expected

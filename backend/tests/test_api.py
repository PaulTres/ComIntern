import io

from fastapi.testclient import TestClient

from app.main import app

PROFILE = {
    "countries": ["DE"], "b2c": True, "employees": 120, "turnover_m": 30, "balance_sheet_m": 20,
    "sector": "software", "processes_personal_data": True, "special_category_data": False,
    "dp_staff_count": 25, "ai_usage": "uses", "ai_high_risk": False, "financial_entity": False,
    "ict_provider_to_finance": False, "listed": False, "aml_obliged": False, "non_eu_supply_chain": True,
}


def test_full_flow():
    with TestClient(app) as client:
        r = client.post("/api/auth/register", json={"email": "a@b.de", "password": "secret123", "company_name": "Acme"})
        assert r.status_code == 201
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        assert client.get("/api/dashboard").status_code == 401
        assert client.get("/api/questionnaire").json()["steps"]

        bad = client.put("/api/company", json={"profile": {"countries": ["XX"]}}, headers=headers)
        assert bad.status_code == 422

        r = client.put("/api/company", json={"profile": PROFILE}, headers=headers)
        assert r.status_code == 200, r.text

        regs = {x["code"] for x in client.get("/api/company/regulations", headers=headers).json()}
        assert regs == {"EU_GDPR", "DE_BDSG", "EU_AI_ACT", "DE_HINSCHG"}

        detail = client.get("/api/regulations/EU_GDPR", headers=headers).json()
        assert detail["score"]["score"] == 0
        req_id = detail["requirements"][0]["id"]

        r = client.put(f"/api/requirements/{req_id}/status", json={"status": "compliant"}, headers=headers)
        assert r.json()["status"] == "compliant"

        r = client.post(
            "/api/documents", headers=headers, data={"requirement_id": str(req_id)},
            files={"file": ("ropa.txt", io.BytesIO(b"Record of processing activities"), "text/plain")},
        )
        assert r.status_code == 201, r.text
        assert r.json()["has_text"] and r.json()["regulation_code"] == "EU_GDPR"

        dash = client.get("/api/dashboard", headers=headers).json()
        assert dash["overall_score"] > 0
        assert dash["totals"]["evidenced"] == 1
        assert dash["recent_documents"][0]["filename"] == "ropa.txt"

        assert client.get("/api/regulations/EU_DORA", headers=headers).status_code == 404
        assert client.post("/api/assistant/ask", json={"question": "Hi"}, headers=headers).json()["available"] is False

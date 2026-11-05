import io
import json

from fastapi.testclient import TestClient

from tests.conftest import GREETING

PROFILE = {
    "countries": ["DE"],
    "b2c": True,
    "employees": 120,
    "turnover_m": 30,
    "balance_sheet_m": 20,
    "sector": "software",
    "processes_personal_data": True,
    "special_category_data": False,
    "dp_staff_count": 25,
    "ai_usage": "uses",
    "ai_high_risk": False,
    "financial_entity": False,
    "ict_provider_to_finance": False,
    "listed": False,
    "aml_obliged": False,
    "non_eu_supply_chain": True,
}


def register(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.de", "password": "secret123", "company_name": "Acme"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_full_compliance_flow(client: TestClient) -> None:
    headers = register(client)

    assert client.get("/api/v1/dashboard").status_code == 401
    assert client.get("/api/v1/questionnaire").json()["steps"]

    bad = client.put(
        "/api/v1/company", json={"profile": {"countries": ["XX"]}}, headers=headers
    )
    assert bad.status_code == 422
    assert bad.json()["detail"]["errors"]

    response = client.put("/api/v1/company", json={"profile": PROFILE}, headers=headers)
    assert response.status_code == 200, response.text

    codes = {
        row["code"]
        for row in client.get("/api/v1/company/regulations", headers=headers).json()
    }
    assert codes == {"EU_GDPR", "DE_BDSG", "EU_AI_ACT", "DE_HINSCHG"}

    detail = client.get("/api/v1/regulations/EU_GDPR", headers=headers).json()
    assert detail["score"]["score"] == 0
    requirement_id = detail["requirements"][0]["id"]

    response = client.put(
        f"/api/v1/requirements/{requirement_id}/status",
        json={"status": "compliant"},
        headers=headers,
    )
    assert response.json()["status"] == "compliant"

    response = client.post(
        "/api/v1/documents",
        headers=headers,
        data={"requirement_id": str(requirement_id)},
        files={
            "file": (
                "ropa.txt",
                io.BytesIO(b"Record of processing activities"),
                "text/plain",
            )
        },
    )
    assert response.status_code == 201, response.text
    document = response.json()
    assert document["has_text"] and document["regulation_code"] == "EU_GDPR"

    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["overall_score"] > 0
    assert dashboard["totals"]["evidenced"] == 1
    assert dashboard["recent_documents"][0]["filename"] == "ropa.txt"

    assert client.get("/api/v1/regulations/EU_DORA", headers=headers).status_code == 404
    assert (
        client.delete(
            f"/api/v1/documents/{document['id']}", headers=headers
        ).status_code
        == 204
    )
    assert client.get("/api/v1/documents", headers=headers).json() == []


def test_chat_streams_and_saves_the_turn(client: TestClient) -> None:
    headers = register(client)

    with client.stream(
        "POST", "/api/v1/chat/stream", json={"content": "Hi"}, headers=headers
    ) as response:
        assert response.status_code == 200
        events = [
            line.removeprefix("event: ")
            for line in response.iter_lines()
            if line.startswith("event: ")
        ]
    assert events[0] == "progress" and events[-1] == "final"

    conversations = client.get("/api/v1/conversations", headers=headers).json()
    messages = client.get(
        f"/api/v1/conversations/{conversations[0]['id']}/messages", headers=headers
    ).json()
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["content"] == GREETING

    other = client.post(
        "/api/v1/auth/register",
        json={"email": "c@d.ro", "password": "secret123", "company_name": "Other"},
    ).json()
    response = client.post(
        "/api/v1/chat/stream",
        json={"content": "Hi", "conversation_id": conversations[0]["id"]},
        headers={"Authorization": f"Bearer {other['access_token']}"},
    )
    assert response.status_code == 404
    assert json.loads(response.text)["code"] == "CONVERSATION_NOT_FOUND"

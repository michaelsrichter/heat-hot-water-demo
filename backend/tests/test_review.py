from pathlib import Path

from fastapi.testclient import TestClient

from app.briefings import _responses_url
from app.fixtures import ScenarioRepository
from app.main import app
from app.services import ProvisionalEligibilityEvaluator, ReviewCoordinator

FIXTURE = Path(__file__).parents[1] / "data" / "practice-scenarios.json"


def test_starting_scenario_has_two_eligible_items() -> None:
    run = ReviewCoordinator(ScenarioRepository(FIXTURE)).run("winter-start")

    assert run.eligible_count == 2
    assert run.strategy_count == 2
    assert {item.building_id for item in run.items} == {"BLD-101", "BLD-103", "BLD-105"}
    assert {item.state for item in run.items} == {"new", "needs_verification"}
    assert {item.owner_team for item in run.items} == {
        "Bronx Response Team",
        "Brooklyn Heights Response Team",
        "Manhattan Housing Response Team",
    }
    assert all(item.action_plan for item in run.items)


def test_later_scenario_carries_items_forward_and_handles_closed_violation() -> None:
    run = ReviewCoordinator(ScenarioRepository(FIXTURE)).run("one-week-later")

    assert run.eligible_count == 4
    assert run.strategy_count == 4
    by_id = {item.building_id: item for item in run.items}
    assert by_id["BLD-101"].state == "carried_forward"
    assert by_id["BLD-102"].state == "new"
    assert by_id["BLD-103"].state == "needs_verification"
    assert by_id["BLD-104"].state == "new"
    assert "BLD-105" not in by_id
    assert by_id["BLD-106"].state == "new"


def test_review_can_focus_on_one_service_area() -> None:
    run = ReviewCoordinator(ScenarioRepository(FIXTURE)).run(
        "winter-start", "Brooklyn Heights"
    )

    assert {item.building_id for item in run.items} == {"BLD-105"}
    assert run.eligible_count == 1
    assert run.strategy_count == 1


def test_practice_source_record_is_a_readable_page() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/practice-records/winter-start/BLD-101",
        )

    assert response.status_code == 200
    assert "River Court" in response.text
    assert "Synthetic practice record" in response.text
    assert "BLD-101" in response.text
    assert "Resident" not in response.text


def test_missing_practice_source_record_is_not_found() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/practice-records/winter-start/not-a-building",
        )

    assert response.status_code == 404


def test_missing_scenario_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/reviews/run",
            headers={"X-Demo-Session": "12345678-1234-1234-1234-123456789012"},
            json={"scenario_id": "not-real"},
        )

    assert response.status_code == 404


def test_unbounded_session_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/reviews/run",
            json={"scenario_id": "winter-start"},
        )

    assert response.status_code == 400


def test_review_is_rate_limited() -> None:
    headers = {"X-Demo-Session": "rate-limit-session-123456789012345"}
    with TestClient(app) as client:
        responses = [
            client.post(
                "/api/reviews/run",
                headers=headers,
                json={"scenario_id": "winter-start"},
            )
            for _ in range(7)
        ]

    assert responses[-1].status_code == 429


def test_future_recorded_date_is_not_eligible() -> None:
    repository = ScenarioRepository(FIXTURE)
    scenario = repository.by_id("winter-start")
    building = next(item for item in scenario.buildings if item.building_id == "BLD-102")

    eligible, reason = ProvisionalEligibilityEvaluator().evaluate(
        building, scenario.simulated_review_date
    )

    assert eligible is False
    assert "not passed" in reason


def test_health_is_explicitly_a_practice_state() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "available"
    assert response.json()["checks"]["strategy"] == "adls_scheduled"
    assert response.json()["checks"]["foundry"] == "practice"


def test_overview_exposes_the_adls_to_strategy_process() -> None:
    with TestClient(app) as client:
        response = client.get("/api/overview")

    pipeline = response.json()["data_pipeline"]
    assert response.status_code == 200
    assert pipeline["mode"] == "adls-gen2-strategy"
    assert [step["id"] for step in pipeline["steps"]] == [
        "public-data",
        "prepare",
        "store",
        "connect",
        "model",
        "briefing",
        "present",
    ]
    assert response.json()["strategy_connection"] == "adls_scheduled"
    assert "Brooklyn Heights" in response.json()["service_areas"]


def test_practice_review_includes_a_cited_strategy_briefing() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/reviews/run",
            headers={"X-Demo-Session": "briefing-session-12345678901234567"},
            json={"scenario_id": "winter-start"},
        )

    briefing = response.json()["briefing"]
    assert response.status_code == 200
    assert briefing["mode"] == "practice"
    assert "Strategy Mosaic" in briefing["text"]
    assert "Action plan by service area" in briefing["text"]
    assert "Bronx Response Team" in briefing["text"]
    assert briefing["citations"]


def test_foundry_endpoint_preserves_the_protocol_query_string() -> None:
    endpoint = (
        "https://example.services.ai.azure.com/api/projects/demo/agents/"
        "hpd/endpoint/protocols/openai/responses?api-version=v1"
    )

    assert _responses_url(endpoint) == endpoint

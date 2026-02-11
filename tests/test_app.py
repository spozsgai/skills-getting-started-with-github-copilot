import copy
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, Client

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    baseline = copy.deepcopy(activities)
    activities.clear()
    activities.update(copy.deepcopy(baseline))
    yield
    activities.clear()
    activities.update(copy.deepcopy(baseline))


def create_client():
    transport = ASGITransport(app=app)
    return Client(transport=transport, base_url="http://test")


def test_get_activities_returns_data():
    with create_client() as client:
        response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Basketball Team" in payload
    assert "participants" in payload["Basketball Team"]


def test_signup_adds_participant():
    email = "newstudent@mergington.edu"
    with create_client() as client:
        response = client.post("/activities/Basketball%20Team/signup", params={"email": email})

    assert response.status_code == 200
    assert email in activities["Basketball Team"]["participants"]


def test_signup_rejects_duplicate():
    email = activities["Soccer Club"]["participants"][0]
    with create_client() as client:
        response = client.post("/activities/Soccer%20Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_unknown_activity():
    with create_client() as client:
        response = client.post("/activities/Unknown/signup", params={"email": "test@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant():
    email = activities["Drama Club"]["participants"][0]
    with create_client() as client:
        response = client.delete("/activities/Drama%20Club/participants", params={"email": email})

    assert response.status_code == 200
    assert email not in activities["Drama Club"]["participants"]


def test_unregister_missing_participant():
    with create_client() as client:
        response = client.delete(
            "/activities/Math%20Club/participants",
            params={"email": "missing@mergington.edu"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"

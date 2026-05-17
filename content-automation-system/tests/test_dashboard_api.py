import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_dashboard_pages_and_core_endpoints():
    assert client.get("/").status_code == 200
    assert client.get("/jobs-page").status_code == 200
    assert client.get("/new-batch").status_code == 200

    stats = client.get("/stats")
    assert stats.status_code == 200
    assert "total" in stats.json()

    health = client.get("/status")
    assert health.status_code == 200
    assert health.json()["db_status"] in {"online", "offline"}

    prompts = client.get("/prompts")
    assert prompts.status_code == 200
    assert len(prompts.json()["prompts"]) >= 4

    settings = client.get("/settings")
    assert settings.status_code == 200
    assert "settings" in settings.json()


def test_job_detail_and_controls():
    job_id = main.state.create_job("dashboard api smoke")

    detail = client.get(f"/jobs/{job_id}")
    assert detail.status_code == 200
    assert detail.json()["keyword"] == "dashboard api smoke"
    assert "artifacts" in detail.json()
    assert "progress" in detail.json()

    assert client.post(f"/jobs/{job_id}/pause", json={"reason": "test"}).json()["action"] == "paused"
    assert client.post(f"/jobs/{job_id}/resume", json={"reason": "test"}).json()["action"] == "active"
    canceled = client.post(f"/jobs/{job_id}/cancel", json={"reason": "test"}).json()
    assert canceled["action"] == "canceled"
    assert canceled["status"] == "canceled"
    assert client.get(f"/jobs/{job_id}").json()["status"] == "canceled"


def test_prompt_and_settings_updates():
    old_prompt = next(p for p in client.get("/prompts").json()["prompts"] if p["id"] == "article")["content"]
    prompt = client.put("/prompts/article", json={"content": "Write about {keyword}"}).json()
    assert prompt["content"] == "Write about {keyword}"

    tested = client.post("/prompts/article/test", json={"keyword": "brownies"}).json()
    assert "brownies" in tested["output"]
    client.put("/prompts/article", json={"content": old_prompt})

    settings = client.put(
        "/settings",
        json={"section": "execution", "value": {"worker_concurrency": 9, "max_retries": 2}},
    ).json()
    assert settings["settings"]["execution"]["worker_concurrency"] == 1

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_job():
    response = client.get("/api/get-job")
    assert response.status_code == 200
    assert "title" in response.json()

def test_extract_resume():
    payload = {
        "resume_text": "Experienced engineer with Docker, Python, Kubernetes, AWS, Terraform, CI/CD, and Linux skills.",
        "target_role": "Senior DevOps & Cloud Architect"
    }
    response = client.post("/extract-resume", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "docker" in data["detected_skills"]
    assert "python" in data["detected_skills"]
    assert data["suitability_score"] >= 60


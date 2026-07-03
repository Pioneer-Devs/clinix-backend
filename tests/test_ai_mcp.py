import pytest
from app.models.enums import EncounterStatus


def test_analyze_symptoms_direct(client, student_auth_headers):
    # Test direct symptom analysis endpoint (does not save to db)
    response = client.post(
        "/api/v1/ai/analyze-symptoms",
        headers=student_auth_headers,
        json={
            "chief_complaint": "High fever, headache, shivering, joint pain",
            "associated_symptoms": ["Fever", "Headache", "Joint Pain", "Chills"],
            "vitals": {"temperature": 39.2, "blood_pressure": "120/80"},
            "patient_age": 28,
            "patient_gender": "female",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "analysis" in data
    analysis = data["analysis"]
    assert "primary_diagnosis" in analysis
    assert "Probable Malaria" in analysis["primary_diagnosis"]
    assert analysis["confidence"] > 0.8
    assert "mcp_actions" in analysis
    assert len(analysis["mcp_actions"]) > 0


def test_encounter_ai_analyze_and_logs(client, student_auth_headers, test_patient):
    # 1. Create a draft encounter
    response = client.post(
        "/api/v1/encounters",
        headers=student_auth_headers,
        json={
            "patient_id": str(test_patient.id),
            "chief_complaint": "Severe chest pain and shortness of breath",
            "associated_symptoms": ["Chest Pain", "Dyspnea"],
            "vitals": {"pulse": 110, "spo2": 93, "blood_pressure": "140/90"},
        }
    )
    assert response.status_code == 201
    encounter_id = response.json()["id"]

    # 2. Trigger AI analysis on the encounter
    response = client.post(
        f"/api/v1/encounters/{encounter_id}/ai-analyze",
        headers=student_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["encounter_id"] == encounter_id
    assert data["status"] == "completed"
    assert "analysis" in data
    
    analysis = data["analysis"]
    assert "Acute Coronary Syndrome" in analysis["primary_diagnosis"]
    assert analysis["urgency"] == "emergency"
    
    # 3. Retrieve the encounter to verify AI fields are populated
    response = client.get(
        f"/api/v1/encounters/{encounter_id}",
        headers=student_auth_headers
    )
    assert response.status_code == 200
    encounter = response.json()
    assert encounter["ai_diagnosis"] == analysis["primary_diagnosis"]
    assert encounter["ai_confidence"] == analysis["confidence"]
    assert encounter["ai_differential"] is not None
    assert len(encounter["ai_actions_triggered"]) > 0

    # 4. Check the MCP skill execution logs for this encounter
    response = client.get(
        f"/api/v1/mcp/encounters/{encounter_id}/skill-logs",
        headers=student_auth_headers
    )
    assert response.status_code == 200
    logs_data = response.json()
    assert logs_data["encounter_id"] == encounter_id
    assert logs_data["total"] > 0
    
    log = logs_data["skill_logs"][0]
    assert log["skill_name"] == "cardiac_alert"
    assert log["success"] is True
    assert log["execution_time_ms"] >= 0


def test_list_mcp_skills(client, student_auth_headers):
    # Test GET /mcp/skills
    response = client.get("/api/v1/mcp/skills", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert data["total"] == 4
    skills = [s["skill"] for s in data["skills"]]
    assert "malaria_detect" in skills
    assert "cardiac_alert" in skills


def test_inventory_endpoints(client, student_auth_headers):
    # Test drug check
    response = client.get(
        "/api/v1/inventory/drugs?name=coartem",
        headers=student_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["brand_name"] == "Coartem"
    assert data["available"] is True
    assert data["stock"] > 0

    # Test test check
    response = client.get(
        "/api/v1/inventory/tests?name=malaria",
        headers=student_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert "Malaria" in data["test"]
    assert data["available"] is True

    # Test full inventory
    response = client.get("/api/v1/inventory", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "drugs" in data
    assert "tests" in data
    assert len(data["drugs"]) > 0

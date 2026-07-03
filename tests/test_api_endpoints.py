"""Integration tests for the new API endpoints.

All tests bypass auth by using `authed_student_client` / `authed_supervisor_client`
fixtures which override `get_current_user` directly — no JWT, no login, no auth module.
"""

import pytest


# ── POST /api/v1/ai/analyze-symptoms ─────────────────────────────────────────

class TestAnalyzeSymptomsEndpoint:
    """Tests for the direct symptom analysis endpoint."""

    def test_malaria_diagnosis(self, authed_student_client):
        """Malaria symptoms return correct diagnosis."""
        response = authed_student_client.post(
            "/api/v1/ai/analyze-symptoms",
            json={
                "chief_complaint": "High fever, headache, shivering, joint pain",
                "associated_symptoms": ["Fever", "Headache", "Joint Pain", "Chills"],
                "vitals": {"temperature": 39.2, "blood_pressure": "120/80"},
                "patient_age": 28,
                "patient_gender": "F",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        analysis = data["analysis"]
        assert "Malaria" in analysis["primary_diagnosis"]
        assert analysis["confidence"] > 0.8
        assert len(analysis["mcp_actions"]) > 0

    def test_cardiac_emergency(self, authed_student_client):
        """Cardiac symptoms return emergency urgency."""
        response = authed_student_client.post(
            "/api/v1/ai/analyze-symptoms",
            json={
                "chief_complaint": "Severe chest pain and shortness of breath",
                "associated_symptoms": ["Chest Pain", "Dyspnea"],
                "vitals": {"pulse": 130, "spo2": 91},
            },
        )
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        assert "Acute Coronary Syndrome" in analysis["primary_diagnosis"]
        assert analysis["urgency"] == "emergency"

    def test_diabetes_diagnosis(self, authed_student_client):
        """Diabetes symptoms return correct diagnosis."""
        response = authed_student_client.post(
            "/api/v1/ai/analyze-symptoms",
            json={
                "chief_complaint": "Excessive thirst, frequent urinating, weight loss",
                "associated_symptoms": ["Polydipsia", "Polyuria"],
            },
        )
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        assert "Diabetes" in analysis["primary_diagnosis"]

    def test_prenatal_diagnosis(self, authed_student_client):
        """Prenatal keywords return prenatal assessment."""
        response = authed_student_client.post(
            "/api/v1/ai/analyze-symptoms",
            json={
                "chief_complaint": "Routine prenatal visit at 32 week gestation",
            },
        )
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        assert "Prenatal" in analysis["primary_diagnosis"]

    def test_generic_fallback(self, authed_student_client):
        """Unknown symptoms return generic analysis with low confidence."""
        response = authed_student_client.post(
            "/api/v1/ai/analyze-symptoms",
            json={
                "chief_complaint": "Mild elbow pain after gardening",
            },
        )
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        assert analysis["confidence"] < 0.5
        assert "note" in analysis

    def test_vitals_alerts_included(self, authed_student_client):
        """Abnormal vitals in request produce vitals_alerts."""
        response = authed_student_client.post(
            "/api/v1/ai/analyze-symptoms",
            json={
                "chief_complaint": "fever headache chills",
                "vitals": {"temperature": 40.0, "spo2": 85},
            },
        )
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        assert "vitals_alerts" in analysis
        assert len(analysis["vitals_alerts"]) >= 2

    def test_metadata_in_response(self, authed_student_client):
        """Response includes analysis_metadata."""
        response = authed_student_client.post(
            "/api/v1/ai/analyze-symptoms",
            json={"chief_complaint": "cough"},
        )
        assert response.status_code == 200
        meta = response.json()["analysis"]["analysis_metadata"]
        assert "engine" in meta
        assert "processing_time_ms" in meta


# ── GET /api/v1/inventory ────────────────────────────────────────────────────

class TestInventoryEndpoints:
    """Tests for the inventory API endpoints."""

    def test_check_drug_found(self, authed_student_client):
        """Drug search returns found=True for known drug."""
        response = authed_student_client.get("/api/v1/inventory/drugs?name=paracetamol")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is True
        assert data["brand_name"] == "Panadol"
        assert data["available"] is True

    def test_check_drug_by_brand(self, authed_student_client):
        """Drug search by brand name works."""
        response = authed_student_client.get("/api/v1/inventory/drugs?name=coartem")
        assert response.status_code == 200
        assert response.json()["found"] is True

    def test_check_drug_not_found(self, authed_student_client):
        """Unknown drug returns found=False."""
        response = authed_student_client.get("/api/v1/inventory/drugs?name=zyrtec")
        assert response.status_code == 200
        assert response.json()["found"] is False

    def test_check_test_found(self, authed_student_client):
        """Test search returns found=True for known test."""
        response = authed_student_client.get("/api/v1/inventory/tests?name=ecg")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is True
        assert "ECG" in data["test"]

    def test_check_test_not_found(self, authed_student_client):
        """Unknown test returns found=False."""
        response = authed_student_client.get("/api/v1/inventory/tests?name=MRI")
        assert response.status_code == 200
        assert response.json()["found"] is False

    def test_full_inventory(self, authed_student_client):
        """Full inventory returns drugs and tests sections."""
        response = authed_student_client.get("/api/v1/inventory")
        assert response.status_code == 200
        data = response.json()
        assert "drugs" in data
        assert "tests" in data
        assert len(data["drugs"]) > 0
        assert len(data["tests"]) > 0


# ── GET /api/v1/mcp/skills ──────────────────────────────────────────────────

class TestMCPSkillsEndpoint:
    """Tests for the MCP skills listing endpoint."""

    def test_list_skills(self, authed_student_client):
        """Skills listing returns 4 active skills."""
        response = authed_student_client.get("/api/v1/mcp/skills")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert data["engine_status"] == "active"
        skill_names = [s["skill"] for s in data["skills"]]
        assert "malaria_detect" in skill_names
        assert "cardiac_alert" in skill_names
        assert "prenatal_screening" in skill_names
        assert "diabetes_management" in skill_names


# ── POST /api/v1/encounters/{id}/ai-analyze ──────────────────────────────────

class TestEncounterAIAnalyze:
    """Tests for the encounter-level AI analysis endpoint."""

    def _create_encounter(self, client, patient_id, chief_complaint, symptoms=None, vitals=None):
        """Helper to create a draft encounter."""
        payload = {
            "patient_id": str(patient_id),
            "chief_complaint": chief_complaint,
        }
        if symptoms:
            payload["associated_symptoms"] = symptoms
        if vitals:
            payload["vitals"] = vitals
        response = client.post("/api/v1/encounters", json=payload)
        assert response.status_code == 201
        return response.json()["id"]

    def test_ai_analyze_encounter(self, authed_student_client, test_patient):
        """AI analysis on an encounter returns completed status and persists results."""
        enc_id = self._create_encounter(
            authed_student_client,
            test_patient.id,
            "Severe chest pain and shortness of breath",
            symptoms=["Chest Pain", "Dyspnea"],
            vitals={"pulse": 110, "spo2": 93},
        )

        response = authed_student_client.post(f"/api/v1/encounters/{enc_id}/ai-analyze")
        assert response.status_code == 200
        data = response.json()
        assert data["encounter_id"] == enc_id
        assert data["status"] == "completed"
        assert "Acute Coronary Syndrome" in data["analysis"]["primary_diagnosis"]

        # Verify AI fields are persisted on the encounter
        enc_response = authed_student_client.get(f"/api/v1/encounters/{enc_id}")
        assert enc_response.status_code == 200
        enc = enc_response.json()
        assert enc["ai_diagnosis"] is not None
        assert enc["ai_confidence"] is not None

    def test_ai_analyze_not_found(self, authed_student_client):
        """404 for nonexistent encounter."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = authed_student_client.post(f"/api/v1/encounters/{fake_id}/ai-analyze")
        assert response.status_code == 404

    def test_ai_analyze_malaria_encounter(self, authed_student_client, test_patient):
        """Malaria encounter analysis returns correct diagnosis and MCP actions."""
        enc_id = self._create_encounter(
            authed_student_client,
            test_patient.id,
            "High fever, headache, and chills for 3 days",
            symptoms=["Fever", "Headache", "Chills"],
            vitals={"temperature": 39.2},
        )

        response = authed_student_client.post(f"/api/v1/encounters/{enc_id}/ai-analyze")
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        assert "Malaria" in analysis["primary_diagnosis"]
        assert analysis["urgency"] == "routine"
        assert len(analysis["mcp_actions"]) > 0


# ── GET /api/v1/mcp/encounters/{id}/skill-logs ──────────────────────────────

class TestMCPSkillLogs:
    """Tests for the MCP skill logs endpoint."""

    def test_skill_logs_after_analysis(self, authed_student_client, test_patient):
        """Skill logs are created after AI analysis triggers MCP skills."""
        # Create and analyze
        payload = {
            "patient_id": str(test_patient.id),
            "chief_complaint": "Severe chest pain and shortness of breath",
            "associated_symptoms": ["Chest Pain", "Dyspnea"],
            "vitals": {"pulse": 110, "spo2": 93},
        }
        create_resp = authed_student_client.post("/api/v1/encounters", json=payload)
        enc_id = create_resp.json()["id"]
        authed_student_client.post(f"/api/v1/encounters/{enc_id}/ai-analyze")

        # Check skill logs
        response = authed_student_client.get(f"/api/v1/mcp/encounters/{enc_id}/skill-logs")
        assert response.status_code == 200
        data = response.json()
        assert data["encounter_id"] == enc_id
        assert data["total"] > 0
        log = data["skill_logs"][0]
        assert log["skill_name"] == "cardiac_alert"
        assert log["success"] is True
        assert log["execution_time_ms"] >= 0

    def test_skill_logs_not_found(self, authed_student_client):
        """404 for nonexistent encounter skill logs."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = authed_student_client.get(f"/api/v1/mcp/encounters/{fake_id}/skill-logs")
        assert response.status_code == 404

    def test_no_logs_for_generic_case(self, authed_student_client, test_patient):
        """Generic analysis produces no skill logs."""
        payload = {
            "patient_id": str(test_patient.id),
            "chief_complaint": "Mild elbow pain after gardening",
        }
        create_resp = authed_student_client.post("/api/v1/encounters", json=payload)
        enc_id = create_resp.json()["id"]
        authed_student_client.post(f"/api/v1/encounters/{enc_id}/ai-analyze")

        response = authed_student_client.get(f"/api/v1/mcp/encounters/{enc_id}/skill-logs")
        assert response.status_code == 200
        assert response.json()["total"] == 0

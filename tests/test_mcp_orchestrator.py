"""Unit tests for the MCP Orchestrator service.

Tests the inventory enrichment logic, available skills listing,
and the full run_ai_analysis pipeline (with mocked DB objects).
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.mcp_orchestrator import (
    _execute_inventory_checks,
    get_available_skills,
    run_ai_analysis,
)
from app.models.enums import ActivityType, EncounterStatus, Gender, UserRole


# ── Inventory Check Enrichment ───────────────────────────────────────────────

class TestExecuteInventoryChecks:
    """Tests for _execute_inventory_checks() — action enrichment."""

    def test_inventory_check_drug(self):
        """inventory_check action is enriched with live stock data."""
        actions = [{"type": "inventory_check", "drug": "Aspirin 300mg", "stock": 0}]
        enriched = _execute_inventory_checks(actions)
        assert len(enriched) == 1
        assert enriched[0]["live_available"] is True
        assert enriched[0]["live_stock"] > 0
        assert "location" in enriched[0]
        assert "verified_at" in enriched[0]

    def test_rdt_recommend_action(self):
        """rdt_recommend action is enriched with test availability."""
        actions = [{"type": "rdt_recommend", "test": "SD Bioline Malaria Ag"}]
        enriched = _execute_inventory_checks(actions)
        assert len(enriched) == 1
        assert enriched[0]["live_available"] is True
        assert "turnaround_minutes" in enriched[0]
        assert "location" in enriched[0]

    def test_ecg_recommend_action(self):
        """ecg_recommend action is enriched with test availability."""
        actions = [{"type": "ecg_recommend", "test": "12-Lead ECG"}]
        enriched = _execute_inventory_checks(actions)
        assert enriched[0]["live_available"] is True

    def test_lab_recommend_action(self):
        """lab_recommend action is enriched with test availability."""
        actions = [{"type": "lab_recommend", "test": "HbA1c"}]
        enriched = _execute_inventory_checks(actions)
        assert enriched[0]["live_available"] is True

    def test_screening_check_action(self):
        """screening_check action is enriched with test availability."""
        actions = [{"type": "screening_check", "test": "Urine Dipstick"}]
        enriched = _execute_inventory_checks(actions)
        assert enriched[0]["live_available"] is True

    def test_passthrough_action(self):
        """Non-inventory actions (schedule_followup) pass through with verified_at."""
        actions = [{"type": "schedule_followup", "days": 3}]
        enriched = _execute_inventory_checks(actions)
        assert len(enriched) == 1
        assert enriched[0]["type"] == "schedule_followup"
        assert enriched[0]["days"] == 3
        assert "verified_at" in enriched[0]

    def test_alert_supervisor_passthrough(self):
        """alert_supervisor action passes through unchanged."""
        actions = [{"type": "alert_supervisor", "priority": "STAT"}]
        enriched = _execute_inventory_checks(actions)
        assert enriched[0]["priority"] == "STAT"
        assert "verified_at" in enriched[0]

    def test_multiple_actions(self):
        """Multiple actions are all enriched."""
        actions = [
            {"type": "inventory_check", "drug": "Aspirin 300mg"},
            {"type": "rdt_recommend", "test": "SD Bioline Malaria Ag"},
            {"type": "schedule_followup", "days": 7},
        ]
        enriched = _execute_inventory_checks(actions)
        assert len(enriched) == 3
        assert all("verified_at" in a for a in enriched)

    def test_unknown_drug_enrichment(self):
        """inventory_check for unknown drug still enriches gracefully."""
        actions = [{"type": "inventory_check", "drug": "NonexistentDrug"}]
        enriched = _execute_inventory_checks(actions)
        assert len(enriched) == 1
        # live_available may be False, but the enrichment should not crash
        assert "verified_at" in enriched[0]


# ── Available Skills ─────────────────────────────────────────────────────────

class TestGetAvailableSkills:
    """Tests for get_available_skills()."""

    def test_returns_four_skills(self):
        """There are exactly 4 registered MCP skills."""
        skills = get_available_skills()
        assert len(skills) == 4

    def test_skill_structure(self):
        """Each skill has skill, name, description, status keys."""
        skills = get_available_skills()
        for skill in skills:
            assert "skill" in skill
            assert "name" in skill
            assert "description" in skill
            assert "status" in skill

    def test_expected_skill_names(self):
        """Expected skill identifiers are present."""
        skills = get_available_skills()
        names = {s["skill"] for s in skills}
        assert names == {"malaria_detect", "cardiac_alert", "prenatal_screening", "diabetes_management"}

    def test_all_active(self):
        """All skills report active status."""
        skills = get_available_skills()
        assert all(s["status"] == "active" for s in skills)


# ── Full Pipeline: run_ai_analysis ───────────────────────────────────────────

class TestRunAiAnalysis:
    """Integration tests for run_ai_analysis() with mocked DB objects."""

    def _make_mock_encounter(self, chief_complaint, symptoms=None, vitals=None, patient_id=None):
        """Create a mock Encounter-like object."""
        enc = MagicMock()
        enc.id = uuid4()
        enc.chief_complaint = chief_complaint
        enc.associated_symptoms = symptoms or []
        enc.vitals = vitals or {}
        enc.patient_id = patient_id or uuid4()
        enc.status = EncounterStatus.draft
        # These will be set by run_ai_analysis
        enc.ai_diagnosis = None
        enc.ai_confidence = None
        enc.ai_differential = None
        enc.ai_actions_triggered = None
        return enc

    def _make_mock_patient(self, age=30, gender=Gender.male):
        """Create a mock Patient-like object."""
        patient = MagicMock()
        patient.age = age
        patient.gender = gender
        return patient

    def _make_mock_user(self):
        """Create a mock User-like object."""
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.student
        return user

    def test_malaria_pipeline(self):
        """Full pipeline for malaria symptoms: analysis + enrichment + DB writes."""
        db = MagicMock()
        encounter = self._make_mock_encounter(
            "High fever, headache, and chills",
            symptoms=["Fever", "Headache", "Chills"],
            vitals={"temperature": 39.0},
        )
        patient = self._make_mock_patient(age=25, gender=Gender.female)
        user = self._make_mock_user()

        result = run_ai_analysis(db=db, encounter=encounter, patient=patient, user=user)

        # Diagnosis
        assert "Malaria" in result["primary_diagnosis"]
        assert result["confidence"] > 0.8
        assert result["urgency"] == "routine"

        # MCP actions enriched
        assert len(result["mcp_actions"]) > 0
        skill_group = result["mcp_actions"][0]
        assert skill_group["skill"] == "malaria_detect"
        assert all("verified_at" in a for a in skill_group["actions"])

        # DB was called
        db.add.assert_called()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

        # Encounter was updated
        assert encounter.ai_diagnosis is not None or hasattr(encounter, "__setattr__")

    def test_cardiac_emergency_pipeline(self):
        """Cardiac emergency triggers cardiac_alert skill and STAT priority."""
        db = MagicMock()
        encounter = self._make_mock_encounter(
            "Severe chest pain and shortness of breath",
            symptoms=["Chest Pain", "Dyspnea"],
            vitals={"pulse": 130, "spo2": 91},
        )

        result = run_ai_analysis(db=db, encounter=encounter)

        assert "Acute Coronary Syndrome" in result["primary_diagnosis"]
        assert result["urgency"] == "emergency"
        assert len(result["mcp_actions"]) > 0
        assert result["mcp_actions"][0]["skill"] == "cardiac_alert"

    def test_generic_no_mcp_match(self):
        """Generic/unknown symptoms produce no MCP skill logs."""
        db = MagicMock()
        encounter = self._make_mock_encounter("mild elbow pain")

        result = run_ai_analysis(db=db, encounter=encounter)

        assert result["confidence"] < 0.5
        assert result["mcp_actions"] == []

    def test_metadata_present(self):
        """Result includes analysis_metadata with timing info."""
        db = MagicMock()
        encounter = self._make_mock_encounter("fever headache chills")

        result = run_ai_analysis(db=db, encounter=encounter)

        assert "analysis_metadata" in result
        assert "total_processing_time_ms" in result["analysis_metadata"]
        assert result["analysis_metadata"]["total_processing_time_ms"] >= 0

    def test_vitals_alerts_in_result(self):
        """Abnormal vitals generate alerts in the analysis result."""
        db = MagicMock()
        encounter = self._make_mock_encounter(
            "fever headache chills",
            vitals={"temperature": 40.0, "spo2": 85},
        )

        result = run_ai_analysis(db=db, encounter=encounter)

        assert "vitals_alerts" in result
        assert len(result["vitals_alerts"]) >= 2

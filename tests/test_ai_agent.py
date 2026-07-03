"""Unit tests for the AI Agent service.

Tests the pattern-matching engine, JSON extraction, Ollama payload builder,
vitals alerts, and the top-level analyze_symptoms function.
No external API calls — Ollama is not invoked (AI_ENGINE defaults to 'mock').
"""

import json
from unittest.mock import patch

import pytest

from app.services.ai_agent import (
    _check_vitals_alerts,
    _extract_json,
    _build_ollama_payload,
    _local_symptom_analysis,
    _match_profile,
    _generic_analysis,
    analyze_symptoms,
    DiseaseProfile,
    DISEASE_PROFILES,
)


# ── Profile Matching ─────────────────────────────────────────────────────────

class TestMatchProfile:
    """Tests for _match_profile() — keyword-based disease matching."""

    def test_malaria_profile(self):
        """Fever + headache + chills triggers the malaria profile."""
        profile = _match_profile("I have fever, headache and chills")
        assert profile is not None
        assert profile.name == "malaria"

    def test_cardiac_profile(self):
        """Chest + pain + shortness of breath triggers cardiac profile."""
        profile = _match_profile("severe chest pain, shortness of breath")
        assert profile is not None
        assert profile.name == "cardiac"

    def test_prenatal_profile(self):
        """Prenatal + week triggers prenatal profile."""
        profile = _match_profile("prenatal checkup at 32 week")
        assert profile is not None
        assert profile.name == "prenatal"

    def test_diabetes_profile(self):
        """Thirst + frequent urination + weight triggers diabetes profile."""
        profile = _match_profile("excessive thirst, frequent urinating, weight loss")
        assert profile is not None
        assert profile.name == "diabetes"

    def test_no_match(self):
        """Unrelated symptoms return None."""
        profile = _match_profile("skin rash on left arm")
        assert profile is None

    def test_combined_with_symptoms_list(self):
        """Associated symptoms list is also checked for keyword matches."""
        profile = _match_profile("I feel unwell", symptoms=["fever", "headache", "chills"])
        assert profile is not None
        assert profile.name == "malaria"

    def test_case_insensitive(self):
        """Matching is case-insensitive."""
        profile = _match_profile("FEVER HEADACHE CHILL")
        assert profile is not None
        assert profile.name == "malaria"


# ── Local Symptom Analysis ───────────────────────────────────────────────────

class TestLocalSymptomAnalysis:
    """Tests for _local_symptom_analysis() output structure."""

    def test_malaria_analysis_output(self):
        """Malaria match returns correct diagnosis and MCP actions."""
        result = _local_symptom_analysis("fever headache chills")
        assert "Malaria" in result["primary_diagnosis"]
        assert result["confidence"] > 0.8
        assert len(result["mcp_actions"]) > 0
        assert result["mcp_actions"][0]["skill"] == "malaria_detect"

    def test_cardiac_analysis_urgency(self):
        """Cardiac match returns emergency urgency."""
        result = _local_symptom_analysis("chest pain shortness of breath")
        assert result["urgency"] == "emergency"

    def test_generic_fallback(self):
        """Unmatched symptoms produce generic analysis with low confidence."""
        result = _local_symptom_analysis("elbow pain")
        assert result["confidence"] < 0.5
        assert len(result["mcp_actions"]) == 0
        assert "note" in result


# ── Generic Analysis ─────────────────────────────────────────────────────────

class TestGenericAnalysis:
    """Tests for _generic_analysis()."""

    def test_structure(self):
        """Generic analysis contains all required keys."""
        result = _generic_analysis("unknown symptom", ["fatigue"], None)
        assert "primary_diagnosis" in result
        assert "confidence" in result
        assert "differential" in result
        assert "recommended_investigations" in result
        assert "urgency" in result
        assert "mcp_actions" in result
        assert "note" in result

    def test_low_confidence(self):
        """Generic analysis has confidence 0.45."""
        result = _generic_analysis("mystery", None, None)
        assert result["confidence"] == 0.45

    def test_empty_mcp_actions(self):
        """Generic analysis has no MCP actions."""
        result = _generic_analysis("mystery", None, None)
        assert result["mcp_actions"] == []


# ── Top-Level analyze_symptoms ───────────────────────────────────────────────

class TestAnalyzeSymptoms:
    """Tests for analyze_symptoms() — the public entry point."""

    def test_returns_complete_schema(self):
        """Result contains primary_diagnosis, confidence, differential, etc."""
        result = analyze_symptoms(
            chief_complaint="fever headache chills",
            associated_symptoms=["Fever", "Headache"],
        )
        assert "primary_diagnosis" in result
        assert "confidence" in result
        assert "differential" in result
        assert "recommended_investigations" in result
        assert "urgency" in result
        assert "mcp_actions" in result
        assert "analysis_metadata" in result

    def test_metadata_engine(self):
        """Metadata reports the mock engine when AI_ENGINE != 'ollama'."""
        result = analyze_symptoms(chief_complaint="cough")
        assert result["analysis_metadata"]["engine"] == "clinix-ai-v1-mock"

    def test_vitals_alerts_included(self):
        """Passing vitals triggers vitals_alerts in the result."""
        result = analyze_symptoms(
            chief_complaint="fever headache chills",
            vitals={"temperature": 39.5, "spo2": 88},
        )
        assert "vitals_alerts" in result
        assert len(result["vitals_alerts"]) > 0

    def test_patient_context_in_metadata(self):
        """Patient age/gender appear in analysis_metadata."""
        result = analyze_symptoms(
            chief_complaint="cough",
            patient_age=45,
            patient_gender="M",
        )
        ctx = result["analysis_metadata"]["patient_context"]
        assert ctx["age"] == 45
        assert ctx["gender"] == "M"

    def test_processing_time_recorded(self):
        """Metadata includes processing_time_ms."""
        result = analyze_symptoms(chief_complaint="cough")
        assert result["analysis_metadata"]["processing_time_ms"] >= 0


# ── Vitals Alerts ────────────────────────────────────────────────────────────

class TestVitalsAlerts:
    """Tests for _check_vitals_alerts()."""

    def test_high_fever_critical(self):
        """Temperature ≥ 39°C triggers critical alert."""
        alerts = _check_vitals_alerts({"temperature": 39.5})
        assert any(a["type"] == "critical" for a in alerts)
        assert any("fever" in a["message"].lower() for a in alerts)

    def test_moderate_fever_warning(self):
        """Temperature 38–39°C triggers warning alert."""
        alerts = _check_vitals_alerts({"temperature": 38.5})
        assert any(a["type"] == "warning" for a in alerts)

    def test_hypothermia_warning(self):
        """Temperature < 35.5°C triggers hypothermia warning."""
        alerts = _check_vitals_alerts({"temperature": 34.0})
        assert any(a["type"] == "warning" for a in alerts)
        assert any("hypothermia" in a["message"].lower() for a in alerts)

    def test_severe_hypoxia_critical(self):
        """SpO2 < 90 triggers critical hypoxia alert."""
        alerts = _check_vitals_alerts({"spo2": 85})
        assert any(a["type"] == "critical" for a in alerts)
        assert any("hypoxia" in a["message"].lower() for a in alerts)

    def test_low_spo2_warning(self):
        """SpO2 90–94 triggers warning alert."""
        alerts = _check_vitals_alerts({"spo2": 92})
        assert any(a["type"] == "warning" for a in alerts)

    def test_tachycardia_critical(self):
        """Pulse > 120 triggers tachycardia critical alert."""
        alerts = _check_vitals_alerts({"pulse": 130})
        assert any(a["type"] == "critical" for a in alerts)

    def test_bradycardia_warning(self):
        """Pulse < 50 triggers bradycardia warning."""
        alerts = _check_vitals_alerts({"pulse": 45})
        assert any(a["type"] == "warning" for a in alerts)

    def test_normal_vitals_no_alerts(self):
        """Normal vitals produce no alerts."""
        alerts = _check_vitals_alerts({"temperature": 36.8, "spo2": 98, "pulse": 72})
        assert alerts == []

    def test_multiple_abnormals(self):
        """Multiple abnormal vitals produce multiple alerts."""
        alerts = _check_vitals_alerts({"temperature": 40.0, "spo2": 85, "pulse": 140})
        assert len(alerts) == 3

    def test_invalid_vitals_ignored(self):
        """Non-numeric vital values are silently ignored."""
        alerts = _check_vitals_alerts({"temperature": "N/A", "spo2": "unknown"})
        assert alerts == []


# ── JSON Extraction ──────────────────────────────────────────────────────────

class TestExtractJson:
    """Tests for _extract_json() — parsing LLM output."""

    def test_clean_json(self):
        """Direct JSON string is parsed correctly."""
        raw = json.dumps({"primary_diagnosis": "test", "confidence": 0.9})
        result = _extract_json(raw)
        assert result["primary_diagnosis"] == "test"

    def test_json_with_surrounding_text(self):
        """JSON embedded in LLM preamble text is extracted."""
        raw = 'Here is my analysis:\n{"primary_diagnosis": "Malaria", "confidence": 0.92}\nThank you.'
        result = _extract_json(raw)
        assert result["primary_diagnosis"] == "Malaria"

    def test_empty_raises_valueerror(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="Empty response"):
            _extract_json("")

    def test_whitespace_only_raises(self):
        """Whitespace-only input raises ValueError."""
        with pytest.raises(ValueError):
            _extract_json("   ")

    def test_no_json_raises(self):
        """Text with no JSON object raises ValueError."""
        with pytest.raises(ValueError):
            _extract_json("I don't have a diagnosis for you")


# ── Ollama Payload Builder ───────────────────────────────────────────────────

class TestBuildOllamaPayload:
    """Tests for _build_ollama_payload()."""

    def test_basic_payload(self):
        """Payload includes model, messages, and temperature."""
        payload = _build_ollama_payload("headache", None, None, None, None)
        assert "model" in payload
        assert "messages" in payload
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
        assert "headache" in payload["messages"][1]["content"]

    def test_includes_symptoms(self):
        """Associated symptoms are appended to the user message."""
        payload = _build_ollama_payload("headache", ["nausea", "vomiting"], None, None, None)
        content = payload["messages"][1]["content"]
        assert "nausea" in content
        assert "vomiting" in content

    def test_includes_vitals(self):
        """Vitals dict is included in the user message."""
        payload = _build_ollama_payload("cough", None, {"temperature": 38.5}, None, None)
        content = payload["messages"][1]["content"]
        assert "temperature" in content
        assert "38.5" in content

    def test_includes_patient_context(self):
        """Patient age and gender are appended."""
        payload = _build_ollama_payload("cough", None, None, 30, "F")
        content = payload["messages"][1]["content"]
        assert "30" in content
        assert "F" in content

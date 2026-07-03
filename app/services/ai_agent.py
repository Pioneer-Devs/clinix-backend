"""AI Diagnosis Agent — Mock GPT-4 Clinical Analysis Engine.

Provides symptom-based clinical analysis using pattern matching against known
disease profiles. For the hackathon MVP, this replaces a real GPT-4 call with
deterministic, high-quality static responses.

In production, this module would integrate with OpenAI GPT-4 via the
`/v1/chat/completions` endpoint with a clinical reasoning system prompt.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import settings


# ── Disease Profile Definitions ──────────────────────────────────────────────

@dataclass
class DiseaseProfile:
    """A pattern-matched clinical disease profile."""
    name: str
    trigger_keywords: list[str]          # ALL must be present (case-insensitive)
    primary_diagnosis: str
    confidence: float
    differential: list[dict[str, Any]]
    recommended_investigations: list[str]
    urgency: str                          # "routine" | "urgent" | "emergency"
    mcp_skill: str
    mcp_actions: list[dict[str, Any]]
    min_keyword_match: int = 0            # 0 means ALL keywords required


DISEASE_PROFILES: list[DiseaseProfile] = [
    # ── Malaria (Primary demo case) ──────────────────────────────────────
    DiseaseProfile(
        name="malaria",
        trigger_keywords=["fever", "headache", "chill"],
        primary_diagnosis="Probable Malaria (Uncomplicated)",
        confidence=0.92,
        differential=[
            {"condition": "Malaria", "probability": 0.92},
            {"condition": "Typhoid fever", "probability": 0.15},
            {"condition": "Viral illness", "probability": 0.08},
        ],
        recommended_investigations=["Malaria RDT", "Full Blood Count"],
        urgency="routine",
        mcp_skill="malaria_detect",
        mcp_actions=[
            {"type": "inventory_check", "drug": "Artemether-Lumefantrine", "stock": 24, "available": True},
            {"type": "rdt_recommend", "test": "SD Bioline Malaria Ag", "available": True},
            {"type": "schedule_followup", "days": 3},
        ],
    ),
    # ── Cardiac Emergency ────────────────────────────────────────────────
    DiseaseProfile(
        name="cardiac",
        trigger_keywords=["chest", "pain", "breath"],
        primary_diagnosis="Acute Coronary Syndrome — Rule Out MI",
        confidence=0.78,
        differential=[
            {"condition": "Acute Coronary Syndrome", "probability": 0.78},
            {"condition": "Pulmonary Embolism", "probability": 0.18},
            {"condition": "Costochondritis", "probability": 0.12},
            {"condition": "GERD", "probability": 0.08},
        ],
        recommended_investigations=["12-Lead ECG", "Troponin I", "Chest X-Ray", "D-Dimer"],
        urgency="emergency",
        mcp_skill="cardiac_alert",
        mcp_actions=[
            {"type": "inventory_check", "drug": "Aspirin 300mg", "stock": 50, "available": True},
            {"type": "inventory_check", "drug": "Clopidogrel 300mg", "stock": 30, "available": True},
            {"type": "ecg_recommend", "test": "12-Lead ECG", "available": True},
            {"type": "alert_supervisor", "priority": "STAT"},
        ],
    ),
    # ── Prenatal Screening ───────────────────────────────────────────────
    DiseaseProfile(
        name="prenatal",
        trigger_keywords=["prenatal", "week"],
        primary_diagnosis="Routine Prenatal Assessment — 3rd Trimester",
        confidence=0.95,
        differential=[
            {"condition": "Normal Pregnancy (3rd Trimester)", "probability": 0.95},
            {"condition": "Gestational Hypertension", "probability": 0.08},
            {"condition": "Gestational Diabetes", "probability": 0.05},
        ],
        recommended_investigations=["Urinalysis", "Blood Glucose", "Blood Pressure Monitoring", "Fetal Heart Rate"],
        urgency="routine",
        mcp_skill="prenatal_screening",
        mcp_actions=[
            {"type": "screening_check", "test": "Urine Dipstick", "available": True},
            {"type": "inventory_check", "drug": "Ferrous Sulphate + Folic Acid", "stock": 100, "available": True},
            {"type": "schedule_followup", "days": 14},
        ],
    ),
    # ── Diabetes Management ──────────────────────────────────────────────
    DiseaseProfile(
        name="diabetes",
        trigger_keywords=["thirst", "urinat", "weight"],
        primary_diagnosis="Suspected Type 2 Diabetes Mellitus",
        confidence=0.84,
        differential=[
            {"condition": "Type 2 Diabetes Mellitus", "probability": 0.84},
            {"condition": "Diabetes Insipidus", "probability": 0.10},
            {"condition": "Hyperthyroidism", "probability": 0.06},
        ],
        recommended_investigations=["Fasting Blood Glucose", "HbA1c", "Urinalysis", "Lipid Profile"],
        urgency="routine",
        mcp_skill="diabetes_management",
        mcp_actions=[
            {"type": "inventory_check", "drug": "Metformin 500mg", "stock": 60, "available": True},
            {"type": "lab_recommend", "test": "HbA1c", "available": True},
            {"type": "schedule_followup", "days": 7},
        ],
    ),
]


# ── Ollama / LLM Integration Helpers ─────────────────────────────────────────────

OLLAMA_SYSTEM_PROMPT = """You are a clinical reasoning assistant embedded in a medical education system.
Return ONLY valid JSON and nothing else. The JSON object must contain these keys:
- primary_diagnosis
- confidence
- differential
- recommended_investigations
- urgency
- mcp_actions
- note (optional)

The mcp_actions list should contain objects with:
- skill
- actions

Match the following schema exactly and keep the structure parseable by a JSON parser.
"""


def _extract_json(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if not candidate:
        raise ValueError("Empty response from Ollama")

    if candidate.startswith("{") and candidate.endswith("}"):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    match = re.search(r"(\{.*\})", candidate, flags=re.DOTALL)
    if not match:
        raise ValueError("Could not locate JSON object in Ollama response")

    payload = match.group(1)
    return json.loads(payload)


def _build_ollama_payload(
    chief_complaint: str,
    associated_symptoms: list[str] | None,
    vitals: dict[str, Any] | None,
    patient_age: int | None,
    patient_gender: str | None,
) -> dict[str, Any]:
    patient_context = {
        key: value
        for key, value in {
            "age": patient_age,
            "gender": patient_gender,
        }.items()
        if value is not None
    }

    symptom_text = chief_complaint.strip()
    if associated_symptoms:
        symptom_text += "\nSymptoms: " + ", ".join(associated_symptoms)

    if vitals:
        vitals_text = ", ".join(f"{k}: {v}" for k, v in vitals.items())
        symptom_text += f"\nVitals: {vitals_text}"

    if patient_context:
        context_text = ", ".join(f"{k}: {v}" for k, v in patient_context.items())
        symptom_text += f"\nPatient: {context_text}"

    return {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": OLLAMA_SYSTEM_PROMPT},
            {"role": "user", "content": symptom_text},
        ],
        "temperature": 0.15,
        "top_p": 0.95,
        "max_tokens": 900,
    }


def _run_ollama_analysis(
    chief_complaint: str,
    associated_symptoms: list[str] | None = None,
    vitals: dict[str, Any] | None = None,
    patient_age: int | None = None,
    patient_gender: str | None = None,
) -> dict[str, Any]:
    url = settings.OLLAMA_URL.rstrip("/") + "/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"

    payload = _build_ollama_payload(
        chief_complaint,
        associated_symptoms,
        vitals,
        patient_age,
        patient_gender,
    )

    response = httpx.post(url, json=payload, headers=headers, timeout=20.0)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise ValueError("Invalid Ollama response format: missing choices")

    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise ValueError("Invalid Ollama response format: missing message.content")

    parsed = _extract_json(content)
    if "mcp_actions" not in parsed:
        parsed["mcp_actions"] = []

    return parsed


# ── Symptom Matching Engine ──────────────────────────────────────────────────

def _match_profile(text: str, symptoms: list[str] | None = None) -> DiseaseProfile | None:
    """Find the best matching disease profile from symptoms + chief complaint.

    Combines the chief complaint text with any additional symptom tags,
    then checks each profile's trigger keywords against the combined text.
    """
    combined = text.lower()
    if symptoms:
        combined += " " + " ".join(s.lower() for s in symptoms)

    best_match: DiseaseProfile | None = None
    best_score: int = 0

    for profile in DISEASE_PROFILES:
        matched = sum(1 for kw in profile.trigger_keywords if kw in combined)
        required = profile.min_keyword_match or len(profile.trigger_keywords)

        if matched >= required and matched > best_score:
            best_score = matched
            best_match = profile

    return best_match


def _local_symptom_analysis(
    chief_complaint: str,
    associated_symptoms: list[str] | None = None,
    vitals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = _match_profile(chief_complaint, associated_symptoms)

    if profile is None:
        return _generic_analysis(chief_complaint, associated_symptoms, vitals)

    return {
        "primary_diagnosis": profile.primary_diagnosis,
        "confidence": profile.confidence,
        "differential": profile.differential,
        "recommended_investigations": profile.recommended_investigations,
        "urgency": profile.urgency,
        "mcp_actions": [
            {
                "skill": profile.mcp_skill,
                "actions": profile.mcp_actions,
            }
        ],
    }


def analyze_symptoms(
    chief_complaint: str,
    associated_symptoms: list[str] | None = None,
    vitals: dict[str, Any] | None = None,
    patient_age: int | None = None,
    patient_gender: str | None = None,
) -> dict[str, Any]:
    """Run AI clinical analysis on the given symptoms.

    Returns a structured diagnosis response matching the PRD Section 8 schema.
    In the hackathon MVP, this can use Ollama if configured, otherwise it
    falls back to the existing pattern-matching engine.

    Args:
        chief_complaint: Patient's chief complaint text.
        associated_symptoms: List of symptom tags (e.g. ["fever", "headache"]).
        vitals: Dict of vitals (temperature, BP, pulse, SpO2).
        patient_age: Patient's age for demographic-aware analysis.
        patient_gender: Patient's gender (M/F).

    Returns:
        Structured AI analysis dict with diagnosis, confidence, differential,
        recommended investigations, urgency level, and MCP actions.
    """
    start_time = time.monotonic()
    engine = settings.AI_ENGINE.lower().strip()

    if engine == "ollama":
        try:
            result = _run_ollama_analysis(
                chief_complaint,
                associated_symptoms,
                vitals,
                patient_age,
                patient_gender,
            )
        except Exception as exc:
            result = _local_symptom_analysis(chief_complaint, associated_symptoms, vitals)
            result["note"] = (
                "Ollama analysis failed — falling back to local pattern-based analysis. "
                f"Error: {str(exc)}"
            )
    else:
        result = _local_symptom_analysis(chief_complaint, associated_symptoms, vitals)

    if vitals:
        result["vitals_alerts"] = _check_vitals_alerts(vitals)

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    metadata = result.get("analysis_metadata", {})
    metadata.update({
        "engine": "ollama" if engine == "ollama" else "clinix-ai-v1-mock",
        "processing_time_ms": elapsed_ms,
        "model": settings.OLLAMA_MODEL if engine == "ollama" else "gpt-4-clinical-mock",
        "patient_context": {
            "age": patient_age,
            "gender": patient_gender,
        },
    })
    result["analysis_metadata"] = metadata

    return result


def _generic_analysis(
    chief_complaint: str,
    symptoms: list[str] | None,
    vitals: dict[str, Any] | None,
) -> dict[str, Any]:
    """Generate a generic clinical analysis when no disease profile matches."""
    symptom_text = ", ".join(symptoms) if symptoms else "unspecified"

    return {
        "primary_diagnosis": f"Clinical Assessment Required — {chief_complaint[:60]}",
        "confidence": 0.45,
        "differential": [
            {"condition": "Further workup needed", "probability": 0.45},
            {"condition": "Infectious etiology", "probability": 0.25},
            {"condition": "Non-specific presentation", "probability": 0.20},
        ],
        "recommended_investigations": [
            "Full Blood Count",
            "Basic Metabolic Panel",
            "Urinalysis",
        ],
        "urgency": "routine",
        "mcp_actions": [],
        "note": (
            f"No high-confidence pattern match for: {symptom_text}. "
            "Manual clinical assessment recommended. AI confidence is below threshold."
        ),
    }


def _check_vitals_alerts(vitals: dict[str, Any]) -> list[dict[str, str]]:
    """Generate alert flags based on abnormal vital signs."""
    alerts: list[dict[str, str]] = []

    temp = vitals.get("temperature") or vitals.get("temp")
    if temp is not None:
        try:
            temp_val = float(temp)
            if temp_val >= 39.0:
                alerts.append({"type": "critical", "message": f"High fever: {temp_val}°C — consider sepsis workup"})
            elif temp_val >= 38.0:
                alerts.append({"type": "warning", "message": f"Fever: {temp_val}°C — monitor and investigate cause"})
            elif temp_val < 35.5:
                alerts.append({"type": "warning", "message": f"Hypothermia: {temp_val}°C — assess for shock"})
        except (ValueError, TypeError):
            pass

    spo2 = vitals.get("spo2")
    if spo2 is not None:
        try:
            spo2_val = int(spo2)
            if spo2_val < 90:
                alerts.append({"type": "critical", "message": f"Severe hypoxia: SpO2 {spo2_val}% — administer O2"})
            elif spo2_val < 94:
                alerts.append({"type": "warning", "message": f"Low SpO2: {spo2_val}% — monitor closely"})
        except (ValueError, TypeError):
            pass

    pulse = vitals.get("pulse")
    if pulse is not None:
        try:
            pulse_val = int(pulse)
            if pulse_val > 120:
                alerts.append({"type": "critical", "message": f"Tachycardia: {pulse_val} bpm — assess for dehydration/shock"})
            elif pulse_val < 50:
                alerts.append({"type": "warning", "message": f"Bradycardia: {pulse_val} bpm — assess cardiac status"})
        except (ValueError, TypeError):
            pass

    return alerts

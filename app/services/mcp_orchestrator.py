"""MCP (Model Context Protocol) Orchestrator.

Coordinates AI analysis with MCP Action Skills — the "agentic" layer that
makes Clinix's AI _act_, not just chat. Each MCP skill is a composable
action that can check inventory, recommend tests, schedule follow-ups,
or alert supervisors.

Registered skills:
  - malaria_detect    → Malaria RDT + Coartem stock check + follow-up
  - cardiac_alert     → ECG + Troponin + emergency drug check + STAT alert
  - prenatal_screening → Antenatal screening + iron/folate stock + follow-up
  - diabetes_management → HbA1c + Metformin stock + follow-up
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import ActivityType
from app.models.skill_log import ActionSkillLog, SKILL_NAMES
from app.services.activity import log_activity
from app.services.ai_agent import analyze_symptoms
from app.services.inventory_scanner import check_drug_availability, check_test_availability


# ── MCP Skill Definitions ───────────────────────────────────────────────────

def _execute_inventory_checks(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Execute inventory/test checks for each action in the MCP output."""
    enriched_actions: list[dict[str, Any]] = []

    for action in actions:
        action_type = action.get("type", "")

        if action_type == "inventory_check":
            drug_name = action.get("drug", "")
            stock_result = check_drug_availability(drug_name)
            enriched_actions.append({
                **action,
                "live_stock": stock_result.get("stock", action.get("stock")),
                "live_available": stock_result.get("available", action.get("available")),
                "location": stock_result.get("location"),
                "verified_at": datetime.utcnow().isoformat(),
            })
        elif action_type in ("rdt_recommend", "ecg_recommend", "screening_check", "lab_recommend"):
            test_name = action.get("test", "")
            test_result = check_test_availability(test_name)
            enriched_actions.append({
                **action,
                "live_available": test_result.get("available", action.get("available")),
                "turnaround_minutes": test_result.get("turnaround_minutes"),
                "location": test_result.get("location"),
                "verified_at": datetime.utcnow().isoformat(),
            })
        else:
            # Pass through other action types (schedule_followup, alert_supervisor)
            enriched_actions.append({
                **action,
                "verified_at": datetime.utcnow().isoformat(),
            })

    return enriched_actions


# ── Main Orchestrator ────────────────────────────────────────────────────────

def run_ai_analysis(
    db: Session,
    encounter,
    patient=None,
    user=None,
) -> dict[str, Any]:
    """Run the full AI + MCP pipeline for an encounter.

    1. Calls the AI diagnosis engine (ai_agent.analyze_symptoms)
    2. For each MCP skill triggered, enriches actions with live inventory data
    3. Logs skill executions to ActionSkillLog table
    4. Updates the encounter with AI results
    5. Returns the complete analysis response

    Args:
        db: Database session.
        encounter: The Encounter ORM object.
        patient: Optional Patient ORM object for demographic context.
        user: The User who triggered the analysis (for activity logging).

    Returns:
        Complete AI analysis result with enriched MCP actions.
    """
    start_time = time.monotonic()

    # 1. Run AI symptom analysis
    patient_age = patient.age if patient else None
    patient_gender = patient.gender.value if patient and patient.gender else None

    analysis = analyze_symptoms(
        chief_complaint=encounter.chief_complaint,
        associated_symptoms=encounter.associated_symptoms or [],
        vitals=encounter.vitals or {},
        patient_age=patient_age,
        patient_gender=patient_gender,
    )

    # 2. Enrich MCP actions with live inventory data
    enriched_mcp_actions: list[dict[str, Any]] = []
    for mcp_group in analysis.get("mcp_actions", []):
        skill_name = mcp_group.get("skill", "unknown")
        raw_actions = mcp_group.get("actions", [])

        skill_start = time.monotonic()
        enriched = _execute_inventory_checks(raw_actions)
        skill_elapsed = int((time.monotonic() - skill_start) * 1000)

        enriched_mcp_actions.append({
            "skill": skill_name,
            "actions": enriched,
        })

        # 3. Log skill execution
        if skill_name in SKILL_NAMES:
            skill_log = ActionSkillLog(
                encounter_id=encounter.id,
                skill_name=skill_name,
                input_data={
                    "chief_complaint": encounter.chief_complaint,
                    "symptoms": encounter.associated_symptoms or [],
                    "vitals": encounter.vitals or {},
                },
                output_data={
                    "actions": enriched,
                    "confidence": analysis.get("confidence"),
                },
                success=True,
                execution_time_ms=skill_elapsed,
            )
            db.add(skill_log)

    # Replace raw MCP actions with enriched versions
    analysis["mcp_actions"] = enriched_mcp_actions

    # 4. Update encounter with AI results
    encounter.ai_diagnosis = analysis["primary_diagnosis"]
    encounter.ai_confidence = analysis["confidence"]
    encounter.ai_differential = analysis["differential"]
    encounter.ai_actions_triggered = enriched_mcp_actions
    db.add(encounter)

    # 5. Log activity
    if user:
        log_activity(
            db,
            user,
            ActivityType.skill_triggered,
            f"AI analysis: {analysis['primary_diagnosis']} ({int(analysis['confidence'] * 100)}%)",
            {
                "encounter_id": str(encounter.id),
                "diagnosis": analysis["primary_diagnosis"],
                "confidence": analysis["confidence"],
                "skills_triggered": [m["skill"] for m in enriched_mcp_actions],
            },
        )

    db.commit()
    db.refresh(encounter)

    total_elapsed = int((time.monotonic() - start_time) * 1000)
    analysis["analysis_metadata"]["total_processing_time_ms"] = total_elapsed

    return analysis


def get_available_skills() -> list[dict[str, str]]:
    """Return list of registered MCP skills with descriptions."""
    return [
        {
            "skill": "malaria_detect",
            "name": "Malaria Detection & Management",
            "description": "RDT recommendation, ACT stock check, follow-up scheduling",
            "status": "active",
        },
        {
            "skill": "cardiac_alert",
            "name": "Cardiac Emergency Alert",
            "description": "ECG, Troponin, emergency drugs, STAT supervisor alert",
            "status": "active",
        },
        {
            "skill": "prenatal_screening",
            "name": "Prenatal Screening Protocol",
            "description": "Antenatal screening, supplements, follow-up scheduling",
            "status": "active",
        },
        {
            "skill": "diabetes_management",
            "name": "Diabetes Management",
            "description": "HbA1c, Metformin check, glucose monitoring follow-up",
            "status": "active",
        },
    ]

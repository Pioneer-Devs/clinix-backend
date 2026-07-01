from app.models.enums import CreditCategory

# ── Credit calculation logic ───────────────────────────────────────────────────

CREDIT_RULES: dict[CreditCategory, int] = {
    CreditCategory.history_taking: 2,   # Complete history documented
    CreditCategory.physical_exam: 2,    # Vitals + exam notes present
    CreditCategory.diagnosis: 2,        # Student pre-AI diagnosis submitted + supervisor agrees
    CreditCategory.treatment: 2,        # Treatment plan appropriate per supervisor
    CreditCategory.communication: 1,    # Optional patient satisfaction
}


def calculate_provisional_credits(encounter) -> dict[str, int]:
    """
    Calculates provisional credits for an encounter before supervisor review.
    Credits are PROVISIONAL here — only confirmed after supervisor approval.
    """
    breakdown: dict[str, int] = {}

    if encounter.chief_complaint and len(encounter.chief_complaint) > 20:
        breakdown[CreditCategory.history_taking.value] = CREDIT_RULES[CreditCategory.history_taking]

    if encounter.vitals and encounter.exam_notes:
        breakdown[CreditCategory.physical_exam.value] = CREDIT_RULES[CreditCategory.physical_exam]

    # Only award diagnosis credit if student submitted a pre-AI diagnosis
    if encounter.student_pre_ai_diagnosis and encounter.working_diagnosis:
        breakdown[CreditCategory.diagnosis.value] = CREDIT_RULES[CreditCategory.diagnosis]

    if encounter.treatment_plan and encounter.investigations:
        breakdown[CreditCategory.treatment.value] = CREDIT_RULES[CreditCategory.treatment]

    return breakdown

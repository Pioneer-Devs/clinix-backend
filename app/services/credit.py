from app.models.enums import CreditCategory
from app.models.credit import ClinicalCredit
from app.services.portfolio_signer import sign_credit

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


def create_verified_credits(db, encounter, supervisor_id):
    breakdown = encounter.credit_breakdown or calculate_provisional_credits(encounter)
    credits: list[ClinicalCredit] = []

    for category_value, points in breakdown.items():
        category = CreditCategory(category_value)
        existing = (
            db.query(ClinicalCredit)
            .filter(
                ClinicalCredit.encounter_id == encounter.id,
                ClinicalCredit.category == category,
            )
            .first()
        )
        if existing:
            credits.append(existing)
            continue

        credit = ClinicalCredit(
            student_id=encounter.student_id,
            encounter_id=encounter.id,
            supervisor_id=supervisor_id,
            category=category,
            points=points,
            verified=True,
        )
        credit.signed_hash = sign_credit(credit)
        db.add(credit)
        credits.append(credit)

    return credits

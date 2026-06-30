from enum import Enum


class UserRole(str, Enum):
    student = "student"
    supervisor = "supervisor"
    admin = "admin"


class Gender(str, Enum):
    male = "M"
    female = "F"


class Severity(str, Enum):
    mild = "mild"
    moderate = "moderate"
    severe = "severe"
    life_threatening = "life_threatening"


class EncounterStatus(str, Enum):
    draft = "draft"
    in_progress = "in_progress"
    pending_review = "pending_review"
    finalized = "finalized"
    rejected = "rejected"


class WalletRecordStatus(str, Enum):
    pending = "pending"
    pushed = "pushed"
    accessed = "accessed"
    expired = "expired"


class CreditCategory(str, Enum):
    history_taking = "history_taking"
    physical_exam = "physical_exam"
    diagnosis = "diagnosis"
    treatment = "treatment"
    communication = "communication"


class ActivityType(str, Enum):
    encounter_complete = "encounter_complete"
    encounter_approved = "encounter_approved"
    encounter_rejected = "encounter_rejected"
    wallet_push = "wallet_push"
    credit_earned = "credit_earned"
    skill_triggered = "skill_triggered"
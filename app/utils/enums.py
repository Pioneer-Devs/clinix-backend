from app.models.enums import UserRole

USER_ROLES = {UserRole.student.value, UserRole.supervisor.value, UserRole.admin.value, UserRole.patient.value}
ROLE_ALIASES = {
    "student": UserRole.student.value,
    "supervisor": UserRole.supervisor.value,
    "admin": UserRole.admin.value,
    "patient": UserRole.patient.value,
}

def normalize_role(role: str) -> str:
    normalized = role.strip().lower()
    return ROLE_ALIASES.get(normalized, normalized)
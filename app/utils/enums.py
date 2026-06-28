from enum import Enum


class UserRole(str, Enum):
	DOCTOR = "doctor"
	PATIENT = "patient"


USER_ROLES = {UserRole.DOCTOR.value, UserRole.PATIENT.value}
ROLE_ALIASES = {
	"doctor": UserRole.DOCTOR.value,
}


def normalize_role(role: str) -> str:
	normalized = role.strip().lower()
	return ROLE_ALIASES.get(normalized, normalized)
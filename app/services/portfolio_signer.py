import hmac
from hashlib import sha256

from app.core.config import settings
from app.models.credit import ClinicalCredit


def sign_credit(credit: ClinicalCredit) -> str:
    payload = (
        f"{credit.student_id}:{credit.encounter_id}:{credit.category.value}:"
        f"{credit.points}:{credit.supervisor_id}"
    )
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        sha256,
    ).hexdigest()

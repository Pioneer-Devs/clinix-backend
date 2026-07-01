from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.enums import ActivityType
from app.models.user import User


def log_activity(
    db: Session,
    user: User,
    activity_type: ActivityType,
    description: str,
    event_data: Optional[dict[str, Any]] = None,
) -> Activity:
    activity = Activity(
        user_id=user.id,
        activity_type=activity_type,
        description=description,
        event_data=event_data or {},
    )
    db.add(activity)
    return activity


def list_user_activity(db: Session, user: User, limit: int = 50) -> list[Activity]:
    return (
        db.query(Activity)
        .filter(Activity.user_id == user.id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
        .all()
    )

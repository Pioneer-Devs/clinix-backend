"""Hospital Inventory API Router.

Exposes endpoints for checking drug availability and diagnostic test
availability. Uses the mock inventory scanner service.
"""

from fastapi import APIRouter, Depends, Query

from app.models.user import User
from app.services.inventory_scanner import (
    check_drug_availability,
    check_test_availability,
    get_full_inventory,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/drugs")
def check_drug(
    name: str = Query(..., description="Drug name to search for"),
    current_user: User = Depends(get_current_user),
):
    """Check availability and stock level of a drug.

    Performs fuzzy matching on brand name, generic name, and drug keys.
    """
    return check_drug_availability(name)


@router.get("/tests")
def check_test(
    name: str = Query(..., description="Diagnostic test name to search for"),
    current_user: User = Depends(get_current_user),
):
    """Check availability of a diagnostic test.

    Returns availability, turnaround time, and lab location.
    """
    return check_test_availability(name)


@router.get("")
def full_inventory(
    current_user: User = Depends(get_current_user),
):
    """Get the complete hospital inventory snapshot.

    Returns all drugs and diagnostic tests with stock levels.
    """
    return get_full_inventory()

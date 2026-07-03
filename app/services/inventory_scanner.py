"""Mock Hospital Inventory Scanner.

Simulates checking drug stock levels and diagnostic test availability.
In production, this would integrate with a real hospital inventory system
(e.g., OpenMRS, DHIS2, or a custom HIS).
"""

from __future__ import annotations

from typing import Any


# ── Mock Inventory Database ──────────────────────────────────────────────────
# Simulates LAUTECH Teaching Hospital pharmacy/lab stock

DRUG_INVENTORY: dict[str, dict[str, Any]] = {
    "artemether-lumefantrine": {
        "brand_name": "Coartem",
        "generic_name": "Artemether-Lumefantrine",
        "stock": 24,
        "unit": "packs",
        "location": "Pharmacy A — Ward 4",
        "expiry": "2027-03-15",
        "available": True,
    },
    "aspirin": {
        "brand_name": "Aspirin",
        "generic_name": "Aspirin 300mg",
        "stock": 50,
        "unit": "tablets",
        "location": "Emergency Cabinet",
        "expiry": "2027-06-01",
        "available": True,
    },
    "clopidogrel": {
        "brand_name": "Plavix",
        "generic_name": "Clopidogrel 300mg",
        "stock": 30,
        "unit": "tablets",
        "location": "Emergency Cabinet",
        "expiry": "2027-04-20",
        "available": True,
    },
    "metformin": {
        "brand_name": "Glucophage",
        "generic_name": "Metformin 500mg",
        "stock": 60,
        "unit": "tablets",
        "location": "Pharmacy A — Chronic Disease",
        "expiry": "2027-08-10",
        "available": True,
    },
    "ferrous-sulphate": {
        "brand_name": "Ferrous Sulphate + Folic Acid",
        "generic_name": "Ferrous Sulphate 200mg + Folic Acid 5mg",
        "stock": 100,
        "unit": "tablets",
        "location": "Antenatal Clinic Pharmacy",
        "expiry": "2027-12-01",
        "available": True,
    },
    "amoxicillin": {
        "brand_name": "Amoxil",
        "generic_name": "Amoxicillin 500mg",
        "stock": 45,
        "unit": "capsules",
        "location": "Pharmacy A — General",
        "expiry": "2027-05-10",
        "available": True,
    },
    "paracetamol": {
        "brand_name": "Panadol",
        "generic_name": "Paracetamol 500mg",
        "stock": 200,
        "unit": "tablets",
        "location": "All Wards",
        "expiry": "2027-11-30",
        "available": True,
    },
}

DIAGNOSTIC_TESTS: dict[str, dict[str, Any]] = {
    "malaria-rdt": {
        "test_name": "SD Bioline Malaria Ag P.f/Pan",
        "stock": 35,
        "turnaround_minutes": 15,
        "location": "Point-of-Care Lab",
        "available": True,
    },
    "ecg": {
        "test_name": "12-Lead ECG",
        "stock": None,  # equipment, not consumable
        "turnaround_minutes": 10,
        "location": "Emergency Department",
        "available": True,
    },
    "fbc": {
        "test_name": "Full Blood Count",
        "stock": None,
        "turnaround_minutes": 45,
        "location": "Central Laboratory",
        "available": True,
    },
    "troponin": {
        "test_name": "Troponin I",
        "stock": 20,
        "turnaround_minutes": 60,
        "location": "Central Laboratory",
        "available": True,
    },
    "urinalysis": {
        "test_name": "Urinalysis (Dipstick)",
        "stock": 80,
        "turnaround_minutes": 5,
        "location": "Point-of-Care Lab",
        "available": True,
    },
    "blood-glucose": {
        "test_name": "Fasting Blood Glucose",
        "stock": None,
        "turnaround_minutes": 30,
        "location": "Central Laboratory",
        "available": True,
    },
    "hba1c": {
        "test_name": "HbA1c",
        "stock": None,
        "turnaround_minutes": 120,
        "location": "Central Laboratory",
        "available": True,
    },
    "chest-xray": {
        "test_name": "Chest X-Ray",
        "stock": None,
        "turnaround_minutes": 30,
        "location": "Radiology Department",
        "available": True,
    },
    "d-dimer": {
        "test_name": "D-Dimer",
        "stock": 15,
        "turnaround_minutes": 90,
        "location": "Central Laboratory",
        "available": True,
    },
    "urine-dipstick": {
        "test_name": "Urine Dipstick",
        "stock": 80,
        "turnaround_minutes": 5,
        "location": "Point-of-Care Lab",
        "available": True,
    },
    "lipid-profile": {
        "test_name": "Lipid Profile",
        "stock": None,
        "turnaround_minutes": 120,
        "location": "Central Laboratory",
        "available": True,
    },
}


# ── Public API ───────────────────────────────────────────────────────────────

def check_drug_availability(drug_name: str) -> dict[str, Any]:
    """Check if a drug is in stock.

    Args:
        drug_name: Drug name to search for (case-insensitive, partial match).

    Returns:
        Dict with availability status, stock level, and location.
    """
    normalized = drug_name.lower().strip()

    # Try exact key match first
    if normalized in DRUG_INVENTORY:
        return _format_drug_result(DRUG_INVENTORY[normalized])

    # Fuzzy match on brand/generic name
    for key, drug in DRUG_INVENTORY.items():
        if (normalized in drug["brand_name"].lower()
            or normalized in drug["generic_name"].lower()
            or normalized in key):
            return _format_drug_result(drug)

    return {
        "found": False,
        "drug": drug_name,
        "available": False,
        "message": f"'{drug_name}' not found in hospital inventory. Contact pharmacy for manual check.",
    }


def check_test_availability(test_name: str) -> dict[str, Any]:
    """Check if a diagnostic test is available.

    Args:
        test_name: Test name to search for (case-insensitive, partial match).

    Returns:
        Dict with availability, turnaround time, and location.
    """
    normalized = test_name.lower().strip()

    for key, test in DIAGNOSTIC_TESTS.items():
        test_name_lower = test["test_name"].lower()
        if (normalized in test_name_lower
            or test_name_lower in normalized
            or normalized in key
            or key in normalized
            or normalized.replace(" ", "-") in key
            or key.replace("-", " ") in normalized):
            return _format_test_result(test)

    # Word-level fuzzy: check if any significant word matches
    query_words = [w for w in normalized.split() if len(w) > 2]
    for key, test in DIAGNOSTIC_TESTS.items():
        test_name_lower = test["test_name"].lower()
        for word in query_words:
            if word in key or word in test_name_lower:
                return _format_test_result(test)

    return {
        "found": False,
        "test": test_name,
        "available": False,
        "message": f"'{test_name}' not found. Contact lab for availability.",
    }


def get_full_inventory() -> dict[str, Any]:
    """Return the full mock inventory for dashboard display."""
    return {
        "drugs": {k: _format_drug_result(v) for k, v in DRUG_INVENTORY.items()},
        "tests": {k: _format_test_result(v) for k, v in DIAGNOSTIC_TESTS.items()},
        "hospital": "LAUTECH Teaching Hospital",
        "last_updated": "2026-07-02T14:00:00Z",
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _format_drug_result(drug: dict[str, Any]) -> dict[str, Any]:
    return {
        "found": True,
        "drug": drug["generic_name"],
        "brand_name": drug["brand_name"],
        "available": drug["available"] and drug["stock"] > 0,
        "stock": drug["stock"],
        "unit": drug["unit"],
        "location": drug["location"],
        "expiry": drug["expiry"],
    }


def _format_test_result(test: dict[str, Any]) -> dict[str, Any]:
    return {
        "found": True,
        "test": test["test_name"],
        "available": test["available"],
        "stock": test["stock"],
        "turnaround_minutes": test["turnaround_minutes"],
        "location": test["location"],
    }

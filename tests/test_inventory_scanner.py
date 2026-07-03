"""Unit tests for the Inventory Scanner service.

Pure function tests — no database, no API, no auth.
"""

import pytest

from app.services.inventory_scanner import (
    check_drug_availability,
    check_test_availability,
    get_full_inventory,
    DRUG_INVENTORY,
    DIAGNOSTIC_TESTS,
)


# ── Drug Availability ────────────────────────────────────────────────────────

class TestCheckDrugAvailability:
    """Tests for check_drug_availability()."""

    def test_exact_key_match(self):
        """Exact inventory key returns the correct drug."""
        result = check_drug_availability("paracetamol")
        assert result["found"] is True
        assert result["brand_name"] == "Panadol"
        assert result["available"] is True
        assert result["stock"] == 200

    def test_brand_name_match(self):
        """Searching by brand name (Coartem) finds Artemether-Lumefantrine."""
        result = check_drug_availability("Coartem")
        assert result["found"] is True
        assert result["drug"] == "Artemether-Lumefantrine"
        assert result["available"] is True

    def test_generic_name_match(self):
        """Searching by generic name partial finds the drug."""
        result = check_drug_availability("Amoxicillin")
        assert result["found"] is True
        assert result["brand_name"] == "Amoxil"

    def test_case_insensitive(self):
        """Search is case-insensitive."""
        result = check_drug_availability("ASPIRIN")
        assert result["found"] is True
        assert result["brand_name"] == "Aspirin"

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is ignored."""
        result = check_drug_availability("  metformin  ")
        assert result["found"] is True
        assert result["brand_name"] == "Glucophage"

    def test_not_found(self):
        """Unknown drug returns found=False with helpful message."""
        result = check_drug_availability("zyrtec")
        assert result["found"] is False
        assert result["available"] is False
        assert "not found" in result["message"].lower()

    def test_result_structure(self):
        """Returned dict has all expected keys for a found drug."""
        result = check_drug_availability("paracetamol")
        expected_keys = {"found", "drug", "brand_name", "available", "stock", "unit", "location", "expiry"}
        assert expected_keys == set(result.keys())

    def test_partial_key_match(self):
        """Partial match on inventory key works (e.g. 'ferrous')."""
        result = check_drug_availability("ferrous")
        assert result["found"] is True
        assert "Ferrous" in result["brand_name"]


# ── Test Availability ────────────────────────────────────────────────────────

class TestCheckTestAvailability:
    """Tests for check_test_availability()."""

    def test_exact_key_match(self):
        """Exact key 'ecg' returns 12-Lead ECG."""
        result = check_test_availability("ecg")
        assert result["found"] is True
        assert "ECG" in result["test"]
        assert result["available"] is True

    def test_partial_name_match(self):
        """Searching 'malaria' finds the malaria RDT."""
        result = check_test_availability("malaria")
        assert result["found"] is True
        assert "Malaria" in result["test"]

    def test_word_level_fuzzy(self):
        """Word-level fuzzy: 'blood glucose' matches Fasting Blood Glucose."""
        result = check_test_availability("blood glucose")
        assert result["found"] is True
        assert "Blood Glucose" in result["test"]

    def test_hyphen_space_normalization(self):
        """'chest xray' matches 'chest-xray' key."""
        result = check_test_availability("chest xray")
        assert result["found"] is True
        assert "Chest X-Ray" in result["test"]

    def test_not_found(self):
        """Unknown test returns found=False."""
        result = check_test_availability("MRI brain")
        assert result["found"] is False
        assert result["available"] is False
        assert "not found" in result["message"].lower()

    def test_result_structure(self):
        """Returned dict has all expected keys for a found test."""
        result = check_test_availability("troponin")
        expected_keys = {"found", "test", "available", "stock", "turnaround_minutes", "location"}
        assert expected_keys == set(result.keys())

    def test_equipment_stock_is_none(self):
        """Equipment-based tests (ECG) have stock=None."""
        result = check_test_availability("ecg")
        assert result["stock"] is None

    def test_consumable_has_stock(self):
        """Consumable tests (troponin) have a numeric stock."""
        result = check_test_availability("troponin")
        assert isinstance(result["stock"], int)
        assert result["stock"] > 0


# ── Full Inventory ───────────────────────────────────────────────────────────

class TestGetFullInventory:
    """Tests for get_full_inventory()."""

    def test_returns_drugs_and_tests(self):
        """Full inventory contains both drugs and tests sections."""
        inventory = get_full_inventory()
        assert "drugs" in inventory
        assert "tests" in inventory
        assert "hospital" in inventory

    def test_all_drugs_included(self):
        """Every drug in the mock DB appears in the full inventory."""
        inventory = get_full_inventory()
        assert len(inventory["drugs"]) == len(DRUG_INVENTORY)

    def test_all_tests_included(self):
        """Every test in the mock DB appears in the full inventory."""
        inventory = get_full_inventory()
        assert len(inventory["tests"]) == len(DIAGNOSTIC_TESTS)

    def test_drug_entries_are_formatted(self):
        """Drug entries in the full inventory use the formatted structure."""
        inventory = get_full_inventory()
        for key, drug in inventory["drugs"].items():
            assert "found" in drug
            assert "drug" in drug
            assert "available" in drug

#!/usr/bin/env python3
"""Tests for fetch-cars.py — validate the seed-based car data pipeline."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Make sure the scripts directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import functions under test directly from the script module
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "fetch_cars", Path(__file__).resolve().parent / "fetch-cars.py"
)
fetch_cars = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fetch_cars)

validate_car = fetch_cars.validate_car
load_seed_data = fetch_cars.load_seed_data
load_existing_cars = fetch_cars.load_existing_cars
extract_wiki_title = fetch_cars.extract_wiki_title
make_fact = fetch_cars.make_fact


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _good_car(**overrides) -> dict:
    """Return a valid car dict, with optional field overrides."""
    base = {
        "id": 1,
        "make": "Toyota",
        "model": "Supra",
        "year": 1993,
        "country": "Japan",
        "horsepower": 320,
        "weight_kg": 1560,
        "engine": "I6 Twin Turbo",
        "drivetrain": "RWD",
        "image": "/cars/toyota-supra.webp",
        "fact": "A great car.",
        "wiki": "https://en.wikipedia.org/wiki/Toyota_Supra",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# validate_car
# ---------------------------------------------------------------------------

class TestValidateCar:
    def test_valid_car_passes(self):
        valid, reasons = validate_car(_good_car())
        assert valid is True
        assert reasons == []

    def test_missing_make(self):
        valid, reasons = validate_car(_good_car(make=""))
        assert valid is False
        assert "missing make" in reasons

    def test_missing_model(self):
        valid, reasons = validate_car(_good_car(model=""))
        assert valid is False
        assert "missing model" in reasons

    def test_invalid_year_too_low(self):
        valid, reasons = validate_car(_good_car(year=1700))
        assert valid is False
        assert any("invalid year" in r for r in reasons)

    def test_invalid_year_too_high(self):
        valid, reasons = validate_car(_good_car(year=2050))
        assert valid is False
        assert any("invalid year" in r for r in reasons)

    def test_missing_country(self):
        valid, reasons = validate_car(_good_car(country=""))
        assert valid is False
        assert "missing country" in reasons

    def test_zero_hp(self):
        valid, reasons = validate_car(_good_car(horsepower=0))
        assert valid is False
        assert any("invalid horsepower" in r for r in reasons)

    def test_negative_hp(self):
        valid, reasons = validate_car(_good_car(horsepower=-10))
        assert valid is False
        assert any("invalid horsepower" in r for r in reasons)

    def test_zero_weight(self):
        valid, reasons = validate_car(_good_car(weight_kg=0))
        assert valid is False
        assert any("invalid weight" in r for r in reasons)

    def test_missing_engine(self):
        valid, reasons = validate_car(_good_car(engine=""))
        assert valid is False
        assert "missing engine" in reasons

    def test_missing_drivetrain(self):
        valid, reasons = validate_car(_good_car(drivetrain=""))
        assert valid is False
        assert "missing drivetrain" in reasons

    def test_multiple_errors(self):
        valid, reasons = validate_car(_good_car(make="", engine="", year=0))
        assert valid is False
        assert len(reasons) == 3


# ---------------------------------------------------------------------------
# extract_wiki_title
# ---------------------------------------------------------------------------

class TestExtractWikiTitle:
    def test_standard_url(self):
        url = "https://en.wikipedia.org/wiki/Toyota_Supra"
        assert extract_wiki_title(url) == "Toyota_Supra"

    def test_url_with_encoded_chars(self):
        url = "https://en.wikipedia.org/wiki/Citro%C3%ABn_DS"
        assert extract_wiki_title(url) == "Citroën_DS"

    def test_empty_url(self):
        assert extract_wiki_title("") == ""

    def test_non_wiki_url(self):
        assert extract_wiki_title("https://example.com/cars") == ""

    def test_url_with_parentheses(self):
        url = "https://en.wikipedia.org/wiki/Toyota_Supra_(A80)"
        assert extract_wiki_title(url) == "Toyota_Supra_(A80)"


# ---------------------------------------------------------------------------
# make_fact
# ---------------------------------------------------------------------------

class TestMakeFact:
    def test_empty_extract(self):
        assert make_fact("") == ""

    def test_single_sentence(self):
        extract = "The Toyota Supra is a sports car"
        result = make_fact(extract)
        assert "Toyota Supra" in result
        assert result.endswith(".")

    def test_two_sentences(self):
        extract = "The Toyota Supra is a sports car. It was first produced in 1978."
        result = make_fact(extract)
        assert "Toyota Supra" in result
        assert "1978" in result

    def test_long_extract_trimmed(self):
        extract = "A" * 300
        result = make_fact(extract)
        assert len(result) <= 283  # 280 + "..."

    def test_adds_period_if_missing(self):
        extract = "The Toyota Supra is a sports car"
        result = make_fact(extract)
        assert result.endswith(".")


# ---------------------------------------------------------------------------
# load_seed_data
# ---------------------------------------------------------------------------

class TestLoadSeedData:
    def test_loads_all_seed_data(self):
        cars = load_seed_data()
        assert len(cars) >= 365
        assert len(cars) <= 600

    def test_limit_works(self):
        cars = load_seed_data(limit=10)
        assert len(cars) == 10

    def test_all_cars_valid(self):
        cars = load_seed_data()
        for car in cars:
            valid, reasons = validate_car(car)
            assert valid, f"{car['make']} {car['model']}: {reasons}"

    def test_cars_have_required_fields(self):
        cars = load_seed_data(limit=5)
        for car in cars:
            assert car["make"]
            assert car["model"]
            assert car["year"] > 0
            assert car["country"]
            assert car["horsepower"] > 0
            assert car["weight_kg"] > 0
            assert car["engine"]
            assert car["drivetrain"]
            assert car["image"]
            assert car["wiki"]


# ---------------------------------------------------------------------------
# load_existing_cars
# ---------------------------------------------------------------------------

class TestLoadExistingCars:
    def test_loads_from_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False,
        ) as f:
            json.dump([
                _good_car(make="Toyota", model="Supra"),
                _good_car(id=2, make="Mazda", model="RX-7"),
            ], f)
            f.flush()
            lookup = load_existing_cars(Path(f.name))
        assert len(lookup) == 2
        assert "toyota|supra" in lookup
        assert "mazda|rx-7" in lookup

    def test_missing_file_returns_empty(self):
        lookup = load_existing_cars(Path("/nonexistent/cars.json"))
        assert lookup == {}

    def test_preserves_fact(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False,
        ) as f:
            json.dump([
                _good_car(fact="A legendary engine"),
            ], f)
            f.flush()
            lookup = load_existing_cars(Path(f.name))
        assert lookup["toyota|supra"]["fact"] == "A legendary engine"


# ---------------------------------------------------------------------------
# Integration: seed data quality
# ---------------------------------------------------------------------------

class TestSeedDataQuality:
    """Verify the seed data produces enough valid cars for a year."""

    def test_at_least_365_cars(self):
        cars = load_seed_data()
        assert len(cars) >= 365, (
            f"Need at least 365 cars for a year, got {len(cars)}"
        )

    def test_no_duplicate_ids(self):
        cars = load_seed_data()
        ids = [c["id"] for c in cars]
        assert len(ids) == len(set(ids))

    def test_sequential_ids(self):
        cars = load_seed_data()
        for i, car in enumerate(cars, 1):
            assert car["id"] == i

    def test_all_images_are_webp_paths(self):
        cars = load_seed_data()
        for car in cars:
            assert car["image"].startswith("/cars/")
            assert car["image"].endswith(".webp")

    def test_all_wikis_are_urls(self):
        cars = load_seed_data()
        for car in cars:
            assert car["wiki"].startswith("https://en.wikipedia.org/wiki/")

    def test_diverse_countries(self):
        cars = load_seed_data()
        countries = set(c["country"] for c in cars)
        assert len(countries) >= 10

    def test_diverse_decades(self):
        cars = load_seed_data()
        decades = set((c["year"] // 10) * 10 for c in cars)
        assert len(decades) >= 5

    def test_diverse_drivetrains(self):
        cars = load_seed_data()
        dts = set(c["drivetrain"] for c in cars)
        assert "RWD" in dts
        assert "FWD" in dts
        assert "AWD" in dts

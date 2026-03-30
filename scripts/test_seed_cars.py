#!/usr/bin/env python3
"""Tests for seed-cars.py — ensure seed data quality and validation."""

import importlib.util
import sys
from pathlib import Path

import pytest

# Import the seed module
_spec = importlib.util.spec_from_file_location(
    "seed_cars", Path(__file__).resolve().parent / "seed-cars.py"
)
seed_cars = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed_cars)

build_cars = seed_cars.build_cars
validate_car = seed_cars.validate_car
make_slug = seed_cars.make_slug
generate_wiki_url = seed_cars.generate_wiki_url
CARS = seed_cars.CARS


# ---------------------------------------------------------------------------
# validate_car tests (same logic as fetch-cars, but verify independently)
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
        "engine": "I6",
        "drivetrain": "RWD",
        "image": "/cars/toyota-supra.webp",
        "fact": "",
        "wiki": "https://en.wikipedia.org/wiki/Toyota_Supra",
    }
    base.update(overrides)
    return base


class TestValidateCar:
    def test_valid_car(self):
        valid, reasons = validate_car(_good_car())
        assert valid is True
        assert reasons == []

    def test_year_zero_rejected(self):
        valid, reasons = validate_car(_good_car(year=0))
        assert valid is False
        assert any("year" in r for r in reasons)

    def test_horsepower_zero_rejected(self):
        valid, reasons = validate_car(_good_car(horsepower=0))
        assert valid is False

    def test_weight_zero_rejected(self):
        valid, reasons = validate_car(_good_car(weight_kg=0))
        assert valid is False

    def test_empty_make_rejected(self):
        valid, reasons = validate_car(_good_car(make=""))
        assert valid is False

    def test_empty_model_rejected(self):
        valid, reasons = validate_car(_good_car(model=""))
        assert valid is False

    def test_empty_country_rejected(self):
        valid, reasons = validate_car(_good_car(country=""))
        assert valid is False

    def test_empty_engine_rejected(self):
        valid, reasons = validate_car(_good_car(engine=""))
        assert valid is False

    def test_empty_drivetrain_rejected(self):
        valid, reasons = validate_car(_good_car(drivetrain=""))
        assert valid is False


# ---------------------------------------------------------------------------
# Seed data quality tests — ensure the curated list has no flaky entries
# ---------------------------------------------------------------------------

class TestSeedDataQuality:
    """Verify that ALL entries in the curated seed data pass validation."""

    @pytest.fixture(scope="class")
    def all_cars(self):
        return build_cars()

    def test_all_cars_have_valid_data(self, all_cars):
        """Every car in the seed dataset must pass validation."""
        invalid = []
        for car in all_cars:
            valid, reasons = validate_car(car)
            if not valid:
                invalid.append(
                    f"{car['make']} {car['model']}: {', '.join(reasons)}"
                )
        assert invalid == [], (
            f"Found {len(invalid)} invalid cars in seed data:\n"
            + "\n".join(invalid)
        )

    def test_no_zero_years(self, all_cars):
        bad = [c for c in all_cars if c["year"] == 0]
        assert bad == [], f"Cars with year=0: {[f'{c['make']} {c['model']}' for c in bad]}"

    def test_no_zero_horsepower(self, all_cars):
        bad = [c for c in all_cars if c["horsepower"] <= 0]
        assert bad == [], f"Cars with hp<=0: {[f'{c['make']} {c['model']}' for c in bad]}"

    def test_no_zero_weight(self, all_cars):
        bad = [c for c in all_cars if c["weight_kg"] <= 0]
        assert bad == [], f"Cars with weight<=0: {[f'{c['make']} {c['model']}' for c in bad]}"

    def test_no_empty_engine(self, all_cars):
        bad = [c for c in all_cars if not c["engine"]]
        assert bad == [], f"Cars with empty engine: {[f'{c['make']} {c['model']}' for c in bad]}"

    def test_no_empty_drivetrain(self, all_cars):
        bad = [c for c in all_cars if not c["drivetrain"]]
        assert bad == [], f"Cars with empty drivetrain: {[f'{c['make']} {c['model']}' for c in bad]}"

    def test_no_empty_country(self, all_cars):
        bad = [c for c in all_cars if not c["country"]]
        assert bad == [], f"Cars with empty country: {[f'{c['make']} {c['model']}' for c in bad]}"

    def test_years_in_reasonable_range(self, all_cars):
        for car in all_cars:
            assert 1800 <= car["year"] <= 2030, (
                f"{car['make']} {car['model']} has year {car['year']}"
            )

    def test_horsepower_in_reasonable_range(self, all_cars):
        for car in all_cars:
            assert 1 <= car["horsepower"] <= 3000, (
                f"{car['make']} {car['model']} has {car['horsepower']}hp"
            )

    def test_weight_in_reasonable_range(self, all_cars):
        for car in all_cars:
            assert 100 <= car["weight_kg"] <= 5000, (
                f"{car['make']} {car['model']} weighs {car['weight_kg']}kg"
            )

    def test_sequential_ids(self, all_cars):
        for idx, car in enumerate(all_cars, 1):
            assert car["id"] == idx, (
                f"Car {car['make']} {car['model']} has id {car['id']} but expected {idx}"
            )

    def test_no_duplicate_slugs(self, all_cars):
        slugs = [c["image"] for c in all_cars]
        dupes = [s for s in slugs if slugs.count(s) > 1]
        assert dupes == [], f"Duplicate image slugs: {set(dupes)}"


# ---------------------------------------------------------------------------
# build_cars tests
# ---------------------------------------------------------------------------

class TestBuildCars:
    def test_returns_list(self):
        cars = build_cars()
        assert isinstance(cars, list)
        assert len(cars) > 0

    def test_limit_works(self):
        cars = build_cars(limit=10)
        assert len(cars) == 10

    def test_limit_reassigns_ids(self):
        cars = build_cars(limit=5)
        for idx, car in enumerate(cars, 1):
            assert car["id"] == idx

    def test_car_structure(self):
        cars = build_cars(limit=1)
        car = cars[0]
        required_keys = {
            "id", "make", "model", "year", "country",
            "horsepower", "weight_kg", "engine", "drivetrain",
            "image", "fact", "wiki",
        }
        assert required_keys.issubset(set(car.keys()))


# ---------------------------------------------------------------------------
# Raw CARS tuple validation
# ---------------------------------------------------------------------------

class TestCarsRawData:
    def test_all_tuples_have_8_fields(self):
        for idx, entry in enumerate(CARS):
            assert len(entry) == 8, (
                f"Entry {idx}: {entry[0]} {entry[1]} has {len(entry)} fields, expected 8"
            )

    def test_all_years_positive(self):
        for entry in CARS:
            make, model, year = entry[0], entry[1], entry[2]
            assert isinstance(year, int) and year > 0, (
                f"{make} {model} has bad year: {year}"
            )

    def test_all_hp_positive(self):
        for entry in CARS:
            make, model, hp = entry[0], entry[1], entry[4]
            assert isinstance(hp, int) and hp > 0, (
                f"{make} {model} has bad hp: {hp}"
            )

    def test_all_weight_positive(self):
        for entry in CARS:
            make, model, weight = entry[0], entry[1], entry[5]
            assert isinstance(weight, int) and weight > 0, (
                f"{make} {model} has bad weight: {weight}"
            )

    def test_all_drivetrains_valid(self):
        valid_dt = {"FWD", "RWD", "AWD", "4WD"}
        for entry in CARS:
            make, model, dt = entry[0], entry[1], entry[7]
            assert dt in valid_dt, (
                f"{make} {model} has invalid drivetrain: {dt}"
            )


# ---------------------------------------------------------------------------
# Utility function tests
# ---------------------------------------------------------------------------

class TestMakeSlug:
    def test_basic_slug(self):
        assert make_slug("Toyota", "Supra") == "toyota-supra"

    def test_spaces_in_name(self):
        assert make_slug("Land Rover", "Range Rover") == "land-rover-range-rover"


class TestGenerateWikiUrl:
    def test_basic_url(self):
        url = generate_wiki_url("Toyota", "Supra")
        assert url == "https://en.wikipedia.org/wiki/Toyota_Supra"

    def test_parenthetical_removed(self):
        url = generate_wiki_url("Chevrolet", "Corvette (C8)")
        assert "(C8)" not in url

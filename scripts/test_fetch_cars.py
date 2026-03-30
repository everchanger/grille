#!/usr/bin/env python3
"""Tests for fetch-cars.py — ensure bad/flaky data is never output."""

import sys
from pathlib import Path

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
clean_make = fetch_cars.clean_make
clean_engine = fetch_cars.clean_engine
clean_drivetrain = fetch_cars.clean_drivetrain
process_results = fetch_cars.process_results
enrich_from_seed = fetch_cars.enrich_from_seed
get_val = fetch_cars.get_val
make_slug = fetch_cars.make_slug


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
        "engine": "I6",
        "drivetrain": "RWD",
        "image": "/cars/toyota-supra.webp",
        "fact": "",
        "wiki": "https://en.wikipedia.org/wiki/Toyota_Supra",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# validate_car tests
# ---------------------------------------------------------------------------

class TestValidateCar:
    """Ensure validate_car rejects cars with bad/missing data."""

    def test_valid_car_passes(self):
        valid, reasons = validate_car(_good_car())
        assert valid is True
        assert reasons == []

    def test_year_zero_rejected(self):
        valid, reasons = validate_car(_good_car(year=0))
        assert valid is False
        assert any("year" in r for r in reasons)

    def test_year_negative_rejected(self):
        valid, reasons = validate_car(_good_car(year=-1))
        assert valid is False

    def test_year_too_old_rejected(self):
        valid, reasons = validate_car(_good_car(year=1700))
        assert valid is False

    def test_year_too_new_rejected(self):
        valid, reasons = validate_car(_good_car(year=2099))
        assert valid is False

    def test_year_1800_accepted(self):
        valid, _ = validate_car(_good_car(year=1800))
        assert valid is True

    def test_year_2030_accepted(self):
        valid, _ = validate_car(_good_car(year=2030))
        assert valid is True

    def test_horsepower_zero_rejected(self):
        valid, reasons = validate_car(_good_car(horsepower=0))
        assert valid is False
        assert any("horsepower" in r for r in reasons)

    def test_horsepower_negative_rejected(self):
        valid, reasons = validate_car(_good_car(horsepower=-50))
        assert valid is False

    def test_weight_zero_rejected(self):
        valid, reasons = validate_car(_good_car(weight_kg=0))
        assert valid is False
        assert any("weight" in r for r in reasons)

    def test_weight_negative_rejected(self):
        valid, reasons = validate_car(_good_car(weight_kg=-100))
        assert valid is False

    def test_missing_make_rejected(self):
        valid, reasons = validate_car(_good_car(make=""))
        assert valid is False
        assert any("make" in r for r in reasons)

    def test_missing_model_rejected(self):
        valid, reasons = validate_car(_good_car(model=""))
        assert valid is False
        assert any("model" in r for r in reasons)

    def test_missing_country_rejected(self):
        valid, reasons = validate_car(_good_car(country=""))
        assert valid is False
        assert any("country" in r for r in reasons)

    def test_missing_engine_rejected(self):
        valid, reasons = validate_car(_good_car(engine=""))
        assert valid is False
        assert any("engine" in r for r in reasons)

    def test_missing_drivetrain_rejected(self):
        valid, reasons = validate_car(_good_car(drivetrain=""))
        assert valid is False
        assert any("drivetrain" in r for r in reasons)

    def test_multiple_bad_fields_all_reported(self):
        valid, reasons = validate_car(_good_car(year=0, horsepower=0, engine=""))
        assert valid is False
        assert len(reasons) == 3

    def test_none_make_rejected(self):
        car = _good_car()
        car["make"] = None
        valid, reasons = validate_car(car)
        assert valid is False

    def test_string_year_rejected(self):
        car = _good_car()
        car["year"] = "1993"
        valid, reasons = validate_car(car)
        assert valid is False


# ---------------------------------------------------------------------------
# clean_make tests
# ---------------------------------------------------------------------------

class TestCleanMake:
    def test_override_bmw(self):
        assert clean_make("Bayerische Motoren Werke") == "BMW"

    def test_override_porsche(self):
        assert clean_make("Dr. Ing. h.c. F. Porsche AG") == "Porsche"

    def test_strip_motor_company(self):
        assert clean_make("Ford Motor Company") == "Ford"

    def test_strip_corporation(self):
        assert clean_make("Toyota Motor Corporation") == "Toyota"

    def test_plain_name_unchanged(self):
        assert clean_make("Ferrari") == "Ferrari"

    def test_empty_returns_original(self):
        assert clean_make("Inc.") != ""


# ---------------------------------------------------------------------------
# clean_engine tests
# ---------------------------------------------------------------------------

class TestCleanEngine:
    def test_v8_type_preferred(self):
        assert clean_engine("gasoline engine", "V8 engine") == "V8"

    def test_gasoline_returns_empty(self):
        assert clean_engine("gasoline engine") == ""

    def test_diesel(self):
        assert clean_engine("diesel engine") == "Diesel"

    def test_electric(self):
        assert clean_engine("electric motor") == "Electric"

    def test_rotary(self):
        assert clean_engine("Wankel engine") == "Rotary"

    def test_already_short(self):
        assert clean_engine("V6") == "V6"

    def test_unknown_label_passthrough(self):
        assert clean_engine("some exotic engine") == "some exotic engine"


# ---------------------------------------------------------------------------
# clean_drivetrain tests
# ---------------------------------------------------------------------------

class TestCleanDrivetrain:
    def test_front_wheel(self):
        assert clean_drivetrain("front-wheel drive") == "FWD"

    def test_rear_wheel(self):
        assert clean_drivetrain("rear-wheel drive") == "RWD"

    def test_all_wheel(self):
        assert clean_drivetrain("all-wheel drive") == "AWD"

    def test_four_wheel(self):
        assert clean_drivetrain("four-wheel drive") == "4WD"

    def test_already_short(self):
        assert clean_drivetrain("AWD") == "AWD"

    def test_empty_returns_empty(self):
        assert clean_drivetrain("") == ""

    def test_layout_mapping(self):
        assert clean_drivetrain("front-engine, front-wheel-drive layout") == "FWD"


# ---------------------------------------------------------------------------
# enrich_from_seed tests
# ---------------------------------------------------------------------------

class TestEnrichFromSeed:
    def test_fills_missing_year(self):
        car = _good_car(year=0)
        seed = {("toyota", "supra"): _good_car(year=1993)}
        result = enrich_from_seed(car, seed)
        assert result["year"] == 1993

    def test_fills_missing_hp(self):
        car = _good_car(horsepower=0)
        seed = {("toyota", "supra"): _good_car(horsepower=320)}
        result = enrich_from_seed(car, seed)
        assert result["horsepower"] == 320

    def test_fills_missing_weight(self):
        car = _good_car(weight_kg=0)
        seed = {("toyota", "supra"): _good_car(weight_kg=1560)}
        result = enrich_from_seed(car, seed)
        assert result["weight_kg"] == 1560

    def test_fills_missing_engine(self):
        car = _good_car(engine="")
        seed = {("toyota", "supra"): _good_car(engine="I6")}
        result = enrich_from_seed(car, seed)
        assert result["engine"] == "I6"

    def test_fills_missing_drivetrain(self):
        car = _good_car(drivetrain="")
        seed = {("toyota", "supra"): _good_car(drivetrain="RWD")}
        result = enrich_from_seed(car, seed)
        assert result["drivetrain"] == "RWD"

    def test_does_not_overwrite_existing(self):
        car = _good_car(year=2000)
        seed = {("toyota", "supra"): _good_car(year=1993)}
        result = enrich_from_seed(car, seed)
        assert result["year"] == 2000

    def test_empty_seed_returns_unchanged(self):
        car = _good_car(year=0)
        result = enrich_from_seed(car, {})
        assert result["year"] == 0

    def test_no_match_returns_unchanged(self):
        car = _good_car(year=0)
        seed = {("ford", "mustang"): _good_car(make="Ford", model="Mustang")}
        result = enrich_from_seed(car, seed)
        assert result["year"] == 0


# ---------------------------------------------------------------------------
# process_results integration tests — ensure flaky data is filtered out
# ---------------------------------------------------------------------------

def _make_sparql_row(
    entity: str = "Q1234",
    car_label: str = "Supra",
    manufacturer: str = "Toyota",
    country: str = "Japan",
    inception: str = "1993-01-01T00:00:00Z",
    image: str = "",
    article: str = "",
    sitelinks: str = "50",
) -> dict:
    """Build a fake SPARQL result row."""
    row = {
        "car": {"value": f"http://www.wikidata.org/entity/{entity}"},
        "carLabel": {"value": car_label},
        "manufacturerLabel": {"value": manufacturer},
        "sitelinks": {"value": sitelinks},
    }
    if country:
        row["countryLabel"] = {"value": country}
    if inception:
        row["inception"] = {"value": inception}
    if image:
        row["image"] = {"value": image}
    if article:
        row["article"] = {"value": article}
    return row


class TestProcessResults:
    def test_car_with_full_specs_included(self):
        rows = [_make_sparql_row()]
        specs = {
            "Q1234": {
                "horsepower": 320,
                "weight_kg": 1560,
                "engine": "I6",
                "drivetrain": "RWD",
            }
        }
        cars = process_results(rows, specs)
        assert len(cars) == 1
        assert cars[0]["make"] == "Toyota"
        assert cars[0]["year"] == 1993

    def test_car_with_zero_year_excluded(self):
        rows = [_make_sparql_row(inception="")]
        specs = {
            "Q1234": {
                "horsepower": 320,
                "weight_kg": 1560,
                "engine": "I6",
                "drivetrain": "RWD",
            }
        }
        cars = process_results(rows, specs)
        assert len(cars) == 0

    def test_car_with_zero_hp_excluded(self):
        rows = [_make_sparql_row()]
        specs = {
            "Q1234": {
                "horsepower": 0,
                "weight_kg": 1560,
                "engine": "I6",
                "drivetrain": "RWD",
            }
        }
        cars = process_results(rows, specs)
        assert len(cars) == 0

    def test_car_with_zero_weight_excluded(self):
        rows = [_make_sparql_row()]
        specs = {
            "Q1234": {
                "horsepower": 320,
                "weight_kg": 0,
                "engine": "I6",
                "drivetrain": "RWD",
            }
        }
        cars = process_results(rows, specs)
        assert len(cars) == 0

    def test_car_with_no_engine_excluded(self):
        rows = [_make_sparql_row()]
        specs = {
            "Q1234": {
                "horsepower": 320,
                "weight_kg": 1560,
                "engine": "",
                "drivetrain": "RWD",
            }
        }
        cars = process_results(rows, specs)
        assert len(cars) == 0

    def test_car_with_no_drivetrain_excluded(self):
        rows = [_make_sparql_row()]
        specs = {
            "Q1234": {
                "horsepower": 320,
                "weight_kg": 1560,
                "engine": "V8",
                "drivetrain": "",
            }
        }
        cars = process_results(rows, specs)
        assert len(cars) == 0

    def test_car_with_no_specs_at_all_excluded(self):
        rows = [_make_sparql_row()]
        specs = {}
        cars = process_results(rows, specs)
        assert len(cars) == 0

    def test_car_with_no_country_excluded(self):
        rows = [_make_sparql_row(country="")]
        specs = {
            "Q1234": {
                "horsepower": 320,
                "weight_kg": 1560,
                "engine": "I6",
                "drivetrain": "RWD",
            }
        }
        cars = process_results(rows, specs)
        assert len(cars) == 0

    def test_qid_labels_excluded(self):
        rows = [_make_sparql_row(car_label="Q99999")]
        specs = {
            "Q1234": {
                "horsepower": 320,
                "weight_kg": 1560,
                "engine": "I6",
                "drivetrain": "RWD",
            }
        }
        cars = process_results(rows, specs)
        assert len(cars) == 0

    def test_seed_enrichment_saves_car(self):
        """A car missing HP can be saved by seed data."""
        rows = [_make_sparql_row()]
        specs = {
            "Q1234": {
                "horsepower": 0,
                "weight_kg": 1560,
                "engine": "I6",
                "drivetrain": "RWD",
            }
        }
        seed = {("toyota", "supra"): _good_car(horsepower=320)}
        cars = process_results(rows, specs, seed_lookup=seed)
        assert len(cars) == 1
        assert cars[0]["horsepower"] == 320

    def test_multiple_bad_cars_all_filtered(self):
        rows = [
            _make_sparql_row(entity="Q1", car_label="CarA", inception=""),
            _make_sparql_row(entity="Q2", car_label="CarB"),
            _make_sparql_row(entity="Q3", car_label="CarC"),
        ]
        specs = {
            "Q1": {"horsepower": 100, "weight_kg": 1000, "engine": "I4", "drivetrain": "FWD"},
            "Q2": {"horsepower": 0, "weight_kg": 1000, "engine": "V6", "drivetrain": "RWD"},
            "Q3": {"horsepower": 200, "weight_kg": 1200, "engine": "V8", "drivetrain": "AWD"},
        }
        cars = process_results(rows, specs)
        # Q1 has no year, Q2 has 0 HP → only Q3 passes
        assert len(cars) == 1
        assert cars[0]["model"] == "CarC"


# ---------------------------------------------------------------------------
# make_slug tests
# ---------------------------------------------------------------------------

class TestMakeSlug:
    def test_basic(self):
        assert make_slug("Toyota", "Supra") == "toyota-supra"

    def test_spaces(self):
        assert make_slug("Land Rover", "Range Rover") == "land-rover-range-rover"

    def test_special_chars(self):
        slug = make_slug("Mercedes-Benz", "C-Class")
        assert slug == "mercedes-benz-c-class"


# ---------------------------------------------------------------------------
# get_val tests
# ---------------------------------------------------------------------------

class TestGetVal:
    def test_returns_value(self):
        binding = {"name": {"value": "Toyota"}}
        assert get_val(binding, "name") == "Toyota"

    def test_returns_default_when_missing(self):
        assert get_val({}, "name") == ""

    def test_returns_custom_default(self):
        assert get_val({}, "name", "unknown") == "unknown"

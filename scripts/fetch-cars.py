#!/usr/bin/env python3
"""
Fetch car data from Wikidata to populate Grille's car database.

Queries the Wikidata SPARQL endpoint for the most notable automobile models,
ranked by number of Wikipedia sitelinks (proxy for popularity/notability).

Usage:
    python scripts/fetch-cars.py [limit]

Output:
    data/cars-wikidata.json — matching the Car interface in types/index.ts
    (with extra metadata fields: image_source, wikidata, sitelinks)
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "GrilleCarFetcher/1.0 (https://github.com/everchanger/grille)"

# Map Wikidata country labels to short display names
COUNTRY_MAP = {
    "United States of America": "USA",
    "United Kingdom": "UK",
    "Germany": "Germany",
    "Japan": "Japan",
    "Italy": "Italy",
    "France": "France",
    "Sweden": "Sweden",
    "South Korea": "South Korea",
    "Czech Republic": "Czech Republic",
    "Czechoslovakia": "Czech Republic",
    "Australia": "Australia",
    "Spain": "Spain",
    "Romania": "Romania",
    "India": "India",
    "China": "China",
    "Malaysia": "Malaysia",
    "Austria": "Austria",
    "Netherlands": "Netherlands",
    "Belgium": "Belgium",
    "Canada": "Canada",
    "Brazil": "Brazil",
    "Mexico": "Mexico",
    "Russia": "Russia",
    "Soviet Union": "Russia",
    "Turkey": "Turkey",
    "Iran": "Iran",
    "Indonesia": "Indonesia",
    "Thailand": "Thailand",
    "Taiwan": "Taiwan",
    "Poland": "Poland",
}


def sparql_query(query: str) -> list[dict]:
    """Execute a SPARQL query against Wikidata and return results."""
    url = WIKIDATA_SPARQL + "?" + urllib.parse.urlencode({
        "query": query,
        "format": "json",
    })
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/sparql-results+json",
    })

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["results"]["bindings"]
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"  Attempt {attempt + 1} failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                raise


def get_val(binding: dict, key: str, default: str = "") -> str:
    """Extract a value from a SPARQL result binding."""
    if key in binding:
        return binding[key]["value"]
    return default


def fetch_car_list(limit: int = 600) -> list[dict]:
    """
    Step 1: Get the most notable car models from Wikidata.
    Searches for automobile models and generations, sorted by sitelinks.
    Returns more than needed to account for filtering.
    """
    print(f"Step 1: Fetching top {limit} car models by notability...")

    query = f"""
    SELECT DISTINCT ?car ?carLabel ?manufacturerLabel ?countryLabel
           ?inception ?image ?article ?sitelinks
    WHERE {{
      # Match automobile models and generations
      VALUES ?carType {{ wd:Q3231690 wd:Q786820 }}
      ?car wdt:P31 ?carType .
      ?car wdt:P176 ?manufacturer .
      ?car wikibase:sitelinks ?sitelinks .
      FILTER(?sitelinks > 10)

      OPTIONAL {{ ?car wdt:P495 ?country . }}
      OPTIONAL {{ ?car wdt:P571 ?inception . }}
      OPTIONAL {{ ?car wdt:P18 ?image . }}
      OPTIONAL {{
        ?article schema:about ?car ;
                 schema:isPartOf <https://en.wikipedia.org/> .
      }}

      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    ORDER BY DESC(?sitelinks)
    LIMIT {limit}
    """

    results = sparql_query(query)
    print(f"  Got {len(results)} results")
    return results


def fetch_car_specs(entity_ids: list[str]) -> dict[str, dict]:
    """
    Step 2: Fetch HP, weight, engine, and drivetrain for specific car entities.
    Batches the queries to avoid timeouts.
    """
    print(f"Step 2: Fetching specs for {len(entity_ids)} cars...")
    all_specs: dict[str, dict] = {}

    batch_size = 100
    for i in range(0, len(entity_ids), batch_size):
        batch = entity_ids[i:i + batch_size]
        values = " ".join(f"wd:{eid}" for eid in batch)

        query = f"""
        SELECT ?car ?hpAmount ?hpUnit ?weightAmount ?engineLabel ?drivetrainLabel
        WHERE {{
          VALUES ?car {{ {values} }}

          OPTIONAL {{
            ?car p:P2325 ?hpStmt .
            ?hpStmt psv:P2325 ?hpNode .
            ?hpNode wikibase:quantityAmount ?hpAmount .
            ?hpNode wikibase:quantityUnit ?hpUnit .
          }}
          OPTIONAL {{
            ?car p:P2067 ?weightStmt .
            ?weightStmt psv:P2067 ?weightNode .
            ?weightNode wikibase:quantityAmount ?weightAmount .
          }}
          OPTIONAL {{ ?car wdt:P516 ?engine . }}
          OPTIONAL {{ ?car wdt:P5765 ?drivetrain . }}

          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
        }}
        """

        results = sparql_query(query)
        print(f"  Batch {i // batch_size + 1}: got {len(results)} spec rows")

        for row in results:
            car_uri = get_val(row, "car")
            entity = car_uri.split("/")[-1]

            hp_raw = get_val(row, "hpAmount")
            hp_unit = get_val(row, "hpUnit")
            weight_raw = get_val(row, "weightAmount")
            engine = get_val(row, "engineLabel")
            drivetrain = get_val(row, "drivetrainLabel")

            # Convert HP: kW (Q25269) -> hp, PS (Q178049) stays ~same, bhp stays
            hp = 0
            if hp_raw:
                try:
                    hp_val = float(hp_raw)
                    if "Q25269" in hp_unit:  # kilowatt
                        hp = round(hp_val * 1.341)
                    elif "Q178049" in hp_unit:  # metric horsepower (PS)
                        hp = round(hp_val)
                    else:  # assume HP/bhp
                        hp = round(hp_val)
                except ValueError:
                    pass

            weight = 0
            if weight_raw:
                try:
                    weight = round(float(weight_raw))
                except ValueError:
                    pass

            # Clean engine/drivetrain labels (skip if looks like QID)
            if engine and engine.startswith("Q") and engine[1:].isdigit():
                engine = ""
            if drivetrain and drivetrain.startswith("Q") and drivetrain[1:].isdigit():
                drivetrain = ""

            if entity not in all_specs:
                all_specs[entity] = {
                    "horsepower": hp,
                    "weight_kg": weight,
                    "engine": engine,
                    "drivetrain": drivetrain,
                }
            else:
                # Merge: keep non-zero/non-empty values
                existing = all_specs[entity]
                if hp and not existing["horsepower"]:
                    existing["horsepower"] = hp
                if weight and not existing["weight_kg"]:
                    existing["weight_kg"] = weight
                if engine and not existing["engine"]:
                    existing["engine"] = engine
                if drivetrain and not existing["drivetrain"]:
                    existing["drivetrain"] = drivetrain

        # Rate limit between batches
        if i + batch_size < len(entity_ids):
            time.sleep(2)

    return all_specs


def make_slug(make: str, model: str) -> str:
    """Create a URL-safe slug from make and model."""
    text = f"{make}-{model}".lower()
    slug = ""
    for ch in text:
        if ch.isalnum() or ch == '-':
            slug += ch
        elif ch in (' ', '_', '/'):
            slug += '-'
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-')


def commons_thumb_url(url: str, width: int = 800) -> str:
    """Convert a Wikimedia Commons file URL to a thumbnail URL."""
    if "Special:FilePath/" in url:
        filename = url.split("Special:FilePath/")[-1]
        return (
            f"https://commons.wikimedia.org/wiki/Special:FilePath/"
            f"{filename}?width={width}"
        )
    return url


def process_results(
    raw_cars: list[dict], specs: dict[str, dict]
) -> list[dict]:
    """Combine car list and specs into final Car objects."""
    # Deduplicate by entity ID (keep first/best row)
    seen: dict[str, dict] = {}
    for row in raw_cars:
        car_uri = get_val(row, "car")
        entity = car_uri.split("/")[-1]
        if entity not in seen:
            seen[entity] = row
        else:
            # Merge optional fields
            existing = seen[entity]
            for key in ("countryLabel", "inception", "image", "article"):
                if not get_val(existing, key) and get_val(row, key):
                    existing[key] = row[key]

    cars = []
    for entity, row in seen.items():
        make = get_val(row, "manufacturerLabel")
        car_label = get_val(row, "carLabel")
        country = get_val(row, "countryLabel")
        inception = get_val(row, "inception")
        image_url = get_val(row, "image")
        wiki = get_val(row, "article")
        sitelinks = int(get_val(row, "sitelinks", "0"))

        # Skip unresolved labels (look like QIDs)
        if not make or not car_label:
            continue
        if car_label.startswith("Q") and car_label[1:].isdigit():
            continue
        if make.startswith("Q") and make[1:].isdigit():
            continue

        # Clean up model name — remove manufacturer prefix if present
        model = car_label
        if model.lower().startswith(make.lower()):
            model = model[len(make):].strip()
        if not model:
            model = car_label

        # Map country names
        country = COUNTRY_MAP.get(country, country)

        # Parse year from inception date
        year = 0
        if inception:
            try:
                # Wikidata dates look like "1993-01-01T00:00:00Z"
                year = int(inception[:4])
            except (ValueError, IndexError):
                pass

        # Get specs
        car_specs = specs.get(entity, {})
        hp = car_specs.get("horsepower", 0)
        weight = car_specs.get("weight_kg", 0)
        engine = car_specs.get("engine", "")
        drivetrain = car_specs.get("drivetrain", "")

        slug = make_slug(make, model)
        image_path = f"/cars/{slug}.webp"
        image_source = commons_thumb_url(image_url) if image_url else ""

        car = {
            "id": 0,  # assigned after sorting
            "make": make,
            "model": model,
            "year": year,
            "country": country,
            "horsepower": hp,
            "weight_kg": weight,
            "engine": engine,
            "drivetrain": drivetrain,
            "image": image_path,
            "image_source": image_source,
            "fact": "",
            "wiki": wiki,
            "wikidata": f"https://www.wikidata.org/wiki/{entity}",
            "sitelinks": sitelinks,
        }
        cars.append(car)

    return cars


def main():
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    output_file = repo_root / "data" / "cars-wikidata.json"

    limit = 500
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [limit]", file=sys.stderr)
            sys.exit(1)

    # Fetch extra to account for dedup/filtering
    fetch_limit = int(limit * 1.3)

    # Step 1: Get car list
    raw_cars = fetch_car_list(fetch_limit)

    # Extract entity IDs for specs query
    entity_ids = []
    seen_ids = set()
    for row in raw_cars:
        eid = get_val(row, "car").split("/")[-1]
        if eid not in seen_ids:
            entity_ids.append(eid)
            seen_ids.add(eid)

    # Step 2: Fetch specs
    specs = fetch_car_specs(entity_ids)

    # Step 3: Process and combine
    print("Step 3: Processing results...")
    cars = process_results(raw_cars, specs)

    # Sort by sitelinks (popularity) descending
    cars.sort(key=lambda c: c["sitelinks"], reverse=True)

    # Take top N
    cars = cars[:limit]

    # Assign sequential IDs
    for idx, car in enumerate(cars, start=1):
        car["id"] = idx

    # Print summary
    print(f"\nProcessed {len(cars)} cars")
    print(f"\nTop 30 by popularity:")
    for car in cars[:30]:
        specs_parts = []
        if car["year"]:
            specs_parts.append(str(car["year"]))
        if car["horsepower"]:
            specs_parts.append(f"{car['horsepower']}hp")
        if car["weight_kg"]:
            specs_parts.append(f"{car['weight_kg']}kg")
        spec_str = ", ".join(specs_parts) if specs_parts else "no specs"
        print(
            f"  {car['id']:3d}. {car['make']} {car['model']} "
            f"({spec_str}) [{car['sitelinks']} sitelinks]"
        )

    # Data completeness stats
    with_year = sum(1 for c in cars if c["year"])
    with_hp = sum(1 for c in cars if c["horsepower"])
    with_weight = sum(1 for c in cars if c["weight_kg"])
    with_engine = sum(1 for c in cars if c["engine"])
    with_dt = sum(1 for c in cars if c["drivetrain"])
    with_image = sum(1 for c in cars if c["image_source"])
    with_wiki = sum(1 for c in cars if c["wiki"])

    print(f"\nData completeness ({len(cars)} cars):")
    print(f"  Year:       {with_year:3d}/{len(cars)}")
    print(f"  Horsepower: {with_hp:3d}/{len(cars)}")
    print(f"  Weight:     {with_weight:3d}/{len(cars)}")
    print(f"  Engine:     {with_engine:3d}/{len(cars)}")
    print(f"  Drivetrain: {with_dt:3d}/{len(cars)}")
    print(f"  Image:      {with_image:3d}/{len(cars)}")
    print(f"  Wikipedia:  {with_wiki:3d}/{len(cars)}")

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cars, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {output_file}")
    print(
        "\nExtra metadata fields (not in Car interface):\n"
        "  - image_source: Wikimedia Commons URL for downloading the photo\n"
        "  - wikidata: Wikidata entity URL for manual verification\n"
        "  - sitelinks: popularity score (# of Wikipedia language editions)\n"
        "  - fact: empty — should be hand-curated for interesting entries\n"
    )
    print(
        "Next steps:\n"
        "  1. Review and curate the list (remove irrelevant entries)\n"
        "  2. Fill in missing specs from Wikipedia articles\n"
        "  3. Download images using image_source URLs, convert to .webp\n"
        "  4. Write fun facts for each car\n"
        "  5. Remove extra metadata fields to match Car interface\n"
    )


if __name__ == "__main__":
    main()

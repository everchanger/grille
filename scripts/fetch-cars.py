#!/usr/bin/env python3
"""
Build the Grille car dataset from curated seed data, enriched with
Wikipedia images and facts.

Uses seed-cars.py as the authoritative data source (~494 validated car entries
with complete specs), then enriches each car with:
  - Wikipedia page image → downloaded and converted to .webp
  - Wikipedia article intro → used as the car's fun fact

Usage:
    python scripts/fetch-cars.py [limit]
    python scripts/fetch-cars.py --skip-images 500

Output:
    data/cars.json        — complete Car-interface-compatible JSON
    public/cars/*.webp    — downloaded car images
"""

import argparse
import importlib.util
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "GrilleCarFetcher/1.0 (https://github.com/everchanger/grille)"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_seed_data(limit: int | None = None) -> list[dict]:
    """Import seed-cars.py and call build_cars() to get validated car data."""
    seed_script = Path(__file__).resolve().parent / "seed-cars.py"
    if not seed_script.exists():
        print("Error: seed-cars.py not found", file=sys.stderr)
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("seed_cars", seed_script)
    if spec is None or spec.loader is None:
        print("Error: could not load seed-cars.py", file=sys.stderr)
        sys.exit(1)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    cars = mod.build_cars(limit)
    return cars


def load_existing_cars(
    cars_file: Path | None = None,
) -> dict[str, dict]:
    """
    Load existing cars.json to preserve hand-written facts and other data.
    Returns a lookup dict keyed by "make|model" (lowercase).
    """
    if cars_file is None:
        cars_file = (
            Path(__file__).resolve().parent.parent / "data" / "cars.json"
        )
    if not cars_file.exists():
        return {}

    try:
        with open(cars_file, encoding="utf-8") as f:
            cars = json.load(f)
        lookup: dict[str, dict] = {}
        for car in cars:
            key = f"{car['make']}|{car['model']}".lower()
            lookup[key] = car
        return lookup
    except (json.JSONDecodeError, KeyError):
        return {}


# ---------------------------------------------------------------------------
# Wikipedia API helpers
# ---------------------------------------------------------------------------


def extract_wiki_title(wiki_url: str) -> str:
    """Extract Wikipedia page title from a URL."""
    if not wiki_url:
        return ""
    parts = wiki_url.split("/wiki/")
    if len(parts) < 2:
        return ""
    return urllib.parse.unquote(parts[-1])


def _wiki_api_request(params: dict, timeout: int = 60) -> dict:
    """Make a single Wikipedia API request with retries."""
    url = WIKIPEDIA_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
            else:
                print(f"  Wikipedia API failed after 3 attempts: {e}",
                      file=sys.stderr)
    return {}


def _build_title_reverse_map(
    query: dict, batch: list[str],
) -> dict[str, str]:
    """
    Build a mapping from Wikipedia API response titles back to originally
    requested titles, accounting for normalization and redirects.
    """
    # Direct mapping: normalize underscores to spaces
    sent = {t.replace("_", " "): t for t in batch}

    # API normalization chain (from → to)
    norm_from: dict[str, str] = {}
    for n in query.get("normalized", []):
        norm_from[n["to"]] = n["from"]

    # API redirect chain (from → to)
    redir_from: dict[str, str] = {}
    for r in query.get("redirects", []):
        redir_from[r["to"]] = r["from"]

    def resolve(api_title: str) -> str:
        """Walk the chain: api_title → redirect source → normalized source."""
        title = api_title
        if title in redir_from:
            title = redir_from[title]
        if title in norm_from:
            title = norm_from[title]
        # Try matching against sent batch
        if title in sent:
            return sent[title]
        # Fallback: match by normalized form
        normalized = title.replace("_", " ")
        if normalized in sent:
            return sent[normalized]
        return api_title

    return {api_title: resolve(api_title) for api_title in
            [p.get("title", "") for p in query.get("pages", [])]}


def fetch_wikipedia_images(
    page_titles: list[str],
) -> dict[str, str]:
    """
    Batch-fetch Wikipedia page image thumbnail URLs.
    Returns {requested_title: thumbnail_url}.
    """
    all_images: dict[str, str] = {}
    batch_size = 50

    for i in range(0, len(page_titles), batch_size):
        batch = page_titles[i:i + batch_size]
        data = _wiki_api_request({
            "action": "query",
            "titles": "|".join(batch),
            "prop": "pageimages",
            "pithumbsize": 800,
            "format": "json",
            "formatversion": "2",
            "redirects": "1",
        })

        query = data.get("query", {})
        reverse = _build_title_reverse_map(query, batch)

        for page in query.get("pages", []):
            if page.get("missing"):
                continue
            api_title = page.get("title", "")
            thumb = page.get("thumbnail", {}).get("source", "")
            if thumb:
                orig = reverse.get(api_title, api_title)
                all_images[orig] = thumb

        if i + batch_size < len(page_titles):
            time.sleep(1)

    return all_images


def fetch_wikipedia_extracts(
    page_titles: list[str],
) -> dict[str, str]:
    """
    Batch-fetch Wikipedia article intro extracts (plain text).
    Returns {requested_title: extract_text}.
    """
    all_extracts: dict[str, str] = {}
    batch_size = 20  # extracts can be large; smaller batches

    for i in range(0, len(page_titles), batch_size):
        batch = page_titles[i:i + batch_size]
        data = _wiki_api_request({
            "action": "query",
            "titles": "|".join(batch),
            "prop": "extracts",
            "exintro": "true",
            "explaintext": "true",
            "exsentences": "3",
            "exlimit": str(len(batch)),
            "format": "json",
            "formatversion": "2",
            "redirects": "1",
        })

        query = data.get("query", {})
        reverse = _build_title_reverse_map(query, batch)

        for page in query.get("pages", []):
            if page.get("missing"):
                continue
            api_title = page.get("title", "")
            extract = page.get("extract", "").strip()
            if extract:
                orig = reverse.get(api_title, api_title)
                all_extracts[orig] = extract

        if i + batch_size < len(page_titles):
            time.sleep(1)

    return all_extracts


# ---------------------------------------------------------------------------
# Image downloading & conversion
# ---------------------------------------------------------------------------


def download_and_convert_image(url: str, output_path: Path) -> bool:
    """Download an image from a URL and convert/save it as .webp."""
    try:
        from PIL import Image
    except ImportError:
        return False

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                image_data = resp.read()

            img = Image.open(io.BytesIO(image_data))
            # Convert to RGB if needed (handles RGBA, palette, etc.)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            # Resize to reasonable dimensions (max 800px wide)
            if img.width > 800:
                ratio = 800 / img.width
                new_size = (800, round(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(output_path), "webp", quality=80)
            return True
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                print(f"  Failed: {output_path.name}: {e}",
                      file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# Fact generation
# ---------------------------------------------------------------------------


def make_fact(extract: str) -> str:
    """
    Create a concise fact string from a Wikipedia extract.
    Takes the first 1-2 sentences, trimmed to a reasonable length.
    """
    if not extract:
        return ""

    # Split into sentences (handle common abbreviations)
    sentences = extract.replace("i.e.", "ie").replace("e.g.", "eg").split(". ")
    fact = sentences[0].replace("ie", "i.e.").replace("eg", "e.g.")
    if len(sentences) > 1 and len(fact) < 120:
        second = sentences[1].replace("ie", "i.e.").replace("eg", "e.g.")
        fact = fact + ". " + second

    # Trim to reasonable length
    if len(fact) > 280:
        fact = fact[:277] + "..."

    # Ensure it ends with punctuation
    if not fact.endswith((".","!","?","...")):
        fact = fact + "."

    return fact


# ---------------------------------------------------------------------------
# Validation (kept for compatibility with tests)
# ---------------------------------------------------------------------------


def validate_car(car: dict) -> tuple[bool, list[str]]:
    """
    Validate that a car has all required fields for the guessing game.
    Returns (is_valid, list_of_reasons).
    """
    reasons: list[str] = []

    if not car.get("make"):
        reasons.append("missing make")
    if not car.get("model"):
        reasons.append("missing model")

    year = car.get("year", 0)
    if not isinstance(year, int) or year < 1800 or year > 2030:
        reasons.append(f"invalid year ({year})")

    if not car.get("country"):
        reasons.append("missing country")

    hp = car.get("horsepower", 0)
    if not isinstance(hp, (int, float)) or hp <= 0:
        reasons.append(f"invalid horsepower ({hp})")

    weight = car.get("weight_kg", 0)
    if not isinstance(weight, (int, float)) or weight <= 0:
        reasons.append(f"invalid weight ({weight})")

    if not car.get("engine"):
        reasons.append("missing engine")

    dt = car.get("drivetrain", "")
    if not dt:
        reasons.append("missing drivetrain")

    return (len(reasons) == 0, reasons)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Build Grille car dataset from seed data + Wikipedia"
    )
    parser.add_argument(
        "limit", nargs="?", type=int, default=500,
        help="Maximum number of cars to output (default: 500)",
    )
    parser.add_argument(
        "--skip-images", action="store_true",
        help="Skip downloading/converting images (for testing)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    output_file = repo_root / "data" / "cars.json"
    cars_dir = repo_root / "public" / "cars"

    # ------------------------------------------------------------------
    # Step 1: Load curated seed data (all specs included)
    # ------------------------------------------------------------------
    print(f"Step 1: Loading seed data (limit={args.limit})...")
    cars = load_seed_data(args.limit)
    print(f"  Loaded {len(cars)} validated cars")

    # ------------------------------------------------------------------
    # Step 2: Load existing cars.json to preserve hand-written facts
    # ------------------------------------------------------------------
    print("Step 2: Loading existing car data for fact preservation...")
    existing = load_existing_cars()
    print(f"  Found {len(existing)} existing cars")

    # ------------------------------------------------------------------
    # Step 3: Collect Wikipedia page titles from car wiki URLs
    # ------------------------------------------------------------------
    print("Step 3: Resolving Wikipedia page titles...")
    # Map: wiki_title → list of car indices (multiple cars may share a page)
    title_to_indices: dict[str, list[int]] = {}
    for idx, car in enumerate(cars):
        title = extract_wiki_title(car.get("wiki", ""))
        if title:
            title_to_indices.setdefault(title, []).append(idx)
    page_titles = list(title_to_indices.keys())
    print(f"  Found {len(page_titles)} unique Wikipedia pages "
          f"for {len(cars)} cars")

    # ------------------------------------------------------------------
    # Step 4: Fetch Wikipedia images & extracts
    # ------------------------------------------------------------------
    print("Step 4a: Fetching Wikipedia page images...")
    images = fetch_wikipedia_images(page_titles)
    print(f"  Got {len(images)} image URLs")

    print("Step 4b: Fetching Wikipedia extracts for facts...")
    extracts = fetch_wikipedia_extracts(page_titles)
    print(f"  Got {len(extracts)} extracts")

    # ------------------------------------------------------------------
    # Step 5: Download and convert images to .webp
    # ------------------------------------------------------------------
    downloaded = 0
    skipped_existing = 0
    failed = 0

    if not args.skip_images:
        print("Step 5: Downloading and converting images to .webp...")
        cars_dir.mkdir(parents=True, exist_ok=True)

        for title, img_url in images.items():
            indices = title_to_indices.get(title, [])
            for car_idx in indices:
                car = cars[car_idx]
                slug = car["image"].replace("/cars/", "").replace(".webp", "")
                out = cars_dir / f"{slug}.webp"

                if out.exists():
                    skipped_existing += 1
                    continue

                if download_and_convert_image(img_url, out):
                    downloaded += 1
                else:
                    failed += 1

        print(f"  Downloaded: {downloaded}, "
              f"Already existed: {skipped_existing}, Failed: {failed}")
    else:
        print("Step 5: Skipping image download (--skip-images)")

    # ------------------------------------------------------------------
    # Step 6: Assign facts (preserve existing, generate from Wikipedia)
    # ------------------------------------------------------------------
    print("Step 6: Assigning facts...")
    facts_preserved = 0
    facts_generated = 0
    facts_missing = 0

    for idx, car in enumerate(cars):
        key = f"{car['make']}|{car['model']}".lower()

        # 1) Preserve existing hand-written facts
        if key in existing and existing[key].get("fact"):
            car["fact"] = existing[key]["fact"]
            facts_preserved += 1
            continue

        # 2) Generate from Wikipedia extract
        title = extract_wiki_title(car.get("wiki", ""))
        if title and title in extracts:
            fact = make_fact(extracts[title])
            if fact:
                car["fact"] = fact
                facts_generated += 1
                continue

        # 3) No fact available
        if not car.get("fact"):
            car["fact"] = ""
            facts_missing += 1

    print(f"  Preserved: {facts_preserved}, "
          f"Generated: {facts_generated}, Missing: {facts_missing}")

    # ------------------------------------------------------------------
    # Step 7: Write clean output (Car interface fields only)
    # ------------------------------------------------------------------
    print("Step 7: Writing output...")
    clean_cars = []
    for car in cars:
        clean_cars.append({
            "id": car["id"],
            "make": car["make"],
            "model": car["model"],
            "year": car["year"],
            "country": car["country"],
            "horsepower": car["horsepower"],
            "weight_kg": car["weight_kg"],
            "engine": car["engine"],
            "drivetrain": car["drivetrain"],
            "image": car["image"],
            "fact": car.get("fact", ""),
            "wiki": car.get("wiki", ""),
        })

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clean_cars, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    with_fact = sum(1 for c in clean_cars if c["fact"])
    with_wiki = sum(1 for c in clean_cars if c["wiki"])
    img_count = sum(
        1 for c in clean_cars
        if (cars_dir / c["image"].lstrip("/").split("/", 1)[-1]).exists()
    ) if not args.skip_images else "N/A"

    print(f"\n{'=' * 50}")
    print(f"Saved {len(clean_cars)} cars to {output_file}")
    print(f"  With facts:  {with_fact}/{len(clean_cars)}")
    print(f"  With wiki:   {with_wiki}/{len(clean_cars)}")
    print(f"  With images: {img_count}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()

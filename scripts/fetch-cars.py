#!/usr/bin/env python3
"""
Fetch car data from Wikidata + Wikipedia to populate Grille's car database.

Step 1: Queries the Wikidata SPARQL endpoint for the most notable automobile
        models, ranked by Wikipedia sitelinks (proxy for popularity).
Step 2: Fetches Wikipedia article infoboxes via the MediaWiki API to get
        detailed specs (HP, weight, engine, drivetrain) that Wikidata lacks.

Usage:
    python scripts/fetch-cars.py [limit]

Output:
    data/cars-wikidata.json — matching the Car interface in types/index.ts
    (with extra metadata fields: image_source, wikidata, sitelinks)
"""

import json
import re
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
    "United States": "USA",
    "United Kingdom": "UK",
    "United Kingdom of Great Britain and Ireland": "UK",
    "Germany": "Germany",
    "West Germany": "Germany",
    "East Germany": "Germany",
    "Nazi Germany": "Germany",
    "German Empire": "Germany",
    "Japan": "Japan",
    "Empire of Japan": "Japan",
    "Italy": "Italy",
    "Kingdom of Italy": "Italy",
    "France": "France",
    "Sweden": "Sweden",
    "South Korea": "South Korea",
    "Czech Republic": "Czech Republic",
    "Czechoslovakia": "Czech Republic",
    "Czechia": "Czech Republic",
    "Australia": "Australia",
    "Spain": "Spain",
    "Romania": "Romania",
    "India": "India",
    "China": "China",
    "People's Republic of China": "China",
    "Malaysia": "Malaysia",
    "Austria": "Austria",
    "Austria-Hungary": "Austria",
    "Netherlands": "Netherlands",
    "Belgium": "Belgium",
    "Canada": "Canada",
    "Brazil": "Brazil",
    "Mexico": "Mexico",
    "Russia": "Russia",
    "Soviet Union": "Russia",
    "Serbia": "Serbia",
    "Yugoslavia": "Serbia",
    "Turkey": "Turkey",
    "Iran": "Iran",
    "Indonesia": "Indonesia",
    "Thailand": "Thailand",
    "Taiwan": "Taiwan",
    "Poland": "Poland",
    "Croatia": "Croatia",
    "Argentina": "Argentina",
    "South Africa": "South Africa",
    "Portugal": "Portugal",
    "Denmark": "Denmark",
    "Finland": "Finland",
    "Norway": "Norway",
    "Switzerland": "Switzerland",
}

# Corporate suffixes to strip from manufacturer labels to get brand names
MAKE_SUFFIXES = [
    " Motor Company", " Motor Corporation", " Motor Co.",
    " Motors Ltd", " Motors", " Motor",
    " Corporation", " Corp.",
    " Automobiles", " Automobile",
    " Group", " Holding",
    ", Inc.", " Inc.", " Inc",
    " Ltd.", " Ltd",
    " S.p.A.", " SpA",
    " SE & Co. KGaA", " SE", " AG", " GmbH",
    " N.V.", " NV",
    " S.A.S.", " S.A.", " SA",
    " plc", " PLC",
    " Co.", " Co",
]

# Explicit manufacturer name overrides (Wikidata label → brand name)
MAKE_OVERRIDES = {
    "Bayerische Motoren Werke": "BMW",
    "Dr. Ing. h.c. F. Porsche AG": "Porsche",
    "Mercedes-Benz Group": "Mercedes-Benz",
    "Daimler-Benz": "Mercedes-Benz",
    "Stellantis": "Stellantis",
    "Tata Motors": "Tata",
    "Rover Group": "Rover",
    "Bertha Benz": "Benz",
    "Benz & Cie.": "Benz",
    "Karl Benz": "Benz",
    "Fuji Heavy Industries": "Subaru",
    "Subaru Corporation": "Subaru",
    "Hyundai Motor Company": "Hyundai",
    "Kia Corporation": "Kia",
    "Honda Motor Co., Ltd.": "Honda",
    "Suzuki Motor Corporation": "Suzuki",
    "Mitsubishi Motors": "Mitsubishi",
    "Volkswagen Group": "Volkswagen",
    "Volkswagenwerk GmbH": "Volkswagen",
    "General Motors": "GM",
    "Chrysler": "Chrysler",
    "Fiat Chrysler Automobiles": "Chrysler",
    "Adam Opel AG": "Opel",
    "AB Volvo": "Volvo",
    "Volvo Cars": "Volvo",
    "Dacia": "Dacia",
}

# Map generic engine labels from Wikidata to cleaner short forms.
# Generic fuel-type labels (e.g. "gasoline engine") are mapped to "" because
# they don't describe the engine configuration — most cars are gasoline-powered,
# so this is effectively the default and not useful display information.
ENGINE_LABEL_MAP = {
    "gasoline engine": "",
    "petrol engine": "",
    "diesel engine": "Diesel",
    "internal combustion engine": "",
    "electric motor": "Electric",
    "induction motor": "Electric",
    "synchronous motor": "Electric",
    "AC motor": "Electric",
    "Wankel engine": "Rotary",
    "rotary engine": "Rotary",
    "flat engine": "Flat",
    "V engine": "V",
    "straight engine": "Inline",
    "inline engine": "Inline",
    "turbocharged direct injection": "Turbo",
}

# Map engine type entities (P31 of engine) to short labels
ENGINE_TYPE_MAP = {
    "V6 engine": "V6",
    "V8 engine": "V8",
    "V10 engine": "V10",
    "V12 engine": "V12",
    "V16 engine": "V16",
    "straight-four engine": "I4",
    "straight-five engine": "I5",
    "straight-six engine": "I6",
    "straight-eight engine": "I8",
    "inline-four engine": "I4",
    "inline-six engine": "I6",
    "inline-three engine": "I3",
    "flat-four engine": "Flat-4",
    "flat-six engine": "Flat-6",
    "flat-twin engine": "Flat-2",
    "W12 engine": "W12",
    "W16 engine": "W16",
    "Wankel engine": "Rotary",
    "electric motor": "Electric",
    "hybrid electric-internal combustion engine": "Hybrid",
}

# Drivetrain label mapping
DRIVETRAIN_MAP = {
    "front-wheel drive": "FWD",
    "rear-wheel drive": "RWD",
    "all-wheel drive": "AWD",
    "four-wheel drive": "4WD",
    "front-engine, front-wheel-drive layout": "FWD",
    "front-engine, rear-wheel-drive layout": "RWD",
    "rear-engine, rear-wheel-drive layout": "RWD",
    "mid-engine, rear-wheel-drive layout": "RWD",
    "front-engine, four-wheel-drive layout": "AWD",
}


def clean_make(raw_make: str) -> str:
    """Clean manufacturer label to a brand-level name."""
    # Check explicit overrides first
    if raw_make in MAKE_OVERRIDES:
        return MAKE_OVERRIDES[raw_make]
    # Strip corporate suffixes
    make = raw_make
    for suffix in MAKE_SUFFIXES:
        if make.endswith(suffix):
            make = make[:-len(suffix)].strip()
            break
    return make if make else raw_make


def clean_engine(engine_label: str, engine_type_label: str = "") -> str:
    """Clean engine label to a short description like 'V8', 'I4', etc."""
    # Prefer the engine type (from P31 of the engine entity) if available
    if engine_type_label:
        mapped = ENGINE_TYPE_MAP.get(engine_type_label)
        if mapped:
            return mapped
    # Fall back to engine label mapping
    if engine_label:
        mapped = ENGINE_LABEL_MAP.get(engine_label)
        if mapped is not None:
            return mapped
        # Check if the label already looks like a short engine type
        if engine_label in ("V6", "V8", "V10", "V12", "I4", "I6"):
            return engine_label
    return engine_label


def clean_drivetrain(dt_label: str) -> str:
    """Map drivetrain label to short form (FWD, RWD, AWD, 4WD)."""
    if not dt_label:
        return ""
    mapped = DRIVETRAIN_MAP.get(dt_label)
    if mapped:
        return mapped
    # Check if already short form
    if dt_label in ("FWD", "RWD", "AWD", "4WD"):
        return dt_label
    return dt_label


WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# Fields that may contain horsepower in Wikipedia infoboxes
HP_FIELDS = ["power", "power_output", "max_power", "hp"]

# Fields that may contain weight in Wikipedia infoboxes
WEIGHT_FIELDS = ["curb_weight", "weight", "kerb_weight", "mass"]

# Fields that may contain engine info in Wikipedia infoboxes
ENGINE_FIELDS = ["engine", "motor", "powertrain", "electric_motor"]

# Fields that may contain drivetrain/layout info in Wikipedia infoboxes
LAYOUT_FIELDS = ["layout", "drive", "drivetrain"]

# Regex patterns for extracting engine types from freetext
ENGINE_TYPE_PATTERNS = [
    (r'\b([Vv])[\s-]?(\d{1,2})\b', lambda m: f"V{m.group(2)}"),
    (r'\b[Ii][\s-]?(\d)\b', lambda m: f"I{m.group(1)}"),
    (r'\b[Ss]traight[\s-]?(\d)\b', lambda m: f"I{m.group(1)}"),
    (r'\b[Ii]nline[\s-]?(\d)\b', lambda m: f"I{m.group(1)}"),
    (r'\b[Ff]lat[\s-]?(\d)\b', lambda m: f"Flat-{m.group(1)}"),
    (r'\b[Ww][\s-]?(\d{2})\b', lambda m: f"W{m.group(1)}"),
    (r'\b[Ww]ankel\b', lambda _: "Rotary"),
    (r'\b[Rr]otary\b', lambda _: "Rotary"),
    (r'\b[Ee]lectric\b', lambda _: "Electric"),
    (r'\b[Hh]ybrid\b', lambda _: "Hybrid"),
]


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
           ?mfgCountryLabel ?inception ?prodStart ?image ?article ?sitelinks
    WHERE {{
      # Match automobile models and generations
      VALUES ?carType {{ wd:Q3231690 wd:Q786820 }}
      ?car wdt:P31 ?carType .
      ?car wdt:P176 ?manufacturer .
      ?car wikibase:sitelinks ?sitelinks .
      FILTER(?sitelinks > 10)

      OPTIONAL {{ ?car wdt:P495 ?country . }}
      OPTIONAL {{ ?manufacturer wdt:P17 ?mfgCountry . }}
      OPTIONAL {{ ?car wdt:P571 ?inception . }}
      OPTIONAL {{ ?car wdt:P580 ?prodStart . }}
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

    Uses:
      P2386 = engine power (replaces wrong P2325)
      P2067 = mass (weight)
      P516  = powered by (engine entity)
      P31   = instance of (to get engine type like 'V8 engine')
      P1552 = has characteristic (for drivetrain: FWD/RWD/AWD)
      P2517 = category for the type of drive (layout)
    """
    print(f"Step 2: Fetching specs for {len(entity_ids)} cars...")
    all_specs: dict[str, dict] = {}

    batch_size = 100
    for i in range(0, len(entity_ids), batch_size):
        batch = entity_ids[i:i + batch_size]
        values = " ".join(f"wd:{eid}" for eid in batch)

        query = f"""
        SELECT ?car ?hpAmount ?hpUnit ?weightAmount
               ?engineLabel ?engineTypeLabel ?driveLabel
        WHERE {{
          VALUES ?car {{ {values} }}

          OPTIONAL {{
            ?car p:P2386 ?hpStmt .
            ?hpStmt psv:P2386 ?hpNode .
            ?hpNode wikibase:quantityAmount ?hpAmount .
            ?hpNode wikibase:quantityUnit ?hpUnit .
          }}
          OPTIONAL {{
            ?car p:P2067 ?weightStmt .
            ?weightStmt psv:P2067 ?weightNode .
            ?weightNode wikibase:quantityAmount ?weightAmount .
          }}
          OPTIONAL {{
            ?car wdt:P516 ?engine .
            OPTIONAL {{ ?engine wdt:P31 ?engineType . }}
          }}
          OPTIONAL {{ ?car wdt:P1552 ?drive . }}

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
            engine_label = get_val(row, "engineLabel")
            engine_type_label = get_val(row, "engineTypeLabel")
            drive_label = get_val(row, "driveLabel")

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

            # Clean engine label: skip QIDs, then apply mappings
            if engine_label and engine_label.startswith("Q") and \
                    engine_label[1:].isdigit():
                engine_label = ""
            if engine_type_label and engine_type_label.startswith("Q") and \
                    engine_type_label[1:].isdigit():
                engine_type_label = ""
            engine = clean_engine(engine_label, engine_type_label)

            # Clean drivetrain label
            if drive_label and drive_label.startswith("Q") and \
                    drive_label[1:].isdigit():
                drive_label = ""
            drivetrain = clean_drivetrain(drive_label)

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


# ---------------------------------------------------------------------------
# Wikipedia infobox fetching & parsing (primary specs source)
# ---------------------------------------------------------------------------


def fetch_wikipedia_pages(page_titles: list[str]) -> dict[str, str]:
    """
    Batch-fetch the lead section wikitext for multiple Wikipedia pages.
    Uses the MediaWiki API with up to 50 titles per request.
    Returns {page_title: wikitext} for pages that exist.
    """
    all_pages: dict[str, str] = {}
    batch_size = 50  # MediaWiki API limit for non-bot users

    for i in range(0, len(page_titles), batch_size):
        batch = page_titles[i:i + batch_size]
        titles_param = "|".join(batch)

        params = urllib.parse.urlencode({
            "action": "query",
            "titles": titles_param,
            "prop": "revisions",
            "rvprop": "content",
            "rvsection": "0",
            "rvslots": "main",
            "format": "json",
            "formatversion": "2",
        })
        url = f"{WIKIPEDIA_API}?{params}"
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        })

        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    pages = data.get("query", {}).get("pages", [])
                    for page in pages:
                        title = page.get("title", "")
                        revisions = page.get("revisions", [])
                        if revisions and not page.get("missing"):
                            content = (
                                revisions[0]
                                .get("slots", {})
                                .get("main", {})
                                .get("content", "")
                            )
                            if content:
                                all_pages[title] = content
                    break
            except (urllib.error.URLError, urllib.error.HTTPError) as e:
                print(
                    f"  Wikipedia batch {i // batch_size + 1} "
                    f"attempt {attempt + 1} failed: {e}",
                    file=sys.stderr,
                )
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                # On final failure, just skip this batch

        batch_num = i // batch_size + 1
        total_batches = (len(page_titles) + batch_size - 1) // batch_size
        print(
            f"  Wikipedia batch {batch_num}/{total_batches}: "
            f"got {len(all_pages) - i} pages"
        )

        # Rate limit between batches
        if i + batch_size < len(page_titles):
            time.sleep(1)

    return all_pages


def _strip_wiki_markup(text: str) -> str:
    """Remove common wiki markup, keeping just readable text."""
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # Remove <ref> tags and their contents
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^/]*/>', '', text)
    # Remove HTML tags but keep content
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'</?(?:small|sup|sub|span|div|nowiki)[^>]*>', '', text)
    # Resolve wikilinks: [[target|display]] → display, [[target]] → target
    text = re.sub(r'\[\[[^\]]*\|([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # Remove bold/italic markup
    text = re.sub(r"'{2,3}", '', text)
    # Remove {{nbsp}}, {{spaces}}, etc.
    text = re.sub(r'\{\{(?:nbsp|spaces?|sp)\}\}', ' ', text, flags=re.IGNORECASE)
    # Remove {{nowrap|text}} → text
    text = re.sub(r'\{\{nowrap\|([^}]+)\}\}', r'\1', text, flags=re.IGNORECASE)
    # Remove {{small|text}} → text
    text = re.sub(r'\{\{small\|([^}]+)\}\}', r'\1', text, flags=re.IGNORECASE)
    return text.strip()


def _parse_convert_template(text: str) -> list[tuple[float, str]]:
    """
    Parse {{convert|value|unit|...}} templates into [(value, unit), ...].
    Handles: {{convert|320|PS|kW hp}}, {{convert|1500|kg|lb}},
             {{convert|1500|–|1600|kg|lb}}
    """
    results = []
    pattern = r'\{\{convert\|([^}]+)\}\}'
    for match in re.finditer(pattern, text, re.IGNORECASE):
        parts = match.group(1).split("|")
        if len(parts) < 2:
            continue
        # Find numeric values and the unit
        values = []
        unit = ""
        for part in parts:
            part = part.strip()
            cleaned = part.replace(",", "").replace("−", "-")
            try:
                values.append(float(cleaned))
            except ValueError:
                # Skip range separators
                if part in ("–", "-", "to", "and", "−"):
                    continue
                # First non-numeric, non-separator part is likely the unit
                if not unit and part not in (
                    "abbr=on", "abbr=off", "disp=or", "disp=s",
                    "0", "1", "2", "3",
                ):
                    unit = part
        for val in values:
            if unit:
                results.append((val, unit))
    return results


def parse_infobox(wikitext: str) -> dict[str, str]:
    """
    Extract key-value pairs from the first automobile infobox in wikitext.
    Returns {field_name: raw_value} dict.
    """
    # Find infobox start — match common automobile infobox variants
    infobox_pattern = (
        r'\{\{\s*[Ii]nfobox\s+'
        r'(?:[Aa]utomobile|[Cc]ar|[Aa]utomobile\s+generation)'
    )
    match = re.search(infobox_pattern, wikitext)
    if not match:
        return {}

    # Find the matching closing braces by counting nesting
    start = match.start()
    depth = 0
    pos = start
    end = len(wikitext)
    while pos < end:
        if wikitext[pos:pos + 2] == '{{':
            depth += 1
            pos += 2
        elif wikitext[pos:pos + 2] == '}}':
            depth -= 1
            if depth == 0:
                pos += 2
                break
            pos += 2
        else:
            pos += 1

    infobox_text = wikitext[start:pos]

    # Parse field = value pairs.
    # Fields start with | at the beginning of a line (or after other fields)
    # and the value continues until the next | at line start or }}
    fields: dict[str, str] = {}

    # Split on top-level pipe characters (not inside nested templates
    # or wikilinks)
    # We'll track template {{...}} and wikilink [[...]] nesting depth
    field_parts = []
    current = ""
    tmpl_depth = 0
    link_depth = 0
    i = 0
    while i < len(infobox_text):
        two_chars = infobox_text[i:i + 2]
        if two_chars == '{{':
            tmpl_depth += 1
            current += '{{'
            i += 2
        elif two_chars == '}}':
            tmpl_depth -= 1
            current += '}}'
            i += 2
        elif two_chars == '[[':
            link_depth += 1
            current += '[['
            i += 2
        elif two_chars == ']]':
            link_depth -= 1
            current += ']]'
            i += 2
        elif infobox_text[i] == '|' and tmpl_depth <= 1 and link_depth == 0:
            # Top-level pipe — marks a new field
            field_parts.append(current)
            current = ""
            i += 1
        else:
            current += infobox_text[i]
            i += 1
    if current:
        field_parts.append(current)

    for part in field_parts:
        if '=' not in part:
            continue
        eq_pos = part.index('=')
        key = part[:eq_pos].strip().lower()
        # Remove leading pipe from key
        key = key.lstrip('|').lstrip('{').strip()
        value = part[eq_pos + 1:].strip()
        if key and value:
            fields[key] = value

    return fields


def extract_horsepower(infobox: dict[str, str]) -> int:
    """Extract horsepower from infobox fields."""
    for field in HP_FIELDS + ENGINE_FIELDS:
        raw = infobox.get(field, "")
        if not raw:
            continue

        # Try {{convert|NUMBER|PS/hp/kW|...}} templates first
        conversions = _parse_convert_template(raw)
        for val, unit in conversions:
            unit_lower = unit.lower()
            if unit_lower in ("ps", "metric horsepower"):
                return round(val * 0.98632)  # PS to hp
            if unit_lower in ("hp", "bhp"):
                return round(val)
            if unit_lower in ("kw",):
                return round(val * 1.34102)

        # Try plain text patterns
        text = _strip_wiki_markup(raw)
        # Match patterns like "320 hp", "320 bhp", "320 PS", "320 kW"
        hp_match = re.search(
            r'(\d[\d,]*(?:\.\d+)?)\s*(?:&nbsp;)?\s*(hp|bhp|PS|kW)\b',
            text, re.IGNORECASE,
        )
        if hp_match:
            val = float(hp_match.group(1).replace(",", ""))
            unit = hp_match.group(2).lower()
            if unit == "kw":
                return round(val * 1.34102)
            if unit == "ps":
                return round(val * 0.98632)
            return round(val)

    return 0


def extract_weight(infobox: dict[str, str]) -> int:
    """Extract curb weight in kg from infobox fields."""
    for field in WEIGHT_FIELDS:
        raw = infobox.get(field, "")
        if not raw:
            continue

        # Try {{convert|NUMBER|kg|...}} templates first
        conversions = _parse_convert_template(raw)
        for val, unit in conversions:
            unit_lower = unit.lower()
            if unit_lower == "kg":
                return round(val)
            if unit_lower == "lb":
                return round(val * 0.453592)

        # Try plain text patterns
        text = _strip_wiki_markup(raw)
        # Match "1,500 kg" or "1500 kg"
        kg_match = re.search(
            r'(\d[\d,]*(?:\.\d+)?)\s*(?:&nbsp;)?\s*kg\b', text,
            re.IGNORECASE,
        )
        if kg_match:
            return round(float(kg_match.group(1).replace(",", "")))

        # Match "3,300 lb" or "3300 lb"
        lb_match = re.search(
            r'(\d[\d,]*(?:\.\d+)?)\s*(?:&nbsp;)?\s*(?:lb|lbs|pounds?)\b',
            text, re.IGNORECASE,
        )
        if lb_match:
            return round(float(lb_match.group(1).replace(",", "")) * 0.453592)

    return 0


def extract_engine_type(infobox: dict[str, str]) -> str:
    """Extract engine type (V8, I4, etc.) from infobox fields."""
    for field in ENGINE_FIELDS:
        raw = infobox.get(field, "")
        if not raw:
            continue

        text = _strip_wiki_markup(raw)

        # Try specific engine type patterns
        for pattern, formatter in ENGINE_TYPE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                result = formatter(match)
                # Validate it's a real engine type, not a model number
                if result in (
                    "V4", "V5", "V6", "V8", "V10", "V12", "V16",
                    "I2", "I3", "I4", "I5", "I6", "I8",
                    "Flat-2", "Flat-4", "Flat-6",
                    "W12", "W16",
                    "Rotary", "Electric", "Hybrid",
                ):
                    return result

        # Try to detect from displacement + cylinder count:
        # e.g. "2.0 L 4-cylinder" or "5.0-litre V8"
        cyl_match = re.search(
            r'(\d)[- ]?(?:cyl(?:inder)?s?)\b', text, re.IGNORECASE,
        )
        if cyl_match:
            ncyl = int(cyl_match.group(1))
            if ncyl <= 6:
                return f"I{ncyl}"
            return f"V{ncyl}"

    return ""


def extract_drivetrain(infobox: dict[str, str]) -> str:
    """Extract drivetrain (FWD/RWD/AWD/4WD) from infobox fields."""
    for field in LAYOUT_FIELDS:
        raw = infobox.get(field, "")
        if not raw:
            continue

        text = _strip_wiki_markup(raw).lower()

        # Check for drivetrain keywords
        if "all-wheel" in text or "awd" in text:
            return "AWD"
        if "four-wheel" in text or "4wd" in text or "4×4" in text:
            return "4WD"
        if "front-wheel" in text or "fwd" in text or "ff layout" in text:
            return "FWD"
        if "rear-wheel" in text or "rwd" in text:
            return "RWD"

        # Check layout patterns like "FR" (front-engine, rear-drive),
        # "FF" (front-engine, front-drive), "MR" (mid-engine, rear-drive)
        if re.search(r'\bfr\b', text):
            return "RWD"
        if re.search(r'\bff\b', text):
            return "FWD"
        if re.search(r'\bmr\b', text):
            return "RWD"
        if re.search(r'\brr\b', text):
            return "RWD"
        if re.search(r'\b[Ff]4\b', text) or "f4" in text:
            return "AWD"

        # Check for "front.engine" + "rear.drive" patterns
        if "front" in text and "rear" in text and "drive" in text:
            return "RWD"
        if "front" in text and "front" in text.split("drive")[0]:
            return "FWD"

    return ""


def fetch_wikipedia_specs(
    entity_wiki_map: dict[str, str],
) -> dict[str, dict]:
    """
    Fetch car specs from Wikipedia infoboxes.

    Args:
        entity_wiki_map: {entity_id: wikipedia_page_title}

    Returns:
        {entity_id: {horsepower, weight_kg, engine, drivetrain}}
    """
    page_titles = list(entity_wiki_map.values())
    # Reverse mapping: title → entity_id
    title_to_entity: dict[str, str] = {}
    for eid, title in entity_wiki_map.items():
        title_to_entity[title] = eid

    print(f"Step 2: Fetching specs from Wikipedia for "
          f"{len(page_titles)} cars...")

    # Batch-fetch Wikipedia article wikitext
    pages = fetch_wikipedia_pages(page_titles)
    print(f"  Retrieved {len(pages)} Wikipedia articles")

    all_specs: dict[str, dict] = {}
    parsed = 0
    for title, wikitext in pages.items():
        entity_id = title_to_entity.get(title)
        if not entity_id:
            # Handle title normalization (Wikipedia may return
            # slightly different titles)
            for orig_title, eid in title_to_entity.items():
                if orig_title.replace("_", " ") == title.replace("_", " "):
                    entity_id = eid
                    break
        if not entity_id:
            continue

        infobox = parse_infobox(wikitext)
        if not infobox:
            continue

        parsed += 1
        hp = extract_horsepower(infobox)
        weight = extract_weight(infobox)
        engine = extract_engine_type(infobox)
        drivetrain = extract_drivetrain(infobox)

        all_specs[entity_id] = {
            "horsepower": hp,
            "weight_kg": weight,
            "engine": engine,
            "drivetrain": drivetrain,
        }

    print(f"  Parsed {parsed} infoboxes")
    hp_count = sum(1 for s in all_specs.values() if s["horsepower"])
    wt_count = sum(1 for s in all_specs.values() if s["weight_kg"])
    en_count = sum(1 for s in all_specs.values() if s["engine"])
    dt_count = sum(1 for s in all_specs.values() if s["drivetrain"])
    print(f"  HP: {hp_count}, Weight: {wt_count}, "
          f"Engine: {en_count}, Drivetrain: {dt_count}")

    return all_specs


def validate_car(car: dict) -> tuple[bool, list[str]]:
    """
    Validate that a car has all required fields for the guessing game.
    Returns (is_valid, list_of_reasons) — if invalid, reasons describe what's
    missing or wrong.

    Required fields:
      - make: non-empty string
      - model: non-empty string
      - year: integer between 1800 and 2030
      - country: non-empty string
      - horsepower: positive integer
      - weight_kg: positive integer
      - engine: non-empty string
      - drivetrain: non-empty string (FWD/RWD/AWD/4WD)
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


def load_seed_lookup() -> dict[tuple[str, str], dict]:
    """
    Load the seed car data as a lookup table keyed by (make_lower, model_lower).
    This is used as a fallback to fill in missing data from Wikidata results.
    Returns empty dict if seed data can't be loaded.
    """
    seed_script = Path(__file__).resolve().parent / "seed-cars.py"
    if not seed_script.exists():
        return {}

    # Import seed module dynamically
    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_cars", seed_script)
    if spec is None or spec.loader is None:
        return {}
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return {}

    seed_cars = mod.build_cars()
    lookup: dict[tuple[str, str], dict] = {}
    for car in seed_cars:
        key = (car["make"].lower(), car["model"].lower())
        lookup[key] = car
        # Also index by just model name for fuzzy matching
        model_key = ("", car["model"].lower())
        if model_key not in lookup:
            lookup[model_key] = car
    return lookup


def enrich_from_seed(car: dict, seed_lookup: dict[tuple[str, str], dict]) -> dict:
    """
    Try to fill in missing car fields from the seed data.
    Only fills fields that are missing/zero/empty.
    """
    if not seed_lookup:
        return car

    make_lower = car.get("make", "").lower()
    model_lower = car.get("model", "").lower()

    # Try exact match first, then model-only match
    seed = seed_lookup.get((make_lower, model_lower))
    if not seed:
        seed = seed_lookup.get(("", model_lower))
    if not seed:
        return car

    # Fill in missing/zero fields from seed
    if not car.get("year") or car["year"] == 0:
        car["year"] = seed.get("year", 0)
    if not car.get("horsepower") or car["horsepower"] == 0:
        car["horsepower"] = seed.get("horsepower", 0)
    if not car.get("weight_kg") or car["weight_kg"] == 0:
        car["weight_kg"] = seed.get("weight_kg", 0)
    if not car.get("engine"):
        car["engine"] = seed.get("engine", "")
    if not car.get("drivetrain"):
        car["drivetrain"] = seed.get("drivetrain", "")
    if not car.get("country"):
        car["country"] = seed.get("country", "")

    return car


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
    raw_cars: list[dict], specs: dict[str, dict],
    seed_lookup: dict[tuple[str, str], dict] | None = None,
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
            for key in ("countryLabel", "mfgCountryLabel",
                        "inception", "prodStart",
                        "image", "article"):
                if not get_val(existing, key) and get_val(row, key):
                    existing[key] = row[key]

    cars = []
    skipped: list[tuple[str, str, list[str]]] = []
    for entity, row in seen.items():
        raw_make = get_val(row, "manufacturerLabel")
        car_label = get_val(row, "carLabel")
        country = get_val(row, "countryLabel")
        mfg_country = get_val(row, "mfgCountryLabel")
        inception = get_val(row, "inception")
        prod_start = get_val(row, "prodStart")
        image_url = get_val(row, "image")
        wiki = get_val(row, "article")
        sitelinks = int(get_val(row, "sitelinks", "0"))

        # Skip unresolved labels (look like QIDs)
        if not raw_make or not car_label:
            continue
        if car_label.startswith("Q") and car_label[1:].isdigit():
            continue
        if raw_make.startswith("Q") and raw_make[1:].isdigit():
            continue

        # Clean manufacturer name to brand-level
        make = clean_make(raw_make)

        # Clean up model name — remove manufacturer/brand prefix if present
        model = car_label
        # Try cleaned brand name first (e.g. "Ford" from "Ford Motor Company")
        if model.lower().startswith(make.lower()):
            model = model[len(make):].strip()
        # Also try original manufacturer label
        elif model.lower().startswith(raw_make.lower()):
            model = model[len(raw_make):].strip()
        # If stripping left nothing, keep original label
        if not model:
            model = car_label

        # Skip entries that are brands/companies, not car models
        # (where model name equals the brand name after stripping)
        if model.lower() == make.lower():
            continue

        # Map country names; fall back to manufacturer's country
        country = COUNTRY_MAP.get(country, country)
        if not country and mfg_country:
            country = COUNTRY_MAP.get(mfg_country, mfg_country)

        # Parse year from inception date, fall back to production start
        year = 0
        for date_str in (inception, prod_start):
            if date_str and not year:
                try:
                    # Wikidata dates look like "1993-01-01T00:00:00Z"
                    parsed = int(date_str[:4])
                    if 1800 <= parsed <= 2030:
                        year = parsed
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

        # Try to enrich missing fields from seed data
        if seed_lookup:
            car = enrich_from_seed(car, seed_lookup)

        # Validate — only include cars with complete data
        valid, reasons = validate_car(car)
        if not valid:
            skipped.append((make, model, reasons))
            continue

        cars.append(car)

    if skipped:
        print(f"\n  Skipped {len(skipped)} cars with incomplete data:")
        for s_make, s_model, s_reasons in skipped[:20]:
            print(f"    - {s_make} {s_model}: {', '.join(s_reasons)}")
        if len(skipped) > 20:
            print(f"    ... and {len(skipped) - 20} more")

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

    # Extract entity IDs and build entity→Wikipedia title mapping
    entity_ids = []
    seen_ids = set()
    entity_wiki_map: dict[str, str] = {}
    for row in raw_cars:
        eid = get_val(row, "car").split("/")[-1]
        if eid not in seen_ids:
            entity_ids.append(eid)
            seen_ids.add(eid)
            wiki_url = get_val(row, "article")
            if wiki_url:
                # Extract page title from URL:
                # https://en.wikipedia.org/wiki/Toyota_Corolla → Toyota_Corolla
                page_title = wiki_url.split("/wiki/")[-1]
                page_title = urllib.parse.unquote(page_title)
                entity_wiki_map[eid] = page_title

    # Step 2: Fetch specs from Wikipedia infoboxes (primary source)
    specs: dict[str, dict] = {}
    if entity_wiki_map:
        wiki_specs = fetch_wikipedia_specs(entity_wiki_map)
        specs.update(wiki_specs)
    else:
        print("  No Wikipedia URLs available, skipping Wikipedia specs")

    # Step 2b: Fetch remaining specs from Wikidata SPARQL (fallback)
    missing_ids = [eid for eid in entity_ids if eid not in specs
                   or not all(specs[eid].get(k)
                              for k in ("horsepower", "weight_kg",
                                        "engine", "drivetrain"))]
    if missing_ids:
        print(f"\nStep 2b: Fetching Wikidata specs for "
              f"{len(missing_ids)} cars missing data...")
        wd_specs = fetch_car_specs(missing_ids)
        # Merge: only fill in what's still missing
        for eid, wd_data in wd_specs.items():
            if eid not in specs:
                specs[eid] = wd_data
            else:
                existing = specs[eid]
                for key in ("horsepower", "weight_kg", "engine", "drivetrain"):
                    if not existing.get(key) and wd_data.get(key):
                        existing[key] = wd_data[key]

    # Load seed data as fallback for enrichment
    print("Loading seed data for fallback enrichment...")
    seed_lookup = load_seed_lookup()
    if seed_lookup:
        print(f"  Loaded {len(seed_lookup)} seed entries for enrichment")
    else:
        print("  No seed data available (enrichment skipped)")

    # Step 3: Process and combine
    print("Step 3: Processing results...")
    cars = process_results(raw_cars, specs, seed_lookup)

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
        "  2. Download images using image_source URLs, convert to .webp\n"
        "  3. Write fun facts for each car\n"
        "  4. Remove extra metadata fields to match Car interface\n"
    )


if __name__ == "__main__":
    main()

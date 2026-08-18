"""Garmin strength exercise catalog.

Backed by a vendored JSON file generated from the FIT SDK profile — see
`scripts/generate_exercises.py`. Loaded lazily so plans without strength
workouts never pay for it.
"""

import difflib
import json
from functools import lru_cache
from pathlib import Path

_CATALOG_PATH = Path(__file__).parent / "data" / "exercises.json"


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, list[str]]:
    """Return the full {CATEGORY: [EXERCISE_NAME, ...]} catalog."""
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def categories() -> list[str]:
    """Return all category names, sorted."""
    return sorted(load_catalog())


def exercises_in(category: str) -> list[str]:
    """Return exercise names in a category, or [] if unknown."""
    return load_catalog().get(category.upper(), [])


def validate(category: str, name: str) -> str | None:
    """Validate a category/exercise pair.

    Returns None when valid, otherwise a human-readable error string with a
    suggestion where one is available.

    Checks three things — the third is the one Garmin accepts silently and
    then ignores on the watch:
      1. the category exists
      2. the exercise exists somewhere in the catalog
      3. the exercise belongs to *this* category
    """
    catalog = load_catalog()
    category_key = (category or "").upper()
    name_key = (name or "").upper()

    if category_key not in catalog:
        suggestion = _closest(category_key, catalog.keys())
        msg = f"unknown category {category_key!r}"
        return f"{msg}{suggestion}"

    if name_key in catalog[category_key]:
        return None

    # Exercise name is real, but filed under a different category.
    owners = [c for c, names in catalog.items() if name_key in names]
    if owners:
        return (
            f"exercise {name_key!r} is not in category {category_key!r} "
            f"— it belongs to {', '.join(sorted(owners))}"
        )

    suggestion = _closest(name_key, catalog[category_key])
    return f"unknown exercise {category_key}/{name_key}{suggestion}"


def _closest(value: str, options) -> str:
    """Return a ' — did you mean X?' fragment, or '' if nothing is close."""
    matches = difflib.get_close_matches(value, list(options), n=1, cutoff=0.6)
    return f" — did you mean {matches[0]!r}?" if matches else ""


def search(term: str) -> list[tuple[str, str]]:
    """Return (category, exercise) pairs matching a substring, sorted.

    Matches against both the category and the exercise name, so 'squat'
    finds the SQUAT category's contents as well as squat-shaped movements
    filed elsewhere (e.g. LUNGE/OVERHEAD_LUNGE variants).
    """
    needle = (term or "").upper().replace(" ", "_")
    results = []
    for category, names in load_catalog().items():
        for name in names:
            if needle in name or needle in category:
                results.append((category, name))
    return sorted(results)


def humanize(name: str) -> str:
    """BARBELL_BENCH_PRESS -> Barbell Bench Press."""
    return " ".join(part.capitalize() for part in (name or "").split("_"))

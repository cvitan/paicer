#!/usr/bin/env python3
"""Regenerate the vendored Garmin exercise catalog.

Garmin Connect does not expose its exercise catalog to authenticated API
clients — every candidate endpoint returns 404 or 410. The canonical source
is the FIT SDK profile, which defines an `exercise_category` enum plus one
`<category>_exercise_name` enum per category. Connect's uppercase
`category` / `exerciseName` strings are those enum values uppercased.

Run this when Garmin ships new exercises:

    uv run --with garmin-fit-sdk python scripts/generate_exercises.py

`garmin-fit-sdk` is a dev-only dependency; paicer does not import it at
runtime.
"""

import json
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "src/paicer/data/exercises.json"


def build_catalog() -> dict[str, list[str]]:
    from garmin_fit_sdk import Profile

    types = Profile["types"]
    categories = types["exercise_category"]

    catalog: dict[str, list[str]] = {}
    for category_name in categories.values():
        enum_key = f"{category_name}_exercise_name"
        if enum_key not in types:
            # `cardio_sensors` and `unknown` carry no exercise names.
            continue
        names = sorted({v.upper() for v in types[enum_key].values()})
        catalog[category_name.upper()] = names

    return dict(sorted(catalog.items()))


def main() -> None:
    catalog = build_catalog()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(catalog, indent=1, sort_keys=True) + "\n")

    total = sum(len(v) for v in catalog.values())
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"Wrote {OUTPUT.relative_to(Path.cwd())}")
    print(f"  {len(catalog)} categories, {total} exercises, {size_kb:.1f} KB")


if __name__ == "__main__":
    main()

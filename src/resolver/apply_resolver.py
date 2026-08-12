import json
import os
import sys

# Ensure local directory is in system path for sub-imports
sys.path.append(os.path.dirname(__file__))

from entity_resolver import resolve_entity


INPUT = "data/startups.json"
OUTPUT = "data/startups_resolved.json"
LOG = "data/entity_mapping_log.json"


def main():

    with open(INPUT, "r", encoding="utf-8") as f:
        startups = json.load(f)

    mapping_log = []

    for startup in startups:

        content = startup.get("content", {})
        raw_name = content.get("entityName")

        if not raw_name:
            continue

        canonical = resolve_entity(raw_name)

        content["entityName"] = canonical

        mapping_log.append({
            "rawName": raw_name,
            "canonicalName": canonical,
            "sourceUrl": startup.get("source", {}).get("url")
        })

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            startups,
            f,
            indent=2,
            ensure_ascii=False
        )

    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(
            mapping_log,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Resolved {len(startups)} startup records.")
    print(f"Saved: {OUTPUT}")
    print(f"Saved: {LOG}")


if __name__ == "__main__":
    main()
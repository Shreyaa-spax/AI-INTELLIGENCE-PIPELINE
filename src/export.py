import json
import os
import csv


DATASETS = {
    "Startups": "data/startups_resolved.json",
    "Products": "data/products.json",
    "Research Papers": "data/research_papers.json",
    "Jobs": "data/jobs.json",
    "News": "data/news.json",
    "Entity Mapping Log": "data/entity_mapping_log.json"
}


def flatten(record):

    result = {}

    def walk(value, prefix=""):

        if isinstance(value, dict):

            for key, val in value.items():

                new_prefix = (
                    f"{prefix}.{key}"
                    if prefix
                    else key
                )

                walk(val, new_prefix)

        elif isinstance(value, list):

            result[prefix] = ", ".join(
                str(x) for x in value
            )

        else:

            result[prefix] = value

    walk(record)

    return result


def export_dataset(name, path):

    if not os.path.exists(path):

        print(
            f"Skipping {name}: file not found"
        )

        return

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        records = json.load(f)

    if not records:

        print(
            f"Skipping {name}: empty"
        )

        return

    rows = [
        flatten(record)
        for record in records
    ]

    fields = sorted({
        key
        for row in rows
        for key in row
    })

    output = (
        "data/export_"
        + name.lower().replace(" ", "_")
        + ".csv"
    )

    with open(
        output,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"{name}: {len(rows)} rows → {output}"
    )


def main():

    for name, path in DATASETS.items():

        export_dataset(
            name,
            path
        )


if __name__ == "__main__":

    main()
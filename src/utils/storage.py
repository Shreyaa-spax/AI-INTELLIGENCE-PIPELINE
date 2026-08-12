import json
import os


def save_json(data, filepath):

    directory = os.path.dirname(
        filepath
    )

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def load_json(filepath):

    if not os.path.exists(filepath):

        return []

    with open(
        filepath,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)
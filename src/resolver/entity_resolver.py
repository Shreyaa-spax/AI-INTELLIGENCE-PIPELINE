import re
import json
import os


# Small seed database required by the assignment
CANONICAL_ENTITIES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "google deepmind": "Google DeepMind",
    "microsoft": "Microsoft",
    "meta": "Meta",
    "meta ai": "Meta AI",
    "nvidia": "NVIDIA",
    "hugging face": "Hugging Face",
    "huggingface": "Hugging Face",
    "mistral": "Mistral AI",
    "mistral ai": "Mistral AI",
    "cohere": "Cohere",
    "perplexity": "Perplexity",
    "xai": "xAI",
    "x ai": "xAI",
    "deepseek": "DeepSeek",
    "stability ai": "Stability AI",
    "stability": "Stability AI",
    "runway": "Runway",
    "character ai": "Character.AI",
    "character.ai": "Character.AI",
    "scale ai": "Scale AI",
    "databricks": "Databricks",
    "cursor": "Cursor",
    "replicate": "Replicate",
    "weights & biases": "Weights & Biases",
    "wandb": "Weights & Biases",
}


def normalize_name(name):

    if not name:
        return ""

    name = name.lower().strip()

    # Remove company suffixes
    name = re.sub(
        r"\b(inc|inc\.|llc|ltd|limited|corp|corporation)\b",
        "",
        name
    )

    # Remove punctuation
    name = re.sub(
        r"[^a-z0-9\s]",
        "",
        name
    )

    # Normalize spaces
    name = re.sub(
        r"\s+",
        " ",
        name
    ).strip()

    return name


def resolve_entity(raw_name):

    normalized = normalize_name(
        raw_name
    )

    if not normalized:
        return None

    # Exact normalized match
    if normalized in CANONICAL_ENTITIES:
        return CANONICAL_ENTITIES[
            normalized
        ]

    # Handle "open ai" → OpenAI
    compact = normalized.replace(
        " ",
        ""
    )

    for key, canonical in CANONICAL_ENTITIES.items():

        if compact == key.replace(" ", ""):
            return canonical

    # No known mapping
    return raw_name.strip()


def create_mapping_log(raw_names):

    mappings = []

    for raw_name in raw_names:

        canonical = resolve_entity(
            raw_name
        )

        mappings.append({
            "rawName": raw_name,
            "canonicalName": canonical
        })

    return mappings


def save_mapping_log(mappings):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        "data/entity_mapping.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            mappings,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved {len(mappings)} mappings."
    )


if __name__ == "__main__":

    test_names = [
        "OpenAI",
        "Open AI",
        "OpenAI Inc.",
        "Anthropic",
        "HuggingFace",
        "Mistral AI",
        "DeepSeek",
        "NVIDIA",
        "Unknown Startup"
    ]

    mappings = create_mapping_log(
        test_names
    )

    for mapping in mappings:

        print(
            f"{mapping['rawName']} "
            f"→ "
            f"{mapping['canonicalName']}"
        )

    save_mapping_log(
        mappings
    )
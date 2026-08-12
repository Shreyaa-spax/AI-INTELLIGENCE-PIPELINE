import re
import json
import os

# Seed database for deterministic entity resolution.
# Includes >50 common AI ecosystem organizations/products.
CANONICAL_ENTITIES = {
    "openai": "OpenAI", "anthropic": "Anthropic", "google": "Google", "google deepmind": "Google DeepMind",
    "microsoft": "Microsoft", "meta": "Meta", "meta ai": "Meta AI", "nvidia": "NVIDIA",
    "hugging face": "Hugging Face", "huggingface": "Hugging Face", "mistral": "Mistral AI", "mistral ai": "Mistral AI",
    "cohere": "Cohere", "perplexity": "Perplexity", "xai": "xAI", "x ai": "xAI", "deepseek": "DeepSeek",
    "stability ai": "Stability AI", "stability": "Stability AI", "runway": "Runway", "character ai": "Character.AI",
    "character.ai": "Character.AI", "scale ai": "Scale AI", "databricks": "Databricks", "cursor": "Cursor",
    "replicate": "Replicate", "weights & biases": "Weights & Biases", "wandb": "Weights & Biases",
    "amazon": "Amazon", "aws": "Amazon Web Services", "ibm": "IBM", "oracle": "Oracle", "salesforce": "Salesforce",
    "adobe": "Adobe", "apple": "Apple", "tesla": "Tesla", "samsung": "Samsung", "intel": "Intel",
    "amd": "AMD", "qualcomm": "Qualcomm", "baidu": "Baidu", "alibaba": "Alibaba", "tencent": "Tencent",
    "bytedance": "ByteDance", "moonshot ai": "Moonshot AI", "01 ai": "01.AI", "zhipu ai": "Zhipu AI",
    "minimax": "MiniMax", "kimi": "Kimi", "ai21 labs": "AI21 Labs", "aleph alpha": "Aleph Alpha",
    "inflection ai": "Inflection AI", "adept": "Adept", "huggingface": "Hugging Face", "together ai": "Together AI",
    "groq": "Groq", "fireworks ai": "Fireworks AI", "together": "Together AI", "modal": "Modal",
    "pinecone": "Pinecone", "weaviate": "Weaviate", "milvus": "Milvus", "qdrant": "Qdrant",
    "langchain": "LangChain", "llamaindex": "LlamaIndex", "llama index": "LlamaIndex", "weights and biases": "Weights & Biases",
    "jasper": "Jasper", "grammarly": "Grammarly", "glean": "Glean", "harvey": "Harvey", "elevenlabs": "ElevenLabs",
    "eleven labs": "ElevenLabs", "suno": "Suno", "descript": "Descript", "quora": "Quora", "character": "Character.AI",
}

def normalize_name(name):
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r"\b(inc|inc\.|llc|ltd|limited|corp|corporation|co|company)\b", "", name)
    name = re.sub(r"[^a-z0-9\s]", "", name)
    return re.sub(r"\s+", " ", name).strip()

def resolve_entity(raw_name):
    normalized = normalize_name(raw_name)
    if not normalized:
        return None
    if normalized in CANONICAL_ENTITIES:
        return CANONICAL_ENTITIES[normalized]
    compact = normalized.replace(" ", "")
    for key, canonical in CANONICAL_ENTITIES.items():
        if compact == key.replace(" ", "").replace("&", "and"):
            return canonical
    return raw_name.strip()

def create_mapping_log(raw_names):
    return [{"rawName": raw_name, "canonicalName": resolve_entity(raw_name)} for raw_name in raw_names]

def save_mapping_log(mappings):
    os.makedirs("data", exist_ok=True)
    with open("data/entity_mapping.json", "w", encoding="utf-8") as file:
        json.dump(mappings, file, indent=2, ensure_ascii=False)
    print(f"Saved {len(mappings)} mappings.")

if __name__ == "__main__":
    test_names = ["OpenAI", "Open AI", "OpenAI Inc.", "Anthropic", "HuggingFace", "Mistral AI", "DeepSeek", "NVIDIA", "Unknown Startup"]
    mappings = create_mapping_log(test_names)
    for mapping in mappings:
        print(f"{mapping['rawName']} → {mapping['canonicalName']}")
    save_mapping_log(mappings)

import os
from dotenv import load_dotenv


load_dotenv()


def get_api_keys():

    gemini_key = os.getenv(
        "GEMINI_API_KEY"
    )

    groq_key = os.getenv(
        "GROQ_API_KEY"
    )

    return gemini_key, groq_key


if __name__ == "__main__":

    gemini_key, groq_key = get_api_keys()

    print(
        "Gemini key found:",
        bool(gemini_key)
    )

    print(
        "Groq key found:",
        bool(groq_key)
    )
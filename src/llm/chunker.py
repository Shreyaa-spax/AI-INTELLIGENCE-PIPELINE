def chunk_text(
    text,
    max_chars=12000
):
    """
    Split large text into smaller chunks.
    """

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = start + max_chars

        chunk = text[start:end]

        chunks.append(chunk)

        start = end

    return chunks
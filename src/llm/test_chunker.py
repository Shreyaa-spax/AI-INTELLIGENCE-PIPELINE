from chunker import chunk_text


text = "AI research is important. " * 2000

chunks = chunk_text(
    text,
    max_chars=12000
)

print(
    "Original characters:",
    len(text)
)

print(
    "Number of chunks:",
    len(chunks)
)

for index, chunk in enumerate(
    chunks,
    start=1
):

    print(
        f"Chunk {index}: "
        f"{len(chunk)} characters"
    )
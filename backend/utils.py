def chunk_text(text: str, max_len: int = 1000):
    for i in range(0, len(text), max_len):
        yield text[i:i+max_len]

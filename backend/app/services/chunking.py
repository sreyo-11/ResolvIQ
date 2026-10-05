def chunk_text(text: str, max_words: int = 100, overlap: int = 20) -> list[str]:
    """Split text into overlapping word windows."""
    if overlap >= max_words:
        raise ValueError("overlap must be smaller than max_words")
    words = text.split()
    if not words:
        return []
    chunks, step = [], max_words - overlap
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + max_words]))
        if start + max_words >= len(words):
            break
    return chunks
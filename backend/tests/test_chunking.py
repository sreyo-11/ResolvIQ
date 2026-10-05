import pytest

from app.services.chunking import chunk_text


def test_short_text_single_chunk():
    assert chunk_text("one two three") == ["one two three"]


def test_overlap_between_chunks():
    text = " ".join(str(i) for i in range(250))
    chunks = chunk_text(text, max_words=100, overlap=20)
    assert len(chunks) == 3
    assert chunks[0].split()[-20:] == chunks[1].split()[:20]


def test_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("a b c", max_words=10, overlap=10)
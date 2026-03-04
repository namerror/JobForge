from types import SimpleNamespace

import logging
import pytest

from app.services import embedding_client


class FakeTokenizer:
    def encode(self, text: str):
        return list(range(len(text)))

    def decode(self, tokens):
        return "x" * len(tokens)


def test_truncate_texts_logs_truncation_with_context(monkeypatch, caplog):
    monkeypatch.setattr(embedding_client, "get_tokenizer", lambda model: FakeTokenizer())

    with caplog.at_level(logging.INFO, logger="embedding_client"):
        result = embedding_client.truncate_texts(
            ["abcdefghij"],
            max_tokens=5,
            model="fake-model",
            text_kind="role",
        )

    assert result == ["xxxxx"]
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.msg == "text_truncated"
    assert record.event == "text_truncated"
    assert record.text_kind == "role"
    assert record.original_length == 10
    assert record.truncated_length == 5


def test_embed_role_passes_dimensions(monkeypatch):
    captured = {}

    class DummyEmbeddings:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])])

    class DummyOpenAI:
        def __init__(self):
            self.embeddings = DummyEmbeddings()

    monkeypatch.setattr(embedding_client, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(
        embedding_client,
        "truncate_texts",
        lambda texts, max_tokens, model, text_kind=None: texts,
    )
    monkeypatch.setattr(
        embedding_client,
        "settings",
        SimpleNamespace(
            EMBEDDING_MODEL=embedding_client.settings.EMBEDDING_MODEL,
            EMBEDDING_DIMENSIONS=64,
        ),
    )

    embedding_client.embed_role("role text")

    assert captured["kwargs"]["dimensions"] == 64
    assert captured["kwargs"]["input"] == "role text"


def test_embed_skills_empty_list_raises():
    with pytest.raises(ValueError, match="empty list"):
        embedding_client.embed_skills([])

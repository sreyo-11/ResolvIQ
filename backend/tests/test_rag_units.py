from unittest.mock import Mock
from uuid import UUID

from app.services import llm, rag
from app.services.extraction import regex_extract
from app.services.rag import ungrounded_numbers


def test_ungrounded_numbers_flags_invented_values():
    ctx = "Refunds return in 5 to 10 business days [1]"
    assert ungrounded_numbers("Your refund arrives in 5 to 10 days [1]", ctx) == []
    assert ungrounded_numbers("We refund within 3 days [1]", ctx) == ["3"]


def test_regex_extraction():
    r = regex_extract("Order #482913 on v4.2.0 gets 502 errors on Windows 11, charged $49")
    assert r["order_id"] == "482913" and r["app_version"] == "4.2.0"
    assert r["error_codes"] == ["502"] and r["amount"] == "$49" and r["device_os"] == "Windows 11"


def test_draft_reply_accepts_low_similarity_hit_and_keeps_citation(monkeypatch):
    ticket_id = UUID("96286a83-19bb-4d67-8070-25c266fcc739")
    article_id = UUID("71a6a134-65fb-496a-a3aa-071914792fcb")
    hit = {
        "article_id": article_id,
        "article_title": "Updating payment methods and downloading invoices",
        "content": "Invoices are available under Billing, Invoices.",
        "similarity": 0.315205523824857,
    }
    monkeypatch.setattr(rag.ticket_repo, "get", lambda conn, _: {
        "subject": "urgent!!",
        "body": "The invoice for Team shows $49 but I expected a lower amount.",
    })
    monkeypatch.setattr(rag.ticket_repo, "get_embedding", lambda conn, _: object())
    monkeypatch.setattr(rag.kb_repo, "search", lambda conn, embedding, k, minimum: [hit])

    def complete(system, user, **kwargs):
        assert "draft a brief follow-up citing that step" in system
        return llm.LLMResult(
            "You can view the invoice under Settings > Billing > Invoices [1]. "
            "Could you share the relevant line items with personal and payment details redacted "
            "so we can understand the difference?",
            "test-model",
        )

    monkeypatch.setattr(rag.llm, "complete", complete)
    monkeypatch.setattr(
        rag.reply_repo,
        "insert",
        lambda conn, **kwargs: {"draft_text": kwargs["draft_text"], "sources": kwargs["sources"]},
    )

    result = rag.draft_reply(Mock(), ticket_id)

    assert result.drafted is True
    assert "[1]" in result.reply["draft_text"]
    assert result.reply["sources"] == [{
        "n": 1,
        "article_id": str(article_id),
        "title": hit["article_title"],
        "similarity": 0.315,
    }]
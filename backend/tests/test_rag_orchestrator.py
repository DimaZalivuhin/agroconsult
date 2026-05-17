"""RAG orchestrator integration test with mocked GigaChat and Qdrant."""
import pytest


@pytest.mark.asyncio
async def test_answer_question_happy_path(fake_gigachat, fake_qdrant, fake_cache):
    from app.rag.orchestrator import answer_question

    result = await answer_question(
        "Что такое грант Агростартап и сколько денег можно получить?",
        profile={"region_name": "Воронежская область", "farm_type": "kfh"},
    )

    assert "Агростартап" in result.answer
    assert len(result.sources) >= 1
    assert result.sources[0]["title"].startswith("Приказ")
    assert "score" in result.sources[0]
    assert result.retrieval_meta["n_candidates"] == 1
    assert result.retrieval_meta["total_ms"] > 0

    fake_gigachat.embed.assert_called_once()
    fake_qdrant.search.assert_called_once()
    fake_gigachat.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_answer_question_returns_fallback_when_no_hits(
    fake_gigachat, fake_qdrant, fake_cache
):
    from app.rag.orchestrator import answer_question

    fake_qdrant.search.return_value = []

    result = await answer_question("Какой-то совершенно посторонний вопрос")
    assert "не удалось найти" in result.answer.lower()
    assert result.sources == []
    fake_gigachat.chat_completion.assert_not_called()


@pytest.mark.asyncio
async def test_cache_hit_skips_generation(fake_gigachat, fake_qdrant, fake_cache):
    from app.rag.orchestrator import answer_question

    fake_cache.get.return_value = {
        "answer": "Кэшированный ответ",
        "sources": [],
        "token_usage": {},
        "retrieval_meta": {"cached": True},
    }

    result = await answer_question("Повторный вопрос")
    assert result.answer == "Кэшированный ответ"
    fake_gigachat.embed.assert_not_called()
    fake_qdrant.search.assert_not_called()
    fake_gigachat.chat_completion.assert_not_called()

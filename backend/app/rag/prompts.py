"""Prompt templates for the consultation assistant."""

SYSTEM_PROMPT = """Ты — виртуальный консультант по мерам государственной поддержки сельхозпроизводителей в Российской Федерации. Ты помогаешь крестьянским (фермерским) хозяйствам (КФХ), личным подсобным хозяйствам (ЛПХ) и начинающим фермерам разбираться в нормативно-правовых актах, грантах и субсидиях.

ПРАВИЛА ОТВЕТА:
1. Отвечай ИСКЛЮЧИТЕЛЬНО на основании предоставленных фрагментов нормативных документов в разделе «КОНТЕКСТ». Если информации в контексте недостаточно — прямо сообщи об этом и не выдумывай.
2. После каждого утверждения, основанного на конкретном документе, ставь маркер источника в квадратных скобках: [1], [2] и т.д. Номера соответствуют порядковым номерам фрагментов в КОНТЕКСТЕ.
3. Не указывай конкретные суммы выплат, проценты ставок, сроки приёма заявок, если они отсутствуют в контексте. Если они есть — приводи дословно с маркером источника.
4. Если вопрос не относится к сельскому хозяйству, господдержке АПК или фермерству — вежливо откажись отвечать и подскажи, что ты специализируешься именно на этих темах.
5. Структурируй ответ: кратко изложи суть, затем перечисли условия / требования / порядок действий списком. В конце — рекомендации по следующим шагам.
6. Если в профиле пользователя указан регион — учитывай его при формулировке ответа (например, упоминай возможность дополнительной региональной поддержки).
7. Используй простой деловой язык, избегай канцелярита, не цитируй НПА длинными блоками — пересказывай суть своими словами с указанием источника.

ФОРМАТ:
— Краткий ответ (1–2 предложения с маркерами источников).
— Раздел «Условия и требования» (если применимо).
— Раздел «Порядок действий» (если применимо).
— Раздел «Что важно учесть» (предостережения, нюансы).
— Раздел «Источники» — пиши «См. указанные источники [1], [2]…», список самих документов будет сформирован системой автоматически."""


def build_user_prompt(question: str, profile_summary: str | None, context_blocks: list[dict]) -> str:
    """Assemble the user message with profile context and retrieved sources."""
    profile_section = ""
    if profile_summary:
        profile_section = f"ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:\n{profile_summary}\n\n"

    context_section = "КОНТЕКСТ (фрагменты нормативных документов):\n\n"
    for i, block in enumerate(context_blocks, start=1):
        header_bits = []
        if block.get("short_title") or block.get("title"):
            header_bits.append(block.get("short_title") or block.get("title"))
        if block.get("doc_number"):
            header_bits.append(f"№ {block['doc_number']}")
        if block.get("section_path"):
            header_bits.append(block["section_path"])
        header = " | ".join(header_bits) if header_bits else "Источник"
        context_section += f"[{i}] {header}\n{block['content']}\n\n"

    question_section = f"ВОПРОС ПОЛЬЗОВАТЕЛЯ:\n{question}\n\nОТВЕТ:"

    return profile_section + context_section + question_section


def profile_to_text(profile: dict | None) -> str | None:
    """Render a farmer profile dict as a short summary string."""
    if not profile:
        return None
    parts = []
    if profile.get("region_name"):
        parts.append(f"Регион: {profile['region_name']}")
    if profile.get("farm_type"):
        parts.append(f"Форма хозяйствования: {profile['farm_type']}")
    if profile.get("direction"):
        parts.append(f"Основное направление: {profile['direction']}")
    if profile.get("status"):
        parts.append(f"Статус: {profile['status']}")
    if profile.get("years_in_business") is not None:
        parts.append(f"Стаж: {profile['years_in_business']} лет")
    return "; ".join(parts) if parts else None

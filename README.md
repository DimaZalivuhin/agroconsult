# AgroConsult

Веб-сервис для оказания консультационных услуг сельхозпроизводителям по мерам государственной поддержки. RAG-система на базе GigaChat и Qdrant.

ВКР, РГАУ-МСХА им. К.А. Тимирязева, 2026.

## Стек

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2, Alembic
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **БД**: PostgreSQL (Supabase)
- **Векторное хранилище**: Qdrant Cloud
- **Кэш**: Upstash Redis
- **LLM + Embeddings**: Sber GigaChat
- **Деплой**: Railway (backend), Vercel (frontend)

## Структура

```
backend/
  app/
    api/v1/         — REST-эндпоинты
    core/           — конфиг, безопасность, логирование
    db/             — подключение к БД, базовый класс
    models/         — SQLAlchemy модели
    schemas/        — Pydantic схемы
    services/       — бизнес-логика
    rag/            — RAG-пайплайн
    utils/          — утилиты
  migrations/       — Alembic
  scripts/          — индексация корпуса

frontend/
  app/              — страницы (App Router)
  components/       — React-компоненты
  lib/              — API-клиент, утилиты

data/
  corpus_raw/       — оригиналы НПА
  corpus_processed/ — обработанные чанки JSON

scripts/            — корневые скрипты
docs/               — материалы ВКР, документация
```

## Деплой

См. `docs/DEPLOYMENT.md`.

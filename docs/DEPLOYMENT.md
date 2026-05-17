# Деплой AgroConsult с нуля

Документ описывает полную процедуру разворачивания сервиса для пользователя
без опыта DevOps. Среднее время прохождения — 60–90 минут.

## 0. Что в итоге получится

- **Frontend**: `https://agroconsult-<твой-аккаунт>.vercel.app` — публичная ссылка для преподавателей
- **Backend API**: `https://agroconsult-<твой-аккаунт>.up.railway.app` — REST API + Swagger на `/docs`
- **БД**: Supabase PostgreSQL (бесплатный тариф)
- **Векторы**: Qdrant Cloud (бесплатный тариф)
- **Кэш**: Upstash Redis (бесплатный тариф)
- **LLM**: GigaChat API Freemium

Все звенья укладываются в **бесплатные тарифы**. Расходов 0 ₽/мес для масштаба ВКР.

---

## 1. Внешние сервисы

### 1.1 GitHub (если ещё нет аккаунта)

1. github.com → Sign Up
2. Создай **публичный** репозиторий `agroconsult` (без README — мы зальём свой)

### 1.2 Supabase (PostgreSQL)

1. supabase.com → Start your project → войти через GitHub
2. New project:
   - Name: `agroconsult`
   - Database password: **сгенерируй и сохрани** (длинный, без `@` и пробелов)
   - Region: `Frankfurt (EU Central)` — ближе всего к Railway
3. После создания (≈2 мин): **Project Settings → Database → Connection string → URI**
4. Выбери режим **Transaction pooler** (порт 6543) — он работает с asyncpg
5. Скопируй строку; замени `[YOUR-PASSWORD]` на свой пароль из шага 2
6. У тебя получится две строки:
   - **DATABASE_URL** (для приложения): `postgresql+asyncpg://postgres.xxxxx:PWD@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`
   - **DATABASE_URL_SYNC** (для миграций): `postgresql+psycopg2://postgres.xxxxx:PWD@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`

   Отличаются только префиксом `+asyncpg` vs `+psycopg2`.

### 1.3 Qdrant Cloud

1. cloud.qdrant.io → Sign up (email)
2. Create Cluster:
   - Provider: AWS, Region: `Frankfurt`
   - Plan: **Free 1GB**
3. После создания: **Cluster URL** и **API Key** (Data Access → New API key)
4. Сохрани:
   - **QDRANT_URL**: `https://xxxxx.eu-central-1-0.aws.cloud.qdrant.io:6333`
   - **QDRANT_API_KEY**: длинная строка

### 1.4 Upstash Redis

1. upstash.com → Sign up через GitHub
2. Create Database:
   - Type: **Global** (или Regional → eu-west-1)
   - TLS: enabled
   - Eviction: enabled
3. После создания на странице базы найди **REST API** секцию:
   - **UPSTASH_REDIS_URL**: `https://xxxxx.upstash.io`
   - **UPSTASH_REDIS_TOKEN**: длинная строка

### 1.5 GigaChat API

1. developers.sber.ru → Войти через Сбер ID
2. Личный кабинет → Получить API GigaChat → Создать проект → Тариф **Freemium**
3. Скачать сертификат `russian_trusted_root_ca.crt` (если потребуется — Railway обычно его уже имеет)
4. На странице проекта взять **Authorization key** — это длинная base64-строка
5. Сохрани:
   - **GIGACHAT_AUTH_KEY**: эта строка (формат `base64(client_id:client_secret)`)

---

## 2. Подготовка кода в репозитории

Я (Claude) пришлю тебе ZIP-архив `agroconsult.zip` со всем кодом.

1. Распакуй на ноут в любую папку
2. Открой Терминал (macOS) / PowerShell (Windows) в этой папке
3. Команды (одна за одной):

```bash
git init
git branch -M main
git add .
git commit -m "Initial commit: AgroConsult MVP"
git remote add origin https://github.com/<твой-логин>/agroconsult.git
git push -u origin main
```

После этого код будет в твоём GitHub-репозитории.

---

## 3. Деплой бэкенда на Railway

1. railway.app → Login with GitHub
2. New Project → Deploy from GitHub repo → выбери `agroconsult`
3. В разделе настройки выбери **Root directory: `backend`** (важно!)
4. Variables → Raw Editor → вставь все переменные одним блоком:

```env
APP_NAME=AgroConsult
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://agroconsult-<твой-логин>.vercel.app,http://localhost:3000

SECRET_KEY=<сгенерируй: python -c "import secrets; print(secrets.token_urlsafe(48))">
ACCESS_TOKEN_EXPIRE_MINUTES=10080

DATABASE_URL=<из Supabase, asyncpg>
DATABASE_URL_SYNC=<из Supabase, psycopg2>

QDRANT_URL=<из Qdrant Cloud>
QDRANT_API_KEY=<из Qdrant Cloud>
QDRANT_COLLECTION=agroconsult_docs
QDRANT_VECTOR_SIZE=1024

UPSTASH_REDIS_URL=<из Upstash REST API>
UPSTASH_REDIS_TOKEN=<из Upstash REST API>
REDIS_CACHE_TTL=3600

GIGACHAT_AUTH_KEY=<из developers.sber.ru>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat-Pro
GIGACHAT_EMBEDDINGS_MODEL=Embeddings
GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
GIGACHAT_AUTH_URL=https://ngw.devices.sberbank.ru:9443/api/v2/oauth

RAG_TOP_K_RETRIEVAL=15
RAG_TOP_K_CONTEXT=6
RAG_MAX_CONTEXT_TOKENS=4000
RAG_TEMPERATURE=0.2
RAG_CHUNK_SIZE=900
RAG_CHUNK_OVERLAP=150

ADMIN_EMAIL=admin@agroconsult.local
ADMIN_PASSWORD=<длинный_пароль_для_админки>
```

5. Deploy запустится автоматически. Дождись сообщения "Deployment successful" (≈5 минут на первый деплой)
6. Settings → Domains → Generate Domain → получишь URL вида `agroconsult-xxx.up.railway.app`
7. Проверка: открой `https://<URL>/health` — должно вернуть `{"status": "ok", "checks": {"database": "ok"}}`
8. Открой `https://<URL>/docs` — увидишь Swagger со всеми эндпоинтами

### Если что-то пошло не так

- **Build failed**: посмотри логи в Deployments → проверь, что Root directory = `backend`
- **Health endpoint показывает database error**: проверь DATABASE_URL — нужен **Transaction pooler** (порт 6543), не Session pooler
- **Login возвращает 500**: проверь что `alembic upgrade head` отработал (логи Deployments → release phase)

---

## 4. Загрузка корпуса документов (seed)

После того как бэкенд запустился и миграции применились:

### Вариант A — через Railway CLI (рекомендую)

```bash
# Установи CLI: https://docs.railway.app/develop/cli
railway login
railway link  # выбери проект agroconsult
railway run -- python -m scripts.seed_documents \
  --manifest scripts/documents_manifest.yaml \
  --corpus-dir ../data/corpus_raw
```

### Вариант B — через временный Railway Shell

Settings → Service → Open Shell → выполни ту же команду.

### Вариант C — вручную через админку

Зайди под `admin@agroconsult.local` через `/docs` → POST `/api/v1/auth/login` → скопируй token → POST `/api/v1/documents/upload` (Authorize → Bearer token) и загружай по одному файлу.

---

## 5. Деплой фронтенда на Vercel

1. vercel.com → Login with GitHub → Add New Project → импортируй `agroconsult`
2. **Root directory**: `frontend`
3. Framework: Next.js (определится автоматически)
4. Environment Variables:
   - `NEXT_PUBLIC_API_URL` = `https://<railway-url>.up.railway.app`
5. Deploy → дождись ≈2 минут
6. Получишь URL вида `https://agroconsult-<имя>.vercel.app`
7. **Вернись в Railway → Variables → CORS_ORIGINS** → добавь этот URL → Redeploy

Готово. По vercel-ссылке доступен сервис.

---

## 6. Проверка работоспособности

1. Открой Vercel-ссылку
2. Зарегистрируйся как обычный фермер
3. Заполни профиль (регион, форма хозяйствования)
4. Задай тестовый вопрос: «Что такое грант Агростартап и какие требования?»
5. Должен прийти ответ со ссылками на документы из корпуса

---

## 7. Troubleshooting

| Симптом | Причина | Решение |
|---|---|---|
| 401 на /chat/ask | Токен истёк | Релогин |
| Долгий первый ответ (>30 сек) | GigaChat прогревает токен | Норма для первого запроса после простоя |
| "По вашему запросу не удалось найти" на все вопросы | Документы не проиндексированы | Запусти seed |
| Vercel build fails | Старая версия Node | Settings → Build → Node 20 |
| CORS error в браузере | CORS_ORIGINS не содержит Vercel URL | Поправь в Railway variables |

---

## 8. Стоимость

- Supabase Free: до 500 МБ БД, 1 GB файлов
- Qdrant Free: 1 ГБ векторов (на 30 НПА уходит <50 МБ)
- Upstash Free: 10 000 команд/день
- Railway: $5 кредитов/мес (хватит на 750 часов = 24/7)
- Vercel Hobby: 100 ГБ трафика/мес
- GigaChat Freemium: 1 млн токенов/мес (~500 запросов)

**Итого: 0 ₽/мес** для трафика уровня ВКР.

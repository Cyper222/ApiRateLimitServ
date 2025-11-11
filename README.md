# Микросервис управления лимитами API

Микросервис на **FastAPI**, реализующий **ограничение частоты запросов**  для каждого клиента и каждого эндпоинта.  
Используется алгоритм **Sliding Window** с хранением данных в **Redis**.

---

## Возможности

- Ограничение запросов по **клиенту** и **эндпоинту**
- Настраиваемые **правила для каждого клиента**
- Поддержка **правила по умолчанию**
- Алгоритм **Sliding Window** на основе Redis Sorted Sets
- Эндпоинты для проверки и обновления правил
- JSON-логирование

---

## Требования

- Python **3.10+**
- Docker & Docker Compose

---

## Конфигурация

Все настройки хранятся в файле `.env`. Конфигурация управляется с помощью **pydantic-settings**, который автоматически загружает переменные окружения и валидирует их типы.

### Настройка переменных окружения

1. Скопируйте `.env.example` в `.env`:
```bash
  cp .env.example .env
```

2. При необходимости измените значения в `.env` файле.

### Доступные переменные окружения

| Переменная окружения           | Описание                               | Значение по умолчанию |
|--------------------------------|----------------------------------------|----------------------|
| `APP_NAME`                     | Название приложения                    | rate-limit-service   |
| `APP_HOST`                     | Хост приложения                        | 0.0.0.0              |
| `APP_PORT`                     | Порт приложения                        | 8080                 |
| `APP_LOG_LEVEL`                | Уровень логирования                    | INFO                 |
| `APP_DEFAULT_LIMIT`            | Лимит запросов по умолчанию            | 100                  |
| `APP_DEFAULT_WINDOW_MINUTES`   | Размер временного окна в минутах       | 60                   |
| `REDIS_HOST`                   | Адрес Redis                            | redis                |
| `REDIS_PORT`                   | Порт Redis                             | 6379                 |
| `REDIS_DB`                     | Номер базы данных Redis                | 0                    |
| `REDIS_SSL`                    | Использовать SSL для Redis             | false                |
| `REDIS_DECODE_RESPONSES`       | Декодировать ответы Redis              | true                 |

**Примечание**: При запуске через Docker Compose переменные окружения автоматически загружаются из `.env` файла.

---

## ▶️ Запуск сервиса

```bash
  docker compose up --build

```

После запуска сервис будет доступен по адресу: http://localhost:8080

Проверка работоспособности:

```bash
  curl http://localhost:8080/health
```

## Эндпоинты

### Проверка и учёт запроса

POST `/api/v1/rate-limit/check`

Запрос:

```json
{
  "clientId": "client-123",
  "endpoint": "/api/users",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

Ответ:

```json
{
  "allowed": true,
  "limit": 100,
  "remaining": 45,
  "resetAt": "2025-01-15T11:00:00Z"
}
```

### Создание/обновление правила

POST `/api/v1/rate-limit/rules`

Индивидуальное правило:

```json
{
  "clientId": "client-123",
  "endpoint": "/api/users",
  "limit": 100,
  "windowMinutes": 60
}
```

Правило по умолчанию:

```json
{
  "limit": 200,
  "windowMinutes": 60
}
```

Ответ:

```json
{
  "status": "ok",
  "clientId": "client-123",
  "endpoint": "/api/users",
  "limit": 100,
  "windowMinutes": 60
}
```

## Примеры запросов (curl)

```bash

  curl -X POST http://localhost:8080/api/v1/rate-limit/rules \
  -H "Content-Type: application/json" \
  -d '{"clientId":"client-123","endpoint":"/api/users","limit":5,"windowMinutes":1}'



now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  curl -X POST http://localhost:8080/api/v1/rate-limit/check \
  -H "Content-Type: application/json" \
  -d "{\"clientId\":\"client-123\",\"endpoint\":\"/api/users\",\"timestamp\":\"$now\"}"

```

## Тестирование

Запуск тестов:

```bash
  pytest -q tests/unit
```

Интеграционные тесты (нужен Redis,`docker compose up -d redis`):

```bash
  pytest -q tests/integration
```

## Используемый алгоритм

- Sliding Window реализован на основе Redis Sorted Sets:
  - `ZREMRANGEBYSCORE` Удаляет старые события
  - `ZADD` Добавляет отметку времени запроса
  - `ZCARD` Возвращает число запросов в окне
  - `ZRANGE 0 0 WITHSCORES` Позволяет вычислить resetAt
- Правила хранятся в Redis Hash rl:rules с ключами вида: `<clientId>|<endpoint>`
- Запись: `default|default` глобальное правило по умолчанию.







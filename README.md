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

Все настройки хранятся в файле `application.yml`.

Основные параметры:

| Параметр                       | Описание                               |
|--------------------------------|----------------------------------------|
| `app.default_limit`            | Лимит запросов по умолчанию            |
| `app.default_window_minutes`   | Размер временного окна в минутах       |
| `redis.host`                   | Адрес Redis (можно переопределить `REDIS_HOST`) |

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






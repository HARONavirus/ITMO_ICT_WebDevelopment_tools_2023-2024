# Лабораторная работа 3: Упаковка FastAPI приложения в Docker, Работа с источниками данных и Очереди

## Цель

Научиться упаковывать FastAPI приложение в Docker, интегрировать парсер данных с базой данных и вызывать парсер через API и очередь.

## Подзадача 1: Упаковка FastAPI приложения, базы данных и парсера данных в Docker

*/app/Dockerfile*

```
FROM python:3.9-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

*/parser/Dockerfile*

```
FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.parser_app:app", "--host", "0.0.0.0", "--port", "8001"]
```

*docker-compose.yml* для управления оркестром сервисов, включающих FastAPI приложение, базу данных и парсер данных. Сюда же добавляются сервисы celery и redis.

```
services:
  db:
    image: postgres:17
    container_name: db
    environment:
      POSTGRES_USER: ${DB_ADMIN}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    env_file:
      - .env
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - bookcrossing_network

  celery:
    build:
      context: ./parser
    container_name: celery-worker
    command: celery -A app.celery_tasks.celery_app worker --loglevel=info
    depends_on:
      - parser
      - redis
      - db
    env_file:
      - .env
    networks:
      - bookcrossing_network

  redis:
    image: redis:7
    container_name: redis
    ports:
      - "6379:6379"
    networks:
      - bookcrossing_network

  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: app
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DB_ADMIN=${DB_ADMIN}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
    env_file:
      - .env
    volumes:
      - ./app:/app/app
    networks:
      - bookcrossing_network

  parser:
    build:
      context: ./parser
      dockerfile: Dockerfile
    container_name: parser
    depends_on:
      db:
        condition: service_healthy
      app:
        condition: service_started
    env_file:
      - .env
    volumes:
      - ./parser:/app/parser
    networks:
      - bookcrossing_network

volumes:
  postgres_data:
    external: true
    name: lr3_postgres_data

networks:
  bookcrossing_network:
```

## Подзадача 2: Вызов парсера из FastAPI

Необходимо добавить в FastAPI приложение ендпоинт, который будет принимать запросы с URL для парсинга от клиента, отправлять запрос парсеру (запущенному в отдельном контейнере) и возвращать ответ с результатом клиенту.

### Код:

*app/crud/parser.py*

```
@router.post("/parse")
async def parse_url(request: RequestURL):
  try:
    async with httpx.AsyncClient() as client:
      response = await client.post(
        f"http://parser:8001/parse",
        json={"url": request.url},
        timeout=30.0
      )
      response.raise_for_status()
      return response.json()
```

*parser/app/parser_app.py*

```
@app.post("/parse")
async def parse_author_books(data: InputUrl):
  try:
    books_parsed = await parse_and_save_books(data.url)

    return {
      "status": "success",
      "author_url": data.url,
      "books_parsed": books_parsed,
      "message": f"Successfully saved {books_parsed} new books"
    }
```

### Выполнение кода:

![работа парсера](https://i.postimg.cc/zXLQHHpV/2025-09-18-16-48-41.png)

### Реузьтат:

![результат работы парсера](https://i.postimg.cc/L6m2FTVj/2025-09-18-16-54-36.png)

Получается, что основное буккроссинг FastAPI приложение делает запрос на ссылку приложения парсера, дальше работа происходит уже в нём (то есть в отдельно поднятом контейнере). Происходит парсинг, сохранение в бд и возврат ответа основному приложению.

## Подзадача 3: Вызов парсера из FastAPI через очередь

### Создание задачи в фоне

#### Код:

*app/crud/parser.py*

```
@router.post("/parse-async")
async def parse_url_async(request: RequestURL):
  try:
    async with httpx.AsyncClient() as client:
      response = await client.post(
        f"http://parser:8001/parse-async",
        json={"url": request.url},
        timeout=30.0
      )
      response.raise_for_status()
      return {"message": "Parse request sent", "response": response.json()}
```

*parser/app/parser_app.py*

```
@app.post("/parse-async")
async def start_parsing(data: InputUrl):
  try:
    logger.info(f"Starting parsing task for URL: {data.url}")
    task = parse_url_task.delay(data.url)
    logger.info(f"Task created with id: {task.id}")

    return {
      "status": "processing",
      "task_id": task.id,
      "message": "Parsing task started successfully",
    }
```

#### Выполнение кода:

![работа парсера](https://i.postimg.cc/zGYyHMK6/2025-09-18-17-03-02.png)

### Проверка статуса задачи

#### Код:

*parser/app/celery_tasks.py*

```
celery_app = Celery(
  'bookcrossing',
  broker='redis://redis:6379/0',
  backend='redis://redis:6379/0',
)


@celery_app.task
def parse_url_task(url: str):
  result = asyncio.run(parse_and_save_books(url))
  return f"There are {result} newly parsed Books"
```

*app/crud/parser.py*

```
@router.get("/task/{task_id}")
async def proxy_task_status(task_id: str):
  try:
    async with httpx.AsyncClient() as client:
      response = await client.get(f"http://parser:8001/task/{task_id}")
    return response.json()
```

*parser/app/parser_app.py*

```
@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
  try:
    task_result = AsyncResult(task_id, app=celery_app)

    response = {
      "task_id": task_id,
      "status": task_result.status,
    }

    if task_result.ready():
      if task_result.successful():
        response["result"] = task_result.result
        response["status"] = "completed"
      else:
        response["error"] = str(task_result.result)
        response["status"] = "failed"

    return response
```

![работа проверки задач](https://i.postimg.cc/QCxth99q/2025-09-18-17-12-41.png)

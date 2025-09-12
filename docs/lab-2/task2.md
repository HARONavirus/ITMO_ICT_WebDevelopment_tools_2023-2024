# Лабораторная работа 2. Потоки. Процессы. Асинхронность.

## Задача 2: Параллельный парсинг веб-страниц с сохранением в базу данных

**Задача**: Напишите программу на Python для параллельного парсинга нескольких веб-страниц с сохранением данных в базу данных с использованием подходов threading, multiprocessing и async. Каждая программа должна парсить информацию с нескольких веб-сайтов, сохранять их в базу данных.

### Общий код

```
import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, create_engine, delete
import time
from models import *
from typing import List


DATABASE_URL = "postgresql://postgres:superuser@localhost:5432/book_exchange_db"
engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)

URLS = [
    "https://www.livelib.ru/author/103808/top-artur-konan-dojl",
    "https://www.livelib.ru/author/1781/top-agata-kristi",
    "https://www.livelib.ru/author/4389/top-sharlotta-bronte"
]


def clear_database():
  """Очистка базы данных перед началом работы"""
  with Session(engine) as session:
    # Сначала удаляем все книги (из-за внешних ключей)
    session.exec(delete(Book))
    # Затем удаляем все профили
    session.exec(delete(Profile))
    session.commit()
  print("База данных очищена")


def create_default_profile():
  """Создание профиля по умолчанию с id=1"""
  with Session(engine) as session:
    # Создаем профиль с явным id=1
    default_profile = Profile(
      id=1,  # Явно указываем id
      username="default_user",
      name="Default",
      surname="User",
      age=30,
      gender=Gender.MALE,
      address="Default address"
    )
    session.add(default_profile)
    session.commit()
    print("Создан профиль по умолчанию с id=1")


def parse_books(url: str) -> List[BookBase]:
  """Парсинг книг со страницы автора"""
  try:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    author = soup.find('div', class_='author-header__name').text.strip()

    books = []
    for book_item in soup.find_all('div', class_='book-item__inner'):
      title = book_item.find('a', class_='book-item__title')
      if title:
        title = title.text.strip()
      else:
        continue

      description = book_item.find('p')
      description = ".".join(description.text.strip().split(".")[:3]) + "." if description else None

      books.append(BookBase(
        title=title,
        author=author,
        description=description,
      ))

    return books
  except Exception as e:
    print(f"Ошибка при парсинге {url}: {e}")
    return []


def save_books(books: List[BookBase]):
  """Сохранение книг в БД"""
  try:
    with Session(engine) as session:
      for book_data in books:
        book = Book(**book_data.model_dump(), owner_id=1)
        session.add(book)
      session.commit()
  except Exception as e:
    print(f"Ошибка при сохранении книг: {e}")
```

### threading

#### Код:

```
import threading

# Сюда вставляем общий код

def parse_and_save(url: str):
    """Функция для потока: парсинг и сохранение"""
    print(f"Парсинг {url}")
    books = parse_books(url)
    save_books(books)
    print(f"Сохранено {len(books)} книг с {url}")


def main():
    start_time = time.time()

    clear_database()

    create_default_profile()

    threads = []
    for url in URLS:
        thread = threading.Thread(target=parse_and_save, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print(f"Общее время выполнения: {end_time - start_time:.2f} секунд")


if __name__ == "__main__":
    main()
```

#### Выполнение кода:

![результат выполнения threading](https://i.ibb.co/fzyDQ6ph/2025-09-12-13-02-53.png)

**Общее время выполнения: 0.48 секунд**

#### Проверка базы данных:

Артур Конан Дойль

![результат выполнения threading в бд](https://i.ibb.co/VWTQWcxW/2025-09-11-23-22-31.png)

Агата Кристи

![результат выполнения threading в бд](https://i.ibb.co/qMDyp2Y9/2025-09-11-23-24-12.png)

Шарлотта Бронте

![результат выполнения threading в бд](https://i.ibb.co/4nRtQFtb/2025-09-11-23-24-44.png)

### multiprocessing

#### Код:

```
import multiprocessing
from multiprocessing import Pool

# Сюда вставляем общий код

def parse_and_save(url: str):
  """Функция для процесса: парсинг и сохранение"""
  print(f"Парсинг {url}")
  books = parse_books(url)
  if books:
    save_books(books)
    print(f"Сохранено {len(books)} книг с {url}")
  else:
    print(f"Не удалось получить книги с {url}")


def main():
  start_time = time.time()

  # Очищаем базу и создаем профиль в основном процессе
  clear_database()
  create_default_profile()

  # Создаем пул процессов
  with Pool(processes=len(URLS)) as pool:
    # Запускаем процессы для каждого URL
    pool.map(parse_and_save, URLS)

  end_time = time.time()
  print(f"Общее время выполнения: {end_time - start_time:.2f} секунд")


if __name__ == "__main__":
  # Для multiprocessing в Windows необходимо использовать эту конструкцию
  multiprocessing.freeze_support()
  main()
```

#### Выполнение кода:

![результат выполнения multiprocessing](https://i.ibb.co/G4FzhHv7/2025-09-12-13-05-01.png)

**Общее время выполнения: 0.79 секунд**

#### Проверка базы данных:

Артур Конан Дойль

![результат выполнения multiprocessing в бд](https://i.ibb.co/tw1C86JN/2025-09-12-13-07-30.png)

Агата Кристи

![результат выполнения multiprocessing в бд](https://i.ibb.co/vpKLk4T/2025-09-12-13-07-51.png)

Шарлотта Бронте

![результат выполнения multiprocessing в бд](https://i.ibb.co/YBkpqGry/2025-09-12-13-08-11.png)

### async

#### Код:

```
import aiohttp
import asyncio
import ssl

# Сюда вставляем общий код и удаляем повторы без async

async def fetch(url):
  """Асинхронное получение HTML с отключенной проверкой SSL"""
  ssl_context = ssl.create_default_context()
  ssl_context.check_hostname = False
  ssl_context.verify_mode = ssl.CERT_NONE

  connector = aiohttp.TCPConnector(ssl=ssl_context)
  async with aiohttp.ClientSession(connector=connector) as session:
    async with session.get(url) as response:
      return await response.text()


async def parse_books(url: str) -> List[BookBase]:
  """Асинхронный парсинг книг со страницы автора"""
  try:
    html = await fetch(url)
    soup = BeautifulSoup(html, 'html.parser')
    author = soup.find('div', class_='author-header__name').text.strip()

    books = []
    for book_item in soup.find_all('div', class_='book-item__inner'):
      title = book_item.find('a', class_='book-item__title')
      if title:
        title = title.text.strip()
      else:
        continue

      description = book_item.find('p')
      description = ".".join(description.text.strip().split(".")[:3]) + "." if description else None

      books.append(BookBase(
        title=title,
        author=author,
        description=description,
      ))

    return books
  except Exception as e:
    print(f"Ошибка при парсинге {url}: {e}")
    return []


async def save_books(books: List[BookBase]):
  """Асинхронное сохранение книг в БД"""
  try:
    # Используем asyncio.to_thread для выполнения синхронной операции БД
    await asyncio.to_thread(_sync_save_books, books)
  except Exception as e:
    print(f"Ошибка при сохранении книг: {e}")


def _sync_save_books(books: List[BookBase]):
  """Синхронная функция для сохранения книг"""
  with Session(engine) as session:
    for book_data in books:
      book = Book(**book_data.model_dump(), owner_id=1)
      session.add(book)
    session.commit()


async def parse_and_save(url: str):
  """Асинхронная задача: парсинг и сохранение"""
  print(f"Парсинг {url}")
  books = await parse_books(url)
  if books:
    await save_books(books)
    print(f"Сохранено {len(books)} книг с {url}")
  else:
    print(f"Не удалось получить книги с {url}")


async def main():
  start_time = time.time()

  # Очищаем базу и создаем профиль (синхронные операции)
  clear_database()
  create_default_profile()

  # Создаем задачи для каждого URL
  tasks = [parse_and_save(url) for url in URLS]
  # Запускаем все задачи параллельно
  await asyncio.gather(*tasks)

  end_time = time.time()
  print(f"Общее время выполнения: {end_time - start_time:.2f} секунд")


if __name__ == "__main__":
  asyncio.run(main())
```

#### Выполнение кода:

![результат выполнения async](https://i.ibb.co/35sfj0Jc/2025-09-12-16-51-50.png)

**Общее время выполнения: 0.46 секунд**

#### Проверка базы данных:

Артур Конан Дойль

![результат выполнения async в бд](https://i.ibb.co/21rjgzR0/2025-09-12-17-04-26.png)

Агата Кристи

![результат выполнения async в бд](https://i.ibb.co/fVPtD41v/2025-09-12-17-04-48.png)

Шарлотта Бронте

![результат выполнения async в бд](https://i.ibb.co/pBNkvZf6/2025-09-12-17-05-09.png)

| Method | Time for 1M (sec) |
|-------------|-------------|
| threading | 0.48 |
| multiprocessing | 0.79 |
| async | 0.46 |

Multiprocessing показал наихудший результат из-за требования отдельного подключения к БД для каждого процесса и накладных расходов на их создание.

Threading и Async показали схожие результаты, но для задачи парсинга и сохранения данных всё же лучше подходит второй процесс, потому что: - Нет необходимости в настоящем параллелизме для такого малого количества URL, - Минимальные накладные расходы.
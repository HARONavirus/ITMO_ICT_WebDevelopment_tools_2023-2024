from bs4 import BeautifulSoup
from sqlmodel import Session, create_engine, delete
import time
from models import *
from typing import List

import aiohttp
import asyncio
import ssl

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
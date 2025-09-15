import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, create_engine, delete
import time
from models import *
from typing import List

import threading


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
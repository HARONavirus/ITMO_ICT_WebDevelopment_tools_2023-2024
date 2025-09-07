from typing import Optional, List, TypedDict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Profile(BaseModel):
  id: Optional[int] = None
  username: str
  name: str
  surname: str
  age: int
  address: Optional[str] = None
  books: List['Book'] = []

class Book(BaseModel):
  id: Optional[int] = None
  title: str
  author: str
  genre: Optional[str] = None
  owner_id: int

test_db = [
  {
    "id": 1,
    "username": "artboch",
    "name": "Артем",
    "surname": "Бочкарь",
    "age": 23,
    "address": "Санкт-Петербург, Разъезжая улица, дом 5, квартира 3",
    "books": [
      {
        "id": 1,
        "title": "Шерлок Холмс",
        "author": "Артур Конан Дойл",
        "genre": "Детектив",
        "owner_id": 1
      }
    ]
  },
  {
    "id": 2,
    "username": "killer",
    "name": "Олег",
    "surname": "Петров",
    "age": 19,
    "address": "Санкт-Петербург, Пролетарская улица, дом 13, квартира 288",
    "books": [
      {
        "id": 2,
        "title": "Джейн Эйр",
        "author": "Шарлотта Бронте",
        "genre": "Роман",
        "owner_id": 2
      }
    ]
  }
]

app = FastAPI(
  title="My Awesome API",
  description="API для работы с профилями и книгами",
  version="1.0.0",
  openapi_tags=[
    {
      "name": "Главная",
      "description": "Основные эндпоинты",
    },
    {
      "name": "Профили",
      "description": "Операции с профилями пользователей",
    },
      {
        "name": "Книги",
        "description": "Операции с книгами",
      }
  ]
)

@app.get("/", tags=["Главная"])
def hello():
  return "Hello, artboch!"

# Профили

# Получить все профили
@app.get("/profiles", tags=["Профили"])
def get_profiles() -> List[Profile]:
  return test_db

# Получить профиль по ID
@app.get("/profile/{profile_id}", tags=["Профили"])
def get_profile(profile_id: int) -> Profile:
  profile = next((prof for prof in test_db if prof.get("id") == profile_id), None)
  if profile is None:
    raise HTTPException(status_code=404, detail="Profile not found")
  return profile

# Создать новый профиль
@app.post("/profile", tags=["Профили"])
def create_profile(profile: Profile) -> TypedDict('Response', {"status": int, "data": Profile}):
  # Генерируем новый ID
  max_id = max(prof["id"] for prof in test_db) if test_db else 0
  profile_data = profile.model_dump()
  profile_data["id"] = max_id + 1

  for book in profile_data["books"]:
    book["owner_id"] = profile_data["id"]
    if book.get("id") is None:
      all_books = [b for prof in test_db for b in prof["books"]]
      max_book_id = max(b["id"] for b in all_books) if all_books else 0
      book["id"] = max_book_id + 1

  test_db.append(profile_data)
  return {"status": 200, "data": profile_data}

# Обновить профиль по ID
@app.put("/profile/{profile_id}", tags=["Профили"])
def update_profile(profile_id: int, profile: Profile) -> Profile:
  for i, prof in enumerate(test_db):
    if prof.get("id") == profile_id:
      profile_data = profile.model_dump()
      profile_data["id"] = profile_id

      for book in profile_data["books"]:
        book["owner_id"] = profile_id

      test_db[i] = profile_data
      return profile_data

  raise HTTPException(status_code=404, detail="Profile not found")

# Удалить профиль по ID
@app.delete("/profile/{profile_id}", tags=["Профили"])
def delete_profile(profile_id: int):
  for i, prof in enumerate(test_db):
    if prof.get("id") == profile_id:
      test_db.pop(i)
      return {"status": 200, "message": "Profile deleted successfully"}

  raise HTTPException(status_code=404, detail="Profile not found")

# Кнгиги

# Получить все книги
@app.get("/books", tags=["Книги"])
def get_books() -> List[Book]:
  all_books = [book for prof in test_db for book in prof["books"]]
  return all_books

# Получить книгу по ID
@app.get("/book/{book_id}", tags=["Книги"])
def get_book(book_id: int) -> Book:
  for prof in test_db:
    for book in prof["books"]:
      if book.get("id") == book_id:
        return book

  raise HTTPException(status_code=404, detail="Book not found")

# Создать новую книгу
@app.post("/book", tags=["Книги"])
def create_book(book: Book) -> TypedDict('Response', {"status": int, "data": Book}):
  # Проверяем, существует ли владелец
  owner_exists = any(prof["id"] == book.owner_id for prof in test_db)
  if not owner_exists:
    raise HTTPException(status_code=404, detail="Owner not found")

  # Генерируем ID для книги
  all_books = [b for prof in test_db for b in prof["books"]]
  max_book_id = max(b["id"] for b in all_books) if all_books else 0
  book_data = book.model_dump()
  book_data["id"] = max_book_id + 1

  # Добавляем книгу владельцу
  for prof in test_db:
    if prof["id"] == book.owner_id:
      prof["books"].append(book_data)
      break

  return {"status": 200, "data": book_data}

# Обновить книгу по ID
@app.put("/book/{book_id}", tags=["Книги"])
def update_book(book_id: int, book: Book) -> Book:
  for prof in test_db:
    for i, existing_book in enumerate(prof["books"]):
      if existing_book.get("id") == book_id:
        book_data = book.model_dump()
        book_data["id"] = book_id  # Сохраняем оригинальный ID
        prof["books"][i] = book_data
        return book_data

  raise HTTPException(status_code=404, detail="Book not found")

# Удалить книгу по ID
@app.delete("/book/{book_id}", tags=["Книги"])
def delete_book(book_id: int):
  for prof in test_db:
    for i, book in enumerate(prof["books"]):
      if book.get("id") == book_id:
        prof["books"].pop(i)
        return {"status": 200, "message": "Book deleted successfully"}

  raise HTTPException(status_code=404, detail="Book not found")
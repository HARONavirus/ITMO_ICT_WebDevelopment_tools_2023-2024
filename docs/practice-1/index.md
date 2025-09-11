# Практика 1: Создание базового приложения на FastAPI

## Задание 1: Запуск FastAPI приложения

```
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def hello():
    return "Hello, artboch!"
```

## Задание 2: Создание основных моделей BookCrossing приложения

Для обеспечения начала работ, адаптации к новому формату и тестирования запросов была разработана модель, включающая две ключевые таблицы: "Профиль" и "Книга"

```
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
```

## Задание 3: Формирование тестовой базы данных

```
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
```

## Задание 4: Написание CRUD-запросов для Профиля

### Демонстрация ручек:

![ручки пользователя](https://i.postimg.cc/zG55qc5P/2025-09-10-14-26-13.png)

### Создание нового пользователя:

```
@app.post("/profile", tags=["Профили"])
def create_profile(profile: Profile) -> TypedDict('Response', {"status": int, "data": Profile}):
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
```

![запрос на создание пользователя](https://i.postimg.cc/66vy3FJ9/2025-09-10-14-38-09.png)

### Запрос на всех пользователей:

```
@app.get("/profiles", tags=["Профили"])
def get_profiles() -> List[Profile]:
  return test_db
```

![запрос на список всех пользователей](https://i.postimg.cc/1zd3Rrvn/2025-09-10-14-39-03.png)

### Запрос на поиск пользователя по его id:

```
@app.get("/profile/{profile_id}", tags=["Профили"])
def get_profile(profile_id: int) -> Profile:
  profile = next((prof for prof in test_db if prof.get("id") == profile_id), None)
  if profile is None:
    raise HTTPException(status_code=404, detail="Profile not found")
  return profile
```

![запрос на поиск пользователя по его id](https://i.postimg.cc/BvjJz1Jq/2025-09-10-14-40-57.png)

### Запрос на обновление пользовательских данных:

```
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
```

![запрос на обновление пользовательских данных](https://i.postimg.cc/sDG93TKS/2025-09-10-14-43-52.png)

### Запрос на удаление пользователя:

```
@app.delete("/profile/{profile_id}", tags=["Профили"])
def delete_profile(profile_id: int):
  for i, prof in enumerate(test_db):
    if prof.get("id") == profile_id:
      test_db.pop(i)
      return {"status": 200, "message": "Profile deleted successfully"}

  raise HTTPException(status_code=404, detail="Profile not found")
```

![запрос на удаление пользователя](https://i.postimg.cc/L8n51snZ/2025-09-10-14-47-40.png)

## Задание 4: Написание CRUD-запросов для Книг

### Демонстраций ручек:

![ручки книг](https://i.postimg.cc/d3Lrfr3r/2025-09-11-12-02-35.png)

### Создание новой книги:

```
@app.post("/book", response_model=schemas.BookRead, tags=["Книги"])
def create_book(book: schemas.BookCreate, session: Session = Depends(get_session)):
  if book.owner_id is not None:
    owner = session.get(models.Profile, book.owner_id)
    if not owner:
      raise HTTPException(status_code=404, detail="Владелец не найден")

  db_book = models.Book(**book.dict())
  session.add(db_book)
  session.commit()
  session.refresh(db_book)
  return db_book
```

![создание новой книги](https://i.postimg.cc/0NR9zwwn/2025-09-11-12-09-07.png)

### Запрос на получение всех книг:

```
@app.get("/books", response_model=List[schemas.BookRead], tags=["Книги"])
def get_books(session: Session = Depends(get_session)):
  books = session.exec(select(models.Book)).all()
  return books
```

![запрос на получение всех книг](https://i.postimg.cc/QC6kx7fx/2025-09-11-12-12-55.png)

### Запрос на получение книги по id:

```
@app.get("/book/{book_id}", response_model=schemas.BookRead, tags=["Книги"])
def get_book(book_id: int, session: Session = Depends(get_session)):
  book = session.get(models.Book, book_id)
  if not book:
    raise HTTPException(status_code=404, detail="Книга не найдена")
  return book
```

![запрос на получение книги по id](https://i.postimg.cc/HW5F6kVc/2025-09-11-12-14-06.png)

### Запрос на получение книг по id пользователя:

```
@app.get("/profile/{profile_id}/books", response_model=List[schemas.BookRead], tags=["Книги"])
def get_books_by_owner(profile_id: int, session: Session = Depends(get_session)):
  owner = session.get(models.Profile, profile_id)
  if not owner:
    raise HTTPException(status_code=404, detail="Владелец не найден")

  books = session.exec(
    select(models.Book).where(models.Book.owner_id == profile_id)
  ).all()
  return books
```

![запрос на получение книг по id пользователя](https://i.postimg.cc/J7jMsLC8/2025-09-11-12-16-34.png)

### Запрос на обновление данных книги:

```
@app.put("/book/{book_id}", response_model=schemas.BookRead, tags=["Книги"])
def update_book(
    book_id: int,
    book_update: schemas.BookUpdate,
    session: Session = Depends(get_session)
):

  db_book = session.get(models.Book, book_id)
  if not db_book:
    raise HTTPException(status_code=404, detail="Книга не найдена")

  if book_update.owner_id is not None:
    owner = session.get(models.Profile, book_update.owner_id)
    if not owner:
      raise HTTPException(status_code=404, detail="Владелец не найден")

  update_data = book_update.dict(exclude_unset=True)
  for key, value in update_data.items():
    setattr(db_book, key, value)

  session.add(db_book)
  session.commit()
  session.refresh(db_book)
  return db_book
```

![запрос на обновление данных книги](https://i.postimg.cc/hPgQCnL4/2025-09-11-12-22-32.png)

### Запрос на удаление книги:

```
@app.delete("/book/{book_id}", tags=["Книги"])
def delete_book(book_id: int, session: Session = Depends(get_session)):
  book = session.get(models.Book, book_id)
  if not book:
    raise HTTPException(status_code=404, detail="Книга не найдена")

  active_requests = session.exec(
    select(models.ExchangeRequest).where(
      models.ExchangeRequest.book_id == book_id,
      models.ExchangeRequest.status == models.RequestStatus.PENDING
    )
  ).all()

  if active_requests:
    raise HTTPException(
      status_code=400,
      detail="Нельзя удалить книгу с активными заявками на обмен"
    )

  session.delete(book)
  session.commit()
  return {"message": "Книга удалена успешно"}
```

![запрос на удаление книги](https://i.postimg.cc/4x3z4GF4/2025-09-11-12-24-42.png)
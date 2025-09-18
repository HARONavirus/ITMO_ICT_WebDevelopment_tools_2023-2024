# Практика 2: Настройка БД, SQLModel и миграции через Alembic

## SQLModel. Реализация и подключение

Устанавливаем СУБД PostgreSQL через официальный сайт, а также вводим необходимые библиотеки в виртуальное окружение: `pip install sqlmodel`, `pip install psycopg2-binary`

### Файл с подключением к БД - **connection.py**

```
from sqlmodel import SQLModel, Session, create_engine

db_url = 'postgresql://postgres:superuser@localhost:5432/book_exchange_db'

engine = create_engine(db_url, echo=True)


def init_db():
  SQLModel.metadata.drop_all(engine)
  SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
```

### Обновляем файл **models.py**, чтобы модели сработались с PostgreSQL СУБД.

```
# Enum для поля пола
class Gender(str, Enum):
  MALE = "male"
  FEMALE = "female"


# Enum для статуса заявки
class RequestStatus(str, Enum):
  PENDING = "pending"
  ACCEPTED = "accepted"
  REJECTED = "rejected"


# Базовые модели для валидации данных
class ProfileBase(SQLModel):
  username: str = Field(index=True, unique=True)
  name: str
  surname: str
  age: int
  gender: Gender
  address: Optional[str] = None


class BookBase(SQLModel):
  title: str
  author: str
  genre: Optional[str] = None
  description: Optional[str] = None
  pages: int | None


class ExchangeRequestBase(SQLModel):
  status: RequestStatus = Field(default=RequestStatus.PENDING)


# Модели для базы данных
class Profile(ProfileBase, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  created_at: datetime = Field(default_factory=datetime.utcnow)

  books: List["Book"] = Relationship(back_populates="owner")
  sent_requests: List["ExchangeRequest"] = Relationship(back_populates="requester")


class Book(BookBase, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  owner_id: Optional[int] = Field(default=None, foreign_key="profile.id")
  created_at: datetime = Field(default_factory=datetime.utcnow)

  owner: Optional[Profile] = Relationship(back_populates="books")
  requests: List["ExchangeRequest"] = Relationship(back_populates="book")


class ExchangeRequest(ExchangeRequestBase, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  book_id: int = Field(foreign_key="book.id")
  requester_id: int = Field(foreign_key="profile.id")
  created_at: datetime = Field(default_factory=datetime.utcnow)

  book: "Book" = Relationship(back_populates="requests")
  requester: "Profile" = Relationship(back_populates="sent_requests")
```

Помимо изменения объявления полей моделей, в процессе работы я разделил модели на базовые и расширенные. Базовые модели - это те, с которыми работает обычный пользователь. Расширенные модели, которые наследуются от базовых, включают в себя автоматически генерируемый id и связи многие-ко-многим.

## Запросы

### Создание объектов (на примере пользователя)

```
@app.post("/profile", response_model=schemas.ProfileRead, tags=["Профили"])
def create_profile(profile: schemas.ProfileCreate, session: Session = Depends(get_session)):
  existing = session.exec(
    select(models.Profile).where(models.Profile.username == profile.username)
  ).first()
  if existing:
    raise HTTPException(status_code=400, detail="Имя пользователя уже занято")

  db_profile = models.Profile.model_validate(profile)
  session.add(db_profile)
  session.commit()
  session.refresh(db_profile)
  return db_profile
```

Создание профиля реализовано по следующему принципу: В эндпоинт поступает базовая модель ProfileCreate и настраивается соединение с базой данных через dependency injection с помощью session=Depends(get_session).

Перед созданием объекта выполняется проверка уникальности имени пользователя - выполняется запрос к базе данных для поиска существующего профиля с таким же username. Если пользователь с таким именем уже существует, возвращается ошибка HTTP 400 с соответствующим сообщением.

Если проверка пройдена успешно, метод model_validate преобразует упрощенную модель в основную ORM-модель, связанную с базой данных. Затем обработанный объект сохраняется в сессии через session.add, изменения фиксируются в базе данных методом commit, после чего данные объекта обновляются до актуального состояния с помощью метода refresh.

Эндпоинт возвращает созданный объект в формате ProfileRead с автоматической валидацией и сериализацией ответа через механизм response_model.

### Получение объектов и списков (на примере пользователя)

```
@app.get("/profiles", response_model=List[schemas.ProfileRead], tags=["Профили"])
def get_profiles(session: Session = Depends(get_session)):
  profiles = session.exec(select(models.Profile)).all()
  return profiles


@app.get("/profile/{profile_id}", response_model=schemas.ProfileWithBooks, tags=["Профили"])
def get_profile(profile_id: int, session: Session = Depends(get_session)):
  profile = session.get(models.Profile, profile_id)
  if not profile:
    raise HTTPException(status_code=404, detail="Профиль не найден")
  return profile

@app.get("/profile/{profile_id}/books", response_model=List[schemas.BookRead], tags=["Книги"])
def get_books_by_owner(profile_id: int, session: Session = Depends(get_session)):
  owner = session.get(models.Profile, profile_id)
  if not owner:
    raise HTTPException(status_code=404, detail="Владелец не найден")

  books = session.exec(
    select(models.Book).where(models.Book.owner_id == profile_id)
  ).all()
  return books

@app.get("/profile/{profile_id}/with-books", response_model=schemas.ProfileWithBooks, tags=["Профили"])
def get_profile_with_books(profile_id: int, session: Session = Depends(get_session)):
  profile = session.get(models.Profile, profile_id)
  if not profile:
    raise HTTPException(status_code=404, detail="Профиль не найден")

  return profile
```

Заметим, что в Профиле есть список Книг, который необходимо раскрывать при выполнении get-запроса, а не просто получать их id. Поэтому был создан новый класс, который расширяет возвращаемые вложенные объекты

![пользователи с раскрытыми книгами](https://i.postimg.cc/3xnQZqjx/2025-09-11-13-21-13.png)

### Обновление и Внешние ключи

Теперь, вместо PUT-метода в коде API будет использоваться PATCH для частичного обновления данных.

#### Новая схема

```
class ProfileUpdate(SQLModel):
  username: Optional[str] = None
  name: Optional[str] = None
  surname: Optional[str] = None
  age: Optional[int] = None
  gender: Optional[Gender] = None
  address: Optional[str] = None

class BookUpdate(SQLModel):
  title: Optional[str] = None
  author: Optional[str] = None
  genre: Optional[str] = None
  description: Optional[str] = None
  pages: Optional[int] = None
  owner_id: Optional[int] = None
```

#### Новые эндпоинты

```
@app.patch("/profile/{profile_id}", response_model=schemas.ProfileRead, tags=["Профили"])
def update_profile(
    profile_id: int,
    profile_update: schemas.ProfileUpdate,
    session: Session = Depends(get_session)
):
    db_profile = session.get(models.Profile, profile_id)
    if not db_profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    # Проверяем уникальность username только если он меняется
    if profile_update.username and db_profile.username != profile_update.username:
        existing = session.exec(
            select(models.Profile).where(models.Profile.username == profile_update.username)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Имя пользователя уже занято")

    # Обновляем только переданные поля
    update_data = profile_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)

    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    return db_profile

@app.patch("/book/{book_id}", response_model=schemas.BookRead, tags=["Книги"])
def update_book(
    book_id: int,
    book_update: schemas.BookUpdate,
    session: Session = Depends(get_session)
):
    db_book = session.get(models.Book, book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    # Проверяем владельца только если он меняется
    if book_update.owner_id is not None and book_update.owner_id != db_book.owner_id:
        owner = session.get(models.Profile, book_update.owner_id)
        if not owner:
            raise HTTPException(status_code=404, detail="Владелец не найден")

    # Обновляем только переданные поля
    update_data = book_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_book, key, value)

    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book
```

#### Новые ручки

![ручка для обновления пользователя](https://i.postimg.cc/2STQzS5k/2025-09-11-13-38-15.png)

![ручка для обновления книги](https://i.postimg.cc/1RNb4Lwh/2025-09-11-13-38-38.png)

### Удаление

API для удаления схожая по логике с обновлением. Реализуем через `delete`

```
@app.delete("/profile/{profile_id}", tags=["Профили"])
def delete_profile(profile_id: int, session: Session = Depends(get_session)):
  profile = session.get(models.Profile, profile_id)
  if not profile:
    raise HTTPException(status_code=404, detail="Профиль не найден")

  session.delete(profile)
  session.commit()
  return {"message": "Профиль удален успешно"}

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
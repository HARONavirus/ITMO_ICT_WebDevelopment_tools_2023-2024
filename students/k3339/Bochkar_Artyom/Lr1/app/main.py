from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from app import models, schemas
from app.conection import get_session, init_db

app = FastAPI(
  title="Book Exchange API",
  description="API для обмена книгами между пользователями",
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

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", tags=["Главная"])
def hello():
  return {"message": "Hello artboch!"}


# Профили
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


@app.post("/profile", response_model=schemas.ProfileRead, tags=["Профили"])
def create_profile(profile: schemas.ProfileCreate, session: Session = Depends(get_session)):
  existing = session.exec(
    select(models.Profile).where(models.Profile.username == profile.username)
  ).first()
  if existing:
    raise HTTPException(status_code=400, detail="Имя пользователя уже занято")

  db_profile = models.Profile(**profile.dict())
  session.add(db_profile)
  session.commit()
  session.refresh(db_profile)
  return db_profile


@app.put("/profile/{profile_id}", response_model=schemas.ProfileRead, tags=["Профили"])
def update_profile(profile_id: int, profile: schemas.ProfileCreate, session: Session = Depends(get_session)):
  db_profile = session.get(models.Profile, profile_id)
  if not db_profile:
    raise HTTPException(status_code=404, detail="Профиль не найден")

  if db_profile.username != profile.username:
    existing = session.exec(
      select(models.Profile).where(models.Profile.username == profile.username)
    ).first()
    if existing:
      raise HTTPException(status_code=400, detail="Имя пользователя уже занято")

  for key, value in profile.dict().items():
    setattr(db_profile, key, value)

  session.add(db_profile)
  session.commit()
  session.refresh(db_profile)
  return db_profile


@app.delete("/profile/{profile_id}", tags=["Профили"])
def delete_profile(profile_id: int, session: Session = Depends(get_session)):
  profile = session.get(models.Profile, profile_id)
  if not profile:
    raise HTTPException(status_code=404, detail="Профиль не найден")

  session.delete(profile)
  session.commit()
  return {"message": "Профиль удален успешно"}


# Книги
@app.get("/books", response_model=List[schemas.BookRead], tags=["Книги"])
def get_books(session: Session = Depends(get_session)):
  books = session.exec(select(models.Book)).all()
  return books


@app.get("/books/available", response_model=List[schemas.BookRead], tags=["Книги"])
def get_available_books(session: Session = Depends(get_session)):
  books = session.exec(
    select(models.Book).where(models.Book.owner_id == None)
  ).all()
  return books


@app.get("/book/{book_id}", response_model=schemas.BookRead, tags=["Книги"])
def get_book(book_id: int, session: Session = Depends(get_session)):
  book = session.get(models.Book, book_id)
  if not book:
    raise HTTPException(status_code=404, detail="Книга не найдена")
  return book


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


# УБИРАЕМ ЭТОТ ENDPOINT - он больше не нужен
# @app.post("/book/with-owner", response_model=schemas.BookRead, tags=["Книги"])
# def create_book_with_owner(book: schemas.BookCreateWithOwner, session: Session = Depends(get_session)):

@app.put("/book/{book_id}/assign", response_model=schemas.BookRead, tags=["Книги"])
def assign_book_to_owner(book_id: int, owner_id: int, session: Session = Depends(get_session)):
  book = session.get(models.Book, book_id)
  if not book:
    raise HTTPException(status_code=404, detail="Книга не найдена")

  owner = session.get(models.Profile, owner_id)
  if not owner:
    raise HTTPException(status_code=404, detail="Владелец не найден")

  book.owner_id = owner_id
  session.add(book)
  session.commit()
  session.refresh(book)
  return book


@app.put("/book/{book_id}/release", response_model=schemas.BookRead, tags=["Книги"])
def release_book_from_owner(book_id: int, session: Session = Depends(get_session)):
  book = session.get(models.Book, book_id)
  if not book:
    raise HTTPException(status_code=404, detail="Книга не найдена")

  book.owner_id = None
  session.add(book)
  session.commit()
  session.refresh(book)
  return book


@app.get("/profile/{profile_id}/books", response_model=List[schemas.BookRead], tags=["Книги"])
def get_books_by_owner(profile_id: int, session: Session = Depends(get_session)):
  owner = session.get(models.Profile, profile_id)
  if not owner:
    raise HTTPException(status_code=404, detail="Владелец не найден")

  books = session.exec(
    select(models.Book).where(models.Book.owner_id == profile_id)
  ).all()
  return books


# ===== MANY-TO-MANY ENDPOINTS =====

@app.post("/exchange-request", response_model=schemas.ExchangeRequestRead, tags=["Заявки"])
def create_exchange_request(
    request: schemas.ExchangeRequestCreate,
    session: Session = Depends(get_session)
):
  book = session.get(models.Book, request.book_id)
  if not book:
    raise HTTPException(status_code=404, detail="Книга не найдена")

  requester = session.get(models.Profile, request.requester_id)
  if not requester:
    raise HTTPException(status_code=404, detail="Пользователь не найден")

  if book.owner_id == request.requester_id:
    raise HTTPException(status_code=400, detail="Нельзя запрашивать обмен своей же книги")

  existing_request = session.exec(
    select(models.ExchangeRequest).where(
      models.ExchangeRequest.book_id == request.book_id,
      models.ExchangeRequest.requester_id == request.requester_id,
      models.ExchangeRequest.status == models.RequestStatus.PENDING
    )
  ).first()

  if existing_request:
    raise HTTPException(status_code=400, detail="Активная заявка уже существует")

  db_request = models.ExchangeRequest(**request.dict())
  session.add(db_request)
  session.commit()
  session.refresh(db_request)
  return db_request


@app.get("/exchange-requests", response_model=List[schemas.ExchangeRequestWithDetails], tags=["Заявки"])
def get_all_exchange_requests(session: Session = Depends(get_session)):
  requests = session.exec(select(models.ExchangeRequest)).all()
  return requests


@app.get("/exchange-request/{request_id}", response_model=schemas.ExchangeRequestWithDetails, tags=["Заявки"])
def get_exchange_request(request_id: int, session: Session = Depends(get_session)):
  request = session.get(models.ExchangeRequest, request_id)
  if not request:
    raise HTTPException(status_code=404, detail="Заявка не найдена")
  return request


@app.put("/exchange-request/{request_id}", response_model=schemas.ExchangeRequestRead, tags=["Заявки"])
def update_exchange_request(
    request_id: int,
    request_update: schemas.ExchangeRequestUpdate,
    session: Session = Depends(get_session)
):
  db_request = session.get(models.ExchangeRequest, request_id)
  if not db_request:
    raise HTTPException(status_code=404, detail="Заявка не найдена")

  db_request.status = request_update.status
  session.add(db_request)
  session.commit()
  session.refresh(db_request)
  return db_request


@app.get("/profile/{profile_id}/sent-requests", response_model=List[schemas.ExchangeRequestWithDetails],
         tags=["Заявки"])
def get_sent_requests(profile_id: int, session: Session = Depends(get_session)):
  profile = session.get(models.Profile, profile_id)
  if not profile:
    raise HTTPException(status_code=404, detail="Пользователь не найден")

  return profile.sent_requests


@app.get("/profile/{profile_id}/received-requests", response_model=List[schemas.ExchangeRequestWithDetails],
         tags=["Заявки"])
def get_received_requests(profile_id: int, session: Session = Depends(get_session)):
  profile = session.get(models.Profile, profile_id)
  if not profile:
    raise HTTPException(status_code=404, detail="Пользователь не найден")

  requests = session.exec(
    select(models.ExchangeRequest)
    .join(models.Book)
    .where(models.Book.owner_id == profile_id)
  ).all()

  return requests


@app.get("/book/{book_id}/requests", response_model=List[schemas.ExchangeRequestWithDetails], tags=["Заявки"])
def get_book_requests(book_id: int, session: Session = Depends(get_session)):
  book = session.get(models.Book, book_id)
  if not book:
    raise HTTPException(status_code=404, detail="Книга не найдена")

  return book.requests


@app.delete("/exchange-request/{request_id}", tags=["Заявки"])
def delete_exchange_request(request_id: int, session: Session = Depends(get_session)):
  request = session.get(models.ExchangeRequest, request_id)
  if not request:
    raise HTTPException(status_code=404, detail="Заявка не найдена")

  session.delete(request)
  session.commit()
  return {"message": "Заявка удалена успешно"}
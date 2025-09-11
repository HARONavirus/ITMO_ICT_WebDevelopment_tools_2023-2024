from sqlmodel import SQLModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enum для поля пола
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

# Enum для статуса заявки
class RequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

# Схемы для создания
class ProfileCreate(SQLModel):
    username: str
    name: str
    surname: str
    age: int
    gender: Gender
    address: Optional[str] = None

class ProfileUpdate(SQLModel):
  username: Optional[str] = None
  name: Optional[str] = None
  surname: Optional[str] = None
  age: Optional[int] = None
  gender: Optional[Gender] = None
  address: Optional[str] = None

class BookCreate(SQLModel):
    title: str
    author: str
    genre: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None

class BookUpdate(SQLModel):
  title: Optional[str] = None
  author: Optional[str] = None
  genre: Optional[str] = None
  description: Optional[str] = None
  pages: Optional[int] = None
  owner_id: Optional[int] = None

# Убираем BookCreateWithOwner, используем обычный BookCreate
class ExchangeRequestCreate(SQLModel):
    book_id: int
    requester_id: int

class ExchangeRequestUpdate(SQLModel):
    status: RequestStatus

# Схемы для ответов
class BookRead(SQLModel):
    id: int
    title: str
    author: str
    genre: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Заменяем orm_mode на from_attributes

class ProfileRead(SQLModel):
    id: int
    username: str
    name: str
    surname: str
    age: int
    gender: Gender
    address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ExchangeRequestRead(SQLModel):
    id: int
    book_id: int
    requester_id: int
    status: RequestStatus
    created_at: datetime

    class Config:
        from_attributes = True

class ExchangeRequestWithDetails(SQLModel):
    id: int
    status: RequestStatus
    created_at: datetime
    book: BookRead
    requester: ProfileRead

    class Config:
        from_attributes = True

class ProfileWithBooks(ProfileRead):
    books: List[BookRead] = []

class ProfileWithRequests(ProfileRead):
    sent_requests: List[ExchangeRequestRead] = []
    received_requests: List[ExchangeRequestRead] = []

class BookWithRequests(BookRead):
    requests: List[ExchangeRequestRead] = []
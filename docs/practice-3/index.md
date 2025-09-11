# Практика 3: Миграции, ENV, GitIgnore и структура проекта

## Миграции. Alembic

В работе будем использовать Alembic для отслеживания миграций нашей БД. Скачиваем библиотеку через менеджер пакетов и настраиваем структуру

![структура проекта](https://i.postimg.cc/4x31DSt0/2025-09-11-18-33-55.png)

Далее настраиваем миграционные файлы по следующему алгоритму:

* В файле alembic.ini переменной sqlalchemy.url необходимо указать адрес БД, по аналогии с тем, что находится в файле connection.py
* В файле env.py импортировать все из models.py и в переменной target_metadata указать значение target_metadata=SQLModel.metadata
* В файле script.py.mako импортировать библиотеку sqlmodel
* Создать файл миграций с помощью команды alembic revision --autogenerate -m "message"
* Применить миграции с помощью команды alembic upgrade head

## Переменные окружения и .gitignore

### .gitignore

Добавляем в корневую папку проекта .gitignore файлы со следующим содержимым:

```
.idea
.ipynb_checkpoints
.mypy_cache
.vscode
__pycache__
.pytest_cache
htmlcov
dist
site
.coverage
coverage.xml
.netlify
test.db
log.txt
Pipfile.lock
env3.*
env
docs_build
site_build
venv
docs.zip
archive.zip
*.env

# vim temporary files
*~
.*.sw?
.cache

# macOS
.DS_Store
```

### .env

Добавляем .env файл со следующим содержимым:

```
DB_ADMIN=postgresql://postgres:superuser@localhost:5432/book_exchange_db
```

Изменяем **conection.py** для работы с энвиком:

```
from sqlmodel import SQLModel, Session, create_engine
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DB_ADMIN')

engine = create_engine(db_url, echo=True)


def init_db():
  SQLModel.metadata.drop_all(engine)
  SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
```

## Как передать в alembic.ini URL базы данных с помощью .env-файла?

Необходимо изменить файл `env.py` в директории `alembic`, чтобы он использовал переменную окружения из `.env`. Для этого импортируем библиотеку `os` и загружаем переменную окружения:

```
import os
from dotenv import load_dotenv

load_dotenv()
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

config.set_main_option("sqlalchemy.url", os.getenv("DB_ADMIN"))
```

Комментируем строку `sqlalchemy.url` в файле `alembic.ini`, чтобы она не конфликтовала с настройками из `env.py`. Это делается для того, чтобы не хранить конфиденциальную информацию в открытом виде.
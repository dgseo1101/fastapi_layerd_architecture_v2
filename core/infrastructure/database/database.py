# -*- coding: utf-8 -*-
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine import URL


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(
        self,
        database_user: str,
        database_password: str,
        database_host: str,
        database_port: int,
        database_name: str,
    ) -> None:
        dsn = URL.create(
            drivername="postgresql+psycopg",
            username=database_user,
            password=database_password,
            host=database_host,
            port=database_port,
            database=database_name,
        )

        self.engine = create_async_engine(url=dsn, echo=True)

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
        )
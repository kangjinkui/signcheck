from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://adjudge:adjudge@localhost:5432/adjudge"
)

# asyncpg는 URL의 sslmode= 파라미터를 지원하지 않아 connect_args로 분리 처리
_connect_args = {}
_url = DATABASE_URL
if "sslmode=require" in _url:
    _url = _url.replace("?sslmode=require", "").replace("&sslmode=require", "")
    _connect_args = {"ssl": "require"}
elif "ssl=require" in _url:
    _url = _url.replace("?ssl=require", "").replace("&ssl=require", "")
    _connect_args = {"ssl": "require"}
# neon.tech 도메인은 항상 SSL 필요
if "neon.tech" in _url and not _connect_args:
    _connect_args = {"ssl": "require"}

engine = create_async_engine(_url, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

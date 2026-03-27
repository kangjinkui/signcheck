from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://adjudge:adjudge@localhost:5432/adjudge"
)

# asyncpg는 sslmode/channel_binding 쿼리 파라미터를 직접 받지 않으므로 분리 처리
_connect_args = {}
_parts = urlsplit(DATABASE_URL)
_query_pairs = []
for key, value in parse_qsl(_parts.query, keep_blank_values=True):
    if key in {"sslmode", "ssl"} and value == "require":
        _connect_args = {"ssl": "require"}
        continue
    if key == "channel_binding":
        continue
    _query_pairs.append((key, value))

_url = urlunsplit((
    _parts.scheme,
    _parts.netloc,
    _parts.path,
    urlencode(_query_pairs),
    _parts.fragment,
))

# neon.tech 도메인은 항상 SSL 필요
if "neon.tech" in _parts.netloc and not _connect_args:
    _connect_args = {"ssl": "require"}

engine = create_async_engine(_url, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

import os

from urllib.parse import urlunsplit

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


def get_pg_uri(
        username=os.environ.get('POSTGRES_USER', 'z1kurat'),
        password=os.environ.get('POSTGRES_PASSWORD', 'example'),
        host=os.environ.get('DB_HOST', 'db'), #localhost
        port=int(os.environ.get('DB_PORT', 5432)),
        db=os.environ.get('POSTGRES_DB', 'bots'),
        protocol=os.environ.get('DB_PROTOCOL', 'postgresql+asyncpg'),
        uri_query=str()
):
    return urlunsplit((protocol, f'{username}:{password}@{host}:{port}', db, uri_query, str()))


async_engine = create_async_engine(get_pg_uri())

async_session = async_sessionmaker(async_engine, expire_on_commit=False)
async_session_noauto = async_sessionmaker(async_engine, autocommit=False, autoflush=False, expire_on_commit=False)

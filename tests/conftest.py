import os

os.environ.setdefault('ENV', 'test')

import asyncio
from asgi_lifespan import LifespanManager

import pytest
from httpx import AsyncClient
from httpx import ASGITransport

from setting import setting

pytestmark = pytest.mark.asyncio(scope="module")


@pytest.fixture(scope='session', autouse=True)
def event_loop():
    """
    Create an instance of the default event loop for the session.
    Make sure all tests use the same event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def client(event_loop):
    from app import app
    async with LifespanManager(app) as manager:
        async with AsyncClient(
                app=app,
                transport=ASGITransport(app=manager.app)) as c:
            yield c


@pytest.fixture(scope='function', autouse=True)
async def session(event_loop):
    from core.db import is_memory_engine, engine, Base, async_session
    from tests.db_init import init_all

    if is_memory_engine:
        async with engine.connect() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with async_session() as _session:
            await init_all(_session)
            yield _session
        async with engine.connect() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    else:
        async with async_session() as _session:
            yield _session


@pytest.fixture
async def token(client):
    response = await client.post(
        'http://127.0.0.1/login',
        json=dict(
            username='admin',
            password=setting.admin_password))
    response_data = response.json()
    yield response_data['token']


@pytest.fixture
def auth_header(token):
    return dict(authorization='bearer ' + token)

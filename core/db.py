from functools import wraps
from typing import Tuple, Sequence, Any
from datetime import datetime

from sqlalchemy import MetaData, select, func, String, and_, VARCHAR
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.pool import StaticPool

from setting import setting

engine: AsyncEngine
is_memory_engine = setting.database_uri == 'sqlite+aiosqlite://'
is_sqlite_engine = 'sqlite' in setting.database_uri
engine_config = {
    'echo': setting.database_print_sql
}
# memory engine (for test)
if is_sqlite_engine:
    engine_config['connect_args'] = {
        'check_same_thread': False
    }
    engine_config['poolclass'] = StaticPool
else:
    engine_config['pool_recycle'] = 1800

engine = create_async_engine(setting.database_uri, **engine_config)
async_session = async_sessionmaker(engine, expire_on_commit=False)
metadata = MetaData()


class Base(AsyncAttrs, DeclarativeBase):
    pass


class TimeBaseMixin:
    create_time: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False, index=True)
    update_time: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=True)


class OperatorBaseMixin:
    create_by: Mapped[str] = mapped_column(VARCHAR(64), nullable=False, index=True)
    update_by: Mapped[str] = mapped_column(VARCHAR(64), nullable=True)


class RemarkBaseMixin:
    remark: Mapped[str] = mapped_column(VARCHAR(500), default='')


class LogicDeleteBaseMixin:
    del_flag: Mapped[str] = mapped_column(String(1), nullable=False, default='0',
                                          comment='删除标志（0代表存在 2代表删除）')


class CoreBaseMixin(TimeBaseMixin, OperatorBaseMixin, LogicDeleteBaseMixin):
    pass


async def get_list_and_total(stmt, page_number: int, page_size: int,
                             session: AsyncSession) -> Tuple[Sequence[Row], int]:
    offset = (page_number - 1) * page_size
    count_stmt = select(func.count()).select_from(stmt)
    count = await session.scalar(count_stmt)
    select_stmt = stmt.offset(offset).limit(page_size)
    records = (await session.scalars(select_stmt)).fetchall()
    return records, count


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


def transactional(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = kwargs.get('session')
        if session is None:
            raise ValueError("Session is required")

        if session.in_transaction():
            return await func(*args, **kwargs)
        else:
            async with session.begin():
                return await func(*args, **kwargs)

    return wrapper


def to_camel(string: str) -> str:
    parts = string.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


async def assert_key_unique(model: type[Base], key: str, value: Any, session, id=None, id_key: str = 'id',
                            use_del_flag: bool = True, error_message: str = None):
    stmt = select(func.count()).where(and_(getattr(model, key) == value))
    if use_del_flag:
        stmt = stmt.where(getattr(model, 'del_flag') == '0')
    if id is not None:
        stmt = stmt.where(and_(getattr(model, id_key) != id))
    count = (await session.execute(stmt)).scalar()
    if count > 0:
        if error_message:
            raise ValueError(error_message)
        else:
            raise ValueError(f'{key} 已经存在')

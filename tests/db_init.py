import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

init_sql_list = None


def get_init_sql_list():
    global init_sql_list
    if init_sql_list is None:
        file_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(file_dir, 'init.sql'), 'r', encoding='utf8') as f:
            init_sql_list = [text(l.strip()) for l in f if l.strip()]
    return init_sql_list


async def init_all(session: AsyncSession):
    """初始化所有数据"""
    for sql in get_init_sql_list():
        await session.execute(sql)
    await session.commit()

from typing import List, Tuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from core.exception import ApiException
from core.schema import ResponseCode, PageParams, make_optional_dto
from core.db import get_list_and_total, assert_key_unique
from core.redis import redis, clear_cache_by_namespace
from .table import SysConfig

CACHE_NAMESPACE = 'sys_config'
SysConfigDTO = make_optional_dto(SysConfig)


async def find_page(params: SysConfigDTO, page: PageParams,
                    session: AsyncSession) -> Tuple[List[SysConfigDTO], int]:
    stmt = select(SysConfig)
    if params.config_name:
        stmt = stmt.where(SysConfig.config_name.like('%' + params.config_name + '%'))
    if params.config_key:
        stmt = stmt.where(SysConfig.config_key == params.config_key)
    if params.config_type:
        stmt = stmt.where(SysConfig.config_type == params.config_type)
    records, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)
    return [SysConfigDTO.model_validate(user, from_attributes=True) for user in records], total


async def find_by_id(id, session) -> SysConfigDTO:
    e = await session.get(SysConfig, id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    return SysConfigDTO.model_validate(e, from_attributes=True)


async def create(form: SysConfigDTO, operator_id: int, session: AsyncSession) -> int:
    await assert_key_unique(model=SysConfig, key='config_key', value=form.config_key, session=session,
                            error_message='参数键名已存在', use_del_flag=False)
    e = SysConfig(**form.model_dump(), create_by=operator_id)
    session.add(e)
    await session.flush()

    return e.config_id


async def update(form: SysConfigDTO, operator_id: int, session: AsyncSession) -> None:
    await assert_key_unique(model=SysConfig, key='config_key', value=form.config_key, session=session,
                            error_message='参数键名已存在', id_key='config_id', id=form.config_id, use_del_flag=False)
    e = await session.get(SysConfig, form.config_id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    for key, value in form.model_dump(exclude={'config_id'}).items():
        setattr(e, key, value)
    e.update_by = operator_id


async def delete_by_ids(ids: str, session: AsyncSession) -> None:
    id_list = [int(i) for i in ids.split(",")]
    stmt = delete(SysConfig).where(SysConfig.config_id.in_(id_list))
    await session.execute(stmt)


async def get_config_key(config_key: str, session: AsyncSession) -> Optional[str]:
    cache_key = f'{CACHE_NAMESPACE}:get_config_key:{config_key}'
    cache_value = await redis.get(cache_key)
    if cache_value:
        return cache_value

    stmt = select(SysConfig).where(and_(SysConfig.config_key == config_key))
    e = (await session.scalars(stmt)).one_or_none()
    if e is not None:
        await redis.set(cache_key, e.config_value)
        return e.config_value
    else:
        return None


async def clear_cache():
    await clear_cache_by_namespace(CACHE_NAMESPACE)

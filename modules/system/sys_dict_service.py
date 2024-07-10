import json
from typing import List, Tuple

from sqlalchemy import select, asc, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.schema import PageParams, make_optional_dto
from core.db import get_list_and_total, assert_key_unique
from core.redis import redis, clear_cache_by_namespace
from .table import SysDictType, SysDictData

REDIS_NAMESPACE = 'sys_dict'
SysDictTypeDTO = make_optional_dto(SysDictType, exclude_fields=['create_by', 'update_by', 'update_time', 'del_flag'])
SysDictDataDTO = make_optional_dto(SysDictData)


async def find_all_dict_type(session: AsyncSession) -> List[SysDictTypeDTO]:
    stmt = select(SysDictType)
    return [SysDictTypeDTO.model_validate(r, from_attributes=True) for r in (await session.execute(stmt)).fetchall()]


async def find_dict_type_page(params, page: PageParams, session: AsyncSession) -> Tuple[List[SysDictTypeDTO], int]:
    stmt = select(SysDictType)
    for key in params.keys():
        if key == 'dictName':
            stmt = stmt.where(SysDictType.dict_name.like(f'%{params[key]}%'))
        elif key == 'dictType':
            stmt = stmt.where(SysDictType.dict_type == params[key])
        elif key == 'status':
            stmt = stmt.where(SysDictType.status == params[key])
    rows, total = await get_list_and_total(stmt, page.page_num, page.page_size, session=session)
    return [SysDictTypeDTO.model_validate(row, from_attributes=True) for row in rows], total


async def find_dict_type_by_id(id: int, session: AsyncSession) -> SysDictTypeDTO:
    entity = await session.get(SysDictType, id)
    return SysDictTypeDTO.model_validate(entity, from_attributes=True)


async def create_dict_type(form: SysDictTypeDTO, operator: int, session: AsyncSession):
    await assert_key_unique(
        model=SysDictType,
        key='dict_type',
        value=form.dict_type,
        session=session,
        error_message='字典类型已存在',
        use_del_flag=False)
    e = SysDictType(**form.model_dump(exclude={'create_time'}))
    e.create_by = operator
    session.add(e)
    await session.flush()

    await clear_cache_by_namespace(REDIS_NAMESPACE)


async def update_dict_type(form: SysDictTypeDTO, operator_id: int, session: AsyncSession):
    await assert_key_unique(
        model=SysDictType,
        key='dict_type',
        value=form.dict_type,
        session=session,
        id_key='dict_id',
        id=form.dict_id,
        error_message='字典类型已存在',
        use_del_flag=False)
    e = await session.get(SysDictType, form.dict_id)
    for key, value in form.model_dump(exclude={'dict_id', 'create_time'}).items():
        setattr(e, key, value)
    e.update_by = operator_id
    await session.flush()

    await clear_cache_by_namespace(REDIS_NAMESPACE)


async def delete_dict_type_by_id_list(id_list: List[int], session: AsyncSession):
    stmt = delete(SysDictType).where(SysDictType.dict_id.in_(id_list))
    await session.execute(stmt)

    await clear_cache_by_namespace(REDIS_NAMESPACE)


async def clear_dict_cache():
    await clear_cache_by_namespace(REDIS_NAMESPACE)


async def find_dict_data_page(params: SysDictDataDTO, page: PageParams,
                              session: AsyncSession) -> Tuple[List[SysDictDataDTO], int]:
    stmt = select(SysDictData)
    if params.dict_label:
        stmt = stmt.where(SysDictData.dict_label.like(f'%{params.dict_label}%'))
    if params.dict_value:
        stmt = stmt.where(SysDictData.dict_value.like(f'%{params.dict_value}%'))
    if params.dict_type:
        stmt = stmt.where(SysDictData.dict_type == params.dict_type)
    stmt = stmt.order_by(asc(SysDictData.dict_sort))
    rows, total = await get_list_and_total(stmt, page.page_num, page.page_size, session=session)
    return [SysDictDataDTO.model_validate(row, from_attributes=True) for row in rows], total


async def find_dict_data_by_id(id: int, session: AsyncSession) -> SysDictDataDTO:
    entity = await session.get(SysDictData, id)
    return SysDictDataDTO.model_validate(entity, from_attributes=True)


async def create_dict_data(form: SysDictDataDTO, operator_id: int, session: AsyncSession):
    e = SysDictData(**form.model_dump())
    e.create_by = operator_id
    session.add(e)
    await session.flush()

    await clear_cache_by_namespace(REDIS_NAMESPACE)


async def update_dict_data(form: SysDictDataDTO, operator_id: int, session: AsyncSession):
    e = await session.get(SysDictData, form.dict_code)
    for key, value in form.model_dump(exclude={'dict_code'}).items():
        setattr(e, key, value)
    e.update_by = operator_id
    await session.flush()

    await clear_cache_by_namespace(REDIS_NAMESPACE)


async def delete_dict_data_by_id_list(id_list: List[int], session: AsyncSession):
    stmt = delete(SysDictData).where(SysDictData.dict_code.in_(id_list))
    await session.execute(stmt)

    await clear_cache_by_namespace(REDIS_NAMESPACE)


async def find_dict_data_by_type(dict_type: str, session: AsyncSession) -> List[SysDictDataDTO]:
    cache_key = f'{REDIS_NAMESPACE}:find_dict_data_by_type:{dict_type}'
    cache_value_str = await redis.get(cache_key)
    if cache_value_str:
        data_list = json.loads(cache_value_str)
        return [SysDictDataDTO.model_validate(item) for item in data_list]

    stmt = select(SysDictData).where(and_(
        SysDictData.dict_type == dict_type
    ))
    stmt = stmt.order_by(asc(SysDictData.dict_sort))
    records = (await session.scalars(stmt)).fetchall()
    result_list = [SysDictDataDTO.model_validate(item, from_attributes=True) for item in records]

    data_list = [item.model_dump() for item in result_list]
    await redis.set(cache_key, json.dumps(data_list), ex=3600)

    return result_list

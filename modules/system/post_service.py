from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from core.exception import ApiException
from core.schema import ResponseCode, PageParams, make_optional_dto
from core.db import get_list_and_total, assert_key_unique

from .table import SysPost, SysUserPost

SysPostDTO = make_optional_dto(SysPost)


async def find_post_page(params: SysPostDTO, page: PageParams,
                         session: AsyncSession) -> Tuple[List[SysPostDTO], int]:
    stmt = select(SysPost)
    if params.post_name:
        stmt = stmt.where(SysPost.post_name.like('%' + params.post_name + '%'))
    records, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)
    return [SysPostDTO.model_validate(user, from_attributes=True) for user in records], total


async def find_all(session: AsyncSession) -> List[SysPostDTO]:
    stmt = select(SysPost)
    records = (await session.scalars(stmt)).fetchall()
    return [SysPostDTO.model_validate(e, from_attributes=True) for e in records]


async def find_post_by_id(id, session) -> SysPostDTO:
    e = await session.get(SysPost, id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    return SysPostDTO.model_validate(e, from_attributes=True)


async def create_post(form: SysPostDTO, operator_id: int, session: AsyncSession) -> id:
    await assert_key_unique(model=SysPost, key='post_name', value=form.post_name, session=session,
                            error_message='名称已存在', use_del_flag=False)
    await assert_key_unique(model=SysPost, key='post_code', value=form.post_code, session=session,
                            error_message='编码已存在', use_del_flag=False)
    e = SysPost(**form.model_dump(), create_by=operator_id)
    session.add(e)
    await session.flush()

    return e.post_id


async def update_post(form: SysPostDTO, operator_id: int, session: AsyncSession) -> None:
    e = await session.get(SysPost, form.post_id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    await assert_key_unique(model=SysPost, key='post_name', value=form.post_name, session=session,
                            id_key='post_id', id=form.post_id, error_message='名称已存在', use_del_flag=False)
    await assert_key_unique(model=SysPost, key='post_code', value=form.post_code, session=session,
                            id_key='post_id', id=form.post_id, error_message='编码已存在', use_del_flag=False)
    for key, value in form.model_dump(exclude={'post_id'}).items():
        setattr(e, key, value)
    e.update_by = operator_id


async def delete_post_by_ids(ids: str, session: AsyncSession) -> None:
    id_list = [int(i) for i in ids.split(",")]
    stmt = delete(SysPost).where(SysPost.post_id.in_(id_list))
    await session.execute(stmt)


async def find_by_user_id(user_id: int, session: AsyncSession) -> List[SysPostDTO]:
    stmt = select(SysPost).where(and_(
        SysUserPost.post_id == SysPost.post_id,
        SysUserPost.user_id == user_id
    ))
    entity_list = (await session.scalars(stmt)).fetchall()
    return [SysPostDTO.model_validate(e, from_attributes=True) for e in entity_list]


async def add_test_post_data(session) -> List[SysPost]:
    await session.execute(delete(SysPost))

    entity_list = [
        SysPost(post_name='职位1', post_code='1', create_by=1),
        SysPost(post_name='职位2', post_code='2', create_by=1)
    ]
    session.add_all(entity_list)
    await session.flush()

    return entity_list

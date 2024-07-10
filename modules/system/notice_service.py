from typing import List, Tuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    select,
    delete
)

from core.exception import ApiException
from core.schema import ResponseCode, PageParams, make_optional_dto
from core.db import get_list_and_total

from .table import SysNotice

SysNoticeDTO = make_optional_dto(SysNotice)


async def find_page(params: SysNoticeDTO, page: PageParams,
                    session: AsyncSession) -> Tuple[List[SysNoticeDTO], int]:
    stmt = select(SysNotice)
    if params.notice_title:
        stmt = stmt.where(SysNotice.notice_title.like('%' + params.notice_title + '%'))
    if params.notice_type:
        stmt = stmt.where(SysNotice.notice_type == params.notice_type)
    if params.status:
        stmt = stmt.where(SysNotice.status == params.status)
    records, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)
    return [SysNoticeDTO.model_validate(user, from_attributes=True) for user in records], total


async def find_by_id(id, session) -> SysNoticeDTO:
    e = await session.get(SysNotice, id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    return SysNoticeDTO.model_validate(e, from_attributes=True)


async def create(form: SysNoticeDTO, operator_id: int, session: AsyncSession) -> int:
    e = SysNotice(**form.model_dump(), create_by=operator_id)
    session.add(e)
    await session.flush()

    return e.notice_id


async def update(form: SysNoticeDTO, operator_id: int, session: AsyncSession) -> None:
    e = await session.get(SysNotice, form.notice_id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    for key, value in form.model_dump(exclude={'notice_id'}).items():
        setattr(e, key, value)
    e.update_by = operator_id


async def delete_by_ids(ids: str, session: AsyncSession) -> None:
    id_list = [int(i) for i in ids.split(",")]
    stmt = delete(SysNotice).where(SysNotice.notice_id.in_(id_list))
    await session.execute(stmt)

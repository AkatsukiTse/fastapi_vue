from fastapi import APIRouter, Depends

from core.depends import (
    Session,
    CurrentUserId,
    login_required
)
from core.schema import PageParams, BaseResponse, TableDataInfo
from modules.system.notice_service import (SysNoticeDTO, create, find_page, update, delete_by_ids, find_by_id)

api = APIRouter(prefix='/system/notice', dependencies=[login_required])


@api.get('/list')
async def find_page_endpoint(session: Session, page: PageParams, params: SysNoticeDTO = Depends()):
    rows, total = await find_page(params, page, session)
    return TableDataInfo(rows=rows, total=total)


@api.get('/{id}')
async def find_by_id_endpoint(id: int, session: Session):
    return BaseResponse(data=await find_by_id(id, session))


@api.post('')
async def create_endpoint(form: SysNoticeDTO, user_id: CurrentUserId, session: Session):
    await create(form, user_id, session=session)
    await session.commit()
    return BaseResponse(msg='创建成功')


@api.put('')
async def update_endpoint(dto: SysNoticeDTO, user_id: CurrentUserId, session: Session):
    await update(dto, user_id, session)
    await session.commit()
    return BaseResponse(msg='编辑成功')


@api.delete('/{ids}')
async def delete_endpoint(ids: str, session: Session):
    await delete_by_ids(ids, session)
    await session.commit()
    return BaseResponse(msg='删除成功')

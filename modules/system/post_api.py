from fastapi import APIRouter, Depends

from core.depends import (
    Session,
    CurrentUserId,
    login_required
)

from core.schema import PageParams, BaseResponse, TableDataInfo

from modules.system.post_service import (SysPostDTO, create_post, find_post_page, find_all,
                                         update_post, delete_post_by_ids, find_post_by_id)

api = APIRouter(prefix='/system/post', dependencies=[login_required])


@api.get('/list')
async def find_post_page_endpoint(session: Session, page: PageParams, params: SysPostDTO = Depends()):
    rows, total = await find_post_page(params, page, session)
    return TableDataInfo(rows=rows, total=total)


@api.get('/{id}')
async def find_post_by_id_endpoint(id: int, session: Session):
    return BaseResponse(data=await find_post_by_id(id, session))


@api.post('')
async def create_post_endpoint(form: SysPostDTO, user_id: CurrentUserId, session: Session):
    await create_post(form, user_id, session=session)
    await session.commit()
    return BaseResponse(msg='创建成功')


@api.put('')
async def update_post_endpoint(dto: SysPostDTO, user_id: CurrentUserId, session: Session):
    await update_post(dto, user_id, session)
    await session.commit()
    return BaseResponse(msg='编辑成功')


@api.delete('/{ids}')
async def delete_post_endpoint(ids: str, session: Session):
    await delete_post_by_ids(ids, session)
    await session.commit()
    return BaseResponse(msg='删除成功')


@api.get('/optionselect')
async def find_all_post_endpoint(session: Session):
    return BaseResponse(data=await find_all(session))

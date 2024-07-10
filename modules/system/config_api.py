from fastapi import APIRouter, Depends

from core.depends import (
    Session,
    CurrentUserId,
    login_required
)
from core.schema import PageParams, BaseResponse, TableDataInfo
from modules.system.config_service import (SysConfigDTO, create, find_page, update, delete_by_ids, find_by_id,
                                           get_config_key, clear_cache)

api = APIRouter(prefix='/system/config', dependencies=[login_required])


@api.get('/list')
async def find_page_endpoint(session: Session, page: PageParams, params: SysConfigDTO = Depends()):
    rows, total = await find_page(params, page, session)
    return TableDataInfo(rows=rows, total=total)


@api.get('/{id}')
async def find_by_id_endpoint(id: int, session: Session):
    return BaseResponse(data=await find_by_id(id, session))


@api.get('/configKey/{configKey}')
async def get_config_key_endpoint(configKey: str, session: Session):
    return BaseResponse(data=await get_config_key(config_key=configKey, session=session))


@api.post('')
async def create_endpoint(form: SysConfigDTO, user_id: CurrentUserId, session: Session):
    await create(form, user_id, session=session)
    await session.commit()
    return BaseResponse(msg='创建成功')


@api.put('')
async def update_endpoint(dto: SysConfigDTO, user_id: CurrentUserId, session: Session):
    await update(dto, user_id, session)
    await session.commit()
    return BaseResponse(msg='编辑成功')


@api.delete('/{ids}')
async def delete_endpoint(ids: str, session: Session):
    await delete_by_ids(ids, session)
    await session.commit()
    return BaseResponse(msg='删除成功')


@api.delete('/refreshCache')
async def refresh_cache_endpoint():
    await clear_cache()
    return BaseResponse(msg='刷新成功')

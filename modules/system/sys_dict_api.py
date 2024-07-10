from fastapi import Depends, APIRouter, Request

from core.depends import CurrentUserId, Session, login_required
from core.schema import BaseResponse, TableDataInfo, PageParams
from .sys_dict_service import SysDictTypeDTO, SysDictDataDTO
from . import sys_dict_service

api = APIRouter(dependencies=[login_required])


@api.get('/system/dict/type/list')
async def find_dict_type_endpoint(session: Session, page: PageParams, request: Request):
    dict_type_list, total = await sys_dict_service.find_dict_type_page(request.query_params, page, session)
    return TableDataInfo(rows=dict_type_list, total=total)


@api.post('/system/dict/type')
async def create_dict_type_endpoint(form: SysDictTypeDTO, user_id: CurrentUserId, session: Session):
    await sys_dict_service.create_dict_type(form, user_id, session)
    await session.commit()
    return BaseResponse(msg='创建成功')


@api.put('/system/dict/type')
async def update_dict_type_endpoint(form: SysDictTypeDTO, user_id: CurrentUserId, session: Session):
    await sys_dict_service.update_dict_type(form, user_id, session)
    await session.commit()
    return BaseResponse()


@api.delete('/system/dict/type/{dictIds}')
async def delete_dict_type_by_dict_ids_endpoint(dictIds: str, session: Session):
    id_list = [int(s) for s in dictIds.split(',')]
    await sys_dict_service.delete_dict_type_by_id_list(id_list, session)
    await session.commit()
    return BaseResponse()


@api.delete('/system/dict/type/refreshCache')
async def refresh_cache_endpoint():
    await sys_dict_service.clear_dict_cache()
    return BaseResponse()


@api.get('/system/dict/type/optionselect')
async def find_dict_type_option_select_endpoint(session: Session):
    return BaseResponse(data=await sys_dict_service.find_all_dict_type(session))


@api.get('/system/dict/type/{dictId}')
async def get_dict_type_endpoint(dictId: int, session: Session):
    return BaseResponse(data=await sys_dict_service.find_dict_type_by_id(dictId, session))


@api.get('/system/dict/data/list')
async def find_dict_data_page_endpoint(session: Session, page: PageParams, params: SysDictDataDTO = Depends()):
    dict_data_list, total = await sys_dict_service.find_dict_data_page(params, page, session)
    return TableDataInfo(rows=dict_data_list, total=total)


@api.get('/system/dict/data/type/{dictType}')
async def get_dict_data_endpoint(dictType: str, session: Session):
    return BaseResponse(data=await sys_dict_service.find_dict_data_by_type(dictType, session))


@api.post('/system/dict/data')
async def create_dict_data_endpoint(form: SysDictDataDTO, user_id: CurrentUserId, session: Session):
    await sys_dict_service.create_dict_data(form, user_id, session)
    await session.commit()
    return BaseResponse(msg='创建成功')


@api.put('/system/dict/data')
async def update_dict_data_endpoint(form: SysDictDataDTO, user_id: CurrentUserId, session: Session):
    await sys_dict_service.update_dict_data(form, user_id, session)
    await session.commit()
    return BaseResponse()


@api.delete('/system/dict/data/{dictCodes}')
async def delete_dict_data_by_dict_codes_endpoint(dictCodes: str, session: Session):
    id_list = [int(s) for s in dictCodes.split(',')]
    await sys_dict_service.delete_dict_data_by_id_list(id_list, session)
    await session.commit()
    return BaseResponse()


@api.get('/system/dict/data/{dictCode}')
async def get_dict_data_endpoint(dictCode: int, session: Session):
    return BaseResponse(data=await sys_dict_service.find_dict_data_by_id(dictCode, session))

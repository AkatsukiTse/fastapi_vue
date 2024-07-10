from fastapi import APIRouter, Depends, Request

from core.depends import (
    Session,
    CurrentUserId,
    login_required
)
from core.schema import BaseResponse, TreeSelect
from modules.system.menu_service import (SysMenuDTO, create, find_page, update, delete_by_ids, find_by_id,
                                         find_menu_list_by_user_id, find_menu_list_by_role_id, SysMenuQueryDTO,
                                         find_all_menu)

api = APIRouter(prefix='/system/menu', dependencies=[login_required])


@api.get('/list')
async def find_page_endpoint(session: Session, request: Request):
    params = request.query_params
    rows = await find_all_menu(params, session)
    return BaseResponse(data=rows)


@api.get('/treeselect')
async def find_tree_select(user_id: CurrentUserId, session: Session, dto: SysMenuQueryDTO = Depends()):
    menu_list = await find_menu_list_by_user_id(dto, user_id, session)
    tree_list = TreeSelect.build_tree(
        data_list=menu_list,
        id_key='menu_id',
        label_key='menu_name'
    )
    return BaseResponse(data=tree_list)


class RoleMenuTreeSelectDTO(BaseResponse):
    menus: list
    checked_keys: list


@api.get('/roleMenuTreeselect/{roleId}')
async def role_menu_tree_select(roleId: int, user_id: CurrentUserId, session: Session):
    menu_list = await find_menu_list_by_user_id(SysMenuQueryDTO(status='0'), user_id, session)
    tree_list = TreeSelect.build_tree(
        data_list=menu_list,
        id_key='menu_id',
        label_key='menu_name'
    )
    menus = tree_list

    menu_list_2 = await find_menu_list_by_role_id(roleId, session)
    checked_keys = [menu.menu_id for menu in menu_list_2]

    return RoleMenuTreeSelectDTO(menus=menus, checked_keys=checked_keys)


@api.post('')
async def create_endpoint(form: SysMenuDTO, user_id: CurrentUserId, session: Session):
    await create(form, user_id, session=session)
    await session.commit()
    return BaseResponse(msg='创建成功')


@api.put('')
async def update_endpoint(dto: SysMenuDTO, user_id: CurrentUserId, session: Session):
    await update(dto, user_id, session)
    await session.commit()
    return BaseResponse(msg='编辑成功')


@api.delete('/{ids}')
async def delete_endpoint(ids: str, session: Session):
    await delete_by_ids(ids, session)
    await session.commit()
    return BaseResponse(msg='删除成功')


@api.get('/{id}')
async def find_by_id_endpoint(id: int, session: Session):
    return BaseResponse(data=await find_by_id(id, session))

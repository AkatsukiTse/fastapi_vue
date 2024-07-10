from fastapi import APIRouter, Depends

from core.exception import ApiException
from core.depends import Session, CurrentUserId, login_required

from core.schema import PageParams, BaseResponse, TableDataInfo, ResponseCode

from modules.system.role_service import (SysRoleQueryDTO, SysRoleDTO, create_role, find_role_page,
                                         update_role, delete_role_by_ids, find_role_by_id, SysRoleChangeStatusDTO,
                                         update_role_status, refresh_role_dept_list, find_all, unbind_users, bind_users)

from modules.system import user_service
from modules.system import dept_service

api = APIRouter(prefix='/system/role', dependencies=[login_required])


@api.get('/list')
async def find_role_page_endpoint(session: Session, page: PageParams, params: SysRoleQueryDTO = Depends()):
    rows, total = await find_role_page(params, page, session)
    return TableDataInfo(rows=rows, total=total)


@api.get('/{id}')
async def find_role_by_id_endpoint(id: int, session: Session):
    role = await find_role_by_id(id, session)
    return BaseResponse(data=role)


@api.post('')
async def create_role_endpoint(form: SysRoleDTO, user_id: CurrentUserId, session: Session):
    await create_role(form, user_id, session=session)
    await session.commit()
    return BaseResponse(msg='创建角色成功')


@api.put('')
async def update_role_endpoint(dto: SysRoleDTO, user_id: CurrentUserId, session: Session):
    if dto.role_id is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '角色ID不能为空')
    await update_role(dto, user_id, session)
    await session.commit()
    return BaseResponse(msg='编辑角色成功')


@api.put('/dataScope')
async def update_data_scope_endpoint(dto: SysRoleDTO, user_id: CurrentUserId, session: Session):
    await update_role(dto, user_id, session)
    await refresh_role_dept_list(dto.role_id, dto.dept_ids, session)
    await session.commit()
    return BaseResponse()


@api.put('/changeStatus')
async def change_role_status_endpoint(dto: SysRoleChangeStatusDTO, user_id: CurrentUserId, session: Session):
    await update_role_status(dto, user_id, session)
    await session.commit()
    return BaseResponse(msg='操作成功')


@api.delete('/{ids}')
async def delete_role_endpoint(ids: str, user_id: CurrentUserId, session: Session):
    await delete_role_by_ids(ids, user_id, session)
    await session.commit()
    return BaseResponse(msg='删除角色成功')


@api.get('/optionselect')
async def find_option_select_endpoint(session: Session):
    return BaseResponse(data=await find_all(session))


@api.get('/authUser/allocatedList')
async def find_allocated_user_list_endpoint(roleId: int, page: PageParams, session: Session):
    users, total = await user_service.find_page_by_role(roleId, page, session)
    return TableDataInfo(rows=users, total=total)


@api.get('/authUser/unallocatedList')
async def find_unallocated_user_list_endpoint(roleId: int, page: PageParams, session: Session):
    users, total = await user_service.find_page_exclude_role(roleId, page, session)
    return TableDataInfo(rows=users, total=total)


@api.put('/authUser/cancel')
async def cancel_user_role_endpoint(roleId: int, userId: int, session: Session):
    await unbind_users(roleId, [userId], session)
    await session.commit()
    return BaseResponse(msg='取消用户授权成功')


@api.put('/authUser/cancelAll')
async def cancel_all_user_role_endpoint(roleId: int, userIds: str, session: Session):
    user_id_list = [int(user_id) for user_id in userIds.split(',')]
    await unbind_users(roleId, user_id_list, session)
    await session.commit()
    return BaseResponse(msg='取消用户授权成功')


class FindRoleDeptTreeResponse(BaseResponse):
    checked_keys: list
    depts: list


@api.get('/deptTree/{roleId}')
async def find_dept_tree(roleId: int, session: Session):
    dept_list = await dept_service.find_dept_list_by_role_id(roleId, session)
    checked_keys = [dept.dept_id for dept in dept_list]
    depts = await dept_service.select_dept_tree_list({}, session)
    return FindRoleDeptTreeResponse(checked_keys=checked_keys, depts=depts)


@api.put('/authUser/selectAll')
async def add_user_role_endpoint(roleId: int, userIds: str, session: Session):
    user_id_list = [int(user_id) for user_id in userIds.split(',')]
    await bind_users(roleId, user_id_list, session)
    await session.commit()
    return BaseResponse(msg='授权用户成功')

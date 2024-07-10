from typing import List

from fastapi import APIRouter, Depends, Request
from core.depends import CurrentUserId, Session, login_required

from core.schema import PageParams, BaseResponse, TableDataInfo, CamelModel
from modules.system.user_service import (create_user, delete_user_by_ids, reset_user_password, CreateSysUserDTO,
                                         SysUserDTO, UpdateSysUserDTO, SysUserIdDTO, update_user_status, find_user_page,
                                         update_user, get_user_by_id, UserQueryParams, refresh_user_roles)
from modules.system import role_service
from modules.system import post_service
from modules.system import dept_service

api = APIRouter(dependencies=[login_required])
endpoint_prefix = '/system/user'


@api.get(endpoint_prefix + '/list')
async def user_list_endpoint(session: Session, page: PageParams, params: UserQueryParams = Depends()):
    rows, total = await find_user_page(params, page, session=session)
    return TableDataInfo(rows=rows, total=total)


@api.get(endpoint_prefix + '/')
async def get_info_endpoint(session: Session):
    return GetUserResponseDTO(
        roles=await role_service.find_all(session),
        posts=await post_service.find_all(session)
    )


class GetUserResponseDTO(BaseResponse, CamelModel):
    roles: List[role_service.SysRoleDTO] | None = None
    posts: List[post_service.SysPostDTO] | None = None
    role_ids: List[int] | None = None
    post_ids: List[int] | None = None


@api.post(f'{endpoint_prefix}')
async def create_user_endpoint(session: Session, form: CreateSysUserDTO, user_id: CurrentUserId):
    await create_user(form, user_id, session=session)
    await session.commit()
    return BaseResponse(msg='创建用户成功')


@api.put(endpoint_prefix)
async def update_user_endpoint(session: Session, form: UpdateSysUserDTO, user_id: CurrentUserId):
    await update_user(form, user_id, session)
    await session.commit()
    return BaseResponse(msg='修改用户成功')


@api.delete(endpoint_prefix + '/{ids}')
async def delete_user(ids: str, user_id: CurrentUserId, session: Session):
    await delete_user_by_ids(ids, user_id, session)
    await session.commit()
    return BaseResponse(msg='删除用户成功')


@api.put(endpoint_prefix + '/resetPwd')
async def reset_password(dto: SysUserIdDTO, session: Session):
    await reset_user_password(dto.user_id, session)
    return BaseResponse()


class GetUserRoleResponse(BaseResponse):
    user: SysUserDTO
    roles: List[role_service.SysRoleDTO]


@api.get(endpoint_prefix + '/authRole/{user_id}')
async def get_user_role(user_id: int, session: Session):
    return GetUserRoleResponse(
        user=await get_user_by_id(user_id, session=session),
        roles=await role_service.find_by_user_id(user_id, session)
    )


@api.put(endpoint_prefix + '/authRole')
async def auth_role(userId: int, roleIds: str, session: Session):
    role_id_list = []
    if roleIds:
        role_id_list= [int(role_id) for role_id in roleIds.split(",")]
    await refresh_user_roles(userId, role_id_list, session)
    await session.commit()
    return BaseResponse()


class ChangeUserStatusDTO(CamelModel):
    user_id: int
    status: str


@api.put(endpoint_prefix + '/changeStatus')
async def change_status_endpoint(dto: ChangeUserStatusDTO, user_id: CurrentUserId, session: Session):
    await update_user_status(dto.user_id, dto.status, user_id, session)
    await session.commit()
    return BaseResponse()


@api.get(endpoint_prefix + '/deptTree')
async def find_dept_tree_endpoint(session: Session, request: Request):
    return BaseResponse(data=await dept_service.select_dept_tree_list(request, session))


@api.get(endpoint_prefix + '/currentUserDept')
async def get_current_user_dept(user_id: CurrentUserId, session: Session):
    user = await get_user_by_id(user_id, session=session)
    if user.dept_id:
        dept = await dept_service.find_dept_by_id(user.dept_id, session)
        return BaseResponse(data=dept)
    else:
        return BaseResponse(data=None)


@api.get(endpoint_prefix + '/{id}')
async def get_user_endpoint(session: Session, id: int):
    user = await get_user_by_id(id, session=session)
    return GetUserResponseDTO(
        data=user,
        role_ids=[role.role_id for role in await role_service.find_by_user_id(id, session)],
        post_ids=[post.post_id for post in await post_service.find_by_user_id(id, session)],
        roles=await role_service.find_all(session),
        posts=await post_service.find_all(session)
    )

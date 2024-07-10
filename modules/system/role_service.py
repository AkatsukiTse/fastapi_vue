from typing import List, Tuple, Optional, Set
from datetime import datetime

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    select,
    delete,
    func,
    and_
)

from setting import setting
from core.exception import ApiException
from core.schema import ResponseCode, PageParams, CamelModel
from core.db import (
    get_list_and_total,
    transactional
)
from modules.system import menu_service
from .table import SysRole, SysUserRole, SysRoleDept


class SysRoleDTO(CamelModel):
    role_id: Optional[int] = None
    role_name: str
    role_key: str
    role_sort: Optional[int] = None
    data_scope: Optional[str] = None
    menu_check_strictly: Optional[bool] = None
    dept_check_strictly: Optional[bool] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    status: Optional[str] = '0'
    dept_ids: Optional[List[int]] = None
    menu_ids: List[int] | None = None


class SysRoleQueryDTO:
    def __init__(self,
                 role_name: str = Query(None),
                 role_key: str = Query(None)):
        self.role_name = role_name
        self.role_key = role_key


async def find_role_page(params: SysRoleQueryDTO, page: PageParams,
                         session: AsyncSession) -> Tuple[List[SysRoleDTO], int]:
    stmt = select(SysRole).where(SysRole.del_flag == '0')
    if params.role_name:
        stmt = stmt.where(SysRole.role_name.like(f'%{params.role_name}%'))
    if params.role_key:
        stmt = stmt.where(SysRole.role_key == params.role_key)
    records, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)
    return [SysRoleDTO.model_validate(user, from_attributes=True) for user in records], total


async def find_role_by_id(id, session) -> SysRoleDTO:
    e = await session.get(SysRole, id)
    if e is None or e.del_flag != '0':
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    return SysRoleDTO.model_validate(e, from_attributes=True)


@transactional
async def create_role(form: SysRoleDTO, operator_id: int, session: AsyncSession) -> id:
    await assert_role_name_unique(form.role_name, session)
    await assert_role_key_unique(form.role_key, session)

    e = SysRole(**form.model_dump(exclude={'dept_ids', 'menu_ids'}), create_by=operator_id)
    session.add(e)
    await session.flush()

    return e.role_id


async def update_role(form: SysRoleDTO, operator_id: int, session: AsyncSession) -> None:
    e = await session.get(SysRole, form.role_id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    for key, value in form.model_dump(exclude={'role_id', 'dept_ids', 'menu_ids'}).items():
        setattr(e, key, value)
    if form.menu_ids is not None:
        await menu_service.update_role_menus(form.role_id, form.menu_ids, session)
    e.update_by = operator_id


class SysRoleChangeStatusDTO(CamelModel):
    role_id: int
    status: str


async def update_role_status(dto: SysRoleChangeStatusDTO, operator_id: int, session: AsyncSession) -> None:
    e = await session.get(SysRole, dto.role_id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    e.status = dto.status
    e.update_by = operator_id
    await session.flush()


async def delete_role_by_ids(ids: str, operator_id: int, session: AsyncSession) -> None:
    for role_id in ids.split(","):
        e = await session.get(SysRole, int(role_id))
        if e is None:
            raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
        e.del_flag = '2'
        e.update_by = operator_id


async def is_name_unique(name: str, session: AsyncSession, before_id: int = None):
    stmt = select(func.count()).where(SysRole.name == name, SysRole.is_delete == False)
    if before_id is not None:
        stmt = stmt.where(SysRole.id != before_id)
    count = (await session.execute(stmt)).scalar()
    return count == 0


async def find_all(session: AsyncSession) -> List[SysRoleDTO]:
    stmt = select(SysRole).where(SysRole.del_flag == '0')
    return [SysRoleDTO.model_validate(e, from_attributes=True) for e in (await session.scalars(stmt)).fetchall()]


async def assert_role_name_unique(role_name: str, session: AsyncSession, role_id: int = None):
    stmt = select(func.count()).where(and_(SysRole.role_name == role_name, SysRole.del_flag == '0'))
    if id is not None:
        stmt = stmt.where(SysRole.role_id != role_id)
    count = (await session.execute(stmt)).scalar()
    if count > 0:
        raise ApiException(ResponseCode.BAD_REQUEST, '角色名称已存在')


async def assert_role_key_unique(role_key: str, session: AsyncSession, role_id: int = None):
    stmt = select(func.count()).where(and_(SysRole.role_key == role_key, SysRole.del_flag == '0'))
    if id is not None:
        stmt = stmt.where(SysRole.role_id != role_id)
    count = (await session.execute(stmt)).scalar()
    if count > 0:
        raise ApiException(ResponseCode.BAD_REQUEST, '角色Key已存在')


async def find_by_user_id(user_id: int, session: AsyncSession) -> List[SysRoleDTO]:
    stmt = select(SysRole)
    if setting.admin_user_id != user_id:
        stmt = stmt.where(and_(
            SysUserRole.role_id == SysRole.role_id,
            SysUserRole.user_id == user_id,
            SysRole.del_flag == '0'
        ))
    entity_list = (await session.scalars(stmt)).fetchall()
    return [SysRoleDTO.model_validate(e, from_attributes=True) for e in entity_list]


async def find_role_permission_set_by_user_id(user_id: int, session: AsyncSession) -> Set[str]:
    role_list = await find_by_user_id(user_id, session)
    permission_set = set()
    for role in role_list:
        if role.role_key:
            for perm in role.role_key.split(","):
                if perm:
                    permission_set.add(perm)
    return permission_set


async def refresh_role_dept_list(role_id: int, dept_id_list: List[int], session: AsyncSession) -> None:
    await session.execute(delete(SysRoleDept).where(SysRoleDept.role_id == role_id))
    if dept_id_list:
        session.add_all([SysRoleDept(role_id=role_id, dept_id=dept_id) for dept_id in dept_id_list])
    await session.flush()


async def unbind_users(role_id: int, user_id_list: List[int], session: AsyncSession):
    await session.execute(
        delete(SysUserRole).where(and_(SysUserRole.user_id.in_(user_id_list), SysUserRole.role_id == role_id)))
    await session.flush()


async def bind_users(role_id: int, user_id_list: List[int], session: AsyncSession):
    session.add_all([SysUserRole(user_id=user_id, role_id=role_id) for user_id in user_id_list])
    await session.flush()

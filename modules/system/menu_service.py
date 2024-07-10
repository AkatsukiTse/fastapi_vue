from typing import List, Tuple, Set, Optional
from datetime import datetime

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    Select,
    select,
    delete,
    and_
)

from core.exception import ApiException
from core.schema import ResponseCode, PageParams, CamelModel, AutoString, make_query_dto
from core.db import get_list_and_total, assert_key_unique

from .table import SysMenu, SysRoleMenu, SysUserRole, SysRole


class SysMenuDTO(CamelModel):
    menu_id: int | None = None
    parent_id: int | None = None
    menu_name: str | None = None
    order_num: int | None = None
    path: str | None = None
    component: str | None = None
    perms: str | None = None
    icon: str | None = None
    is_frame: AutoString | None = None
    is_cache: AutoString | None = None
    menu_type: str | None = None
    query: str | None = None
    visible: str | None = None
    status: str | None = None
    create_time: datetime | None = None
    update_time: datetime | None = None
    create_by: str | None = None
    update_by: str | None = None
    children: List['SysMenuDTO'] | None = None


class SysMenuQueryDTO:
    def __init__(self,
                 menu_name: str = '',
                 status: str = '',
                 menu_type_list: List[str] = None):
        self.menu_name = menu_name
        self.status = status
        self.menu_type_list = menu_type_list


def build_query_stmt(params: dict) -> Select:
    stmt = select(SysMenu)
    for key in params.keys():
        if key == 'menuName':
            stmt = stmt.where(SysMenu.menu_name.like('%' + params[key] + '%'))
        elif key == 'parent_id':
            stmt = stmt.where(SysMenu.parent_id == params[key])
        elif key == 'status':
            stmt = stmt.where(SysMenu.status == params[key])
    return stmt


async def find_page(params: SysMenuDTO, page: PageParams,
                    session: AsyncSession) -> Tuple[List[SysMenuDTO], int]:
    stmt = select(SysMenu)
    if params.menu_name:
        stmt = stmt.where(SysMenu.menu_name.like('%' + params.menu_name + '%'))
    if params.parent_id:
        stmt = stmt.where(SysMenu.parent_id == params.parent_id)
    if params.status:
        stmt = stmt.where(SysMenu.status == params.status)
    records, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)
    return [SysMenuDTO.model_validate(user, from_attributes=True) for user in records], total


async def find_all_menu(params, session: AsyncSession) -> List[SysMenuDTO]:
    stmt = build_query_stmt(params)
    records = (await session.scalars(stmt)).fetchall()
    return [SysMenuDTO.model_validate(user, from_attributes=True) for user in records]


async def find_by_id(id, session) -> SysMenuDTO:
    e = await session.get(SysMenu, id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    return SysMenuDTO.model_validate(e, from_attributes=True)


async def create(form: SysMenuDTO, operator_id: int, session: AsyncSession) -> int:
    await assert_key_unique(model=SysMenu, key='menu_name', value=form.menu_name, session=session,
                            error_message='菜单名称已存在', use_del_flag=False)
    e = SysMenu(**form.model_dump(exclude={'create_by', 'children'}), create_by=operator_id)
    session.add(e)
    await session.flush()

    return e.menu_id


async def update(form: SysMenuDTO, operator_id: int, session: AsyncSession) -> None:
    await assert_key_unique(model=SysMenu, key='menu_name', value=form.menu_name, session=session,
                            error_message='菜单名称已存在', id_key='menu_id', id=form.menu_id, use_del_flag=False)
    if form.menu_id == form.parent_id:
        raise ApiException(ResponseCode.BAD_REQUEST, '菜单不能设置为自己的子菜单')
    e = await session.get(SysMenu, form.menu_id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    for key, value in form.model_dump(exclude={'menu_id'}).items():
        setattr(e, key, value)
    e.update_by = operator_id


async def delete_by_ids(ids: str, session: AsyncSession) -> None:
    dept_id_list = [int(dept_id) for dept_id in ids.split(',')]
    stmt = delete(SysMenu).where(and_(SysMenu.menu_id.in_(dept_id_list)))
    await session.execute(stmt)


SysMenuQueryDTO = make_query_dto('menu_name', 'status', 'menu_type_list')


async def find_menu_list_by_user_id(dto: SysMenuQueryDTO, user_id: int, session: AsyncSession) -> List[SysMenuDTO]:
    stmt = select(SysMenu)
    # 如果是超级管理员，不过滤菜单
    if user_id != 1:
        stmt = stmt.where(and_(
            SysMenu.menu_id.in_(
                select(SysRoleMenu.menu_id).where(
                    and_(
                        SysRoleMenu.role_id == SysRole.role_id,
                        SysRole.del_flag == '0',
                        SysUserRole.role_id == SysRole.role_id,
                        SysUserRole.user_id == user_id,
                    )
                )
            )
        ))
    if dto.menu_name:
        stmt = stmt.where(SysMenu.menu_name.like('%' + dto.menu_name + '%'))
    if dto.status:
        stmt = stmt.where(and_(SysMenu.status == dto.status))
    if dto.menu_type_list:
        stmt = stmt.where(SysMenu.menu_type.in_(dto.menu_type_list))
    stmt = stmt.order_by(SysMenu.parent_id, SysMenu.order_num)
    records = (await session.scalars(stmt)).fetchall()
    return [SysMenuDTO.model_validate(user, from_attributes=True) for user in records]


async def find_menu_permission_set_by_user_id(user_id: int, session: AsyncSession) -> Set[str]:
    menu_list = await find_menu_list_by_user_id(SysMenuQueryDTO(status='0'), user_id, session)
    permission_set = set()
    for menu in menu_list:
        if menu.perms:
            for perm in menu.perms.split(','):
                if perm:
                    permission_set.add(perm)
    return permission_set


async def find_menu_list_by_role_id(role_id: int, session: AsyncSession) -> List[SysMenuDTO]:
    stmt = select(SysMenu).where(and_(
        SysMenu.menu_id == SysRoleMenu.menu_id,
        SysRoleMenu.role_id == role_id
    ))
    records = (await session.scalars(stmt)).fetchall()
    return [SysMenuDTO.model_validate(user, from_attributes=True) for user in records]


async def update_role_menus(role_id: int, menu_ids: List[int], session: AsyncSession) -> None:
    delete_stmt = delete(SysRoleMenu).where(and_(SysRoleMenu.role_id == role_id))
    await session.execute(delete_stmt)
    sys_role_menu_list = [SysRoleMenu(role_id=role_id, menu_id=menu_id) for menu_id in menu_ids]
    session.add_all(sys_role_menu_list)
    await session.flush()


class RouterMetaVO(CamelModel):
    title: Optional[str] = None
    icon: Optional[str] = None
    no_cache: Optional[bool] = False
    link: Optional[str] = None


class RouterVO(CamelModel):
    name: Optional[str] = None
    path: Optional[str] = None
    hidden: Optional[bool] = False
    redirect: Optional[str] = None
    component: Optional[str] = None
    query: Optional[dict] = None
    always_show: Optional[bool] = False
    meta: Optional[RouterMetaVO] = None
    children: Optional[List['RouterVO']] = None


def is_menu_frame(menu: SysMenuDTO) -> bool:
    return menu.parent_id == 0 and menu.menu_type == 'C' and menu.is_frame == '1'


def get_route_name(menu: SysMenuDTO) -> str:
    router_name = menu.path.capitalize()
    if is_menu_frame(menu):
        router_name = ''
    return router_name


def is_inner_link(menu: SysMenuDTO):
    return menu.is_frame == '0' and menu.path.startswith('http')


def inner_link_replace_each(path: str) -> str:
    return (path.replace('http', '')
            .replace('https', '')
            .replace('www', '')
            .replace('.', '/')
            .replace(':', '/'))


def get_router_path(menu: SysMenuDTO) -> str:
    router_path = menu.path
    if menu.parent_id != 0 and is_inner_link(menu):
        router_path = inner_link_replace_each(router_path)
    if menu.parent_id == 0 and menu.menu_type == 'M' and menu.is_frame == '1':
        router_path = '/' + menu.path
    elif is_menu_frame(menu):
        router_path = '/'
    return router_path


def get_component(menu: SysMenuDTO) -> str:
    component = 'Layout'
    if menu.component and not is_menu_frame(menu):
        component = menu.component
    elif not menu.component and menu.parent_id != 0 and is_inner_link(menu):
        component = 'InnerLink'
    elif not menu.component and menu.parent_id == 0 and menu.menu_type == 'C':
        component = menu.path
    return component


def build_menus(menu_list: List[SysMenuDTO]) -> List[RouterVO]:
    routers = []
    for menu in menu_list:
        router = RouterVO()
        router.hidden = menu.visible == '1'
        router.name = get_route_name(menu)
        router.path = get_router_path(menu)
        router.component = get_component(menu)
        router.query = menu.query
        router.meta = RouterMetaVO(
            title=menu.menu_name,
            icon=menu.icon,
            no_cache=menu.is_cache == '1',
            link=None)
        if menu.children:
            router.always_show = True
            router.redirect = 'noRedirect'
            router.children = build_menus(menu.children)
        elif is_menu_frame(menu):
            router.meta = None
            children_list = []
            children = RouterVO()
            children.path = menu.path
            children.component = menu.component
            children.name = menu.path.capitalize()
            children.meta = RouterMetaVO(
                title=menu.menu_name,
                icon=menu.icon,
                no_cache=menu.is_cache == '1',
                link=menu.path)
            children.query = menu.query
            children_list.append(children)
            router.children = children_list
        elif menu.parent_id == 0 and is_inner_link(menu):
            router.meta = RouterMetaVO(title=menu.menu_name, icon=menu.icon)
            router.path = '/'
            children_list = []
            children = RouterVO()
            router_path = inner_link_replace_each(menu.path)
            children.path = router_path
            children.component = 'InnerLink'
            children.name = router_path.capitalize()
            children.meta = RouterMetaVO(
                title=menu.menu_name,
                icon=menu.icon,
                link=menu.path)
            children_list.append(children)
            router.children = children_list
        routers.append(router)

    return routers

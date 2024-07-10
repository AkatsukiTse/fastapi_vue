from typing import List, Tuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    Select,
    select,
    delete,
    func,
    and_
)

from core.exception import ApiException
from core.schema import ResponseCode, PageParams, TreeSelect, CamelModel, make_query_dto
from core.db import (
    get_list_and_total
)

from .table import SysDept, SysUser, SysRoleDept


class SysDeptDTO(CamelModel):
    dept_id: Optional[int] = None
    parent_id: Optional[int] = None
    ancestors: Optional[str] = None
    dept_name: Optional[str] = None
    order_num: Optional[int] = None
    leader: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    children: Optional[List['SysDeptDTO']] = None


def build_stmt(params) -> Select:
    stmt = select(SysDept).where(and_(SysDept.del_flag == '0'))
    for key in params.keys():
        if key == 'parentId':
            stmt = stmt.where(and_(SysDept.parent_id == params[key]))
        elif key == 'deptId':
            stmt = stmt.where(and_(SysDept.dept_id == params[key]))
        elif key == 'status':
            stmt = stmt.where(and_(SysDept.status == params[key]))
        elif key == 'deptName':
            stmt = stmt.where(SysDept.dept_name.like('%' + params[key] + '%'))
    return stmt


async def find_dept_page(params, page: PageParams, session: AsyncSession) -> Tuple[List[SysDeptDTO], int]:
    stmt = build_stmt(params)
    records, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)
    return [SysDeptDTO.model_validate(user, from_attributes=True) for user in records], total


async def find_all_dept(params, session: AsyncSession) -> List[SysDeptDTO]:
    stmt = build_stmt(params)
    stmt = stmt.order_by(SysDept.parent_id, SysDept.order_num)
    records = (await session.scalars(stmt)).fetchall()
    return [SysDeptDTO.model_validate(e, from_attributes=True) for e in records]


async def select_dept_tree_list(params, session: AsyncSession) -> List[TreeSelect]:
    stmt = build_stmt(params)
    stmt = stmt.order_by(SysDept.parent_id, SysDept.order_num)
    records = (await session.scalars(stmt)).fetchall()
    print(len(records))
    return TreeSelect.build_tree(
        data_list=[SysDeptDTO.model_validate(e, from_attributes=True) for e in records],
        id_key='dept_id',
        label_key='dept_name')


async def find_children_by_ancestors(ancestors: str, session: AsyncSession) -> List[SysDept]:
    stmt = select(SysDept).where(SysDept.ancestors.like(ancestors + '%'), SysDept.del_flag == '0')
    return [r for r in (await session.scalars(stmt)).fetchall()]


async def find_dept_by_id(id, session) -> SysDept:
    e = await session.get(SysDept, id)
    if e is None or e.del_flag != '0':
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    return e


async def create_dept(form: SysDeptDTO, operator_id: int, session: AsyncSession) -> id:
    await assert_dept_name_unique(form.dept_name, session)

    e = SysDept(**form.model_dump(exclude={'children'}), create_by=operator_id)
    e.ancestors = await get_ancestor_by_parent_id(e.parent_id, session)
    session.add(e)
    await session.flush()

    return e.dept_id


async def get_ancestor_by_parent_id(parent_id: Optional[int], session: AsyncSession) -> str:
    if parent_id is 0:
        return ''
    parent = await find_dept_by_id(parent_id, session)
    return parent.ancestors + ',' + str(parent.dept_id)


async def update_dept(form: SysDeptDTO, operator_id: int, session: AsyncSession) -> None:
    e = await session.get(SysDept, form.dept_id)
    if e is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
    await assert_dept_name_unique(form.dept_name, session, form.dept_id)
    if form.dept_id == form.parent_id:
        raise ApiException(ResponseCode.BAD_REQUEST, '上级部门不能是自己')
    if form.status == '1':
        children = await find_children_by_ancestors(e.ancestors + ',' + str(e.dept_id), session)
        for child in children:
            if child.status == '0':
                raise ApiException(ResponseCode.BAD_REQUEST, '该部门包含未停用的子部门')
    for key, value in form.model_dump(exclude={'dept_id'}).items():
        setattr(e, key, value)
    e.ancestors = await get_ancestor_by_parent_id(e.parent_id, session)
    e.update_by = operator_id


async def delete_dept_by_ids(ids: str, operator_id: int, session: AsyncSession) -> None:
    for dept_id in ids.split(","):
        e = await session.get(SysDept, int(dept_id))
        if e is None:
            raise ApiException(ResponseCode.BAD_REQUEST, '记录不存在')
        child_count = await get_child_dept_count(e.dept_id, session)
        if child_count > 0:
            raise ApiException(ResponseCode.BAD_REQUEST, '存在下级部门,不允许删除')
        user_count = await get_dept_user_count(e.dept_id, session)
        if user_count > 0:
            raise ApiException(ResponseCode.BAD_REQUEST, '部门包含用户,不允许删除')
        e.del_flag = '2'
        e.update_by = operator_id


async def assert_dept_name_unique(name: str, session: AsyncSession, id: int = None):
    stmt = select(func.count()).where(and_(SysDept.dept_name == name, SysDept.del_flag == '0'))
    if id is not None:
        stmt = stmt.where(SysDept.dept_id != id)
    count = (await session.execute(stmt)).scalar()
    if count > 0:
        raise ApiException(ResponseCode.BAD_REQUEST, '名称已存在')


async def get_child_dept_count(parent_id: int, session: AsyncSession) -> int:
    stmt = select(func.count()).where(SysDept.parent_id == parent_id, SysDept.del_flag == '0')
    return (await session.execute(stmt)).scalar()


async def get_dept_user_count(dept_id: int, session: AsyncSession) -> int:
    stmt = select(func.count()).where(SysUser.dept_id == dept_id, SysUser.del_flag == '0')
    return (await session.execute(stmt)).scalar()


async def find_dept_list_by_role_id(role_id: int, session: AsyncSession) -> List[SysDeptDTO]:
    stmt = select(SysDept).join(SysRoleDept, SysDept.dept_id == SysRoleDept.dept_id).where(
        SysRoleDept.role_id == role_id, SysDept.del_flag == '0')
    records = (await session.scalars(stmt)).fetchall()
    return [SysDeptDTO.model_validate(e, from_attributes=True) for e in records]

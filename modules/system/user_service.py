from typing import List, Optional, Tuple
from datetime import datetime


import bcrypt
from fastapi import Query
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy import select, func, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from setting import setting
from core.exception import ApiException
from core.schema import ResponseCode
from core.schema import PageParams, CamelModel
from core.db import get_list_and_total, transactional, assert_key_unique
from modules.system import dept_service
from .table import SysUser, SysDept, SysUserRole, SysUserPost


class UpdateUserParams(BaseModel):
    nickname: str = Field(None)
    roles: List[int] = None


class SysUserDTO(CamelModel):
    user_id: int
    dept_id: Optional[int] = None
    dept_name: str | None = None
    user_name: str | None = None
    nick_name: Optional[str] = None
    email: Optional[str] = None
    phonenumber: Optional[str] = None
    sex: Optional[str] = None
    avatar: Optional[str] = None
    status: str = '0'
    login_ip: Optional[str] = None
    login_date: Optional[datetime] = None
    create_time: datetime | None = None

    dept: dept_service.SysDeptDTO | None = None


class CreateSysUserDTO(SysUserDTO):
    user_id: Optional[int] = None
    password: str
    post_ids: Optional[List[int]] = []
    role_ids: Optional[List[int]] = []


class SysUserIdDTO(CamelModel):
    user_id: int


class UpdateSysUserDTO(CamelModel):
    user_id: int
    user_name: Optional[str] = None
    nick_name: Optional[str] = None
    email: Optional[str] = None
    phonenumber: Optional[str] = None
    sex: Optional[str] = None
    avatar: Optional[str] = None
    status: str
    remark: str | None = ''
    post_ids: Optional[List[int]] = []
    role_ids: Optional[List[int]] = []


class UserQueryParams:
    def __init__(self,
                 user_id: Optional[int] = Query(alias='userId', default=None),
                 user_name: Optional[str] = Query(alias='userName', default=None),
                 status: str = Query(default=None),
                 phonenumber: Optional[str] = Query(default=None),
                 begin_time: Optional[datetime] = Query(alias='beginTime', default=None),
                 end_time: Optional[datetime] = Query(alias='endTime', default=None),
                 dept_id: Optional[int] = Query(alias='deptId', default=None)):
        self.user_id = user_id
        self.user_name = user_name
        self.status = status
        self.phonenumber = phonenumber
        self.begin_time = begin_time
        self.end_time = end_time
        self.dept_id = dept_id


@transactional
async def create_user(form: CreateSysUserDTO, operator_id: int, session: AsyncSession) -> None:
    await assert_key_unique(SysUser, 'user_name', form.user_name, session,
                            error_message='用户名已经存在')
    if form.phonenumber:
        await assert_key_unique(SysUser, 'phonenumber', form.phonenumber, session=session,
                                error_message='手机号码已经存在')
    if form.email:
        await assert_key_unique(SysUser, 'email', form.email, session=session,
                                error_message='邮箱已经存在')
    data = form.model_dump(exclude={'password', 'user_id', 'status', 'post_ids', 'role_ids',
                                    'dept_name', 'dept'})

    user = SysUser(**data)
    user.password = generate_password_hash(form.password)
    user.create_by = operator_id
    user.status = '0'
    session.add(user)
    await session.flush()

    await refresh_user_roles(user.user_id, form.role_ids, session)
    await refresh_user_positions(user.user_id, form.post_ids, session)


async def refresh_user_roles(user_id: int, role_ids: List[int], session: AsyncSession) -> None:
    delete_stmt = delete(SysUserRole).where(and_(SysUserRole.user_id == user_id))
    await session.execute(delete_stmt)
    role_list = [SysUserRole(user_id=user_id, role_id=role_id) for role_id in role_ids]
    if len(role_list) > 0:
        session.add_all(role_list)


async def refresh_user_positions(user_id: int, post_ids: List[int], session: AsyncSession) -> None:
    await session.execute(delete(SysUserPost).where(SysUserPost.user_id == user_id))
    position_list = [SysUserPost(user_id=user_id, post_id=post_id) for post_id in post_ids]
    if len(position_list) > 0:
        session.add_all(position_list)


async def update_user(form: UpdateSysUserDTO, operator_id: int, session: AsyncSession) -> None:
    user = await session.get(SysUser, [form.user_id])
    if user is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '用户不存在')
    await assert_key_unique(SysUser, 'user_name', form.user_name, session,
                            error_message='用户名已经存在', id_key='user_id', id=form.user_id)
    if form.phonenumber:
        await assert_key_unique(SysUser, 'phonenumber', form.phonenumber, session=session,
                                error_message='手机号码已经存在', id_key='user_id', id=form.user_id)
    await refresh_user_roles(form.user_id, form.role_ids, session=session)
    await refresh_user_positions(form.user_id, form.post_ids, session=session)
    for key, value in form.model_dump().items():
        setattr(user, key, value)
    user.update_by = operator_id


async def get_user_by_id(id: int, session: AsyncSession) -> SysUserDTO:
    stmt = select(SysUser).where(and_(SysUser.user_id == id))
    user = (await session.scalars(stmt)).first()
    return SysUserDTO.model_validate(user, from_attributes=True)


async def delete_user_by_ids(ids: str, operator_id: int, session: AsyncSession) -> None:
    for id in ids.split(","):
        user = await session.get(SysUser, int(id))
        if user is None:
            raise ApiException(ResponseCode.BAD_REQUEST, '用户不存在')
        user.del_flag = '2'
        user.update_by = operator_id


async def reset_user_password(id: int, session: AsyncSession) -> None:
    user = await session.get(SysUser, id)
    if user is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '用户不存在')
    user.password = generate_password_hash(setting.default_reset_password)
    await session.commit()


async def update_user_status(user_id: int, status: str, operator_id: int, session: AsyncSession) -> None:
    user = await session.get(SysUser, user_id)
    if user is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '用户不存在')
    user.status = status
    user.update_by = operator_id


async def change_user_password(user_id: int, old_password: str, new_password: str, session: AsyncSession):
    user = await session.get(SysUser, user_id)
    if user is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '用户不存在')
    if not check_password_hash(user.password, old_password):
        raise ApiException(ResponseCode.BAD_REQUEST, '密码错误')
    password_hash = generate_password_hash(new_password)
    user.password = password_hash
    await session.commit()


async def find_user_page(
        params: UserQueryParams,
        page: PageParams,
        session: AsyncSession) -> Tuple[List[SysUserDTO], int]:
    stmt = select(SysUser).where(SysUser.del_flag == '0')
    stmt = stmt.outerjoin(SysDept, SysUser.dept_id == SysDept.dept_id)
    if params.user_id:
        stmt = stmt.where(SysUser.user_id == params.user_id)
    if params.user_name:
        stmt = stmt.where(SysUser.user_name.like(f'%{params.user_name}%'))
    if params.status:
        stmt = stmt.where(SysUser.status == params.status)
    if params.phonenumber:
        stmt = stmt.where(SysUser.phonenumber.like(f'%{params.phonenumber}%'))
    if params.begin_time:
        stmt = stmt.where(SysUser.create_time >= params.begin_time)
    if params.end_time:
        stmt = stmt.where(SysUser.create_time <= params.end_time)
    if params.dept_id:
        dept = await session.get(SysDept, params.dept_id)
        stmt = stmt.where(or_(
            and_(
                SysDept.del_flag == '0',
                SysDept.ancestors.like(dept.ancestors + f',{params.dept_id}%')
            ),
            SysUser.dept_id == params.dept_id
        ))
    records, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)

    dto_list = []
    for record in records:
        dto = SysUserDTO.model_validate(record, from_attributes=True)
        if dto.dept_id:
            dto.dept = await dept_service.find_dept_by_id(dto.dept_id, session=session)
        dto_list.append(dto)
    return dto_list, total


async def _is_username_unique(username: str, session: AsyncSession) -> bool:
    user_count = await _count_by_username(username, session=session)
    return user_count == 0


async def find_user_by_username(user_name: str, session: AsyncSession) -> SysUser | None:
    stmt = select(SysUser).where(SysUser.user_name == user_name, SysUser.del_flag == '0')
    return (await session.scalars(stmt)).one_or_none()


async def user_login(username: str, password: str, session: AsyncSession) -> SysUser:
    user = await find_user_by_username(username, session)
    if user is None:
        raise ApiException(ResponseCode.BAD_REQUEST, '用户名或密码错误')
    if not check_password_hash(user.password, password):
        raise ApiException(ResponseCode.BAD_REQUEST, '用户名或密码错误')
    return user


async def find_page_by_role(role_id: int, page: PageParams, session: AsyncSession) -> Tuple[List[SysUserDTO], int]:
    stmt = select(SysUser).where(and_(
        SysUser.del_flag == '0',
        SysUserRole.role_id == role_id,
        SysUser.user_id == SysUserRole.user_id
    ))
    users, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)
    return [SysUserDTO.model_validate(user, from_attributes=True) for user in users], total


async def find_page_exclude_role(role_id: int, page: PageParams, session: AsyncSession) -> Tuple[List[SysUserDTO], int]:
    stmt = select(SysUser).outerjoin(SysUserRole, SysUser.user_id == SysUserRole.user_id).where(and_(
        SysUser.del_flag == '0',
        or_(
            SysUserRole.role_id != role_id,
            SysUserRole.role_id == None
        )
    ))
    users, total = await get_list_and_total(stmt, page.page_num, page.page_size, session)
    return [SysUserDTO.model_validate(user, from_attributes=True) for user in users], total


async def _count_by_username(username: str, session: AsyncSession) -> int:
    stmt = select(func.count(SysUser.user_id)).where(SysUser.user_name == username, SysUser.del_flag == '0')
    return await session.scalar(stmt)


def generate_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode('utf8')


def check_password_hash(password_hash: str, password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf8'), password_hash.encode('utf8'))

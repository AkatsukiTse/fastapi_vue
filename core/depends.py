from typing import Optional, Annotated, Union
import hashlib
import json
import time

from fastapi import Header, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger

from core.db import (
    AsyncSession,
    get_session
)

from core.redis import redis
from core.exception import ApiException
from core.jwt import jwt_decode
from core.schema import ResponseCode

from modules.system import menu_service


def get_jwt_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if authorization is None:
        return None
    try:
        token_type, token = authorization.split(None, 1)
    except ValueError:
        logger.exception('解析Token失败')
        return None
    if token_type.lower() != 'bearer':
        return None
    return token


def get_current_user_id(token: str = Depends(get_jwt_token)) -> Optional[str]:
    if token is None:
        return None
    # 判断token是否合法
    payload = jwt_decode(token)
    user_id = payload['user_id']
    return user_id


CurrentUserId = Annotated[Union[str, None], Depends(get_current_user_id)]
Session = Annotated[AsyncSession, Depends(get_session)]


async def is_login(user_id: CurrentUserId):
    """必须登陆校验"""
    if user_id is None:
        raise ApiException(ResponseCode.LOGIN_REQUIRE)


login_required = Depends(is_login)


async def get_user_permissions(user_id: int, token: str, session: Session) -> set:
    # 用token的哈希值作为key
    key = f"user_permission:{hashlib.md5(token.encode()).hexdigest()}"
    # 从redis中获取用户权限
    cache_str = await redis.get(key)
    if cache_str:
        return json.loads(cache_str)

    permissions = await menu_service.find_menu_permission_set_by_user_id(int(user_id), session)

    await redis.set(key, json.dumps(permissions), expire=60 * 60 * 24)

    return permissions


def permission_required(control_path: str) -> Depends:
    async def permission_required_inner(
            user_id: CurrentUserId,
            session: Session,
            token: str = Depends(get_jwt_token)):
        """权限校验"""
        if user_id is None:
            raise ApiException(ResponseCode.LOGIN_REQUIRE)
        if user_id == 1:
            return None

        permissions = await get_user_permissions(int(user_id), token, session)
        if control_path not in permissions:
            raise ApiException(ResponseCode.PERMISSION_DENY, '没有操作权限')

    return Depends(permission_required_inner)


__all__ = [
    'Session',
    'CurrentUserId',
    'login_required',
    'permission_required'
]

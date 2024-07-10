from datetime import datetime, timedelta
import jwt

from setting import setting
from core.exception import ApiException
from core.schema import ResponseCode


def jwt_encode(payload: dict, timeout: int):
    # jwt设置过期时间的本质 就是在payload中 设置exp字段, 值要求为格林尼治时间
    payload.update({
        'exp': datetime.utcnow() + timedelta(seconds=timeout)
    })
    token = jwt.encode(payload, key=setting.token_secret, algorithm='HS256')
    return token


def jwt_decode(token: str) -> dict:
    try:
        return jwt.decode(str(token), key=setting.token_secret, algorithms='HS256')
    except jwt.PyJWTError:
        raise ApiException(ResponseCode.LOGIN_EXPIRE, '凭证已经过期')
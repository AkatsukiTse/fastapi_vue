from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from core.redis import redis
from core.schema import BaseResponse, ResponseCode
from core.exception import ApiException
from core.middleware import SlowRequestMiddleware, log_request


@asynccontextmanager
async def lifespan(_):
    """"前置和后置事件"""
    yield
    if redis is not None:
        await redis.close()


def create_app() -> FastAPI:
    """初始化app实例，注册各种扩展"""
    application = FastAPI(lifespan=lifespan)
    register_api(application)
    register_exception_handler(application)

    # middleware
    application.middleware('http')(SlowRequestMiddleware())
    application.middleware('http')(log_request)

    return application


def register_exception_handler(application: FastAPI):
    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc):
        logger.exception('request validation error', exc)
        return JSONResponse(BaseResponse(code=ResponseCode.BAD_REQUEST, msg=str(exc)).model_dump())

    @application.exception_handler(ApiException)
    async def api_exception_handler(_, e):
        return JSONResponse(BaseResponse(code=e.code, msg=e.msg).dict())

    @application.exception_handler(Exception)
    async def base_exception_handler(_, e):
        logger.exception('request error')
        message = e.msg if hasattr(e, 'message') else ''
        return JSONResponse(BaseResponse(code=ResponseCode.SYSTEM_ERROR, msg=message).dict())


def register_api(application: FastAPI):
    from modules.system.auth_api import api as auth_api
    from modules.system.user_api import api as user_api
    from modules.system.role_api import api as role_api
    from modules.system.sys_dict_api import api as sys_dict_api
    from modules.system.dept_api import api as dept_api
    from modules.system.post_api import api as post_api
    from modules.system.notice_api import api as notice_api
    from modules.system.menu_api import api as menu_api
    from modules.system.config_api import api as config_api

    application.include_router(auth_api)
    application.include_router(user_api)
    application.include_router(role_api)
    application.include_router(sys_dict_api)
    application.include_router(dept_api)
    application.include_router(post_api)
    application.include_router(notice_api)
    application.include_router(menu_api)
    application.include_router(config_api)


app = create_app()

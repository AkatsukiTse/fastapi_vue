import time

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger


class SlowRequestMiddleware(object):
    def __init__(self, limit=1):
        self.limit = limit

    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        if process_time > self.limit:
            logger.warning(f'{request.url.path}[{request.method}]---{process_time}')
        return response


# 记录日志的依赖函数
async def log_request(request: Request, call_next):
    start_time = time.time()

    # 记录请求参数
    request_body = await request.body() if request.method in ["POST", "PUT"] else None
    request_params = str(request.query_params) if request.query_params else None

    response = await call_next(request)

    # 计算请求耗时
    process_time = time.time() - start_time

    # 记录响应JSON
    response_body = None
    if isinstance(response, JSONResponse):
        response_body = response.body.decode('utf-8')

    # 记录日志
    # TODO 落盘到SysOperLog表
    logger.info(f"Request: {request.method} {request.url.path} Params: {request_params} Body: {request_body}")
    logger.info(f"Response: {response.status_code} Body: {response_body}")
    logger.info(f"Processing time: {process_time:.2f} seconds")

    return response

class ApiException(Exception):
    def __init__(self, code: int, msg: str = '非法请求'):
        self.code = code
        self.msg = msg

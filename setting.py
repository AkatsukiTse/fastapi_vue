import os
from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict

file_dir = os.path.dirname(os.path.abspath(__file__))

if os.environ.get('env') == 'test':
    load_dotenv(os.path.join(file_dir, '.env.test'))
else:
    load_dotenv(os.path.join(file_dir, '.env'))


class Setting(BaseSettings):
    model_config = SettingsConfigDict(validate_default=False)
    env: str = 'test'
    database_uri: str
    # 是否打印SQL语句
    database_print_sql: bool = False
    admin_password: str = 'admin123'
    admin_user_id: int = 1
    redis_url: str | None = None
    # JWT 相关
    token_secret: str = 'fastapi_vue'
    token_prefix: str = 'AUTH_TOKEN_'
    token_timeout: int = 3600 * 24 * 30
    # 是否忽略验证码
    ignore_captcha: bool = False
    # 重置默认密码
    default_reset_password: str = 'a123456A'


setting = Setting()

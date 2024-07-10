import random
import base64
from io import BytesIO
import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from captcha.image import ImageCaptcha

from setting import setting
from core.depends import Session, CurrentUserId
from core.jwt import jwt_encode
from core.redis import redis
from core.schema import BaseResponse, ResponseCode
from core.exception import ApiException
from modules.system import user_service
from modules.system import role_service
from modules.system import menu_service

api = APIRouter()
image_captcha = ImageCaptcha()
captcha_chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def generate_token(user: user_service.SysUser):
    """根据用户创建访问凭证"""
    return jwt_encode(dict(user_id=user.user_id), setting.token_timeout)


class LoginForm(BaseModel):
    username: str
    password: str
    uuid: str | None = None
    code: str | None = None


@api.post('/login')
async def login_endpoint(form: LoginForm, session: Session):
    if not setting.ignore_captcha:
        if form.uuid is None or form.code is None:
            raise ApiException(ResponseCode.CAPTCHA_ERROR, '验证码错误')
        captcha_text = await redis.get(f"captcha:{form.uuid}")
        if captcha_text is None:
            raise ApiException(ResponseCode.CAPTCHA_TIMEOUT, '验证码已过期')
        if captcha_text.lower() != form.code.lower():
            raise ApiException(ResponseCode.CAPTCHA_ERROR, '验证码错误')
    user = await user_service.user_login(form.username, form.password, session=session)
    token = generate_token(user)
    base_response = BaseResponse(data="")
    dict_response = base_response.model_dump()
    dict_response['token'] = token
    return dict_response


@api.post('/logout')
async def logout_endpoint():
    return BaseResponse.ok()


class GetInfoResponse(BaseResponse):
    user: user_service.SysUserDTO
    roles: set[str]
    permissions: set[str]


@api.get('/getInfo')
async def get_info(user_id: CurrentUserId, session: Session):
    return GetInfoResponse(
        user=await user_service.get_user_by_id(user_id, session),
        roles=await role_service.find_role_permission_set_by_user_id(user_id, session),
        permissions=await menu_service.find_menu_permission_set_by_user_id(user_id, session)
    )


@api.get('/getRouters')
async def get_routers(user_id: CurrentUserId, session: Session):
    query_dto = menu_service.SysMenuQueryDTO(menu_type_list=['M', 'C'], status='0')
    menu_list = await menu_service.find_menu_list_by_user_id(query_dto, user_id, session)
    for menu in menu_list:
        menu.children = [child for child in menu_list if child.parent_id == menu.menu_id]
    menu_list = [menu for menu in menu_list if menu.parent_id == 0]
    return BaseResponse(data=menu_service.build_menus(menu_list))


class GetCaptchaResponse(BaseResponse):
    uuid: str
    img: str


@api.get('/captchaImage')
async def get_captcha():
    # get 4 random char from captcha_chars
    text = ''.join(random.choices(captcha_chars, k=4))
    print('text:', text)
    image = image_captcha.generate_image(text)

    # Convert image to base64 string
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # generate uid by uuid
    uid = uuid.uuid4().hex

    # save captcha to redis
    await redis.set(f"captcha:{uid}", text, ex=60)

    return GetCaptchaResponse(code=ResponseCode.SUCCESS, uuid=uid, img=img_str)

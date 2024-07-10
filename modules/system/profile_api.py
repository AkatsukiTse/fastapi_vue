from fastapi import APIRouter
from fastapi.responses import JSONResponse
from core.depends import (
    Session,
    CurrentUserId,
    login_required
)
from core.schema import BaseResponse
from modules.system import user_service
from modules.system import role_service
from modules.system import post_service

api = APIRouter(prefix='/system/user/profile', dependencies=[login_required])


@api.get('')
async def get_profile(user_id: CurrentUserId, session: Session):
    user = await user_service.get_user_by_id(user_id, session)
    response = BaseResponse(data=user).model_dump()
    response['roleGroup'] = await role_service.find_by_user_id(user_id, session)
    response['postGroup'] = await post_service.find_by_user_id(user_id, session)

    return JSONResponse(content=response)


@api.put('')
async def update_profile(user_id: CurrentUserId, form: user_service.UpdateSysUserDTO, session: Session):
    origin = await user_service.get_user_by_id(user_id, session)
    user = user_service.UpdateSysUserDTO.model_validate(origin, from_attributes=True)
    user.nick_name = form.nick_name
    user.phonenumber = form.phonenumber
    user.email = form.email
    user.sex = form.sex
    await user_service.update_user(user, user_id, session)

    return BaseResponse()


@api.put('/updatePwd')
async def update_pwd(olsPassword, newPassword, user_id: CurrentUserId, session: Session):
    await user_service.change_user_password(user_id, olsPassword, newPassword, session)
    return BaseResponse()


# todo avatar

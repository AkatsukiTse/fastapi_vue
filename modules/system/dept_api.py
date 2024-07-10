from fastapi import APIRouter, Request

from core.depends import (
    Session,
    CurrentUserId,
    login_required
)

from core.schema import BaseResponse

from modules.system.dept_service import (SysDeptDTO, create_dept, find_all_dept,
                                         update_dept, delete_dept_by_ids, find_dept_by_id)

api = APIRouter(prefix='/system/dept', dependencies=[login_required])


@api.get('/list')
async def find_dept_page_endpoint(session: Session, request: Request):
    rows = await find_all_dept(request.query_params, session)
    return BaseResponse(data=rows)


@api.get('/list/exclude/{dept_id}')
async def exclude_child_endpoint(dept_id: int, session: Session):
    dept_list = await find_all_dept({}, session)
    result_dept_list = []
    for dept in dept_list:
        if dept.dept_id == dept_id:
            continue
        if dept.ancestors and str(dept_id) in dept.ancestors.split(','):
            continue
        result_dept_list.append(dept)
    return BaseResponse(data=result_dept_list)


@api.get('/{id}')
async def find_dept_by_id_endpoint(id: int, session: Session):
    dept = await find_dept_by_id(id, session)
    return BaseResponse(data=SysDeptDTO.model_validate(dept, from_attributes=True))


@api.post('')
async def create_dept_endpoint(form: SysDeptDTO, user_id: CurrentUserId, session: Session):
    await create_dept(form, user_id, session=session)
    await session.commit()
    return BaseResponse(msg='创建成功')


@api.put('')
async def update_dept_endpoint(dto: SysDeptDTO, user_id: CurrentUserId, session: Session):
    await update_dept(dto, user_id, session)
    await session.commit()
    return BaseResponse(msg='编辑成功')


@api.delete('/{ids}')
async def delete_role_endpoint(ids: str, user_id: CurrentUserId, session: Session):
    await delete_dept_by_ids(ids, user_id, session)
    await session.commit()
    return BaseResponse(msg='删除成功')

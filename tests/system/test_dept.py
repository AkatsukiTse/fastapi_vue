import pytest

from core.schema import ResponseCode
from tests.test_util import extract_response

baseurl = 'http://127.0.0.1/system/dept'


async def get_dept_list(client, auth_header):
    params = {}
    response = await client.get(f'{baseurl}/list', headers=auth_header, params=params)
    response_data = extract_response(response)
    return response_data


@pytest.mark.asyncio
async def test_get_dept_list(client, auth_header):
    await get_dept_list(client, auth_header)


@pytest.mark.asyncio
async def test_get_dept_by_id(client, auth_header):
    entity_list = await get_dept_list(client, auth_header)
    e = entity_list[0]
    response = await client.get(f'{baseurl}/{e["deptId"]}', headers=auth_header)
    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data['code'] == ResponseCode.SUCCESS
    assert resp_data['data']['deptId'] == e['deptId']


@pytest.mark.asyncio
async def test_create_dept(client, auth_header):
    post_data = {
        'deptName': 'testDeptName',
        'parentId': 0,
    }
    response = await client.post(baseurl, json=post_data, headers=auth_header)
    extract_response(response)

    entity_list = await get_dept_list(client, auth_header)
    assert len([e for e in entity_list if e['deptName'] == 'testDeptName']) == 1


@pytest.mark.asyncio
async def test_update_dept(client, auth_header):
    roles = await get_dept_list(client, auth_header)
    role = roles[0]
    role['deptName'] = 'testDeptName'
    response = await client.put(baseurl, json=role, headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS

    roles = await get_dept_list(client, auth_header)
    target_role = next(filter(lambda x: x['deptId'] == role['deptId'], roles))
    assert target_role['deptName'] == role['deptName']


@pytest.mark.asyncio
async def test_delete(client, auth_header):
    roles = await get_dept_list(client, auth_header)
    before_count = len(roles)
    delete_role_id = roles[-1]['deptId']

    response = await client.delete(baseurl + f'/{delete_role_id}', headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS

    after_roles = await get_dept_list(client, auth_header)
    assert before_count - 1 == len(after_roles)

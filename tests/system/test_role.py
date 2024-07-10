import pytest

from core.schema import ResponseCode

from tests.test_util import extract_response

baseurl = 'http://127.0.0.1/system/role'


async def get_roles(client, auth_header):
    params = {}
    response = await client.get(f'{baseurl}/list', headers=auth_header, params=params)
    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data['code'] == ResponseCode.SUCCESS
    assert len(resp_data['rows']) > 0
    return resp_data['rows']


@pytest.mark.asyncio
async def test_get_roles(client, auth_header):
    await get_roles(client, auth_header)


@pytest.mark.asyncio
async def test_get_role_by_id(client, auth_header):
    roles = await get_roles(client, auth_header)
    role = roles[0]
    response = await client.get(f'{baseurl}/{role["roleId"]}', headers=auth_header)
    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data['code'] == ResponseCode.SUCCESS
    assert resp_data['data']['roleId'] == role['roleId']


@pytest.mark.asyncio
async def test_create_role(client, auth_header):
    post_data = {
        'roleName': 'TestRole',
        'roleKey': 'TestRole'
    }
    response = await client.post(baseurl, json=post_data, headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS

    roles = await get_roles(client, auth_header)
    assert len([role for role in roles if role['roleName'] == 'TestRole']) == 1


@pytest.mark.asyncio
async def test_update_role(client, auth_header):
    roles = await get_roles(client, auth_header)
    role = roles[1]
    role_id = role['roleId']
    role['roleName'] = 'NewTestRole'
    role['menuIds'] = [4]
    response = await client.put(baseurl, json=role, headers=auth_header)
    extract_response(response)

    roles = await get_roles(client, auth_header)
    target_role = next(filter(lambda x: x['roleId'] == role['roleId'], roles))
    assert target_role['roleName'] == role['roleName']

    response = await client.get(f'http://127.0.0.1/system/menu/roleMenuTreeselect/{role_id}',
                                headers=auth_header)
    response_data = extract_response(response, return_data=False)
    checked_keys = response_data['checkedKeys']
    assert len(checked_keys) == 1
    assert checked_keys[0] == 4


@pytest.mark.asyncio
async def test_change_role_status(client, auth_header):
    roles = await get_roles(client, auth_header)
    role = roles[0]
    post_data = {
        'roleId': role['roleId'],
        'status': '1'
    }
    response = await client.put(f'{baseurl}/changeStatus', json=post_data, headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    print(response_data)
    assert response_data['code'] == ResponseCode.SUCCESS

    roles = await get_roles(client, auth_header)
    target_role = next(filter(lambda x: x['roleId'] == role['roleId'], roles))
    assert target_role['status'] == '1'


@pytest.mark.asyncio
async def test_delete(client, auth_header):
    roles = await get_roles(client, auth_header)
    before_count = len(roles)
    delete_role_id = roles[-1]['roleId']

    response = await client.delete(baseurl + f'/{delete_role_id}', headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS

    after_roles = await get_roles(client, auth_header)
    assert before_count - 1 == len(after_roles)


@pytest.mark.asyncio
async def test_dept_tree(client, auth_header):
    response = await client.get(f'{baseurl}/deptTree/2', headers=auth_header)
    extract_response(response)


@pytest.mark.asyncio
async def test_update_data_scope(client, auth_header):
    role_id = 2
    response = await client.get(f'{baseurl}/{role_id}', headers=auth_header)
    response_data = extract_response(response)

    response_data['dataScope'] = '1'
    response = await client.put(f'{baseurl}/dataScope', json=response_data, headers=auth_header)
    extract_response(response)

    response = await client.get(f'{baseurl}/{role_id}', headers=auth_header)
    response_data = extract_response(response)
    assert response_data['dataScope'] == '1'

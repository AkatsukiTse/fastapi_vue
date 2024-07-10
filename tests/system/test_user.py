import pytest

from setting import setting
from core.schema import ResponseCode
from tests.system.test_auth import get_token
from tests.test_util import extract_response

baseurl = 'http://127.0.0.1/system/user'


async def get_users(client, auth_header, **kwargs):
    response = await client.get(f"{baseurl}/list", headers=auth_header, params=kwargs)
    data = extract_response(response, return_data=False)
    return data['rows']


@pytest.mark.asyncio
async def test_get_users(client, auth_header):
    user_list = await get_users(client, auth_header)
    assert len(user_list) > 0

    # 根据部门查询
    user_list = await get_users(client, auth_header, deptId=101)
    assert len(user_list) > 0


@pytest.mark.asyncio
async def test_get_user(client, auth_header):
    users = await get_users(client, auth_header)
    user_id = users[0]['userId']
    response = await client.get(f'{baseurl}/{user_id}', headers=auth_header)
    data = extract_response(response, return_data=False)
    assert data['data']['userId'] == user_id


@pytest.mark.asyncio
async def test_create_user(client, auth_header):
    before_users = await get_users(client, auth_header)
    username = 'test_create_user'
    password = 'abc'
    response = await client.post(baseurl, json=dict(userName=username, password=password), headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS
    after_users = await get_users(client, auth_header)
    assert len(before_users) + 1 == len(after_users)


@pytest.mark.asyncio
async def test_update_user(client, auth_header):
    # Case1 1个角色减少到0
    response = await client.get(f'{baseurl}/2', headers=auth_header)
    data = extract_response(response, return_data=False)
    assert len(data['roleIds']) == 1

    post_json = data['data']
    post_json['postIds'] = data['postIds']
    post_json['roleIds'] = []
    response = await client.put(f'{baseurl}', json=post_json, headers=auth_header)
    extract_response(response)

    response = await client.get(f'{baseurl}/2', headers=auth_header)
    data = extract_response(response, return_data=False)
    assert len(data['roleIds']) == 0


@pytest.mark.asyncio
async def test_update_user_2(client, auth_header, session):
    # Case2 2个角色减少到一个
    response = await client.get(f'{baseurl}/2', headers=auth_header)
    data = extract_response(response, return_data=False)
    assert len(data['roleIds']) == 1

    response = await client.get(f'{baseurl}/2', headers=auth_header)
    data = extract_response(response, return_data=False)
    post_json = data['data']
    post_json['postIds'] = data['postIds']
    post_json['roleIds'] = [1, 2]
    response = await client.put(f'{baseurl}', json=post_json, headers=auth_header)
    extract_response(response)
    response = await client.get(f'{baseurl}/2', headers=auth_header)
    data = extract_response(response, return_data=False)
    assert len(data['roleIds']) == 2

    post_json['roleIds'] = [2]
    response = await client.put(f'{baseurl}', json=post_json, headers=auth_header)
    extract_response(response)
    response = await client.get(f'{baseurl}/2', headers=auth_header)
    data = extract_response(response, return_data=False)
    assert len(data['roleIds']) == 1


@pytest.mark.asyncio
async def test_delete_user(client, auth_header):
    before_users = await get_users(client, auth_header)
    user_ids = ','.join([str(user['userId']) for user in before_users[-2:]])
    response = await client.delete(f'{baseurl}/{user_ids}', headers=auth_header)
    extract_response(response)
    after_users = await get_users(client, auth_header)
    assert len(before_users) - 2 == len(after_users)


@pytest.mark.asyncio
async def test_reset_password(client, auth_header):
    users = await get_users(client, auth_header)
    user = users[0]
    post_data = {
        'userId': user['userId']
    }
    response = await client.put(f'{baseurl}/resetPwd', json=post_data, headers=auth_header)
    extract_response(response)

    await get_token(client, user['userName'], setting.default_reset_password)


@pytest.mark.asyncio
async def test_change_status(client, auth_header):
    users = await get_users(client, auth_header)
    user = users[-1]
    post_data = {
        'userId': user['userId'],
        'status': '1'
    }
    response = await client.put(f'{baseurl}/changeStatus', json=post_data, headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS

    users = await get_users(client, auth_header)
    assert users[-1]['status'] == '1'


@pytest.mark.asyncio
async def test_dept_tree(client, auth_header):
    response = await client.get(f'{baseurl}/deptTree', headers=auth_header)
    response_data = extract_response(response)
    assert len(response_data) > 0


@pytest.mark.asyncio
async def test_get_auth_role(client, auth_header):
    users = await get_users(client, auth_header)
    user_id = users[0]['userId']
    response = await client.get(f'{baseurl}/authRole/{user_id}', headers=auth_header)
    print(extract_response(response, return_data=False))


@pytest.mark.asyncio
async def test_update_auth_role(client, auth_header):
    users = await get_users(client, auth_header)
    user_id = users[1]['userId']

    # Case 1
    response = await client.put(f'{baseurl}/authRole', headers=auth_header, params={
        'userId': user_id,
        'roleIds': ''
    })
    extract_response(response)

    response = await client.get(f'{baseurl}/authRole/{user_id}', headers=auth_header)
    response_data = extract_response(response, return_data=False)
    assert len(response_data['roles']) == 0

    # Case2
    response = await client.put(f'{baseurl}/authRole', headers=auth_header, params={
        'userId': user_id,
        'roleIds': '1,2'
    })
    extract_response(response)

    response = await client.get(f'{baseurl}/authRole/{user_id}', headers=auth_header)
    response_data = extract_response(response, return_data=False)
    assert len(response_data['roles']) == 2

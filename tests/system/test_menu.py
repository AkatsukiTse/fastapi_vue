import pytest

from core.schema import ResponseCode

from tests.test_util import extract_response

baseurl = 'http://127.0.0.1/system/menu'

pk_key = 'menuId'
name_key = 'menuName'
test_name = 'testMenu'
test_data = {
    name_key: test_name,
    'parentId': 0
}


async def get_data_list(client, auth_header):
    params = {}
    response = await client.get(f'{baseurl}/list', headers=auth_header, params=params)
    response_data = extract_response(response)
    assert len(response_data) > 0
    return response_data


@pytest.mark.asyncio
async def test_get_data_list(client, auth_header):
    await get_data_list(client, auth_header)


@pytest.mark.asyncio
async def test_get_by_id(client, auth_header):
    entity_list = await get_data_list(client, auth_header)
    e = entity_list[0]
    response = await client.get(f'{baseurl}/{e[pk_key]}', headers=auth_header)
    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data['code'] == ResponseCode.SUCCESS
    assert resp_data['data'][pk_key] == e[pk_key]


@pytest.mark.asyncio
async def test_create(client, auth_header):
    response = await client.post(baseurl, json=test_data, headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS

    entity_list = await get_data_list(client, auth_header)
    assert len([e for e in entity_list if e[name_key] == test_name]) == 1


@pytest.mark.asyncio
async def test_update_dept(client, auth_header):
    entity_list = await get_data_list(client, auth_header)
    entity = entity_list[0]
    entity[name_key] = test_name
    response = await client.put(baseurl, json=entity, headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS

    entity_list = await get_data_list(client, auth_header)
    target_entity = next(filter(lambda x: x[pk_key] == entity[pk_key], entity_list))
    assert target_entity[name_key] == entity[name_key]


@pytest.mark.asyncio
async def test_delete(client, auth_header):
    entity_list = await get_data_list(client, auth_header)
    before_count = len(entity_list)
    delete_id = entity_list[-1][pk_key]

    response = await client.delete(baseurl + f'/{delete_id}', headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS

    after_roles = await get_data_list(client, auth_header)
    assert before_count - 1 == len(after_roles)


@pytest.mark.asyncio
async def test_tree_select(client, auth_header):
    response = await client.get(f'{baseurl}/treeselect', headers=auth_header)
    extract_response(response)


@pytest.mark.asyncio
async def test_role_menu_treeselect(client, auth_header):
    response = await client.get(f'{baseurl}/roleMenuTreeselect/2', headers=auth_header)
    extract_response(response)

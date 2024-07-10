import pytest

from core.redis import redis, clear_cache_by_namespace
from modules.system import sys_dict_service
from tests.test_util import extract_response

dict_url = 'http://127.0.0.1/system/dict/type'
item_url = 'http://127.0.0.1/system/dict/data'
DICT_KEY = 'pytest_dict_key'

id_key = 'dictId'
test_dict_type = {
    'dictName': 'test_dict_type_name',
    'dictType': 'test_dict_type',
    'status': '0'
}
new_name = 'test_dict_type_name2'
test_dict_data = {
    'dictLabel': 'test_dict_label',
    'dictValue': 'test_dict_value'
}


async def create_dict(client, auth_header):
    response = await client.post(f'{dict_url}', headers=auth_header, json=test_dict_type)
    extract_response(response)


async def get_dict_list(client, auth_header):
    response = await client.get(f'{dict_url}/list', headers=auth_header)
    response_data = extract_response(response, return_data=False)
    return response_data['rows']


async def get_test_dict_type(client, auth_header):
    response = await client.get(
        f'{dict_url}/list',
        params={'dictName': test_dict_type['dictName']},
        headers=auth_header)
    response = extract_response(response, return_data=False)
    return response['rows'][0]


async def get_test_dict_id(client, auth_header):
    dict_type = await get_test_dict_type(client, auth_header)
    return dict_type[id_key]


async def get_item_by_parent_id(client, auth_header, parent_id):
    response = await client.get(item_url, params={'parent_id': parent_id}, headers=auth_header)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == 0
    return response_data['data']


@pytest.mark.asyncio
async def test_get_sys_dict_type_list(client, auth_header):
    sys_dict_type_list = await get_dict_list(client, auth_header)
    assert len(sys_dict_type_list) > 0
    print(sys_dict_type_list[0])
    assert sys_dict_type_list[0]['createTime'] is not None


@pytest.mark.asyncio
async def test_post_sys_dict(client, auth_header):
    await create_dict(client, auth_header)


@pytest.mark.asyncio
async def test_put_sys_dict(client, auth_header):
    dict_type_list = await get_dict_list(client, auth_header)
    json_data = dict_type_list[0]
    json_data['dictName'] = new_name
    response = await client.put(f'{dict_url}', headers=auth_header, json=json_data)
    extract_response(response)

    dict_list = await get_dict_list(client, auth_header)
    target_dict = [d for d in dict_list if d['dictId'] == json_data['dictId']][0]
    assert target_dict['dictName'] == new_name


@pytest.mark.asyncio
async def test_delete_sys_dict(client, auth_header):
    dict_type_list = await get_dict_list(client, auth_header)
    json_data = dict_type_list[0]

    response = await client.delete(
        f'{dict_url}/{json_data["dictId"]}',
        headers=auth_header)
    extract_response(response)

    dict_list = await get_dict_list(client, auth_header)
    assert len([d for d in dict_list if d['dictId'] == json_data['dictId']]) == 0


@pytest.mark.asyncio
async def test_post_sys_dict_data(client, auth_header):
    await create_dict(client, auth_header)
    data_type_data = await get_test_dict_type(client, auth_header)
    await create_dict_data(client, auth_header, dict_type=data_type_data['dictType'])


async def create_dict_data(client, auth_header, dict_type):
    json_data = test_dict_data.copy()
    json_data['dictType'] = dict_type
    response = await client.post(item_url, headers=auth_header, json=json_data)
    extract_response(response)


async def find_dict_item_list(client, auth_header):
    response = await client.get(f'{item_url}/list', headers=auth_header)
    response_data = extract_response(response, return_data=False)
    return response_data['rows']


@pytest.mark.asyncio
async def test_put_sys_dict_item(client, auth_header):
    await create_dict(client, auth_header)
    dict_type_data = await get_test_dict_type(client, auth_header)
    await create_dict_data(client, auth_header, dict_type=dict_type_data['dictType'])
    item_list = await find_dict_item_list(client, auth_header)
    dict_data = [i for i in item_list if i['dictType'] == dict_type_data['dictType']][0]

    json_data = dict_data.copy()
    new_dict_label = 'pytest_dict_label2'
    json_data['dictLabel'] = new_dict_label
    response = await client.put(f'{item_url}', headers=auth_header, json=json_data)
    extract_response(response)

    item_list = await find_dict_item_list(client, auth_header)
    target_item = [i for i in item_list if i['dictCode'] == dict_data['dictCode']][0]
    assert target_item['dictLabel'] == new_dict_label


async def find_dict_data_list(client, auth_header):
    response = await client.get(f'{item_url}/list', headers=auth_header)
    response_data = extract_response(response, return_data=False)
    return response_data['rows']


@pytest.mark.asyncio
async def test_del_sys_dict_data(client, auth_header):
    dict_data_list = await find_dict_data_list(client, auth_header)
    dict_code = dict_data_list[0]['dictCode']

    response = await client.delete(f'{item_url}/{dict_code}', headers=auth_header)
    extract_response(response)

    item_list = await find_dict_item_list(client, auth_header)
    assert len([i for i in item_list if i['dictCode'] == dict_code]) == 0


@pytest.mark.asyncio
async def test_sys_dict_type_option_select(client, auth_header):
    response = await client.get(f'http://127.0.0.1/system/dict/type/optionselect', headers=auth_header)
    extract_response(response)


@pytest.mark.asyncio
async def test_cache_for_find_dict_data_by_type(session):
    await clear_cache_by_namespace('sys_dict')

    dict_data_list = await sys_dict_service.find_dict_data_by_type(
        dict_type='sys_yes_no',
        session=session
    )
    assert len(dict_data_list) == 2

    keys = await redis.keys(f'sys_dict:*')
    assert len(keys) == 1


@pytest.mark.asyncio
async def test_cache_evict_for_create_dict_data(session):
    await clear_cache_by_namespace('sys_dict')

    dict_data_list = await sys_dict_service.find_dict_data_by_type(dict_type='sys_yes_no', session=session)
    assert len(dict_data_list) == 2

    await sys_dict_service.create_dict_data(
        form=sys_dict_service.SysDictDataDTO(
            dictLabel='test_label',
            dictValue='test_value',
            dictType='sys_yes_no'
        ),
        operator_id=1,
        session=session
    )

    keys = await redis.keys(f'sys_dict:*')
    assert len(keys) == 0

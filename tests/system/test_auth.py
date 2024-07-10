import pytest

from setting import setting
from core.schema import ResponseCode
from tests.test_util import extract_response

baseurl = 'http://127.0.0.1/login'


async def get_token(client, username, password):
    response = await client.post(baseurl, json=dict(
        username=username,
        password=password
    ))
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS
    return response_data['token']


@pytest.mark.asyncio
async def test_post(client):
    await get_token(client, 'admin', setting.admin_password)


@pytest.mark.asyncio
async def test_post_error(client):
    response = await client.post(baseurl, json=dict(
        username='admin',
        password='1'
    ))
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.BAD_REQUEST


@pytest.mark.asyncio
async def test_post_user_not_exists(client):
    response = await client.post(baseurl, json=dict(
        username='admin_not_exists',
        password='admin'
    ))
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.BAD_REQUEST


@pytest.mark.asyncio
async def test_get_info(client, auth_header):
    response = await client.get('http://127.0.0.1/getInfo', headers=auth_header)
    extract_response(response)


@pytest.mark.asyncio
async def test_get_routes(client, auth_header):
    response = await client.get('http://127.0.0.1/getRouters', headers=auth_header)
    response_data = extract_response(response)
    print(response_data)

from core.schema import ResponseCode


def extract_response(response, return_data=True):
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['code'] == ResponseCode.SUCCESS
    if return_data:
        return response_data['data']
    else:
        return response_data

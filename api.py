import requests
from models import ResponseResult


def perform_api_call(api_url, method, headers=dict(), body=dict()):
    if method.lower() in ['get', 'delete']:
        api_url = f"{api_url}?" + '&'.join([f"{k}={v}" for k, v in body.items()])
        
    if method.lower() == 'get':  
        response = requests.get(api_url, headers=headers)
    elif method.lower() == 'post':
        response = requests.post(api_url, headers=headers, json=body)
    elif method.lower() == 'put':
        response = requests.put(api_url, headers=headers, json=body)
    elif method.lower() == 'delete':
        response = requests.delete(api_url, headers=headers)
    elif method.lower() == 'patch':
        response = requests.patch(api_url, headers=headers, json=body)
    else:
        response = None

    if response is None:
        api_call_result = ResponseResult(False, 405, dict())
    else:
        api_call_result = ResponseResult(response.ok, response.status_code, response.json())

    return api_call_result

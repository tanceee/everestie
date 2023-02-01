import requests as r
from ..utils.constants import TEST_URL, HEADERS


def make_http_call(data, url, timeout=None):
    response = r.post(url=url, data=data, headers=HEADERS, verify=False, timeout=timeout)
    return response.content

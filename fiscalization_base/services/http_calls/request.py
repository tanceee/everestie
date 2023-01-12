import requests as r

from ..utils.constants import HEADERS


def make_http_call(data, url):
    response = r.post(url=url, data=data, headers=HEADERS, verify=False)
    return response.content

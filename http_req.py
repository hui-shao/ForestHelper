import json

import requests
from requests.cookies import RequestsCookieJar
from urllib import parse


# 自定义的HttpRequest模块
class HttpReq:
    def __init__(self, _remember_token):
        self.remember_token = _remember_token

    def my_requests(self, _method, _url, _data=None, _ex_hea=None):
        url_parse = parse.urlparse(_url)
        cookie_jar = RequestsCookieJar()
        str_json = json.dumps(_data)  # 注意, 不可使用str()方法转换
        hea = {
            "Accept": "*/*",
            "Accept-Encoding": "br, gzip, deflate",
            "Accept-Language": "zh-Hans-CN;q=1",
            "Connection": "keep-alive",
            "Content-Length": str(len(json.dumps(_data))),
            "Content-Type":
                "application/json; charset=utf-8",
            "Host": url_parse.netloc,
            "User-Agent": "okhttp/4.9.1"
        }
        if _ex_hea:
            hea.update(_ex_hea)
        if len(self.remember_token):
            cookie_jar.set("remember_token", self.remember_token, domain=url_parse.netloc)
        if _method.upper() == 'GET':
            res = requests.get(_url, data=str_json, headers=hea, cookies=cookie_jar)
        elif _method.upper() == 'POST':
            res = requests.post(_url, data=str_json, headers=hea, cookies=cookie_jar)
        elif _method.upper() == 'PUT':
            res = requests.put(_url, data=str_json, headers=hea, cookies=cookie_jar)
        elif _method.upper() == 'DELETE':
            res = requests.delete(_url, data=str_json, headers=hea, cookies=cookie_jar)
        else:
            print('TypeError')
            return None
        return res

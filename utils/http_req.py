import json
import time
import traceback
from urllib import parse

import requests
from requests.cookies import RequestsCookieJar

try:
    from utils.avalon import Avalon
except ModuleNotFoundError:
    from avalon import Avalon


# 自定义的HttpRequest模块
class HttpReq:
    def __init__(self, _remember_token):
        self.remember_token = _remember_token

    def my_requests(self, _method: str, _url: str, _data=None, _ex_hea=None):
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
        retry_n = 0
        while retry_n < 5:
            try:
                if _ex_hea:
                    hea.update(_ex_hea)
                if len(self.remember_token):
                    cookie_jar.set("remember_token", self.remember_token, domain=url_parse.netloc)
                if _method.upper() == 'GET':
                    res = requests.get(_url, data=str_json, headers=hea, cookies=cookie_jar, timeout=(12.05, 72))
                elif _method.upper() == 'POST':
                    res = requests.post(_url, data=str_json, headers=hea, cookies=cookie_jar, timeout=(12.05, 54))
                elif _method.upper() == 'PUT':
                    res = requests.put(_url, data=str_json, headers=hea, cookies=cookie_jar, timeout=(12.05, 54))
                elif _method.upper() == 'DELETE':
                    res = requests.delete(_url, data=str_json, headers=hea, cookies=cookie_jar, timeout=(12.05, 54))
                else:
                    Avalon.error('TypeError')
                    return None
            except requests.exceptions.SSLError:
                Avalon.error("SSL 错误, 2s后重试 -> SSLError: An SSL error occurred.")
                time.sleep(2)
            except requests.exceptions.ConnectTimeout:
                Avalon.error(
                    "建立连接超时, 5s后重试 -> ConnectTimeout: The request timed out while trying to connect to the remote server.")
                time.sleep(5)
            except requests.exceptions.ReadTimeout:
                Avalon.error(
                    "读取数据超时, 3s后重试 -> ReadTimeout: The server did not send any data in the allotted amount of time.")
                time.sleep(3)
            except requests.exceptions.ConnectionError:
                Avalon.error(f"{traceback.format_exc(3)}")
                Avalon.error("建立连接错误, 5s后重试", front="\n")
                time.sleep(5)
            except requests.exceptions.RequestException:
                Avalon.error(f"{traceback.format_exc(3)}")
                Avalon.error("其他网络连接错误, 5s后重试", front="\n")
                time.sleep(5)
            except KeyboardInterrupt:
                Avalon.warning("捕获到 KeyboardInterrupt, 退出", front="\n")
                return None
            else:
                return res
            retry_n += 1
            continue
        Avalon.error("达到最大重试次数, 退出", front="\n")
        return None

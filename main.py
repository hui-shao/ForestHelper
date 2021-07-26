# -*- coding: UTF-8 -*-
# @Time    : 2021/7/24 23:36
# @Author  : Hui-Shao
# %% imports
import json
import os
import random
import shutil
import sys
import time
from datetime import datetime, timedelta
from urllib import parse

import requests
import toml
from requests.cookies import RequestsCookieJar

from avalon import Avalon


# %% 建立用于保存用户文件的目录
def makedir():
    if not os.path.exists("UserFiles"):
        os.mkdir("UserFiles")
    else:
        pass


# %% 读取配置文件
def read_config():
    Avalon.info("读取配置文件中……")
    global config, username, passwd, uid, remember_token
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = toml.load(f)
    except UnicodeEncodeError:
        with open(config_file, "r", encoding="gbk") as f:
            config = toml.load(f)
    except IOError:
        Avalon.error(f"无法加载{config_file}, 请检查文件是否存在, 文件名是否正确")
        return False
    except Exception:
        Avalon.error(f"无法加载{config_file}, 其他错误")
        return False
    else:
        username = config["user"]["username"]
        passwd = config["user"]["password"]
        uid = config["user"]["uid"]
        remember_token = config["user"]["remember_token"]
        return True


# %% 写配置文件
def write_config():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    config_2 = config.copy()
    config_2["user"].update({"uid": uid, "remember_token": remember_token})
    try:
        f = open(config_file, "w+", encoding="utf-8")
        toml.dump(config_2, f)
        f.close()
    except IOError:
        Avalon.error("IOError")
        return False
    else:
        return True


# %% 自定义的HttpRequest模块
def _requests(_method, _url, _data=None, _ex_hea=None):
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
        "User-Agent": "Forest/342 (iPhone; iOS 12.1.2; Scale/3.00)"
    }
    if _ex_hea:
        hea.update(_ex_hea)
    if len(remember_token):
        cookie_jar.set("remember_token", remember_token, domain=url_parse.netloc)
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


# %% 登录 获取uid, remember_token 等信息
def login():
    Avalon.info("正在登录...", front="\n")
    global remember_token, uid
    data = {
        "session": {
            "email": username,
            "password": passwd,
        },
        "seekruid": ""
    }
    r = _requests("post", "https://c88fef96.forestapp.cc/api/v1/sessions", data, {})
    if r.status_code != 200:
        Avalon.error("登录可能失败")
        return False
    else:
        id_info = json.loads(r.text)
        remember_token = id_info["remember_token"]
        uid = id_info["user_id"]
        Avalon.info("登录成功, 欢迎你~: %s" % id_info["user_name"])
        return True


# %% 登出
def logout():
    Avalon.info("正在登出...", front="\n")
    global uid, remember_token
    url = f"https://c88fef96.forestapp.cc/api/v1/sessions/signout?seekrua=android_cn-4.20.1&seekruid={uid}"
    r = _requests("delete", url, {}, {})
    if r.status_code != 200:
        Avalon.error(f"登出可能失败")
        return False
    else:
        Avalon.info(f"登出成功")
        uid = 0
        remember_token = ""
        write_config()
        try:
            shutil.rmtree("UserFiles")
        except IOError:
            Avalon.warning("删除UserFiles目录失败, 在切换用户前务必手动删除！")
            return False
        return True


# %% 获取树种列表  树木的gid, 名称, 哪些已解释
def get_plants():
    file_name = "plants.json"

    def run():
        Avalon.info(f"正在获取已种植列表 ({file_name})", front="\n")
        if os.path.exists(f"UserFiles/{file_name}"):
            Avalon.info(f"发现本地已存在 {file_name} , 进行读取...")
            get_from_local()
        else:
            Avalon.warning(f"在本地未发现 {file_name} , 尝试从服务器端获取...")
            get_from_server()

    def get_from_local():
        global plants
        with open(f"UserFiles/{file_name}", "r", encoding="utf-8") as f:
            plants = json.loads(f.read())
        Avalon.info(f"从本地获取 已种植列表 ({file_name}) 成功")

    def get_from_server():
        global plants
        url = f"https://c88fef96.forestapp.cc/api/v1/plants?seekrua=android_cn-4.20.1&seekruid={uid}"
        r = _requests("get", url, {}, {})
        if r.status_code == 200:
            plants = json.loads(r.text)
            Avalon.info(f"从服务器端获取 已种植列表 ({file_name}) 成功")
            with open(f"UserFiles/{file_name}", "w", encoding="utf-8") as f:
                f.write(r.text)
            return True
        else:
            Avalon.error(f"从服务端获取 {file_name} 可能失败")
            return False

    try:
        run()
    except KeyboardInterrupt:
        Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")


# %% 获取树木种类列表
def get_coin_tree_types():
    file_name = "coin_tree_types.json"

    def run():
        Avalon.info(f"正在获取树木种类列表 ({file_name})", front="\n")
        if os.path.exists(f"UserFiles/{file_name}"):
            Avalon.info(f"发现本地已存在 {file_name} , 进行读取...")
            get_from_local()
        else:
            Avalon.warning(f"在本地未发现 {file_name} , 尝试从服务器端获取...")
            get_from_server()

    def get_from_local():
        global coin_tree_types
        with open(f"UserFiles/{file_name}", "r", encoding="utf-8") as f:
            coin_tree_types = json.loads(f.read())
        Avalon.info(f"从本地获取 已种植列表 ({file_name}) 成功")

    def get_from_server():
        global coin_tree_types
        url = f"https://c88fef96.forestapp.cc/api/v1/products/coin_tree_types?seekrua=android_cn-4.20.1&seekruid={uid}"
        r = _requests("get", url)
        if r.status_code == 200:
            coin_tree_types = json.loads(r.text)
            Avalon.info(f"从服务器端获取 树木种类列表 ({file_name}) 成功")
            with open(f"UserFiles/{file_name}", "w", encoding="utf-8") as f:
                f.write(r.text)
            return True
        else:
            Avalon.error(f"从服务端获取 {file_name} 可能失败")
            return False

    try:
        run()
    except KeyboardInterrupt:
        Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")


# %% 模拟观看广告删除枯树
def remove_plants_by_rewarded_ad():
    def run():
        dead_plants = find_dead_plant_id()
        if not dead_plants:
            Avalon.warning("当前plants.json中未发现枯树")
            return True
        for tree in dead_plants:
            Avalon.info(f"正在删除枯树...编号:%d  种类代码:%d  数量:%d棵" % (tree["id"], tree["tree_type_gid"], tree["tree_count"]),
                        front="\n")
            ad_session_token = get_ad_session_token()
            ad_token = get_ad_token(ad_session_token)
            if ad_token is False:
                return False
            else:
                time.sleep(1)
                if not simulate_watch_ad(ad_token, ad_session_token):
                    return False
                else:
                    time.sleep(0.5)
                    return delete_plants(tree["id"])

    # 从plants.json中查找枯树的id
    def find_dead_plant_id():
        Avalon.info("正在查找枯树的id...用时可能较长..请稍候...", front="\n")
        dead_trees = []
        if len(plants) <= 0:
            get_plants()
        for a in plants:
            if a["is_success"]:
                continue
            else:
                dead_trees.append(a)
                continue
        return dead_trees

    def get_ad_session_token():
        r = _requests("post", "https://receipt-system.seekrtech.com/projects/1/ad_sessions", {}, {})
        if (r.status_code == 201) or (r.status_code == 200):
            Avalon.info("获取 ad_session_token 成功")
            return json.loads(r.text)["token"]
        else:
            Avalon.error("获取 ad_session_token 失败")
            return False

    def get_ad_token(_ad_session_token):
        data = {"ad_session_token": f"{_ad_session_token}"}
        r = _requests("post", "https://receipt-system.seekrtech.com/sv_rewarded_ad_views", data, {})
        if (r.status_code == 201) or (r.status_code == 200):
            Avalon.info("获取 ad_token 成功")
            return json.loads(r.text)["token"]
        else:
            Avalon.error("获取 ad_token 失败")
            return False

    def simulate_watch_ad(_ad_token, _ad_session_token):
        url_1 = f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views/{_ad_token}/watched?seekrua=android_cn-4.20.1&seekruid={uid}"
        data_1 = {"ad_session_token": f"{_ad_session_token}"}
        r_1 = _requests("put", url_1, data_1)
        if r_1.status_code != 200:
            Avalon.error("模拟观看广告失败!  位置: 1")
            return False
        time.sleep(0.3)
        url_2 = f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views/{_ad_token}/claim?seekrua=android_cn-4.20.1&seekruid={uid}"
        data_2 = {"ad_session_token": f"{_ad_session_token}", "user_id": uid}
        r_2 = _requests("put", url_2, data_2)
        if r_2.status_code != 200:
            Avalon.error("模拟观看广告失败!  位置: 2")
            return False
        else:
            Avalon.info("模拟观看广告成功")
            return True

    def delete_plants(_id):
        if uid <= 0:
            Avalon.error("uid错误")
            return False
        url = f"https://c88fef96.forestapp.cc/api/v1/plants/{_id}/remove_plant_by_rewarded_ad?seekrua=android_cn-4.20.1&seekruid={uid}"
        r = _requests("delete", url)
        if r.status_code != 200:
            Avalon.error("删除种植记录失败!")
            if r.status_code == 422:
                Avalon.error("原因: Cannot find the product with given id")
            elif r.status_code == 403:
                Avalon.error("原因: 403 Forbidden. 请检查cookie")
            else:
                pass
            return False
        else:
            Avalon.info("删除种植记录成功")
            return True

    try:
        run()
    except KeyboardInterrupt:
        Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")


# %% 自动植树刷金币
def auto_plant():
    def run():
        plant_time = random.choice(list(range(30, 180, 5)))
        tree_type = str(random.randint(1, 110))
        note = random.choice(["学习", "娱乐", "工作", "锻炼", "休息", "其他"])
        i = 1
        while i <= config["auto_plant"]["number"]:
            plant_a_tree(tree_type, plant_time, note, i)
            Avalon.info(f"将在 {plant_time} min后种植下一棵树")
            time.sleep(plant_time * 60)
            i += 1

    try:
        run()
    except KeyboardInterrupt:
        Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")


# %% 按照时间段种树
def manually_plant():
    def run():
        i = 1
        while 1:
            tree_type = int(Avalon.gets("请输入树的种类编码(-1为退出): ", front="\n"))
            if tree_type == -1:
                break
            plant_time = int(Avalon.gets("请输入种树时长(单位为分钟 应输入5的倍数): "))
            note = str(Avalon.gets("请输入植树备注(可选): "))
            while 1:
                end_time = str(Avalon.gets("请输入植树完成时的时间. 格式为 \'2021-07-24 17:30:05\' (可选): "))
                if not len(end_time):
                    break  # 如果没有指定end_time, 则跳出循环, 防止被当成异常而被捕获
                try:
                    datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")  # 尝试将str转换为datetime, 以检查格式是否错误
                except ValueError:
                    Avalon.warning("日期输入有误，请重新输入", end="\n")
                else:
                    break
            print("\n")
            plant_a_tree(tree_type, plant_time, note, i, end_time)
            i += 1

    try:
        run()
    except KeyboardInterrupt:
        Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")


# %% 种植一棵树
def plant_a_tree(_tree_type, _plant_time, _note, _number, _end_time=""):
    """
    :param _plant_time: 种植时长 以分钟为单位 接受5的整数倍(int)
    :param _tree_type: 树的种类 (int)
    :param _note: 植树备注(str)
    :param _number: 树的编号, 用于控制台输出(int)
    :param _end_time: 种植完成的时间(str) 格式 2021-07-24 17:30:05
    :return:
    """
    if len(_end_time):
        end_time = datetime.strptime(_end_time, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8)  # 注: 减去8小时是为了换算时区, 下同
        start_time = end_time - timedelta(minutes=_plant_time)
    else:
        end_time = datetime.now() - timedelta(hours=8)
        start_time = (end_time - timedelta(minutes=_plant_time))
    data = {
        "plant": {
            "end_time": end_time.isoformat(),
            "longitude": 0,
            "note": _note,
            "is_success": 1,
            "room_id": 0,
            "die_reason": '',
            "tag": random.randint(1, 6),
            "latitude": 0,
            "has_left": 0,
            "start_time": start_time.isoformat(),
            "trees": [{
                "phase": 4,
                "theme": 0,
                "is_dead": 0,
                "position": -1,
                "tree_type": _tree_type
            }]
        },
        "seekruid": uid
    }
    res = _requests("post", 'https://c88fef96.forestapp.cc/api/v1/plants', data, {})
    try:
        result = json.loads(res.text)
        if result["is_success"]:
            Avalon.info(f"第 {_number} 棵植树成功")
            return True
        else:
            Avalon.error(f"第 {_number} 棵植树失败")
            return False
    except Exception:
        Avalon.error(f"第 {_number} 棵植树失败")
        return False


def main():
    makedir()
    read_config()
    if uid * len(remember_token) == 0:
        login()
        write_config()
    if config["remove_plants_by_rewarded_ad"]["enable"]:
        remove_plants_by_rewarded_ad()
    if config["auto_plant"]["enable"]:
        auto_plant()
    if config["manually_plant"]["enable"]:
        manually_plant()
    Avalon.info("所有任务执行完毕~", front="\n")


if __name__ == '__main__':
    config = {}
    plants = []
    coin_tree_types = {}
    username = ""
    passwd = ""
    remember_token = ""
    uid = 0
    os.chdir(sys.path[0])
    main()
    sys.exit(0)

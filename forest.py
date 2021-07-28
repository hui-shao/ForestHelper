# -*- coding: UTF-8 -*-
# @Time    : 2021/7/27 15:18
# @Author  : Hui-Shao
import json
import os
import random
import time
from datetime import datetime, timedelta
from urllib import parse

import requests
from requests.cookies import RequestsCookieJar

from avalon import Avalon


class Forest:
    def __init__(self, _username, _passwd, _uid, _remember_token):
        self.username = _username
        self.passwd = _passwd
        self.uid = _uid
        self.remember_token = _remember_token
        self.plants = []
        self.coin_tree_types = {}

    # %% 自定义的HttpRequest模块
    def _requests(self, _method, _url, _data=None, _ex_hea=None):
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

    # %% 登录 获取uid, remember_token 等信息
    def login(self):
        """
        :return: 若登录成功，则返回包含 uid 和 remember_token 的一个字典。否则返回空字典
        """
        Avalon.info("正在登录...", front="\n")
        data = {
            "session": {
                "email": self.username,
                "password": self.passwd,
            },
            "seekruid": ""
        }
        r = self._requests("post", "https://c88fef96.forestapp.cc/api/v1/sessions", data, {})
        if r.status_code == 403:
            Avalon.error("登录失败! 请检查账号及密码 响应代码: 403 Forbidden")
            return {}
        elif r.status_code != 200:
            Avalon.error(f"登录可能失败 响应代码: {r.status_code}")
            return {}
        else:
            id_info = json.loads(r.text)
            self.remember_token = id_info["remember_token"]
            self.uid = id_info["user_id"]
            Avalon.info("登录成功, 欢迎你~: %s" % id_info["user_name"])
            return {"uid": self.uid, "remember_token": self.remember_token}

    # %% 登出
    def logout(self):
        Avalon.info("正在登出...", front="\n")
        url = f"https://c88fef96.forestapp.cc/api/v1/sessions/signout?seekrua=android_cn-4.41.0&seekruid={self.uid}"
        r = self._requests("delete", url, {}, {})
        if r.status_code != 200:
            Avalon.error(f"登出可能失败")
            return False
        else:
            Avalon.info(f"登出成功")
            self.uid = 0
            self.remember_token = ""
            return True

    # %% 获取树种列表  树木的gid, 名称, 哪些已解释
    def get_plants(self, _force_update=False):
        file_name = "plants.json"

        def run():
            Avalon.info(f"正在获取已种植列表 ({file_name})", front="\n")
            if _force_update:
                Avalon.info("已启用强制更新 plants.json")
                get_from_server()
            else:
                if os.path.exists(f"UserFiles/{file_name}"):
                    Avalon.info(f"发现本地已存在 {file_name} , 进行读取...")
                    get_from_local()
                else:
                    Avalon.warning(f"在本地未发现 {file_name} , 尝试从服务器端获取...")
                    get_from_server()

        def get_from_local():
            with open(f"UserFiles/{file_name}", "r", encoding="utf-8") as f:
                self.plants = json.loads(f.read())
            Avalon.info(f"从本地获取 已种植列表 ({file_name}) 成功")

        def get_from_server():
            url = f"https://c88fef96.forestapp.cc/api/v1/plants?seekrua=android_cn-4.41.0&seekruid={self.uid}"
            r = self._requests("get", url, {}, {})
            if r.status_code == 200:
                self.plants = json.loads(r.text)
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
    def get_coin_tree_types(self):
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
            with open(f"UserFiles/{file_name}", "r", encoding="utf-8") as f:
                self.coin_tree_types = json.loads(f.read())
            Avalon.info(f"从本地获取 已种植列表 ({file_name}) 成功")

        def get_from_server():
            url = f"https://c88fef96.forestapp.cc/api/v1/products/coin_tree_types?seekrua=android_cn-4.41.0&seekruid={self.uid}"
            r = self._requests("get", url)
            if r.status_code == 200:
                self.coin_tree_types = json.loads(r.text)
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
    def remove_plants_by_rewarded_ad(self):
        def run():
            Avalon.info("========== 当前任务: 删除枯树 ==========", front="\n")
            dead_plants = find_dead_plant_id()
            if not dead_plants:
                Avalon.warning("当前plants.json中未发现枯树")
                return True
            for tree in dead_plants:
                Avalon.info(
                    f"正在删除枯树...编号:%d  种类代码:%d  数量:%d棵" % (tree["id"], tree["tree_type_gid"], tree["tree_count"]),
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
            if len(self.plants) <= 0:
                self.get_plants(True)
            for a in self.plants:
                if a["is_success"]:
                    continue
                else:
                    dead_trees.append(a)
                    continue
            return dead_trees

        def get_ad_session_token():
            r = self._requests("post", "https://receipt-system.seekrtech.com/projects/1/ad_sessions", {}, {})
            if (r.status_code == 201) or (r.status_code == 200):
                Avalon.info("获取 ad_session_token 成功")
                return json.loads(r.text)["token"]
            else:
                Avalon.error("获取 ad_session_token 失败")
                return False

        def get_ad_token(_ad_session_token):
            data = {"ad_session_token": f"{_ad_session_token}"}
            r = self._requests("post", "https://receipt-system.seekrtech.com/sv_rewarded_ad_views", data, {})
            if (r.status_code == 201) or (r.status_code == 200):
                Avalon.info("获取 ad_token 成功")
                return json.loads(r.text)["token"]
            else:
                Avalon.error("获取 ad_token 失败")
                return False

        def simulate_watch_ad(_ad_token, _ad_session_token):
            url_1 = f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views/{_ad_token}/watched?seekrua=android_cn-4.41.0&seekruid={self.uid}"
            data_1 = {"ad_session_token": f"{_ad_session_token}"}
            r_1 = self._requests("put", url_1, data_1)
            if r_1.status_code != 200:
                Avalon.error("模拟观看广告失败!  位置: 1")
                return False
            time.sleep(0.3)
            url_2 = f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views/{_ad_token}/claim?seekrua=android_cn-4.41.0&seekruid={self.uid}"
            data_2 = {"ad_session_token": f"{_ad_session_token}", "user_id": self.uid}
            r_2 = self._requests("put", url_2, data_2)
            if r_2.status_code != 200:
                Avalon.error("模拟观看广告失败!  位置: 2")
                return False
            else:
                Avalon.info("模拟观看广告成功")
                return True

        def delete_plants(_id):
            if self.uid <= 0:
                Avalon.error("uid错误")
                return False
            url = f"https://c88fef96.forestapp.cc/api/v1/plants/{_id}/remove_plant_by_rewarded_ad?seekrua=android_cn-4.41.0&seekruid={self.uid}"
            r = self._requests("delete", url)
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

    # %% 创建房间(一起种)
    def create_room(self):
        def run():
            Avalon.info("========== 当前任务: 创建房间 ==========", front="\n")
            room_info = create()
            if not len(room_info):
                Avalon.error("未获取到服务器返回的房间信息!")
                return None
            try:
                Avalon.info("接下来将显示房间内成员数, 当人数足够(大于1)时请按下 \"Ctrl + C\"")
                i = 1
                while i <= 100:
                    members_info = get_members_info(room_info["id"])
                    name_list = []
                    for user in members_info["participants"]:
                        name_list.append(user["name"])
                    Avalon.info(f"循环次数: {i} 当前人数: {members_info['participants_count']} -> id: {name_list}", end="\r")
                    time.sleep(15)
                    i += 1
                Avalon.warning("达到最大循环次数, 自动退出成员监视", front="\n")
            except KeyboardInterrupt:
                Avalon.info("捕获 KeyboardInterrupt, 已退出成员监视 ", front="\n")
            if str(Avalon.gets("是否保留该房间 -> 1.是 2.否 : ")) == "2":
                leave(room_info["id"])
                return None
            if str(Avalon.gets("是否开始 -> 1.是 2.否 : ")) == "1":
                plant_time = int(room_info["target_duration"]) / 60
                end_time = datetime.strftime(
                    datetime.now() + timedelta(minutes=plant_time), "%Y-%m-%d %H:%M:%S")
                start(room_info["id"], end_time)
                Avalon.info("开始发送种植信息...")
                self.plant_a_tree("countdown", room_info["tree_type"], plant_time, "", 1, end_time, room_info["id"])
            return None

        def create():
            tree_type = int(Avalon.gets("请输入树的种类编码(-1为退出): ", front="\n"))
            if tree_type == -1:
                return None
            plant_time = int(Avalon.gets("请输入种树时长(分钟): "))
            if plant_time % 5 != 0:
                plant_time = int(plant_time / 5) * 5
            data = {
                "is_birthday_2019_client": True,  # 不知道有什么用
                "target_duration": plant_time * 60,
                "tree_type": tree_type,
                "room_type": "chartered"
            }
            res = self._requests("post",
                                 f'https://c88fef96.forestapp.cc/api/v1/rooms?seekrua=android_cn-4.41.0&seekruid={self.uid}',
                                 data, {})
            if res.status_code != 201:
                Avalon.error(f"创建房间可能失败  响应码: {res.status_code}")
                return None
            try:
                result = json.loads(res.text)
                Avalon.info(f"房间创建成功!  token: {result['token']}")
                return result
            except Exception as err_info:
                Avalon.error(f"创建失败 原因: {err_info}")
                return None

        def get_members_info(_room_id):
            res = self._requests("get", f'https://c88fef96.forestapp.cc/api/v1/rooms/{_room_id}',
                                 {"is_birthdat_2019_client": True, "detail": True, "seekrua": "android_cn-4.41.0",
                                  "seekruid": self.uid}, {})
            if res.status_code != 200:
                Avalon.error(f"获取成员信息可能失败  响应码: {res.status_code}")
                return None
            else:
                result = json.loads(res.text)
                return result

        def leave(_room_id):
            res = self._requests("put",
                                 f'https://c88fef96.forestapp.cc/api/v1/rooms/{_room_id}/leave?seekrua=android_cn-4.41.0&seekruid={self.uid}',
                                 {}, {})
            if res.status_code != 200:
                Avalon.error(f"退出房间可能失败  响应码: {res.status_code}")
                return False
            else:
                Avalon.info("退出房间成功")
            return True

        def start(_room_id, _end_time):
            res = self._requests("put",
                                 f'https://c88fef96.forestapp.cc/api/v1/rooms/{_room_id}/start?seekrua=android_cn-4.41.0&seekruid={self.uid}',
                                 {}, {})
            if res.status_code == 423:
                Avalon.error(f"房间开始失败, 人数不足")
                return False
            elif res.status_code != 200:
                Avalon.error(f"房间开始可能失败  响应码: {res.status_code}")
                return False
            else:
                result = json.loads(res.text)
                Avalon.info(
                    f"房间开始成功! 共计{result['participants_count']}人  预计完成时间: {_end_time}")
                return True

        try:
            run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")

    # %% 自动植树刷金币
    def auto_plant(self, _total_n):
        def run():
            Avalon.info("========== 当前任务: 自动植树 ==========", front="\n")
            plant_time = random.choice(list(range(30, 180, 5)))
            tree_type = str(random.randint(1, 110))
            note = random.choice(["学习", "娱乐", "工作", "锻炼", "休息", "其他"])
            i = 1
            while i <= _total_n:
                self.plant_a_tree("countdown", tree_type, plant_time, note, i)
                Avalon.info(f"将在 {plant_time} min后种植下一棵树")
                time.sleep(plant_time * 60)
                i += 1

        try:
            run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")

    # %% 手动植树
    def manually_plant(self):
        def run():
            Avalon.info("========== 当前任务: 手动种植 ==========", front="\n")
            i = 1
            while 1:
                tree_type = int(Avalon.gets("请输入树的种类编码(-1为退出): ", front="\n"))
                if tree_type == -1:
                    break
                plant_mode = "countup" if str(Avalon.gets("选择种植模式 -> 1.倒计时 2.正计时 : ")) == "2" else "countdown"
                plant_time = int(Avalon.gets("请输入种树时长(分钟): "))
                if (plant_mode == "countdown") and (plant_time % 5 != 0):
                    plant_time = int(plant_time / 5) * 5
                note = str(Avalon.gets("请输入植树备注(可选): "))
                while 1:
                    end_time = str(Avalon.gets("请输入植树完成时的时间. 格式为 \'2021-07-24 17:30:05\' (可选): "))
                    if not len(end_time):
                        break  # 如果没有指定end_time, 则跳出循环, 防止被当成异常而被捕获
                    try:
                        datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")  # 尝试将str转换为datetime, 以检查格式是否错误
                    except ValueError:
                        Avalon.warning("日期输入有误，请重新输入")
                    else:
                        break
                self.plant_a_tree(plant_mode, tree_type, plant_time, note, i, end_time)
                i += 1

        try:
            run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")

    # %% 种植一棵树
    def plant_a_tree(self, _plant_mode, _tree_type, _plant_time, _note, _number, _end_time="", _room_id=-1):
        """
        :param _plant_mode: 种植模式(str) 接受 "countup"（正计时） 和 "countdown"（倒计时）
        :param _plant_time: 种植时长 以分钟为单位
        :param _tree_type: 树的种类 (int)
        :param _note: 植树备注(str)
        :param _number: 树的编号, 用于控制台输出(int)
        :param _end_time: 种植完成的时间(str) 格式 2021-07-24 17:30:05
        :param _room_id: 一起种模式下的房间ID(int)
        :return:
        """
        if len(_end_time):
            end_time = datetime.strptime(_end_time, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8)  # 注: 减去8小时是为了换算时区, 下同
            start_time = end_time - timedelta(minutes=_plant_time)
        else:
            end_time = datetime.now() - timedelta(hours=8)
            start_time = (end_time - timedelta(minutes=_plant_time))
        trees_list = []  # 储存植树信息, 用于data的构造
        tree_count = int(_plant_time / 30)
        if tree_count > 4:  # forest规定最多只能种4棵树，最少1棵树
            tree_count = 4
        elif tree_count < 1:
            tree_count = 1
        for i in range(0, tree_count, 1):  # 要种几棵树, trees里面就要有几个元素
            trees_list.append({
                "plant_id": -1,  # 本来应该取 len(plants) 然后再加个1，但是这里直接传 -1 似乎也没影响
                "tree_type": _tree_type,
                "is_dead": False,
                "phase": i + 4
            })
        data = {
            "plant": {
                "id": -1,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "mode": _plant_mode,
                "is_success": True,
                "die_reason": '',
                "tag": random.randint(1, 6),
                "note": _note,
                "has_left": False,
                "deleted": False,
                "room_id": _room_id,
                "trees": trees_list
            },
            "seekruid": self.uid
        }
        res = self._requests("post",
                             f'https://c88fef96.forestapp.cc/api/v1/plants?seekrua=android_cn-4.41.0&seekruid={self.uid}',
                             data, {})
        try:
            result = json.loads(res.text)
            if result["is_success"]:
                count = result["tree_count"]
                Avalon.info(f"第 {_number} 棵植树成功  数量: {count}")
                return True
            else:
                Avalon.error(f"第 {_number} 棵植树失败  响应码: {res.status_code}  {result}")
                return False
        except Exception:
            Avalon.error(f"第 {_number} 棵植树失败  响应码: {res.status_code}")
            return False

# -*- coding: UTF-8 -*-
# @Time    : 2021/7/27 15:18
# @Author  : Hui-Shao
import json
import os
import random
import time
from datetime import datetime, timedelta

import requests

from avalon import Avalon
from http_req import HttpReq


class Forest:
    def __init__(self, _user):
        self.user = _user
        self.req = HttpReq(self.user.remember_token)
        self.plants = []
        self.coin_tree_types = {}

    # %% 登录 获取uid, remember_token 等信息
    def login(self):
        """
        :return: 若登录成功，则返回包含 uid 和 remember_token 的一个字典。否则返回空字典
        """
        Avalon.info("正在登录...", front="\n")
        data = {
            "session": {
                "email": self.user.username,
                "password": self.user.passwd,
            },
            "seekruid": ""
        }
        r = self.req.my_requests("post", "https://c88fef96.forestapp.cc/api/v1/sessions", data, {})
        if r.status_code == 403:
            Avalon.error("登录失败! 请检查账号及密码 响应代码: 403 Forbidden")
            return {}
        elif r.status_code != 200:
            Avalon.error(f"登录可能失败 响应代码: {r.status_code}")
            return {}
        else:
            id_info = json.loads(r.text)
            self.user.remember_token = id_info["remember_token"]
            self.req.remember_token = id_info["remember_token"]  # 首次登陆调用 login() 后必须更新 req.remember_token 的值, 否则相当于未登录
            self.user.uid = id_info["user_id"]
            Avalon.info("登录成功, 欢迎你~: %s" % id_info["user_name"])
            return {"uid": self.user.uid, "remember_token": self.user.remember_token}

    # %% 登出
    def logout(self):
        Avalon.info("正在登出...", front="\n")
        url = f"https://c88fef96.forestapp.cc/api/v1/sessions/signout?seekrua=android_cn-4.41.0&seekruid={self.user.uid}"
        r = self.req.my_requests("delete", url, {}, {})
        if r.status_code != 200:
            Avalon.error(f"登出可能失败")
            return False
        else:
            Avalon.info(f"登出成功")
            self.user.uid = 0
            self.user.remember_token = ""
            return True

    # %% 获取树种列表  树木的gid, 名称, 哪些已解锁
    def get_plants(self, _force_update=False):
        file_name = "plants.json"

        def run():
            Avalon.info(f"正在获取已种植列表 ({file_name})")
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
            url = f"https://c88fef96.forestapp.cc/api/v1/plants?seekrua=android_cn-4.41.0&seekruid={self.user.uid}"
            r = self.req.my_requests("get", url, {}, {})
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
            url = f"https://c88fef96.forestapp.cc/api/v1/products/coin_tree_types?seekrua=android_cn-4.41.0&seekruid={self.user.uid}"
            r = self.req.my_requests("get", url)
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

    # %% 获取指定用户概述
    def get_user_profile(self, _target_user_id):
        """
        获取指定用户的 Profile
        :param _target_user_id: 目标用户的id
        :return: (json)
        """
        try:
            res = self.req.my_requests("get", f"https://c88fef96.forestapp.cc/api/v1/users/{_target_user_id}/profile",
                                       {"seekrua": "android_cn-4.41.0", "seekruid": self.user.uid}, {})
        except (ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout,
                requests.exceptions.SSLError):
            return {}
        except Exception:
            return {}
        else:
            if res.status_code == 200:
                return json.loads(res.text)
            else:
                return {}

    # %% 模拟观看广告操作
    def simulate_watch_ad(self):
        """
        模拟观看广告操作
        :return: (bool)
        """

        def run():
            ad_session_token = get_ad_session_token()
            if ad_session_token is False:
                return False
            ad_token = get_ad_token(ad_session_token)
            if ad_token is False:
                return False
            time.sleep(1)
            return simulate_watch(ad_token, ad_session_token)

        def get_ad_session_token():
            """
            获取 ad_session_token 以便接下来获取 ad_token
            """
            r = self.req.my_requests("post", "https://receipt-system.seekrtech.com/projects/1/ad_sessions", {}, {})
            if (r.status_code == 201) or (r.status_code == 200):
                Avalon.info("获取 ad_session_token 成功")
                return json.loads(r.text)["token"]
            else:
                Avalon.error("获取 ad_session_token 失败")
                return False

        def get_ad_token(_ad_session_token):
            data = {"ad_session_token": f"{_ad_session_token}"}
            r = self.req.my_requests("post",
                                     f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views?seekrua=android_cn-4.41.0&seekruid={self.user.uid}",
                                     data, {})
            if (r.status_code == 201) or (r.status_code == 200):
                Avalon.info("获取 ad_token 成功")
                return json.loads(r.text)["token"]
            else:
                Avalon.error("获取 ad_token 失败")
                return False

        def simulate_watch(_ad_token, _ad_session_token):
            res_1 = self.req.my_requests("put",
                                         f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views/{_ad_token}/watched?seekrua=android_cn-4.41.0&seekruid={self.user.uid}",
                                         {"ad_session_token": f"{_ad_session_token}"})
            if res_1.status_code != 200:
                Avalon.error("模拟观看广告失败!  位置: 1 -> watched")
                return False
            time.sleep(0.3)
            res_2 = self.req.my_requests("put",
                                         f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views/{_ad_token}/claim?seekrua=android_cn-4.41.0&seekruid={self.user.uid}",
                                         {"ad_session_token": f"{_ad_session_token}", "user_id": self.user.uid})
            if res_2.status_code != 200:
                Avalon.error("模拟观看广告失败!  位置: 2 -> claim")
                return False
            else:
                Avalon.info("模拟观看广告成功")
                return True

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")

    # %% 模拟观看广告删除枯树
    def remove_plants_by_rewarded_ad(self):
        """
        通过模拟观看广告从而免金币删除枯树
        :return: (bool)
        """

        def run():
            Avalon.info("========== 当前任务: 删除枯树 ==========", front="\n")
            dead_plants = find_dead_plant_id()
            if not dead_plants:
                Avalon.warning("当前plants.json中未发现枯树 已退出")
                return True
            Avalon.info(f"已找到枯树数据共计 {len(dead_plants)} 组")
            for tree in dead_plants:
                Avalon.info("正在删除枯树...编号:%d  种类代码:%d  数量:%d棵" % (tree["id"], tree["tree_type_gid"], tree["tree_count"]))
                if self.simulate_watch_ad() is False:
                    return False
                else:
                    time.sleep(0.5)
                    delete_plants(tree["id"])
            return True

        # 从plants.json中查找枯树的id
        def find_dead_plant_id():
            dead_trees = []
            if len(self.plants) <= 0:
                self.get_plants(True)
            Avalon.info("正在查找枯树的id...用时可能较长..请稍候...")
            for a in self.plants:
                if a["is_success"]:
                    continue
                else:
                    dead_trees.append(a)
                    continue
            return dead_trees

        def delete_plants(_id):
            if self.user.uid <= 0:
                Avalon.error("uid错误")
                return False
            url = f"https://c88fef96.forestapp.cc/api/v1/plants/{_id}/remove_plant_by_rewarded_ad?seekrua=android_cn-4.41.0&seekruid={self.user.uid}"
            r = self.req.my_requests("delete", url)
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
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")

    # %% 模拟观看广告加速种植
    def boost_plant_by_rewarded_ad(self, _plant_id):
        def run():
            Avalon.info("正在尝试获取双倍金币...")
            try:
                if self.simulate_watch_ad() is False:
                    return False
                res = self.req.my_requests("put",
                                           f"https://c88fef96.forestapp.cc/api/v1/plants/{_plant_id}/boost_plant_by_rewarded_ad",
                                           {"seekrua": "android_cn-4.41.0", "seekruid": self.user.uid}, {})
            except (ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout,
                    requests.exceptions.SSLError):
                Avalon.error("网络连接超时")
                return False
            except Exception as err_info:
                Avalon.error(f"未知错误! {err_info}")
                return False
            else:
                if res.status_code == 200:
                    Avalon.info(f"获取双倍金币成功")
                    return True
                else:
                    Avalon.error(f"获取双倍金币失败!  返回码: {res.status_code}")
                    return False

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到KeyboardInterrupt, 退出")

    # %% 创建房间(一起种)
    def create_room(self, _boost_by_ad):
        def run():
            Avalon.info("========== 当前任务: 创建房间 ==========", front="\n")
            room_info_basic = create()
            if not len(room_info_basic):
                Avalon.error("未获取到服务器返回的房间信息! 当前任务退出")
                return None
            elif "exit" in room_info_basic:
                return None
            try:
                Avalon.info("接下来将显示房间内成员数, 当人数足够(大于1)时请按下 \"Ctrl + C\"")
                i = 1
                while i <= 100:
                    room_info_detail = get_room_info(room_info_basic["id"])
                    name_list = []
                    for user in room_info_detail["participants"]:
                        user_info = f"{user['name']} {user['user_id']}"
                        user_profile = self.get_user_profile(user["user_id"])
                        if len(user_profile) > 0:
                            success_rate = 100 * user_profile["health_count"] / (
                                    user_profile["health_count"] + user_profile["death_count"])
                            success_rate = round(success_rate, 2)
                            user_info += f" {success_rate}%"
                        name_list.append(user_info)
                    Avalon.info(f"循环次数: {i} 当前人数: {room_info_detail['participants_count']} -> id: {name_list}",
                                end="\r")
                    time.sleep(15)
                    i += 1
                Avalon.warning("达到最大循环次数, 自动退出成员监视", front="\n")
            except KeyboardInterrupt:
                Avalon.info("捕获 KeyboardInterrupt, 已退出成员监视 ", front="\n")
            if not Avalon.ask("是否保留该房间?"):
                leave(room_info_basic["id"])
                return None
            if Avalon.ask("是否有需要移除的成员?"):
                kick_uid_list = str(Avalon.gets("输入需要移除的成员的uid, 用空格分隔: ")).split(" ")
                kick(room_info_basic["id"], kick_uid_list)
            if Avalon.ask("是否开始?"):
                plant_time = int(room_info_basic["target_duration"]) / 60
                end_time = datetime.strftime(
                    datetime.now() + timedelta(minutes=plant_time), "%Y-%m-%d %H:%M:%S")
                if start(room_info_basic["id"], end_time):
                    Avalon.info("开始发送种植信息...")
                    self.plant_a_tree("countdown", room_info_basic["tree_type"], plant_time, "", 1, _boost_by_ad,
                                      end_time, room_info_basic["id"])
            return None

        def create():
            tree_type = int(Avalon.gets("请输入树的种类编码(-1为退出): ", front="\n"))
            if tree_type == -1:
                return {"exit": True}
            plant_time = int(Avalon.gets("请输入种树时长(分钟): "))
            if plant_time % 5 != 0:
                plant_time = int(plant_time / 5) * 5
            data = {
                "is_birthday_2019_client": True,  # 不知道有什么用
                "target_duration": plant_time * 60,
                "tree_type": tree_type,
                "room_type": "chartered"
            }
            res = self.req.my_requests("post",
                                       f'https://c88fef96.forestapp.cc/api/v1/rooms?seekrua=android_cn-4.41.0&seekruid={self.user.uid}',
                                       data, {})
            if res.status_code != 201:
                Avalon.error(f"创建房间可能失败  响应码: {res.status_code}")
                return {}
            try:
                result = json.loads(res.text)
                Avalon.info(f"房间创建成功!  token: {result['token']}")
                return result
            except json.decoder.JSONDecodeError:
                Avalon.error(f"房间创建失败! 载入服务器返回Text失败")
                return {}
            except Exception as err_info:
                Avalon.error(f"创建失败 原因: {err_info}")
                return {}

        def get_room_info(_room_id):
            res = self.req.my_requests("get", f'https://c88fef96.forestapp.cc/api/v1/rooms/{_room_id}',
                                       {"is_birthdat_2019_client": True, "detail": True, "seekrua": "android_cn-4.41.0",
                                        "seekruid": self.user.uid}, {})
            if res.status_code != 200:
                Avalon.error(f"获取房间详细信息可能失败  响应码: {res.status_code}")
                return None
            else:
                result = json.loads(res.text)
                return result

        def kick(_room_id, _uid_list):
            if not len(_uid_list):
                Avalon.warning("未接收到传入的uid")
                return False
            for uid_str in _uid_list:
                try:
                    res = self.req.my_requests("put", f"https://c88fef96.forestapp.cc/api/v1/rooms/{_room_id}/kick",
                                               {"user_id": int(uid_str), "seekrua": "android_cn-4.41.0",
                                                "seekruid": self.user.uid}, {})
                except ValueError:
                    Avalon.warning(f"输入的uid \"{uid_str}\" 有误, 已跳过")
                    continue
                except (ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout,
                        requests.exceptions.SSLError):
                    Avalon.error("网络连接超时")
                    continue
                except Exception as err_info:
                    Avalon.error(f"未知错误! {err_info}")
                    return False
                else:
                    if res.status_code == 200:
                        Avalon.info(f"移除成员 {uid_str} 成功")
                        continue
                    elif res.status_code == 410:
                        Avalon.warning(f"成员 {uid_str} 不存在")
                        continue
                    else:
                        Avalon.error(f"移除成员 {uid_str} 失败!  返回码: {res.status_code}")
                        continue
            return True

        def leave(_room_id):
            res = self.req.my_requests("put",
                                       f'https://c88fef96.forestapp.cc/api/v1/rooms/{_room_id}/leave?seekrua=android_cn-4.41.0&seekruid={self.user.uid}',
                                       {}, {})
            if res.status_code != 200:
                Avalon.error(f"退出房间可能失败  响应码: {res.status_code}")
                return False
            else:
                Avalon.info("退出房间成功")
            return True

        def start(_room_id, _end_time):
            res = self.req.my_requests("put",
                                       f'https://c88fef96.forestapp.cc/api/v1/rooms/{_room_id}/start?seekrua=android_cn-4.41.0&seekruid={self.user.uid}',
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
    def auto_plant(self, _total_n, _boost_by_ad, _by_time_frame):
        def run():
            Avalon.info("========== 当前任务: 自动植树 ==========", front="\n")
            if _by_time_frame:
                mode_1()
            else:
                mode_2()

        def mode_1():
            i = 1
            endtime_list = gen_list()
            while i <= len(endtime_list):
                tree_type = random.randint(1, 80)
                plant_time = random.choice(list(range(120, 185, 5)))  # 随机选择范围在 [120,185) 之间的 5 的倍数作为时长
                note = f"{tree_type}"
                end_time = endtime_list[i - 1]
                print("\n")
                self.plant_a_tree("countdown", tree_type, plant_time, note, i, _boost_by_ad, end_time)
                sleep_time = random.randint(2, 10) + random.random()
                sleep_time = round(sleep_time, 2)
                Avalon.info(f"Wait {sleep_time} seconds")
                time.sleep(sleep_time)
                i += 1

        def mode_2():
            plant_time = random.choice(list(range(30, 180, 5)))
            tree_type = str(random.randint(1, 110))
            note = random.choice(["学习", "娱乐", "工作", "锻炼", "休息", "其他"])
            i = 1
            while i <= _total_n:
                self.plant_a_tree("countdown", tree_type, plant_time, note, i, _boost_by_ad)
                Avalon.info(f"将在 {plant_time} min后种植下一棵树")
                time.sleep(plant_time * 60)
                i += 1

        def gen_list():
            time_list = []
            target_time = datetime.strptime(Avalon.gets("输入起始时间 (格式为 2021-01-01 00:00:00) : "), "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(Avalon.gets("输入结束时间 (格式为 2021-12-31 00:00:00) : "), "%Y-%m-%d %H:%M:%S")
            max_tree_num = abs((end_time - target_time).days * 12)  # 每天最多种 12 棵 2h 的树木
            for i in range(0, max_tree_num + 10, 1):
                # 以下: 以三小时以上的间隔来生成植树完成的时间 (因为后方植树时间设置在 120min-180min 之间)
                target_time = target_time + timedelta(minutes=random.randint(185, 210)) + timedelta(
                    seconds=random.randint(1, 59))
                # 以下: 控制植树完成时间在 9:00 ~ 23:45 之间
                while target_time.hour > 23 and target_time.minute > 45:
                    target_time = target_time + timedelta(hours=9)
                while target_time.hour < 9:
                    target_time = target_time + timedelta(minutes=random.randint(25, 60))
                if (time.mktime(end_time.timetuple()) - time.mktime(
                        target_time.timetuple())) < 0:  # 通过比较时间戳以控制植树完成时间在截止时间前面
                    break
                target_time_s = datetime.strftime(target_time, "%Y-%m-%d %H:%M:%S")
                time_list.append(target_time_s)
            return time_list

        try:
            run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")

    # %% 手动植树
    def manually_plant(self, _boost_by_ad):
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
                self.plant_a_tree(plant_mode, tree_type, plant_time, note, i, _boost_by_ad, end_time)
                i += 1

        try:
            run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到KeyboardInterrupt, 退出当前任务")

    # %% 种植一棵树
    def plant_a_tree(self, _plant_mode, _tree_type, _plant_time, _note, _number, _boost_by_ad, _end_time="",
                     _room_id=-1):
        """
        :param _plant_mode: 种植模式(str) 接受 "countup"（正计时） 和 "countdown"（倒计时）
        :param _plant_time: 种植时长 以分钟为单位
        :param _tree_type: 树的种类 (int)
        :param _note: 植树备注(str)
        :param _number: 树的编号, 用于控制台输出(int)
        :param _boost_by_ad: 是否通过模拟观看广告进行加速(bool)
        :param _end_time: 种植完成的时间(str) 格式 2021-01-01 12:00:00
        :param _room_id: 一起种模式下的房间ID(int)
        :return: (bool)
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
            "seekruid": self.user.uid
        }
        try:
            res = self.req.my_requests("post",
                                       f'https://c88fef96.forestapp.cc/api/v1/plants?seekrua=android_cn-4.41.0&seekruid={self.user.uid}',
                                       data, {})
            if res.status_code == 403:
                Avalon.error(f"第 {_number} 棵植树失败! 请检查Cookies 响应代码: 403 Forbidden")
                return False
            result = json.loads(res.text)
            if result["is_success"]:
                Avalon.info(f"第 {_number} 棵植树成功  数量: {result['tree_count']}  id: {result['id']}")
                if _boost_by_ad:
                    self.boost_plant_by_rewarded_ad(_plant_id=result["id"])
                return True
            else:
                Avalon.error(f"第 {_number} 棵植树失败  响应码: {res.status_code}  {result}")
                return False
        except json.decoder.JSONDecodeError:
            Avalon.error(f"第 {_number} 棵植树失败 载入服务器返回Text失败")
            return False
        except Exception as err_info:
            Avalon.error(f"第 {_number} 棵植树失败  其他错误: {err_info}")
            return False

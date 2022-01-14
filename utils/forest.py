# -*- coding: UTF-8 -*-
# @Time    : 2021/7/27 15:18
# @Author  : Hui-Shao
import json
import os
import random
import time
import traceback
from datetime import datetime, timedelta

# 在 main.py 调用该模块时, 该模块的运行目录仍然为 main.py 所在目录
try:
    from utils.avalon import Avalon
    from utils.http_req import HttpReq
except ModuleNotFoundError:
    from avalon import Avalon
    from http_req import HttpReq


class Forest:
    api_url_tuple = (
        "https://c88fef96.forestapp.cc", "https://forest.dc.upwardsware.com", "https://forest-china.upwardsware.com")
    app_version = "4.50.0"
    plants = []
    coin_tree_types = {}

    def __init__(self, _user):
        self.login_trial_n = 0
        self.user = _user
        self.req = HttpReq(self.user.remember_token)
        self.api_url = self.api_url_tuple[1]
        self.select_api_url()

    # %% 设置 api_url
    def select_api_url(self, _i: int = -1):
        """
        用于设置 self.api_url 不传入 _i 参数时, 则根据 self.user.server 进行选择
        :param _i: 可选值为 0 or 1 or 2  分别对应 默认地址(全球服务器) | 针对大陆的加速地址(全球服务器) | 中国大陆服务器地址
        :return: None
        """
        if _i == -1:
            if self.user.server == "china":
                self.select_api_url(2)
            elif self.user.server == "global":
                self.select_api_url(1)  # 若用户 server 为 global, 默认启用 "加速链接"
        elif 0 <= _i <= 2:
            self.api_url = self.api_url_tuple[_i]
        else:
            pass

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
        r = self.req.my_requests("post", f"{self.api_url}/api/v1/sessions", data, {})
        if r is None:
            Avalon.error("登录失败! 请检查网络连接")
            return {}
        if r.status_code == 481:
            if self.login_trial_n >= 2:
                Avalon.error("登录失败! 请检查账号及密码 响应代码: 481")
                return {}
            else:
                self.api_url = self.api_url_tuple[2]  # 收到 481 返回码, 可能是由于中国区用户在全球服务器登陆造成 (目前看来是这样 2021.12.03)
                self.login_trial_n += 1
                return self.login()
        elif r.status_code == 403:
            if self.user.server != "auto" or self.login_trial_n >= 2:
                Avalon.error("登录失败! 请检查账号及密码 响应代码: 403 Forbidden")
                return {}
            else:
                self.api_url = self.api_url_tuple[2]  # 在 auto 模式下, 若第一次登录失败, 切换为中国服务器 api 再次尝试登录
                self.login_trial_n += 1
                return self.login()
        elif r.status_code != 200:
            Avalon.error(f"登录可能失败 响应代码: {r.status_code}")
            return {}
        else:
            id_info = json.loads(r.text)
            self.user.remember_token = id_info["remember_token"]
            self.req.remember_token = id_info["remember_token"]  # 首次登录调用 login() 后必须更新 req.remember_token 的值, 否则相当于未登录
            self.user.uid = id_info["user_id"]
            self.user.server = ("global", "global", "china")[self.api_url_tuple.index(self.api_url)]
            Avalon.info("登录成功, 欢迎你~: %s (%d) (%s)" % (id_info["user_name"], id_info["user_id"], self.user.server))
            return {"uid": self.user.uid, "remember_token": self.user.remember_token, "server": self.user.server}

    # %% 登出
    def logout(self):
        """
        :return: 若登出成功则返回 True
        """
        Avalon.info("正在登出...", front="\n")
        url = f"{self.api_url}/api/v1/sessions/signout?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}"
        r = self.req.my_requests("delete", url, {}, {})
        if r is None:
            Avalon.error("登出失败! 请检查网络连接")
            return False
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
        """
        :param _force_update: 若为 True 则强制从服务器获取并覆盖本地文件
        :return: 若获取成功则返回 True
        """
        file_name = "plants.json"

        def run():
            Avalon.info(f"正在获取已种植列表 ({file_name})", front="\n")
            if _force_update:
                Avalon.info("已启用强制更新 plants.json")
                return get_from_server()
            else:
                if os.path.exists(f"_user_files/{file_name}"):
                    Avalon.info(f"发现本地已存在 {file_name} , 进行读取...")
                    return get_from_local()
                else:
                    Avalon.warning(f"在本地未发现 {file_name} , 尝试从服务器端获取...")
                    return get_from_server()

        def get_from_local():
            with open(f"_user_files/{file_name}", "r", encoding="utf-8") as f:
                self.plants = json.loads(f.read())
            if len(self.plants):
                Avalon.info(f"从本地获取 已种植列表 ({file_name}) 成功")
                return True
            else:
                Avalon.error(f"从本地获取 已种植列表 {file_name} 失败")
                return False

        def get_from_server():
            url = f"{self.api_url}/api/v1/plants?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}"
            r = self.req.my_requests("get", url, {}, {})
            if r is None:
                Avalon.error(f"从服务器端获取 已种植列表 ({file_name}) 失败! 请检查网络连接")
                return False
            if r.status_code == 200:
                self.plants = json.loads(r.text)
                Avalon.info(f"从服务器端获取 已种植列表 ({file_name}) 成功")
                with open(f"_user_files/{file_name}", "w", encoding="utf-8") as f:
                    f.write(r.text)
                return True
            else:
                Avalon.error(f"从服务端获取 已种植列表 {file_name} 可能失败")
                return False

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到 KeyboardInterrupt, 退出当前任务")
            return False
        except Exception:
            Avalon.error(traceback.format_exc(3))
            return False

    # %% 获取树木种类列表
    def get_coin_tree_types(self, _force_update=False):
        """
        :param _force_update: 若为 True 则强制从服务器获取并覆盖本地文件
        :return: 若获取成功则返回 True
        """
        file_name = "coin_tree_types.json"

        def run():
            Avalon.info(f"正在获取树木种类列表 ({file_name})", front="\n")
            if _force_update:
                Avalon.info("已启用强制更新 plants.json")
                return get_from_server()
            else:
                if os.path.exists(f"_user_files/{file_name}"):
                    Avalon.info(f"发现本地已存在 {file_name} , 进行读取...")
                    return get_from_local()
                else:
                    Avalon.warning(f"在本地未发现 {file_name} , 尝试从服务器端获取...")
                    return get_from_server()

        def get_from_local():
            with open(f"_user_files/{file_name}", "r", encoding="utf-8") as f:
                self.coin_tree_types = json.loads(f.read())
            if len(self.coin_tree_types):
                Avalon.info(f"从本地获取 树木种类列表 ({file_name}) 成功")
                return True
            else:
                Avalon.error(f"从本地获取 树木种类列表 ({file_name}) 失败")
                return False

        def get_from_server():
            url = f"{self.api_url}/api/v1/products/coin_tree_types?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}"
            r = self.req.my_requests("get", url)
            if r is None:
                Avalon.error(f"从服务器端获取 树木种类列表 ({file_name}) 失败! 请检查网络连接")
                return False
            if r.status_code == 200:
                self.coin_tree_types = json.loads(r.text)
                Avalon.info(f"从服务器端获取 树木种类列表 ({file_name}) 成功")
                with open(f"_user_files/{file_name}", "w", encoding="utf-8") as f:
                    f.write(r.text)
                return True
            else:
                Avalon.error(f"从服务端获取 树木种类列表 {file_name} 可能失败")
                return False

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到 KeyboardInterrupt, 退出当前任务")
            return False
        except Exception:
            Avalon.error(traceback.format_exc(3))
            return False

    # %% 获取指定用户概述
    def get_user_profile(self, _target_user_id: int, _is_print: bool = False):
        """
        获取指定用户的 Profile
        :param _target_user_id: 目标用户的id
        :param _is_print: 是否在控制台输出结果
        :return: (json)
        """
        try:
            res = self.req.my_requests("get", f"{self.api_url}/api/v1/users/{_target_user_id}/profile",
                                       {"seekrua": f"android_cn-{self.app_version}", "seekruid": self.user.uid}, {})
            if res is None:
                return {}
            elif res.status_code == 200:
                if _is_print:
                    Avalon.info(f"{res.text}\n", front="\n")
                return json.loads(res.text)
            else:
                return {}
        except Exception:
            return {}

    # %% 获取成就列表
    def get_achievements_info(self) -> bool:
        """
        :return: 若获取成功则返回 True
        """
        file_name = "achievements.json"

        def run():
            Avalon.info(f"正在获取 成就列表 ({file_name})", front="\n")
            return get_from_server()

        def get_from_server():
            url = f"{self.api_url}/api/v1/achievements"
            data = {
                "today": (datetime.utcnow() - timedelta(hours=1)).isoformat()[:-3] + "Z",
                "achievement_system_2020": False,
                "seekrua": f"android_cn-{self.app_version}",
                "seekruid": self.user.uid
            }
            r = self.req.my_requests("get", url, data, {})
            if r is None:
                Avalon.error(f"从服务器端获取 成就列表 ({file_name}) 失败! 请检查网络连接")
                return False
            if r.status_code == 200:
                self.plants = json.loads(r.text)
                Avalon.info(f"从服务器端获取 成就列表 ({file_name}) 成功")
                with open(f"_user_files/{file_name}", "w", encoding="utf-8") as f:
                    f.write(r.text)
                return True
            else:
                Avalon.error(f"从服务端获取 成就列表 {file_name} 可能失败")
                return False

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到 KeyboardInterrupt, 退出当前任务")
            return False
        except Exception:
            Avalon.error(traceback.format_exc(3))
            return False

    # %% 领取成就
    def claim_achievement(self, _achievement_id: int) -> bool:
        url = f"{self.api_url}/api/v1/achievements/{_achievement_id}/claim_reward?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}"
        r = self.req.my_requests("put", url)
        if r is None:
            Avalon.error(f"领取成就 id:{_achievement_id} 失败! 空 response")
            return False
        if r.status_code in (200, 201):
            Avalon.info(f"领取成就 id:{_achievement_id} 成功")
            return True
        elif r.status_code == 204:
            Avalon.info(f"成就 id:{_achievement_id} 已经领取过啦")
            return True
        elif r.status_code == 423:
            Avalon.warning(f"成就 id:{_achievement_id} 尚未达到领取条件")
            return False
        else:
            Avalon.warning(f"领取成就 id:{_achievement_id} 未知 状态码: {r.status_code}")
            return False

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
            if r is None:
                Avalon.error("获取 ad_session_token 失败! 请检查网络连接")
                return False
            if (r.status_code == 201) or (r.status_code == 200):
                Avalon.info("获取 ad_session_token 成功")
                return json.loads(r.text)["token"]
            else:
                Avalon.error(f"获取 ad_session_token 失败! 状态码: {r.status_code}")
                return False

        def get_ad_token(_ad_session_token):
            data = {"ad_session_token": f"{_ad_session_token}"}
            r = self.req.my_requests("post",
                                     f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}",
                                     data, {})
            if r is None:
                Avalon.error("获取 ad_token 失败! 请检查网络连接")
                return False
            if (r.status_code == 201) or (r.status_code == 200):
                Avalon.info("获取 ad_token 成功")
                return json.loads(r.text)["token"]
            else:
                Avalon.error(f"获取 ad_token 失败! 状态码: {r.status_code}")
                return False

        def simulate_watch(_ad_token, _ad_session_token):
            res_1 = self.req.my_requests("put",
                                         f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views/{_ad_token}/watched?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}",
                                         {"ad_session_token": f"{_ad_session_token}"})
            if res_1 is None:
                Avalon.error("模拟观看广告失败! 请检查网络连接 位置: 1 -> watched")
                return False
            if res_1.status_code != 200:
                Avalon.error("模拟观看广告失败!  位置: 1 -> watched")
                return False
            time.sleep(0.3)
            res_2 = self.req.my_requests("put",
                                         f"https://receipt-system.seekrtech.com/sv_rewarded_ad_views/{_ad_token}/claim?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}",
                                         {"ad_session_token": f"{_ad_session_token}", "user_id": self.user.uid})
            if res_2 is None:
                Avalon.error("模拟观看广告失败! 请检查网络连接 位置: 2 -> claim")
                return False
            if res_2.status_code != 200:
                Avalon.error("模拟观看广告失败!  位置: 2 -> claim")
                return False
            else:
                Avalon.info("模拟观看广告成功")
                return True

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到 KeyboardInterrupt, 退出当前任务")
            return False
        except Exception:
            Avalon.error(traceback.format_exc(3))
            return False

    # %% 模拟观看广告删除枯树
    def remove_plants_by_rewarded_ad(self):
        """
        通过模拟观看广告从而免金币删除枯树
        :return: 若成功则返回 True
        """

        def run():
            Avalon.info("========== 当前任务: 删除枯树 ==========\n", front="\n")
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

        def delete_plants(_id: int):
            if self.user.uid <= 0:
                Avalon.error("uid错误")
                return False
            url = f"{self.api_url}/api/v1/plants/{_id}/remove_plant_by_rewarded_ad?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}"
            r = self.req.my_requests("delete", url)
            if r is None:
                Avalon.error("删除种植记录失败! 请检查网络连接")
                return False
            if r.status_code == 200:
                Avalon.info("删除种植记录成功")
                return True
            elif r.status_code == 422:
                Avalon.error("原因: 422 Cannot find the product with given id")
                return False
            elif r.status_code == 403:
                Avalon.error("原因: 403 Forbidden. 请检查cookie")
                return False
            else:
                Avalon.error(f"删除种植记录失败! 状态码: {r.status_code}")
                return False

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到 KeyboardInterrupt, 退出当前任务")
            return False
        except Exception:
            Avalon.error(traceback.format_exc(3))
            return False

    # %% 模拟观看广告加速种植
    def boost_plant_by_rewarded_ad(self, _plant_id: int):
        """
        :param _plant_id: 树木的种植id, 例如 896588593
        :return: 若成功则返回 True
        """

        def run():
            Avalon.info("正在尝试获取双倍金币...")
            if self.simulate_watch_ad() is False:
                return False
            res = self.req.my_requests("put", f"{self.api_url}/api/v1/plants/{_plant_id}/boost_plant_by_rewarded_ad",
                                       {"seekrua": f"android_cn-{self.app_version}", "seekruid": self.user.uid}, {})
            if res is None:
                Avalon.error("获取双倍金币失败! 请检查网络连接")
                return False
            if res.status_code == 200:
                Avalon.info(f"获取双倍金币成功")
                return True
            else:
                Avalon.error(f"获取双倍金币失败!  返回码: {res.status_code}")
                return False

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到 KeyboardInterrupt, 退出当前任务")
            return False
        except Exception:
            Avalon.error(traceback.format_exc(3))
            return False

    # %% 创建房间(一起种)
    def create_room(self, _boost_by_ad: bool):
        """
        :param _boost_by_ad: 是否启用 模拟观看广告获取双倍金币
        :return: 若成功则返回 True
        """

        def run():
            Avalon.info("========== 当前任务: 创建房间 ==========\n", front="\n\n")
            room_info_basic = create()
            if not len(room_info_basic):
                Avalon.error("未获取到服务器返回的房间信息! 当前任务退出")
                return False
            elif "exit" in room_info_basic:
                return False
            try:
                show_member_info(room_info_basic["id"])
            except KeyboardInterrupt:
                Avalon.info("捕获 KeyboardInterrupt, 已退出成员监视 ", front="\n")
            except Exception:
                Avalon.warning(f"{traceback.format_exc(3)}")
                Avalon.warning("发生未定义异常, 已退出成员监视 ", front="\n")
            if not Avalon.ask("是否保留该房间 (Y)?", default=True):
                leave(room_info_basic["id"])
                return False
            if Avalon.ask("是否有需要移除的成员 (N)?", default=False):
                kick(room_info_basic["id"])
            if Avalon.ask("是否开始 (Y)?", default=True):
                plant_time = int(room_info_basic["target_duration"] / 60)
                end_time = datetime.now() + timedelta(minutes=plant_time)
                if start(room_info_basic["id"], end_time):
                    Avalon.info("开始发送种植信息...")
                    self.plant_a_tree("countdown", room_info_basic["tree_type"], plant_time,
                                      "{} room".format(room_info_basic["tree_type"]), 1, _boost_by_ad,
                                      end_time, room_info_basic["id"])
            return True

        def create():
            tree_type = int(Avalon.gets("请输入树的种类编码(-1为退出): "))
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
                                       f'{self.api_url}/api/v1/rooms?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}',
                                       data, {})
            if res is None:
                Avalon.error("创建房间失败! 请检查网络连接")
                return {}
            if res.status_code != 201:
                Avalon.error(f"创建房间可能失败  响应码: {res.status_code}")
                return {}
            try:
                result = json.loads(res.text)
                Avalon.info(f"房间创建成功!  token: {result['token']} id: {result['id']}")
                return result
            except json.decoder.JSONDecodeError:
                Avalon.error(f"房间创建失败! 载入服务器返回Text失败")
                return {}
            except Exception as err_info:
                Avalon.error(f"创建失败 原因: {err_info}")
                return {}

        def show_member_info(_room_id: int):
            Avalon.info("接下来将显示房间内成员数, 当人数足够(大于1)时请按下 \"Ctrl + C\"")
            i = 1
            while i <= 100:
                room_info_detail = get_room_info(_room_id)
                name_list = []
                for user in room_info_detail["participants"]:
                    user_info = f"{user['name']} {user['user_id']}"
                    user_profile = self.get_user_profile(user["user_id"])
                    if len(user_profile) > 0:
                        user_total_tree = user_profile["health_count"] + user_profile["death_count"]
                        if user_total_tree != 0:
                            success_rate = (100 * user_profile["health_count"] / user_total_tree).__round__(2)
                        else:
                            success_rate = 0.00
                        days, m = divmod(user_profile["total_minute"], (60 * 24))
                        hours, minutes = divmod(m, 60)
                        user_info += f" {success_rate}% {days}天{hours}时{minutes}分"
                    name_list.append(user_info)
                Avalon.info(f"循环次数: {i} 当前人数: {room_info_detail['participants_count']} -> id: {name_list}",
                            end="\n")
                time.sleep(15)
                i += 1
            Avalon.warning("达到最大循环次数, 自动退出成员监视", front="\n")

        def get_room_info(_room_id: int):
            res = self.req.my_requests("get", f'{self.api_url}/api/v1/rooms/{_room_id}',
                                       {"is_birthdat_2019_client": True, "detail": True,
                                        "seekrua": f"android_cn-{self.app_version}",
                                        "seekruid": self.user.uid}, {})
            if res is None:
                Avalon.error("获取房间详细信息失败! 请检查网络连接")
                return {}
            if res.status_code != 200:
                Avalon.error(f"获取房间详细信息可能失败  响应码: {res.status_code}")
                return {}
            else:
                result = json.loads(res.text)
                return result

        def kick(_room_id: int):
            kick_uid_list = str(Avalon.gets("输入需要移除的成员的uid, 用空格分隔: ")).split(" ")
            for uid_str in kick_uid_list:
                try:
                    res = self.req.my_requests("put", f"{self.api_url}/api/v1/rooms/{_room_id}/kick",
                                               {"user_id": int(uid_str), "seekrua": f"android_cn-{self.app_version}",
                                                "seekruid": self.user.uid}, {})
                except ValueError:
                    Avalon.warning(f"输入的uid \"{uid_str}\" 有误, 已跳过")
                    continue
                except Exception as err_info:
                    Avalon.error(f"未知错误, 退出成员移除! {err_info}")
                    return False
                else:
                    if res is None:
                        Avalon.error(f"移除成员 {uid_str} 失败! 请检查网络连接")
                        continue
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

        def leave(_room_id: int):
            res = self.req.my_requests("put",
                                       f'{self.api_url}/api/v1/rooms/{_room_id}/leave?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}',
                                       {}, {})
            if res is None:
                Avalon.error("退出房间失败! 请检查网络连接")
                return False
            if res.status_code != 200:
                Avalon.error(f"退出房间可能失败  响应码: {res.status_code}")
                return False
            else:
                Avalon.info("退出房间成功")
            return True

        def start(_room_id: int, _end_time: datetime):
            res = self.req.my_requests("put",
                                       f'{self.api_url}/api/v1/rooms/{_room_id}/start?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}',
                                       {}, {})
            if res is None:
                Avalon.error("房间开始失败! 请检查网络连接")
                return False
            if res.status_code == 423:
                Avalon.error(f"房间开始失败, 人数不足")
                return False
            elif res.status_code != 200:
                Avalon.error(f"房间开始可能失败  响应码: {res.status_code}")
                return False
            else:
                result = json.loads(res.text)
                Avalon.info(
                    f"房间开始成功! 共计{result['participants_count']}人  预计完成时间: {datetime.strftime(_end_time, '%Y-%m-%d %H:%M:%S')}")
                return True

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获 KeyboardInterrupt, 退出当前任务")
            return False
        except Exception:
            Avalon.error(traceback.format_exc(3))
            return False

    # %% 自动植树刷金币
    def auto_plant(self, _boost_by_ad: bool, _mode: int, _total_n: int, _short_sleep_time: bool = False,
                   _customize_plant_time: int = -1):
        """
        :param _boost_by_ad: 是否启用 模拟观看广告获取双倍金币
        :param _mode: 自动植树模式选择 可选值 1-3, 分别对应 by_time_frame server_regular server_rank
        :param _total_n: 植树的总数 (若启用 by_time_frame 此项无效)
        :param _short_sleep_time: 是否启用 缩短植树请求间的 time_sleep 延迟 (仅对 by_time_frame 有效)
        :param _customize_plant_time: 是否启用 自定义每棵树的种植时间 单位为分钟 (对 server_rank 无效)
        :return: 无返回值
        """

        def run():
            Avalon.info("========== 当前任务: 自动植树 ==========\n", front="\n\n")
            if _mode == 1:
                mode_by_time_frame()
            elif _mode == 2:
                mode_server_regular()
            elif _mode == 3:
                mode_server_rank()
            else:
                Avalon.warning(f"输入的模式: {_mode} 无效!")
                return None

        def mode_by_time_frame():
            """
            按照指定时间区间植树
            """
            i = 1
            endtime_list = gen_list()
            tree_total = len(endtime_list)
            Avalon.info("共需种植 %d 棵树" % tree_total)
            while i <= tree_total:
                tree_type = random.randint(1, 83)
                if _customize_plant_time == -1 or _customize_plant_time == "":
                    plant_time = random.choice(list(range(120, 185, 5)))  # 随机选择范围在 [120,185) 之间的 5 的倍数作为时长
                else:
                    plant_time = int(int(_customize_plant_time) / 5) * 5
                note = f"{tree_type}"
                end_time = endtime_list[i - 1]
                print("\n")
                self.plant_a_tree("countdown", tree_type, plant_time, note, i, _boost_by_ad, end_time)
                if _short_sleep_time:
                    sleep_time = 0.3
                else:
                    sleep_time = random.randint(2, 10) + random.random()
                    sleep_time = round(sleep_time, 2)
                Avalon.info(f"Wait {sleep_time} seconds")
                time.sleep(sleep_time)
                i += 1

        def mode_server_regular():
            """
            服务器挂机循环植树模式
            """
            # 此模式下 plant_time 在循环之前指定 实际上每棵树的种植时长都是固定
            if _customize_plant_time == -1 or _customize_plant_time == "":
                plant_time = random.choice(list(range(30, 180, 5)))
            else:
                plant_time = int(int(_customize_plant_time) / 5) * 5
            i = 1
            while i <= int(_total_n):
                tree_type = random.randint(1, 83)
                note = random.choice(["学习", "娱乐", "工作", "锻炼", "休息", "其他"])
                Avalon.info(f"将在 {plant_time} min后种植第 {i} 棵树")
                self.sleep(plant_time * 60, False)
                time.sleep(1)
                self.plant_a_tree("countdown", tree_type, plant_time, note, i, _boost_by_ad, datetime.now())
                i += 1

        def mode_server_rank():
            """
            mode_server_regular 修改版, 随机短植树时间, 用于刷排行榜
            """
            i = 1
            while i <= int(_total_n):
                note = random.choice(["学习S", "娱乐S", "工作S", "锻炼S", "休息S", "其他S"])
                tree_type = random.randint(1, 83)
                plant_time = random.choice(list(range(10, 25, 5)))
                Avalon.debug_info(f"将在 {plant_time} min后种植第 {i} 棵树")
                self.sleep(plant_time * 60, False)
                time.sleep(0.5)
                self.plant_a_tree("countdown", tree_type, plant_time, note, i, _boost_by_ad, datetime.now())
                i += 1

        def gen_list():
            time_list = []
            while 1:
                try:
                    target_time = datetime.strptime(Avalon.gets("输入起始时间 (格式为 \'20210101 000000\') : "),
                                                    "%Y%m%d %H%M%S")
                    end_time = datetime.strptime(Avalon.gets("输入结束时间 (格式为 \'20211231 235959\') : "),
                                                 "%Y%m%d %H%M%S")
                except ValueError:
                    Avalon.warning("日期输入有误，请重新输入")
                else:
                    break
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
                time_list.append(target_time)
            return time_list

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到 KeyboardInterrupt, 退出当前任务")
        except Exception:
            Avalon.error(traceback.format_exc(3))

    # %% 手动植树
    def manually_plant(self, _boost_by_ad: bool):
        """
        :param _boost_by_ad: 是否启用 模拟观看广告获取双倍金币
        :return: 无返回值
        """

        def run():
            Avalon.info("========== 当前任务: 手动种植 ==========", front="\n\n")
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
                    end_time_s = str(Avalon.gets("请输入植树完成时的时间. 格式为 \'20210724 173005\' (可选): "))
                    if len(end_time_s):
                        try:
                            end_time = datetime.strptime(end_time_s, "%Y%m%d %H%M%S")  # 尝试将str转换为datetime, 以检查格式是否错误
                        except ValueError:
                            Avalon.warning("日期输入有误，请重新输入")
                            continue
                        else:
                            self.plant_a_tree(plant_mode, tree_type, plant_time, note, i, _boost_by_ad, end_time)
                            break
                    else:  # 如果没有指定 end_time, 则取当前时间, 并退出循环
                        self.plant_a_tree(plant_mode, tree_type, plant_time, note, i, _boost_by_ad, datetime.now())
                        break
                i += 1

        try:
            return run()
        except KeyboardInterrupt:
            Avalon.warning("捕获到 KeyboardInterrupt, 退出当前任务")
        except Exception:
            Avalon.error(traceback.format_exc(3))

    # %% 种植一棵树
    def plant_a_tree(self, _plant_mode: str, _tree_type: int, _plant_time: int, _note: str, _number: int,
                     _boost_by_ad: bool, _end_time: datetime,
                     _room_id: int = -1) -> bool:
        """
        :param _plant_mode: 种植模式(str) 接受 "countup"（正计时） 和 "countdown"（倒计时）
        :param _plant_time: 种植时长 以分钟为单位
        :param _tree_type: 树的种类 (int)
        :param _note: 植树备注(str)
        :param _number: 树的编号, 用于控制台输出(int)
        :param _boost_by_ad: 是否通过模拟观看广告进行加速(bool)
        :param _end_time: 种植完成的时间(datetime)
        :param _room_id: 一起种模式下的房间ID(int)
        :return: (bool)
        """
        end_time = _end_time - timedelta(hours=8)  # 注: 减去8小时是为了换算时区, 下同
        start_time = end_time - timedelta(minutes=_plant_time)
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
                                       f'{self.api_url}/api/v1/plants?seekrua=android_cn-{self.app_version}&seekruid={self.user.uid}',
                                       data, {})
        except json.decoder.JSONDecodeError:
            Avalon.error(f"第 {_number} 棵植树失败 载入服务器返回 Text 失败")
            return False
        except Exception as err_info:
            Avalon.error(f"第 {_number} 棵植树失败  其他错误: {err_info}")
            return False
        else:
            if res is None:
                Avalon.error(f"第 {_number} 棵植树失败! 请检查网络连接")
            elif res.status_code == 403:
                Avalon.error(f"第 {_number} 棵植树失败! 请检查 Cookies 响应代码: 403 Forbidden")
                return False
            else:
                result = json.loads(res.text)
                if result["is_success"]:
                    Avalon.info(f"第 {_number} 棵植树成功  数量: {result['tree_count']}  id: {result['id']}")
                    if _boost_by_ad:
                        self.boost_plant_by_rewarded_ad(_plant_id=result["id"])
                    return True
                else:
                    Avalon.error(f"第 {_number} 棵植树失败  响应码: {res.status_code}  {result}")
                    return False

    # %% 自定义的 sleep 函数 (长时间使用 time.sleep() 计时可能会不准确)
    @staticmethod
    def sleep(duration: float, high_accuracy: bool):
        """
        :param duration: 以秒为单位的时间间隔
        :param high_accuracy: 是否启用高精度计时(占资源)
        :return: None
        """

        def high():
            now = get_now()
            end = now + duration
            while now < end:
                now = get_now()

        def low():
            now = get_now()
            end = now + duration
            while now < end:
                if end - now > 60:  # 若当前时间距离距离目标时间 1 min 外, 执行sleep
                    time.sleep(10)
                now = get_now()

        get_now = time.perf_counter
        high() if high_accuracy else low()


if __name__ == '__main__':
    import sys


    class _UserInfo:
        def __init__(self, _username, _passwd, _uid, _remember_token, _server):
            self.username = _username
            self.passwd = _passwd
            self.uid = _uid
            self.remember_token = _remember_token
            self.server = _server


    def _show_menu():
        menu = """
        ====================== 菜单 ======================
        
          0. 退出程序
          1. 获取已种植树木列表 (plants.json)
          2. 获取已解锁树木列表 (coin_tree_types.json)
          3. 获取指定用户的 Profile
          4. 免金币删除枯树 (模拟观看广告)
          5. 创建房间 (一起种功能)
          6. 自动植树
          7. 手动植树
          8. 获取成就列表 (achievements.json)
          9. 领取指定成就
        
        =================================================
        """
        Avalon.info(menu, front="\n")


    def _get_choice():
        while 1:
            try:
                choice = int(Avalon.gets("输入你的选择: ", front="\n"))
            except ValueError:
                Avalon.warning("输入无效")
            else:
                break
        return choice


    def _do(_n: int):
        if _n <= 0:
            sys.exit(0)
        elif _n == 1:
            F.get_plants(_force_update=True)
        elif _n == 2:
            F.get_coin_tree_types(_force_update=True)
        elif _n == 3:
            F.get_user_profile(int(Avalon.gets("输入目标用户的uid: ")), True)
        elif _n == 4:
            F.remove_plants_by_rewarded_ad()
        elif _n == 5:
            F.create_room(Avalon.ask("是否启用双倍金币"))
        elif _n == 6:
            F.auto_plant(Avalon.ask("是否启用双倍金币"), int(Avalon.gets("选择自动植树模式 (1.按时间段 2.挂机 3.挂机刷榜):", default=-1)),
                         Avalon.gets("自动种植总数 (可选 默认1000 仅在\'非 mode1\'时有效): ", default=1000),
                         Avalon.ask("是否缩短植树请求间隔时间 (可选 仅在\'mode1\'时有效)", default=True),
                         Avalon.gets("输入自定义的每棵树植树时长(单位为分钟 可选 仅在\'非 mode3\'时有效): ", default=-1))
        elif _n == 7:
            F.manually_plant(Avalon.ask("是否启用双倍金币"))
        elif _n == 8:
            F.get_achievements_info()
        elif _n == 9:
            F.claim_achievement(int(Avalon.gets("输入 achievement_id: ")))
        else:
            Avalon.warning("选项不存在!")
            time.sleep(2)


    os.chdir(sys.path[0])
    os.chdir("../")
    if not os.path.exists("_user_files"):
        os.mkdir("_user_files")
    username = Avalon.gets("请输入用户名: ", front="\n")
    passwd = Avalon.gets("请输入密码: ")
    server = Avalon.gets("请选择服务器: 1.自动  2.大陆  3.全球  -> (1) : ", default="1")
    F = Forest(_UserInfo(username, passwd, 0, "", ("auto", "china", "global")[int(server) - 1]))
    if len(F.login()) <= 0:
        Avalon.error("登录出现问题, 程序退出!")
        sys.exit(0)
    while True:
        try:
            _show_menu()
            _do(_get_choice())
            time.sleep(1.5)
        except KeyboardInterrupt:
            Avalon.warning("用户中断操作, 程序退出")
            sys.exit(0)
        except Exception:
            Avalon.error(traceback.format_exc(3))

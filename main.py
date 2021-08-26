# -*- coding: UTF-8 -*-
# @Time    : 2021/7/27 17:21
# @Author  : Hui-Shao
# %% imports

import os
import shutil
import sys

import toml

from utils.avalon import Avalon
from utils.forest import Forest
from utils.user import User


# %% 建立用于保存用户文件的目录
def makedir():
    if not os.path.exists("_user_files"):
        os.mkdir("_user_files")
    else:
        pass


# %% 读取配置文件
def read_config():
    Avalon.info("读取配置文件中……", front="\n")
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
        Avalon.info("配置文件读取成功")
        return True


# %% 写配置文件
def write_config():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    config_2 = config.copy()
    config_2["user"].update({"uid": user.uid, "remember_token": user.remember_token})
    try:
        f = open(config_file, "w+", encoding="utf-8")
        toml.dump(config_2, f)
        f.close()
    except IOError:
        Avalon.error("IOError")
        return False
    else:
        return True


def logout():
    if F.logout():
        user.uid = 0
        user.remember_token = ""
        write_config()
    try:
        shutil.rmtree("_user_files")
    except IOError:
        Avalon.warning("删除_user_files目录失败, 在切换用户前务必手动删除！")


def login():
    if user.uid * len(user.remember_token) == 0:  # 若未读取到保存的 uid 和 remember_token 则调用登录
        login_info = F.login()
        if len(login_info):
            user.uid = login_info["uid"]
            user.remember_token = login_info["remember_token"]
            write_config()
    else:
        Avalon.info(f"当前用户信息 -> {user.username} ({user.uid})", front="\n")


def run():
    login()
    if config["remove_plants_by_rewarded_ad"]["enable"]:
        F.remove_plants_by_rewarded_ad()
    if config["auto_plant"]["enable"]:
        F.auto_plant(_total_n=config["auto_plant"]["number"],
                     _boost_by_ad=config["boost_plant_by_rewarded_ad"]["enable"],
                     _by_time_frame=config["auto_plant"]["by_time_frame"])
    if config["manually_plant"]["enable"]:
        F.manually_plant(_boost_by_ad=config["boost_plant_by_rewarded_ad"]["enable"])
    if config["create_room"]["enable"]:
        F.create_room(_boost_by_ad=config["boost_plant_by_rewarded_ad"]["enable"])
    if config["auto_logout"]["enable"]:
        logout()
    Avalon.info("所有任务执行完毕~", front="\n")


if __name__ == '__main__':
    os.chdir(sys.path[0])
    config = {}
    username = ""
    passwd = ""
    uid = 0
    remember_token = ""
    makedir()
    if read_config():
        user = User(username, passwd, uid, remember_token)
        F = Forest(user)
        run()
    else:
        sys.exit(0)

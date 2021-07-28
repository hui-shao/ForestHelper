# -*- coding: UTF-8 -*-
# @Time    : 2021/7/27 17:21
# @Author  : Hui-Shao
# %% imports

import os
import shutil
import sys

import toml

from avalon import Avalon
from forest import Forest


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


def logout():
    global uid, remember_token
    if F.logout():
        uid = 0
        remember_token = ""
        write_config()
    try:
        shutil.rmtree("UserFiles")
    except IOError:
        Avalon.warning("删除UserFiles目录失败, 在切换用户前务必手动删除！")


def login():
    global uid, remember_token
    if uid * len(remember_token) == 0:  # 若未读取到保存的 uid 和 remember_token 则调用登录
        login_info = F.login()
        if len(login_info):
            uid = login_info["uid"]
            remember_token = login_info["remember_token"]
            write_config()


def run():
    login()
    if config["remove_plants_by_rewarded_ad"]["enable"]:
        F.remove_plants_by_rewarded_ad()
    if config["auto_plant"]["enable"]:
        F.auto_plant(config["auto_plant"]["number"])
    if config["manually_plant"]["enable"]:
        F.manually_plant()
    if config["create_room"]["enable"]:
        F.create_room()
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
        F = Forest(username, passwd, uid, remember_token)
        run()
    else:
        sys.exit(0)

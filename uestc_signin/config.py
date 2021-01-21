# coding=utf-8
#
# Copyright (c) 2020 The UESTC-Signin Authors. All rights reserved.
# Use of this source code is governed by a MIT-style license that can be
# found in the LICENSE file. See the AUTHORS file for names of contributors.
#
# Authors: ehds(ds.he@foxmail.com)

import os
import logging
import json
import configparser
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = 'uestc.conf'
# TODO
# https://zhuanlan.zhihu.com/p/37534850
# 元类里的call是去创建一个对象，创建完之后会初始化（__init__), 
# 而_instance这个dict是类所有的(不是每个对象），它key是class，
#  value是一个对象，从而实现单例，我觉得我们应该把key改成路径或者不同的userid，来达到单例
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton,
                                        cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(object, metaclass=Singleton):
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self._config_path = config_path
        self.parse()

    def parse(self):
        if not os.path.exists(self._config_path):
            raise ValueError(f"{self._config_path} not exists")
        self.cf = configparser.ConfigParser()
        self.cf.read(self._config_path)

    def __getattr__(self, attr):
        return self.cf[self._section][attr]


class UserConfig(Config):
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self._section = "user"
        super(UserConfig, self).__init__(config_path)


class MailConfig(Config):
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        super(MailConfig, self).__init__(config_path)
        self._section = "mail"


# __name__ = __main__ if run directly
if __name__ == "__main__":
    m = MailConfig("../uestc.conf")
    print(m.pop_host)
    c = UserConfig("../uestc.conf")
    print(c.password)

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
该模块用于存放全局参数设置

调用方通过 Connector 获取数据库 connection, engine 和 session 对象
"""

__author__ = 'Laurent.Chen'
__date__ = '2019/7/15'
__version__ = '1.0.0'

import os
import yaml
import MySQLdb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 注意相对路径与绝对路径在 直接run/import 和 execute in console 中是不一样的
# 仅供导入而不会 execute in console 的用以下做法
with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r', encoding='utf-8') as f:
    config_dict = yaml.full_load(f)


class Connector(object):
    """
    定义数据库参数和连接方法

    :param str db: 连接数据库名称
    """

    host = config_dict['host']
    port = config_dict['port']
    user = config_dict['user']
    password = config_dict['password']
    charset = config_dict['charset']

    def __init__(self, db):
        if not isinstance(db, str):
            raise ValueError('必须以字符串类型传入数据库名')
        self.db = db

    def get_conn(self):
        # 可供 pandas.read_sql 使用的数据库连接
        conn = MySQLdb.connect(host=self.host, port=self.port, user=self.user,
                               password=self.password, db=self.db, charset=self.charset)
        return conn

    def get_engine(self):
        """
        根据设定连接参数返回一个 SQLAlchemy engine 对象，目前使用 ORM

        :return: SQLAlchemy engine
        """
        engine = create_engine(f"mysql+mysqldb://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
                               f"?charset=utf8mb4")
        return engine

    def get_session(self):
        """
        根据设定连接参数返回一个 SQLAlchemy session，目前使用 ORM

        :return: SQLAlchemy session
        """
        session = sessionmaker(bind=self.get_engine())
        return session()


if __name__ == '__main__':
    pass

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
User-Agent 前期准备

更有针对性地伪装请求头
"""

from faker import Faker


class FakeUA(object):
    """
    随机伪装 UA
    
    :param str language: 本地化语言。Default 'zh-CN'
    """

    def __init__(self, language='zh-CN'):
        """

        :param str language: 本地化语言。Default 'zh-CN'
        """
        self.local_faker = Faker(language)

    def get_ua(self, platform, browser='chrome'):
        """
        按指定平台和浏览器获取随机 ua

        TODO: 不修改 faker 源码情况下不断尝试的时间可能比较长

        :param str platform: {'PC', 'mobile'}，系统平台
        :param str browser: {'chrome', 'firefox', 'safari', 'internet_explorer', 'opera'}
        :return: random user-agent
        :rtype: str
        """
        fake_ua_func = getattr(self.local_faker, browser)
        while True:
            ua = fake_ua_func()
            if platform == 'PC':
                if 'Windows' in ua:
                    return ua
                else:
                    continue

            if platform == 'mobile':
                if 'iPhone' in ua:
                    return ua
                else:
                    continue


if __name__ == '__main__':
    pass

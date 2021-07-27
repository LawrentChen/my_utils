# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
selenium 基本前期准备与其他通用动作

提供一个准备完成的 selenium driver
"""

import os
import random
import time
import yaml

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

import spider.myua as myua

# selenium 的 page_source 不能获取到动态内容，必须通过 get_attribute('outerHTML')
# selenium 下滚似乎也会受到防爬

with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r', encoding='utf-8') as f:
    config_dict = yaml.full_load(f)


class SeleniumChrome(object):
    """
    Chrome 浏览器所用 selenium 对象

    :param str chrome_river: 可执行的 chrome_driver 路径
    """

    def __init__(self, chrome_river=config_dict['LocalPath']['chromedriver_path']):
        """

        :param str chrome_river: 可执行的 chrome_driver 路径
        """
        self.chrome_driver = chrome_river
        self.chrome_options = Options()
        self.ua = myua.FakeUA()

    def prepare(self, ua, download_path, incognito=True, no_pic=False, headless=False,
                resolution=config_dict['BrowserConfig']['resolution']):
        """
        预处理准备

        - 固定分辨率为 1600*900 以避免不同设备简单最大化的差异
        - 取消消息栏
        - 取消下载提示，直接下载到参数设定的下载目录
        - 取消密码记录管理
        - （可选）匿名模式，默认开启。

            但 chrome 默认匿名模式下不加载任何插件。可以通过手动在 chrome 设置--扩展程序--某插件详细信息中设置其在无痕模式下启用，
            再通过 chrome_options.add_argument(f'--user-data-dir={chrome://version/中的个人资料路径}') 以 chrome 的个人
            配置文件启动从而实现兼顾匿名模式和插件。但这种方法正常情况下不能和正常人工打开的 chrome 在同一时间并存，似乎有“多开”的方法

        - （可选）无图模式
        - （可选）无头模式

        :param str or dict or None ua: 指定将要使用的 user-agent。

            - 允许直接以字符串指定，或是以字典形式传入 {'faker_ua': 'PC'}/{'faker_ua': 'mobile'} 以根据平台抽取随机 ua
            - 如果传入 None，则会使用浏览器真正的 ua

        :param str download_path: 默认下载地址
        :param boolean incognito: 是否启用匿名模式，默认是
        :param boolean no_pic: 是否不加载图片，默认加载
        :param boolean headless: 是否开启无头模式，默认不开启
        :param list resolution: 分辨率设置
        :return: None
        """
        self.chrome_options.add_argument('disable-infobars')
        self.chrome_options.add_argument('--profile-directory=Default')
        self.chrome_options.add_argument(f'--window-size={resolution[0]},{resolution[1]}')

        if isinstance(ua, dict):
            given_ua = f'user-agent="{self.ua.get_ua(platform=ua["faker_ua"])}"'
            self.chrome_options.add_argument(given_ua)

        if isinstance(ua, str):
            given_ua = f'user-agent="{ua}"'
            self.chrome_options.add_argument(given_ua)

        if incognito:
            self.chrome_options.add_argument('--incognito')

        if headless:
            self.chrome_options.add_argument('--headless')

        prefs = {'download.prompt_for_download': False,
                 'credentials_enable_service': False,
                 'profile.password_manager_enabled': False
                 }
        if download_path:
            prefs['download.default_directory'] = download_path
        self.chrome_options.add_experimental_option('prefs', prefs)

        # 不加载图片
        if no_pic:
            self.chrome_options.add_experimental_option('prefs',
                                                        {'profile.managed_default_content_settings_.images': 2})

        # 开发者模式，可以防止被 js 的'window.navigator.webdriver'识别为 selenium
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])

    def get_driver(self):
        """
        按照类设定的参数返回一个 chrome driver

        参数可先通过 self.prepare 进行预设，或直接修改 self.chrome_oprions 来达到目的

        :return: chrome driver 对象
        """
        # chromedriver 没有加入 path 的话就要在参数中指定
        driver = webdriver.Chrome(self.chrome_driver, options=self.chrome_options)

        return driver


class SeleniumFirefox(object):
    """
    Firefox 所用 Selenium 对象

    :param str gecko_driver: 可执行的 chrome_driver(firefox driver) 路径
    """

    def __init__(self, gecko_driver=config_dict['LocalPath']['geckodriver_path']):
        """

        :param str gecko_driver: 可执行的 chrome_driver(firefox driver) 路径
        """
        self.gecko_driver = gecko_driver

    def get_driver(self):
        driver = webdriver.Firefox(executable_path=self.gecko_driver)
        return driver


def human_click(element, driver, sleep_time=random.uniform(0.5, 1)):
    """
    使用随机时间延迟模仿真人鼠标操作的移动、悬停、点击

    （移动轨迹应该还有更多办法可以伪装）

    :param element: 目标页面元素，如果被遮挡则点击会点击到上层遮挡物
    :param webdriver driver: selenium driver
    :param float sleep_time: 移动、点击完成后的阻塞时长。默认取 0.5 到 1 秒的均匀分布
    :return: None
    """
    actions = ActionChains(driver)  # 实例化
    actions.move_to_element(element)  # 移动鼠标
    actions.click(element)  # 鼠标点击
    actions.perform()  # 执行整个操作链
    time.sleep(sleep_time)


def human_typewrite(element, content, interval=random.uniform(0.05, 0.1)):
    """
    模拟真人输入内容，单个字符间设置输入间隔

    :param webelement element: 目标页面元素，一般是可供填写的文本框
    :param str content: 待输入内容
    :param float interval: 单一字符间隔
    :return: None
    """
    i = 0
    while i < len(content):
        element.send_keys(content[i])
        i += 1
        time.sleep(interval)


def scroll_down(driver, sleep_time=random.uniform(0.5, 1)):
    """
    页面下滚

    通过按 page down 实现

    :param webdriver driver: selenium driver
    :param sleep_time: 滚动完成后的阻塞时长。默认取 0.5 到 1 秒的均匀分布
    :return: None
    """
    ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()  # 按下并释放
    time.sleep(sleep_time)


def scroll_up(driver, sleep_time=random.uniform(0.5, 1)):
    """
    页面上滚

    通过按 page up 实现

    :param webdriver driver: selenium driver
    :param sleep_time: 滚动完成后的阻塞时长。默认取 0.5 到 1 秒的均匀分布
    :return: None
    """
    ActionChains(driver).send_keys(Keys.PAGE_UP).perform()  # 按下并释放
    time.sleep(sleep_time)


if __name__ == '__main__':
    pass

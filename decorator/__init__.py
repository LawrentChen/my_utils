# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用装饰器

这里的类实现装饰器的调用一般为@classname()，注意括号
"""

import random
import time
from threading import Lock

import wrapt


class Logging(object):
    pass


class TimeIt(object):
    """
    计算某函数耗时

    TODO: 加入时间格式化参数
    """

    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        begin_time = time.time()
        func = wrapped(*args, **kwargs)
        end_time = time.time()
        time_consumed = end_time - begin_time
        print(f'{wrapped.__name__} took {time_consumed} secs')
        return func


class Retry(object):
    """
    任意异常后重试

    造轮子，应该使用 tenacity
    """

    def __init__(self, retry_times=3, wait_secs=5, errors=(Exception,)):
        self.retry_times = retry_times
        self.wait_secs = wait_secs
        self.errors = errors

    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        for _ in range(self.retry_times):
            try:
                return wrapped(*args, **kwargs)
            except self.errors as e:
                print(e)
                time.sleep((random.random() + 1) * self.wait_secs)
            return None


class Singleton:
    """
    单例模式

    使用了线程锁，但不确定是否真的线程安全
    """

    def __init__(self):
        self.lock = Lock()
        self._instance = {}  # 用来记录实例

    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        # 没有实例才创建
        if wrapped not in self._instance:
            with self.lock:
                self._instance[wrapped] = wrapped()
        # 返回 self._instance 里的实例，已经有了就不会再新建
        return self._instance[wrapped]


if __name__ == '__main__':
    pass

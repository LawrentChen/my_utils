# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用上下文管理器

e.g.
::

    from contextlib import contextmanager

    class Query(object):

        def __init__(self, name):
            self.name = name

        def query(self):
            print('Query info about %s...' % self.name)

    @contextmanager
    def create_query(name):
        print('Begin')
        q = Query(name)
        yield q
        print('End')

    with create_query('Bob') as f:
        f.query()

with语句首先执行yield之前的语句

yield调用会执行with语句内部（冒号之后的代码块）的所有语句, as [什么]就是 yield 了[什么]，上面 f = q

最后执行yield之后的语句

类似于装饰器，都是用来包装代码（在代码本体的前后加上功能），但装饰器只能用于函数或类，上下文管理器任何代码块均可

但如果逻辑复杂，且需要多态复用，那可能还是多个类按顺序组合功能更好

"""

if __name__ == '__main__':
    pass

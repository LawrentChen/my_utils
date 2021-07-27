# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
各种常用 pandas 的定制函数
"""

import os
import re

import pandas as pd


def list_file_in_path(folder_path, pattern=None):
    """
    列出给定路径下文件名符合指定模式的所有文件

    :param str folder_path: 指定路径
    :param str pattern: 正则指定模式。默认为 None，路径下所有文件都将被纳入
    :return: 符合要求的文件列表
    :type: list
    """
    filename_list = os.listdir(folder_path)
    pathname = []

    for filename in filename_list:
        if pattern:
            filename = re.match(pattern=pattern, string=filename)
            if filename:
                pathname.append(os.path.join(folder_path, filename.group(0)))
        if not pattern:
            pathname.append(os.path.join(folder_path, filename))

    return pathname


def better_read_excel(pathname, *args, **kwargs):
    """
    一次性打开单个 excel 文件内所有同型 sheet，并将它们合并为单个 DataFrame

    由于存在后续合并和重置 index 的问题，似乎没法简单地用偏函数 sheet_name=None 实现

    :param str pathname: 目标单个 excel 路径
    :return: 返回合并表
    :rtype: DataFrame
    """
    content_list = []
    # 显式声明 sheet_name=None 以读取所有 sheet，返回 OrderedDict
    content = pd.read_excel(pathname, sheet_name=None, *args, **kwargs)
    for k, v in content.items():
        content_list.append(v)
    df = pd.concat(content_list)
    df = df.reset_index(drop=True)
    return df


def read_folder_excel(folder_path, pattern=None, *args, **kwargs):
    """
    打开指定文件夹内的文件名符合 pattern 的全部 excel 文件， 并将它们 append 合并为单个 DataFrame

    需要保证文件夹内文件名符合 pattern 的文件都是同型的 excel 表格。允许单个 excel 中有多张 sheet，但它们都必须同型

    :param str folder_path: 指定路径，确保路径内文件名符合 pattern 的只有同型的 excel 文件
    :param str pattern: 正则表达式。默认为 None，路径下所有文件都将被纳入
    :return: 返回合并表
    :rtype: DataFrame
    """
    pathname = list_file_in_path(folder_path, pattern=pattern)
    content_list = []
    for file in pathname:
        file_df = better_read_excel(file, *args, **kwargs)
        content_list.append(file_df)
    result = pd.concat(content_list, ignore_index=True)
    return result


def better_to_excel(df, pathname, mode='a', rows_per_sheet=1000000, **kwargs):
    """
    更好的 DataFrame 导出 excel 方法

        - 超过一百万行时，自动切分 sheet 导出
        - 默认允许追加至一个已存在 excel 的新 sheet 中

    另外，参数中还可原样传入原生 to_excel 的所有参数，以调用 to_excel 的全部功能

    **需要 pandas 版本 >= 0.24.0**

    # TODO: 以装饰器实现，但是 to_excel 是 df 类的一个方法，不是一个普通函数，能否装饰？

    :param DataFrame df: 作为数据源的 DataFrame
    :param str pathname: 指定输出 excel 文件路径名
    :param str mode: {'w', 'a'}, default 'a'

        - 'w': (over)write, 覆写原 excel 内容
        - 'a': append，追加到原 excel 的新 sheet 中

    :param int rows_per_sheet: 指定每张 sheet 的行数。默认为 1,000,000，不得大于默认值
    :return: None
    """
    if not isinstance(rows_per_sheet, int) or (rows_per_sheet < 0):
        raise ValueError('行数必须为正整数')

    if rows_per_sheet > 1000000:
        raise ValueError('Excel 单张 Sheet 行数不得大于 1,000,000 行')

    total_sheet_num = int(round(len(df) / rows_per_sheet, 0) + 1)

    if not os.path.exists(pathname):
        df_empty = pd.DataFrame()
        df_empty.to_excel(pathname)
        mode = 'w'

    with pd.ExcelWriter(pathname, engine='openpyxl', mode=mode) as writer:
        if total_sheet_num == 1:
            df.to_excel(excel_writer=writer, **kwargs)
        elif total_sheet_num > 1:
            for i in range(total_sheet_num):
                df_i = df.iloc[i * rows_per_sheet: i * rows_per_sheet + rows_per_sheet, :]
                if 'sheet_name' in kwargs:
                    df_i.to_excel(excel_writer=writer, sheet_name=f"{kwargs['sheet_name']}_{i}", **kwargs)
                else:
                    df_i.to_excel(excel_writer=writer, sheet_name=f'df_{i}', **kwargs)


if __name__ == '__main__':
    pass

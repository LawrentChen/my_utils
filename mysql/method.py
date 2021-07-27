# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
定制的 MySQL 读写方法

读取数据库时，使用 pandas 的 read_sql 搭配 MysqlClient 连接以取得较佳性能。但代价是只能使用原生 SQL 查询
写入数据库时，使用 SQLAlchemy 以兼顾 orm、原生查询和反注入。

注意：
    - 表结构中要求主键仅有 MySQL 自增ID单一字段
    - 写入的目标表格需要先行建好，这里的方法均不会自动生成不存在的目标表。临时表则不需要提前生成

TODO: 每次操作写入记录表的装饰器，取代以往的 progress_registration()。抑或是使用 logging 输出文本日志？
"""
from contextlib import contextmanager

from sqlalchemy.dialects.mysql import insert
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import scoped_session

from mysql import Connector


class Operation(object):
    """
    自定义 MySQL 数据库读写操作

    :param str db: 指定数据库名
    """

    def __init__(self, db):
        self.db = db
        self.engine = Connector(db=self.db).get_engine()

    @contextmanager
    def _session_scope(self, scoped=True):
        """
        Provide a transactional scope around a series of operations.

        :param bool scoped: 是否使用线程安全的类似单例模式，默认是

        调用方法
        >>> with self._session_scope() as session:
        >>>     # Some sql operations
        >>>     pass
        """
        if not scoped:
            session = Connector(db=self.db).get_session()
        else:
            session = scoped_session(Connector(db=self.db).get_session)
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def _my_insert(target_table, temp_table, session, if_record_exists):
        """
        指定目标表和对应临时表，执行插入操作。可选择 **更新** 或 **忽略** 重复记录

        :param SQLAlchemy.ext.declarative.api.DeclarativeMeta target_table: 目标表类
        :param SQLAlchemy.ext.declarative.api.DeclarativeMeta temp_table: 临时表类
        :param session: 数据库会话
        :param str if_record_exists: {'update', 'ignore'}

            选择对已存在记录（由唯一索引确定）的处理策略

            - 'update': 更新原有记录。相当于执行 INSERT INTO target_table (column_list) SELECT column_list FROM temp_table
                        ON DUPLICATE KEY UPDATE col=VALUES(col)
            - 'ignore': 忽略原有记录，相当于执行 INSERT IGNORE INTO target_table (column_list) SELECT column_list FROM
                        temp_table

        :return: None
        """
        temp_inspect = inspect(temp_table)

        # 类型需要先转化为 python 列表
        column_list = [c for c in temp_inspect.columns]
        pk_list = [k for k in temp_inspect.primary_key]

        # 不带有表信息的单纯列名
        bare_column_list = [c.key for c in temp_inspect.columns]
        bare_pk_list = [k.name for k in temp_inspect.primary_key]

        # 获取临时表中除主键(**这里要求只有 MySQL 的自增ID单一字段**)的其他列名
        # 由于是先行按照 temp 表结构建表，所以即便原始数据源表字段有所增加。只要第一步 to_sql 到临时表没有问题，这里就不会出现问题
        for k in bare_pk_list:
            bare_column_list.remove(k)

        for k in pk_list:
            column_list.remove(k)

        # TODO: 能否有更好的方法避免现在类似拼接字符串的做法？ SqlAlchemy 的 load_only 方法无效
        if if_record_exists == 'update':
            stmt = insert(target_table).from_select(bare_column_list, session.query(*column_list))
            update_dict = {column: stmt.inserted[f'{column}'] for column in bare_column_list}
            stmt = stmt.on_duplicate_key_update(update_dict)
        elif if_record_exists == 'ignore':
            stmt = insert(target_table).from_select(bare_column_list, session.query(*column_list))
            stmt = stmt.prefix_with('IGNORE')
        else:
            raise ValueError('if_record_exists 参数只接受 update 或 ignore')
        session.execute(stmt)

    def to_mysql(self, df, target_table, temp_table, if_record_exists):
        """
        指定DataFrame, 目标表和对应临时表，执行插入操作。可选择 **更新** 或 **忽略** 重复记录

        :param DataFrame df: 数据表
        :param SQLAlchemy.ext.declarative.api.DeclarativeMeta target_table: 目标表类
        :param SQLAlchemy.ext.declarative.api.DeclarativeMeta temp_table: 临时表类
        :param str if_record_exists: {'update', 'ignore'}

            选择对已存在记录（由唯一索引确定）的处理策略

            - 'update': 更新原有记录。

                        相当于执行::

                            INSERT INTO target_table (column_list) SELECT column_list FROM temp_table ON DUPLICATE KEY
                            UPDATE col=VALUES(col)

                        注意，INSERT INTO ... ON DUPLICATE KEY UPDATE 与 REPLACE INTO 不同，不会伤及其他无关字段，
                        从而允许仅个别字段发生变化。但本方法中指定的 column_list 为 table 类中定义的表结构（也即全表更新），
                        故不能支持灵活地就某一部分字段进行更新，同时还不伤及其他字段

                        而且如果记录完全一样。那么 MySQL 受影响行数为0，自身的 update_time 也不会发生变化

                        #TODO: 增加一个说明以上问题的最小实例

            - 'ignore': 忽略原有记录。

                        相当于执行::

                            INSERT IGNORE INTO target_table (column_list) SELECT column_list FROM temp_table

        :return: None
        """
        if if_record_exists not in ('update', 'ignore'):
            raise ValueError('if_record_exists 取值必须为"update"或"ignore"')

        # 临时表在线程中断时就会自动删除，故需要保持在同一线程下完成操作
        with self._session_scope() as session:
            # create 方法生成临时表，注意其 checkfirst 参数默认取False，如果表已存在则抛出异常。但既然是临时表就不会有这问题
            temp_table.__table__.create(bind=session.connection(), checkfirst=False)

            try:
                df.to_sql(temp_table.__tablename__, con=session.connection(),
                          if_exists='append', index=False, chunksize=1000)
                # 插入临时表时，如果 df 与目标数据库表结构字段不同（以下为 df 相对变化）:
                #   - 增：报错
                #   - 删：只插入对应字段
                #   - 改：报错
            except Exception as e:
                raise e
            else:
                self._my_insert(target_table=target_table, temp_table=temp_table, session=session,
                                if_record_exists=if_record_exists)


if __name__ == '__main__':
    pass

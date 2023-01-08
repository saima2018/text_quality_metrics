# !/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@version:
@author: fzq
@contact: fanzhiqiang@bat100.net
@software: PyCharm
@file: MysqlUtils.py
@time: 2019/9/9 14:28
@description:
"""
import os
import sys
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)
import pymysql
from Utils.DataUtils import load_xml_conf

# 从配置文件获取数据库配置
conf = load_xml_conf()
db = conf['MysqlUtils_Database']['db']

def connectMysql(host=db['host'], port=db['port'], user=db['user'], password=db['password'], database=db['database']):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
        conn.ping(reconnect=True)
        cursor = conn.cursor()
        return conn, cursor
    except:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
        conn.ping(reconnect=True)
        cursor = conn.cursor()
        return conn, cursor

def connClose(conn, cursor):
    cursor.close()
    conn.close()

if __name__ == '__main__':
#     conn, cursor = connectMysql()
#     sql = "update queue set queue_list = %s where id =1"
#
#
#     while True:
#         try:
#             with conn.cursor() as cursor:
#                 cursor.execute(sql,'[adsfl]')
#             conn.commit()
#             break
#         except OperationalError:
#             conn.ping(True)
#     print("saved")
    sql_status = "SELECT id, status FROM training WHERE id = %s"
    conn, cursor = connectMysql()
    cursor.execute(sql_status, 15)
    status = cursor.fetchall()
    print(status)
    connClose(conn, cursor)
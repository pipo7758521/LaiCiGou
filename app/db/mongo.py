#!/usr/bin/python
# -*- coding: utf-8 -*-
from pymongo import MongoClient
from app.config.util import load_json
import app.logger.logger as logger


class MongoConfig():
    def __init__(self, host=None, port=None, user_name=None, password=None, db_name=None):
        self.host = host
        self.port = port
        self.user_name = user_name
        self.password = password
        self.db_name = db_name


def get_mongo_config():
    mongo_dic = load_json('mongo.json')
    config = MongoConfig()
    config.__dict__ = mongo_dic
    return config


config = get_mongo_config()
logger.suc("数据库地址：{0} 端口：{1}".format(config.host, config.port))

mongo_client = MongoClient(config.host, config.port)
mongo_client.LaiCiGou.authenticate(config.user_name, config.password)

db = mongo_client[config.db_name]

# 页面"缓存"数据集
# App 所有页面"缓存"数据，当有请求过来时，自动检查数据是否过期（半天），如超过则清除旧数据，重新统计新数据写入
page_caches = db['pageCaches']
# 用户财产"缓存"数据集
user_asset_caches = db['userAssetCaches']
# 狗狗数据集
pets = db['pets']
# 属性数据集
attributes = db['attributes']
# 相同属性狗狗数据集
twins = db['twins']
# 繁育信息数据集
breed_info = db['breedInfo']
# 交易订单数据集
orders = db['orders']
# 狗蛋识别记录数据集
recognized_babies = db['recognizedBabies']
# id转换记录数据集
converted_ids = db['convertedId']
# 用户账号数据集
users = db['users']
# 处理标记数据集
# 记录各个处理过程中最后一次处理的id号，方便下一次继续处理
last_process_ids = db['lastProcessIds']
# 带有owner字段的狗狗数据表
my_pets = db['myPets']
# 个人收藏的狗狗（已拥有）
private_collection = db['privateCollection']
# 收藏准备购买的狗狗数据表
public_collection = db['publicCollection']
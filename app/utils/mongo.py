#!/usr/bin/python
# -*- coding: utf-8 -*-
import pymongo
import app.db.mongo as mongo
from bson import ObjectId
from pymongo import MongoClient
import app.logger.logger as logger


# 获取上次统计到的id
def get_last_process_id(key):
    doc = mongo.last_process_ids.find_one({'key': key})
    if doc:
        return doc['id']
    else:
        return None


# 写入或者更新最后的处理document id
def insert_update_last_process_id(key, id):
    if not id:
        return

    doc = mongo.last_process_ids.find_one({'key': key})
    if doc:
        mongo.last_process_ids.update_one({
            '_id': doc['_id']
        }, {
            '$set': {
                'id': id
            }
        }, upsert=False)
    else:
        new_doc = {
            'key': key,
            'id': id
        }
        mongo.last_process_ids.insert(new_doc)


# 检查是否有重复入库的狗狗
def check_duplicate_pet():
    duplicate = []
    index = 0
    for pet in mongo.pets.find():
        index = index + 1
        count = mongo.pets.find({'petId': pet['petId']}).count()
        if count > 1:
            duplicate.append(pet['petId'])
            logger.warn('检查第 {0} 条狗狗 {1} ：有重复'.format(index, pet['petId']))
        else:
            logger.info('检查第 {0} 条狗狗 {1} ：无重复'.format(index, pet['petId']))

    logger.info(duplicate)


# 数据库collection拷贝
# local_to_remote=True：本地到远程（缺省）
# local_to_remote=False：远程到本地
def db_copy(name, local_to_remote=True):
    if local_to_remote:
        src_client = MongoClient()
        src_db = src_client['LaiCiGou']
        src_coll = src_db[name]

        des_db = mongo.db
        des_coll = des_db[name]
    else:
        src_db = mongo.db
        src_coll = src_db[name]

        des_client = MongoClient()
        des_db = des_client['LaiCiGou']
        des_coll = des_db[name]

    last_process_id = get_last_process_id('db_copy')
    if last_process_id:
        # 有处理记录， 接着上次继续处理
        logger.suc('继续上次的处理，上次最后处理的id为：{0}'.format(last_process_id))
        query = {'_id': {'$gt': ObjectId(last_process_id)}}
        total = src_coll.find(query).sort('_id', pymongo.ASCENDING).count()
        # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
        cursor = src_coll.find(query, no_cursor_timeout=True).sort('_id', pymongo.ASCENDING)
    else:
        # 无处理记录， 清除数据从头开始处理
        logger.warn('无上次处理记录， 强制清除数据从头开始处理')
        mongo.breed_info.drop()
        total = src_coll.find({}).sort('_id', pymongo.ASCENDING).count()
        # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
        cursor = src_coll.find({}, no_cursor_timeout=True).sort('_id', pymongo.ASCENDING)

    index = 0
    for doc in cursor:
        index = index + 1
        des_coll.insert(doc)
        insert_update_last_process_id('db_copy', doc['_id'])
        if index % 100 == 0:
            logger.info('一共 {0} 份文档，已迁移 {1} 条'.format(total, index))

    logger.info('一共 {0} 份文档，已迁移 {1} 条'.format(total, index))
    cursor.close()


if __name__ == '__main__':
    # check_duplicate_pet()
    db_copy('pets')
    pass

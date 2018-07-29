#!/usr/bin/python
# -*- coding: utf-8 -*-
import pymongo
from bson import ObjectId
import app.db.mongo as mongo
import app.logger.logger as logger
from app.utils.mongo import get_last_process_id, insert_update_last_process_id


# 给所有的属性添加int类型的id
def create_int_id():
    index = 1
    count = mongo.attributes.find({}, no_cursor_timeout=True).sort('_id', pymongo.ASCENDING).count()
    cursor = mongo.attributes.find({}, no_cursor_timeout=True).sort('_id', pymongo.ASCENDING)
    for doc in cursor:
        mongo.attributes.update_one({
            '_id': doc['_id']
        }, {
            '$set': {
                'intId': index
            }
        }, upsert=False)
        logger.info('一共 {0} 种独立属性，已处理 {1} 条'.format(count, index))
        index = index + 1
    cursor.close()


# 创建字段aIds：表示属性记录的整型id数组，大幅减少存储空间和方便创建索引
def create_attributes_int_ids():
    last_process_id = get_last_process_id('create_attributes_int_ids')
    if last_process_id:
        # 有处理记录， 接着上次继续处理
        logger.suc('继续上次的处理，上次最后处理的id为：{0}'.format(last_process_id))
        total = mongo.pets.find({'_id': {'$gt': ObjectId(last_process_id)}}).sort('_id', pymongo.ASCENDING).count()
        cursor = mongo.pets.find({'_id': {'$gt': ObjectId(last_process_id)}}, no_cursor_timeout=True).sort('_id',
                                                                                                           pymongo.ASCENDING)
    else:
        # 无处理记录， 清除数据从头开始处理
        logger.warn('无上次处理记录， 强制清除数据从头开始处理')
        total = mongo.pets.find({}).sort('_id', pymongo.ASCENDING).count()
        cursor = mongo.pets.find({}, no_cursor_timeout=True).sort('_id', pymongo.ASCENDING)

    index = 0
    for pet in cursor:
        attributes = pet['attributes']
        aIds = list()
        for attribute in attributes:
            doc = mongo.attributes.find_one(attribute)
            aIds.append(doc['intId'])

        mongo.pets.update_one({
            '_id': pet['_id']
        }, {
            '$set': {
                'aIds': aIds
            }
        }, upsert=False)

        insert_update_last_process_id('create_attributes_int_ids', pet['_id'])
        logger.info('一共 {0} 条狗狗，已统计处理 {1} 条'.format(total, index))
        index = index + 1

    logger.info('一共 {0} 条狗狗，已统计处理 {1} 条'.format(total, index))
    cursor.close()


if __name__ == '__main__':
    # create_int_id()
    create_attributes_int_ids()

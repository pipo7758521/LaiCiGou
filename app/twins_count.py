#!/usr/bin/python
#  -*- coding: utf-8 -*-
import pymongo
import app.db.mongo as mongo
import app.logger.logger as logger
from bson import ObjectId
from app.utils.mongo import get_last_process_id, insert_update_last_process_id
from app.operations.lai_ci_gou import LaiCiGou


def check_pet(pet):
    attributes = pet['attributes']
    doc = mongo.twins.find_one({'attributes': attributes})
    if doc:
        petIds = doc['petIds']
        petIds.append(pet['petId'])
        mongo.twins.update_one({
            '_id': doc['_id']
        }, {
            '$set': {
                'petIds': petIds,
                'petAmount': len(petIds),
            }
        }, upsert=False)
    else:
        new_doc = {
            'rareAmount': LaiCiGou.get_rare_amount(attributes),
            'petAmount': 1,
            'attributes': attributes,
            'petIds': [pet['petId']],
            'petUrl': pet['petUrl']
        }
        mongo.twins.insert(new_doc)

# 统计所有存在的属性组合，并记录完全相同的属性狗狗petId
def count():
    last_process_id = get_last_process_id('twins_count')
    if last_process_id:
        # 有处理记录， 接着上次继续处理
        logger.suc('继续上次的处理，上次最后处理的id为：{0}'.format(last_process_id))
        total = mongo.pets.find({'_id': {'$gt': ObjectId(last_process_id)}}).sort('_id', pymongo.ASCENDING).count()
        # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
        cursor = mongo.pets.find({'_id': {'$gt': ObjectId(last_process_id)}}, no_cursor_timeout=True).sort('_id',
                                                                                                           pymongo.ASCENDING)
    else:
        # 无处理记录， 清除数据从头开始处理
        logger.warn('无上次处理记录， 强制清除数据从头开始处理')
        mongo.twins.drop()
        total = mongo.pets.find({}).sort('_id', pymongo.ASCENDING).count()
        # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
        cursor = mongo.pets.find({}, no_cursor_timeout=True).sort('_id', pymongo.ASCENDING)

    index = 0
    for pet in cursor:
        check_pet(pet)
        insert_update_last_process_id('twins_count', pet['_id'])
        index = index + 1
        if index % 100 == 0:
            logger.info('一共 {0} 条狗狗，已统计处理 {1} 条'.format(total, index))

    logger.info('一共 {0} 条狗狗，已统计处理 {1} 条'.format(total, index))
    cursor.close()


if __name__ == '__main__':
    # total = mongo.pets.find({}).count()
    # logger.info(total)
    i = 0
    while True:
        try:
            count()
        except:
            i = i + 1
            logger.warn('异常 {0}'.format(i))

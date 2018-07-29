#!/usr/bin/python
# -*- coding: utf-8 -*-
import pymongo
import traceback
from bson import ObjectId
import app.db.mongo as mongo
from app.utils.mongo import get_last_process_id, insert_update_last_process_id
import app.logger.logger as logger


# 统计狗狗及双亲稀有属性数量之间的关系
def create_breed_info():
    last_process_id = get_last_process_id('breed_info')
    if last_process_id:
        # 有处理记录， 接着上次继续处理
        logger.suc('继续上次的处理，上次最后处理的id为：{0}'.format(last_process_id))
        query = {
            '_id': {
                '$gt': ObjectId(last_process_id)
            },
            'fatherId': {
                '$ne': None
            }
        }
        total = mongo.pets.find(query).sort('_id', pymongo.ASCENDING).count()
        # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
        cursor = mongo.pets.find(query, no_cursor_timeout=True).sort('_id', pymongo.ASCENDING)
    else:
        # 无处理记录， 清除数据从头开始处理
        logger.warn('无上次处理记录， 强制清除数据从头开始处理')
        mongo.breed_info.drop()
        total = mongo.pets.find({'fatherId': {'$ne': None}}).sort('_id', pymongo.ASCENDING).count()
        # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
        cursor = mongo.pets.find({'fatherId': {'$ne': None}}, no_cursor_timeout=True).sort('_id', pymongo.ASCENDING)

    index = 0
    for pet in cursor:
        index = index + 1
        father = mongo.pets.find_one({'petId': pet['fatherId']})
        mother = mongo.pets.find_one({'petId': pet['motherId']})
        if not father or not mother:
            continue

        data = {
            'childRareAmount': pet['rareAmount'],
            'fatherRareAmount': father['rareAmount'],
            'motherRareAmount': mother['rareAmount'],
        }

        exist = mongo.breed_info.find_one(data)
        if exist:
            mongo.breed_info.update_one({
                '_id': exist['_id']
            }, {
                '$inc': {
                    'childAmount': 1
                }
            }, upsert=False)
        else:
            data['childAmount'] = 1
            mongo.breed_info.insert(data)

        insert_update_last_process_id('breed_info', pet['_id'])
        logger.info('一共 {0} 条狗狗，已统计处理 {1} 条'.format(total, index))
        # if index % 100 == 0:
        #     logger.info('一共 {0} 条狗狗，已统计处理 {1} 条'.format(total, index))

    logger.info('一共 {0} 条狗狗，已统计处理 {1} 条'.format(total, index))
    cursor.close()

    return total == index


def count():
    while True:
        try:
            if create_breed_info():
                return
        except KeyboardInterrupt:
            logger.warn("强制停止")
            return
        except:
            traceback.print_exc()


if __name__ == '__main__':
    count()

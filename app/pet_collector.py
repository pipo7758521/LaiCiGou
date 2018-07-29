#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import time
import traceback
import app.db.mongo as mongo
import app.logger.logger as logger
from app.config.user import user
from app.operations.lai_ci_gou import LaiCiGou


class Collector(LaiCiGou):
    def __init__(self, user):
        super(Collector, self).__init__(user)

    def get_pets_on_sale(self, page_no, rare_degree):
        url = 'https://pet-chain.baidu.com/data/market/queryPetsOnSale'
        headers = self.headers_template
        data = {
            "pageNo": page_no,
            "pageSize": 10,
            "lastAmount": "",
            "lastRareDegree": "",
            "filterCondition": "{\"1\":\"" + str(rare_degree) + "\"}",
            "querySortType": "AMOUNT_ASC",
            "petIds": [],
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        pets = response['data']['petsOnSale']
        return pets

    def get_pets_on_breed(self, page_no, rare_degree):
        url = 'https://pet-chain.baidu.com/data/market/breed/pets'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/breedCentre?appId=1&tpl='
        data = {
            "pageNo": page_no,
            "pageSize": 10,
            "lastAmount": "",
            "lastRareDegree": "",
            "filterCondition": "{\"1\":\"" + str(rare_degree) + "\"}",
            "querySortType": "AMOUNT_ASC",
            "petIds": [],
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        pets = response['data']['pets4Breed']
        return pets

    # 统计属性中的稀有属性数量
    def get_rare_amount(self, attributes):
        amount = 0
        for attribute in attributes:
            if attribute['rareDegree'] == '稀有':
                amount = amount + 1

        return amount

    # 保存狗狗到数据库
    def save_pet(self, pet_info):
        pet = {
            'id': pet_info['id'],
            'petId': pet_info['petId'],
            'generation': pet_info['generation'],
            'rareDegree': pet_info['rareDegree'],
            'rareAmount': self.get_rare_amount(pet_info['attributes']),
            'fatherId': pet_info['father']['petId'] if pet_info['father'] else None,
            'motherId': pet_info['mother']['petId'] if pet_info['father'] else None,
            'bgColor': pet_info['bgColor'],
            'petUrl': pet_info['petUrl'],
            'attributes': pet_info['attributes'],
        }
        mongo.pets.insert(pet)
        logger.info('保存狗狗：{0}'.format(pet_info['petId']))

    # 保存或者更新属性数据
    def save_update_attributes(self, attributes):
        for attribute in attributes:
            exist = mongo.attributes.find_one(attribute)
            if exist:
                mongo.attributes.update_one({
                    '_id': exist['_id']
                }, {
                    '$inc': {
                        'amount': 1
                    }
                }, upsert=False)
            else:
                attribute['amount'] = 1
                attribute['svgValue'] = None
                mongo.attributes.insert(attribute)

    # 查询该狗狗信息是否已经入库
    def pet_exist(self, pet_id):
        return mongo.pets.find({"petId": pet_id}).count() != 0

    # 查询并保存狗狗及其祖宗（如果有的话）
    def query_save_pet_and_ancestors(self, pet_id):
        if self.pet_exist(pet_id):
            return

        info = self.get_pet_info_on_market(pet_id)
        self.save_pet(info)
        self.save_update_attributes(info['attributes'])

        if info['father']:
            logger.info('狗狗父亲：{0}'.format(info['father']['petId']))
            self.query_save_pet_and_ancestors(info['father']['petId'])
            logger.info('狗狗母亲：{0}'.format(info['mother']['petId']))
            self.query_save_pet_and_ancestors(info['mother']['petId'])
        else:
            return

    # 按指定稀有度查询狗狗，包括售卖的和挂出繁育的
    def get_save_pets(self, rare_degree):
        # 当前百度允许查询的最大页数为200
        max_page_no = 200
        for page_no in range(max_page_no):
            page_no = page_no + 1
            logger.info('第{0}页{1}狗狗'.format(page_no, self.rare_degree_dic[rare_degree]))
            # 获取市场上售卖的狗狗
            pets_on_sale = self.get_pets_on_sale(page_no, rare_degree)
            # 获取市场上繁育的狗狗
            pets_on_breed = self.get_pets_on_breed(page_no, rare_degree)
            # 合并市场上售卖和繁育的狗狗
            pets = pets_on_sale + pets_on_breed
            for pet in pets:
                self.query_save_pet_and_ancestors(pet['petId'])

    # 按稀有度无限循环查询和保存狗狗
    def get_save_pets_forever(self):
        rare_degree = 0
        while True:
            try:
                self.get_save_pets(rare_degree)
                rare_degree = rare_degree + 1
                if rare_degree > 5:
                    rare_degree = 0
            except KeyboardInterrupt:
                logger.warn("强制停止")
                return
            except:
                traceback.print_exc()


if __name__ == '__main__':
    collector = Collector(user)
    # 按稀有度无限循环查询和保存狗狗
    collector.get_save_pets_forever()
    # 收集单个
    # 2071930672149428690 鹿角传说！
    # collector.query_save_pet_and_ancestors('2071930672149428690')

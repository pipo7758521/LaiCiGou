#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import json
import time
import math
import app.logger.logger as logger
from app.config.user import user
from app.config.cfg import BAIDU_PUBLIC_KEY as baidu_pub_key
from app.utils.encrypt import sha256
from app.utils.encrypt import rsa_encrypt
from app.operations.lai_ci_gou import LaiCiGou
from app.db.mongo import private_collection


class Shelf(LaiCiGou):
    def __init__(self, user):
        super(Shelf, self).__init__(user)

        self.rare_degree_dic = {0: '普通', 1: '稀有', 2: '卓越', 3: '史诗', 4: '神话', 5: '传说'}

    # 创建繁育单子
    def _create(self, pet_id, price):
        url = 'https://pet-chain.baidu.com/data/market/breed/shelf/create'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        data = {
            "petId": pet_id,
            "amount": str(price),
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.fail('创建单子失败：{0} {1}'.format(response['errorNo'], response['errorMsg']))
            return None, None

        return response['data']['orderId'], response['data']['nonce']

    # 输入交易密码确认繁育单子
    def _confirm(self, pet_id, order_id, nonce):
        url = 'https://pet-chain.baidu.com/data/order/confirm'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        secret = sha256(self.user.secret) + '|' + order_id + '|' + nonce
        secret = rsa_encrypt(baidu_pub_key, secret)
        data = {
            "appId": 1,
            'confirmType': 3,
            "s": secret,
            "requestId": int(time.time() * 1000),
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.fail('挂出繁育失败: {0}'.format(response['errorMsg']))

        return response

    # 挂出繁育
    def shelf(self, pet_id, price):
        order_id, nonce = self._create(pet_id, price)
        if order_id:
            response = self._confirm(pet_id, order_id, nonce)
            return response['errorNo'] == '00'
        else:
            return False

    # 取消繁育
    def off_shelf(self, pet_id):
        url = 'https://pet-chain.baidu.com/data/market/breed/offShelf'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        data = {
            "appId": 1,
            'petId': pet_id,
            "requestId": int(time.time() * 1000),
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.fail('繁育下架失败: {0}'.format(response['errorMsg']))

        return response

    # 按条件挂出繁育所有的狗
    def shelf_by_rare_num(self, rare_num, price):
        page_size, total = 10, self.get_idle_pets_count()
        pages = math.ceil(total / page_size)

        logger.info('共 {0} 条狗狗，每页 {1} 条，共 {2} 页'.format(total, page_size, pages))

        for page in range(pages):
            logger.info('处理第{0}页：'.format(page + 1))
            pets = self.get_idle_pets(page + 1, page_size)

            for pet in pets:
                # 珍藏的狗狗不上架
                if private_collection.find_one({'user': self.user.name, 'petId': pet['petId']}):
                    logger.warn('珍藏的狗狗不上架：{0}'.format(pet['petId']))
                    continue

                pet_info = self.get_pet_info_on_market(pet['petId'])
                pet_rare_num = self.get_rare_amount(pet_info['attributes'])
                if pet_rare_num != rare_num:
                    continue

                logger.info('挂出繁育 {0}，{1}稀，价格 {2}'.format(pet['petId'], rare_num, price))
                self.shelf(pet['petId'], price)

                # 百度控制的上架时间间隔目前约为10秒，少于10秒会被拒绝
                self.random_sleep(10, 15)

    # 按稀有属性数量批次挂出繁育，时间上会成倍增加，如不需按稀有数量批次上架请使用shelf_by_rare_num_once
    def shelf_by_rare_nums(self, rare_num_price_dic=None):
        for rare_num in rare_num_price_dic:
            self.shelf_by_rare_num(rare_num, rare_num_price_dic[rare_num])

    # 按稀有属性数量一次性挂出繁育所有的狗
    def shelf_by_rare_nums_once(self, rare_num_price_dic=None):
        if rare_num_price_dic is None:
            logger.warn('没有设置价格字典！')
            return

        page_size, total = 10, self.get_idle_pets_count()
        pages = math.ceil(total / page_size)

        logger.info('共 {0} 条狗狗，每页 {1} 条，共 {2} 页'.format(total, page_size, pages))

        for page in range(pages):
            logger.info('处理第{0}页：'.format(page + 1))
            pets = self.get_idle_pets(page + 1, page_size)

            for pet in pets:
                # 珍藏的狗狗不上架
                if private_collection.find_one({'user': self.user.name, 'petId': pet['petId']}):
                    logger.warn('珍藏的狗狗不上架：{0}'.format(pet['petId']))
                    continue

                pet_info = self.get_pet_info_on_market(pet['petId'])
                rare_num = self.get_rare_amount(pet_info['attributes'])
                if rare_num not in rare_num_price_dic:
                    continue

                price = rare_num_price_dic[rare_num]
                logger.info('挂出繁育 {0}，{1}稀，价格 {2}'.format(pet['petId'], rare_num, price))
                self.shelf(pet['petId'], price)
                # 百度控制的上架时间间隔目前约为10秒，少于10秒会被拒绝
                self.random_sleep(10, 15)


if __name__ == '__main__':
    shelf = Shelf(user)
    rare_num_price_dic = {0: 100, 1: 100, 2: 100, 3: 100, 4: 500}
    # rare_num_price_dic = {0: 100, 1: 100, 2: 100, 3: 100, 4: 500}
    # 按稀有属性数量批次挂出繁育，时间上会成倍增加，如不需按稀有数量批次上架请使用shelf_by_rare_num_once
    # shelf.shelf_by_rare_nums(rare_num_price_dic)
    # 按稀有属性数量一次性挂出繁育所有的狗
    shelf.shelf_by_rare_nums_once(rare_num_price_dic)

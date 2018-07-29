#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import json
import time
import app.logger.logger as logger
from app.config.user import user
from app.config.cfg import BAIDU_PUBLIC_KEY as baidu_pub_key
from app.utils.encrypt import sha256
from app.utils.encrypt import rsa_encrypt
from app.operations.lai_ci_gou import LaiCiGou
from app.db.mongo import private_collection


class Sale(LaiCiGou):
    def __init__(self, user):
        super(Sale, self).__init__(user)

    def get_attribute(self, attributes, name):
        for attribute in attributes:
            if attribute['name'] == name:
                return attribute['value']

    # 创建卖出单子
    def create(self, pet_id, price):
        logger.info('创建卖出狗狗单子 {0}，价格{1}'.format(pet_id, price))
        url = 'https://pet-chain.baidu.com/data/market/sale/shelf/create'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        data = {
            "petId": pet_id,
            "amount": price,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.fail('创建单子失败：{0}'.format(response['errorMsg']))

        return response

    # 确认卖出
    def confirm(self, pet_id, order_id, nonce):
        url = 'https://pet-chain.baidu.com/data/order/confirm'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        secret = sha256(self.user.secret) + '|' + order_id + '|' + nonce
        secret = rsa_encrypt(baidu_pub_key, secret)
        data = {
            "appId": 1,
            'confirmType': 1,
            "s": secret,
            "requestId": int(time.time() * 1000),
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.fail('卖出单子确认失败: {0}'.format(response['errorMsg']))

        return response

    # 卖出
    def sale(self, pet_id, price):
        response = self.create(pet_id, price)
        if response['errorNo'] == '00':
            order_id = response['data']['orderId']
            nonce = response['data']['nonce']
            self.confirm(pet_id, order_id, nonce)

    # 取消卖出
    def unsale(self, pet_id):
        url = 'https://pet-chain.baidu.com/data/market/unsalePet'
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
            logger.fail('取消卖出失败: {0}'.format(response['errorMsg']))

        return response

    # 按条件卖出所有狗狗
    def sale_all(self, rare_num_price_dic, include_angel=False):
        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                # 珍藏的狗狗不上架
                if private_collection.find_one({'user': self.user.name, 'petId': pet['petId']}):
                    logger.warn('珍藏的狗狗不上架：{0}'.format(pet['petId']))
                    continue

                cooling_interval = pet['coolingInterval']
                if '分钟' in cooling_interval:
                    continue

                cooling_interval = int(cooling_interval.replace('天'))
                if cooling_interval <= 4:  # 只卖休息时间大于4天的狗狗
                    continue

                if pet['shelfStatus'] != 0 or pet['lockStatus'] == 1:
                    continue

                pet_info = self.get_pet_info_on_market(pet['petId'])
                rare_num = self.get_rare_amount(pet_info['attributes'])

                if rare_num not in rare_num_price_dic:
                    continue

                if not include_angel:
                    physique = self.get_attribute(pet_info['attributes'], '体型')
                    if physique == '天使':
                        logger.warn('天使狗狗不卖： {0}'.format(pet['petId']))
                        continue

                self.sale(pet['petId'], rare_num_price_dic[rare_num])
            time.sleep(5)


if __name__ == '__main__':
    sale = Sale(user)
    rare_num_price_dic = {0: 200, 1: 200, 2: 200, 3: 200}
    sale.sale_all(rare_num_price_dic)

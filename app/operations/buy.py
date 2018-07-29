#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import time
import traceback
import app.logger.logger as logger
from app.config.user import user
from app.config.cfg import BAIDU_PUBLIC_KEY as baidu_pub_key
from app.utils.encrypt import sha256
from app.utils.encrypt import rsa_encrypt
from app.operations.lai_ci_gou import LaiCiGou
# from ml.captcha_crack_baidu.captcha_crack import Crack
from app.captcha_crack.captcha_recognize_new import Crack


class Buy(LaiCiGou):
    def __init__(self, user):
        super(Buy, self).__init__(user)

    def get_pets_on_sale(self):
        url = 'https://pet-chain.baidu.com/data/market/queryPetsOnSale'
        headers = self.headers_template
        data = {
            "pageNo": 1,
            "pageSize": 10,
            "lastAmount": "",
            "lastRareDegree": "",
            "filterCondition": "{}",
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

    def get_pets_with_condition(self, page_no, rare_degree):
        url = 'https://pet-chain.baidu.com/data/market/queryPetsOnSale'
        headers = self.headers_template
        data = {
            "pageNo": page_no,
            "pageSize": 10,
            "lastAmount": "",
            "lastRareDegree": "",
            "filterCondition": "{\"1\":" + str(rare_degree) + ",\"3\":\"0-1\"}",
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

    def get_attribute(self, attributes, name):
        for attribute in attributes:
            if attribute['name'] == name:
                return attribute['value']

    def get_captcha_and_seed(self, pet_id, valid_code):
        url = 'https://pet-chain.baidu.com/data/captcha/gen'
        headers = self.headers_template
        headers[
            'Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=market&petId=' + pet_id + '&validCode=' + valid_code + '&appId=1&tpl='
        data = {
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.err('获取验证码失败：{0}'.format(response['errorMsg']))
            return None, None

        return response['data']['seed'], response['data']['img']

    def create(self, pet_id, valid_code, seed, captcha, price):
        url = 'https://pet-chain.baidu.com/data/txn/sale/create'
        headers = self.headers_template
        headers[
            'Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=market&petId=' + pet_id + '&validCode=' + valid_code + '&appId=1&tpl='
        data = {
            "petId": pet_id,
            "amount": price,
            "seed": seed,
            "captcha": captcha,
            "validCode": valid_code,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.fail('创建单子失败：{0}'.format(response['errorMsg']))

        return response

    def confirm(self, pet_id, order_id, nonce, valid_code):
        url = 'https://pet-chain.baidu.com/data/order/confirm'
        headers = self.headers_template
        headers[
            'Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=market&petId=' + pet_id + '&validCode=' + valid_code + '&appId=1&tpl='
        secret = sha256(self.user.secret) + '|' + order_id + '|' + nonce
        secret = rsa_encrypt(baidu_pub_key, secret)
        data = {
            "appId": 1,
            'confirmType': 2,
            "s": secret,
            "requestId": int(time.time() * 1000),
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.fail('买入失败: {0}'.format(response['errorMsg']))

        return response

    # 机器学习破解验证码自动购买
    def buy(self, pet):
        pet_id, price, valid_code, generation = pet['petId'], pet["amount"], pet['validCode'], pet['generation']
        count = 1
        while True:
            logger.info('第{0}次尝试购买，狗狗ID：{1}, 代数 {2}, 价格 {3}'.format(count, pet_id, generation, price))
            count += 1

            seed, img = self.get_captcha_and_seed(pet_id, valid_code)
            if not seed:
                self.random_sleep(30, 60)
                continue

            captcha = Crack.predict(img)
            response = self.create(pet_id, valid_code, seed, captcha, price)
            if response['errorNo'] == '00':
                order_id = response['data']['orderId']
                nonce = response['data']['nonce']
                response = self.confirm(pet_id, order_id, nonce, valid_code)
                if response['errorNo'] == '00':
                    return response

            # 10002: 有人抢先下单啦
            # 10018：您今日交易次数已超限，明天再试试吧
            errors = ['10002', '10018']
            if response['errorNo'] in errors:
                return response

            self.random_sleep(30, 60)

    # 购买低于指定价格的天使狗，直到达到当日最大交易次数为止
    def buy_angel_pets_until_max_trade_times(self, price_limit):
        while True:
            try:
                pets = self.get_pets_on_sale()
                for pet in pets:
                    price = float(pet["amount"])
                    if price > price_limit:
                        continue

                    pet_info = self.get_pet_info_on_market(pet['petId'])
                    physique = self.get_attribute(pet_info['attributes'], '体型')
                    logger.info("{:\u3000<10} {:>8}".format('体型：' + physique, '价格：' + str(price)))

                    if physique != '天使':
                        continue

                    response = self.buy(pet)
                    # 10018：您今日交易次数已超限，明天再试试吧
                    if response['errorNo'] == '10018':
                        return
            except:
                traceback.print_exc()

    # 购买符合条件的狗狗，直到达到当日最大交易次数为止
    def buy_pets_until_max_trade_times(self, price_limit, rare_degree, max_generation, max_count):
        count = 0
        page_no = 1
        while True:
            try:
                pets = self.get_pets_with_condition(page_no, rare_degree)
                logger.warn('第 {0} 页'.format(page_no))
                page_no = page_no + 1
                for pet in pets:
                    price = float(pet["amount"])
                    if price > price_limit:
                        page_no = 1

                    generation = pet['generation']
                    if generation > max_generation:
                        continue

                    response = self.buy(pet)
                    if response['errorNo'] == '00':
                        count = count + 1
                        logger.info('已购买 {0} 条'.format(count))
                        self.random_sleep(180, 240)

                    # 购买已达最大数量限制
                    if count == max_count:
                        return

                    # 10018：您今日交易次数已超限，明天再试试吧
                    if response['errorNo'] == '10018':
                        logger.warn('达到最大交易次数时已购买 {0} 条'.format(count))
                        return
                self.random_sleep(30, 60)
            except:
                self.random_sleep(30, 60)
                traceback.print_exc()


if __name__ == '__main__':
    buy = Buy(user)
    # 购买天使狗 价格不高于200
    # buy.buy_angel_pets_until_max_trade_times(200)
    # 购买卓越狗 价格不高于100， 代数不高于2代，数量不超过100条
    buy.buy_pets_until_max_trade_times(100, 2, 2, 100)
    # 购买史诗狗 价格不高于2500， 代数不高于2代，数量不超过5条
    #buy.buy_pets_until_max_trade_times(2500, 3, 2, 5)

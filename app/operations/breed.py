#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
import traceback
import requests
import app.logger.logger as logger
from app.config.user import user
from app.db.mongo import private_collection
from app.config.cfg import BAIDU_PUBLIC_KEY as baidu_pub_key
from app.utils.encrypt import sha256
from app.utils.encrypt import rsa_encrypt
from app.operations.sale import Sale
from app.operations.shelf import Shelf
from app.operations.lai_ci_gou import LaiCiGou
# from ml.captcha_crack_baidu.captcha_crack import Crack
from app.captcha_crack.captcha_recognize_new import Crack


class Breed(LaiCiGou):
    def __init__(self, user):
        super(Breed, self).__init__(user)

    # 获取验证码和种子
    def get_captcha_and_seed(self):
        url = 'https://pet-chain.baidu.com/data/captcha/gen'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/chooseMyDog?appId=1&tpl='
        data = {
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.warn('获取验证码失败：{0}'.format(response['errorMsg']))
            return None, None

        return response['data']['seed'], response['data']['img']

    # 繁殖请求
    def create(self, father_pet_id, mother_pet_id, amount, captcha, seed):
        url = 'https://pet-chain.baidu.com/data/txn/breed/create'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/chooseMyDog?appId=1&tpl='
        data = {
            "petId": father_pet_id,
            "senderPetId": mother_pet_id,
            "amount": amount,
            "captcha": captcha,
            "seed": seed,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] == '00':
            logger.suc('繁育下单成功')
        else:
            logger.fail('繁育下单失败: {0} {1}'.format(response['errorNo'], response['errorMsg']))

        return response

    def confirm(self, order_id, nonce):
        url = 'https://pet-chain.baidu.com/data/order/confirm'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/chooseMyDog?appId=1&tpl='
        secret = sha256(self.user.secret) + '|' + order_id + '|' + nonce
        secret = rsa_encrypt(baidu_pub_key, secret)
        data = {
            "appId": 1,
            'confirmType': 4,
            "s": secret,
            "requestId": int(time.time() * 1000),
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] == '00':
            logger.suc('繁育确认成功')
        else:
            logger.fail('繁育确认失败: {0}'.format(response['errorMsg']))

        return response

    # 机器学习破解验证码自动繁育
    def breed(self, father, mother):
        father_id = father['petId']
        mother_id = mother['petId']
        price = father['amount']

        count = 1
        while True:
            logger.info('第{0}次尝试繁殖，父亲狗狗ID：{1}, 母亲狗狗ID: {2}，价格 {3}'.format(count, father_id, mother_id, price))
            count += 1

            seed, img = self.get_captcha_and_seed()
            if not seed:
                time.sleep(3)
                continue

            captcha = Crack.predict(img)
            response = self.create(father_id, mother_id, price, captcha, seed)

            if response['errorNo'] == '00':
                order_id = response['data']['orderId']
                nonce = response['data']['nonce']
                response = self.confirm(order_id, nonce)
                if response['errorNo'] == '00':
                    return response

            # 10002: 有人抢先下单啦
            # 10018：您今日交易次数已超限，明天再试试吧
            #      : 狗狗已经下架啦
            # TODO 添加错误码到列表
            errors = ['10002', '10018']
            if response['errorNo'] in errors:
                return response

            self.random_sleep(30, 60)

    # 获取指定稀有属性数量的狗狗
    def get_parents(self, father_rare_num, mother_rare_num):
        father, mother = None, None
        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                if pet['isCooling'] or pet['lockStatus'] == 1:
                    continue

                pet_info = self.get_pet_info_on_market(pet['petId'])
                rare_num = self.get_rare_amount(pet_info['attributes'])

                if not father and father_rare_num == rare_num:
                    father = pet
                    logger.info('选中狗狗父亲：{0}'.format(father['petId']))
                    continue

                if not mother and mother_rare_num == rare_num:
                    mother = pet
                    logger.info('选中狗狗母亲：{0}'.format(mother['petId']))
                    break
            father_id = father['petId'] if father else None
            mother_id = mother['petId'] if mother else None
            logger.info('第{0}页时： 狗狗父亲 {1}， 狗狗母亲 {2}'.format(page_no, father_id, mother_id))
            if father and mother:
                break

        return (father, mother)

    # 从珍藏的狗狗中选取要繁殖的双亲
    def get_parents_from_private_collection(self):
        father, mother = None, None
        cursor = private_collection.find({'user': self.user.name})
        for pet in cursor:
            pet = self.get_pet_info_on_market(pet['petId'])
            pet['rareAmount'] = self.get_rare_amount(pet['attributes'])

            if pet['isCooling'] or pet['lockStatus'] == 1:
                continue

            if not father:
                father = pet
                logger.info('选中狗狗父亲：{0}'.format(father['petId']))
                continue

            if not mother:
                mother = pet
                logger.info('选中狗狗母亲：{0}'.format(mother['petId']))
                break

            if father and mother:
                break

        cursor.close()

        if not father or not mother:
            return (father, mother)

        # 确保父亲狗狗稀有度低于母亲狗狗，上架时可降低价格，从而减少成本，同时也减少由于上架高稀有度狗狗而被狗友抢走繁殖的可能
        if father['rareAmount'] > mother['rareAmount']:
            father, mother = mother, father
            logger.warn('父亲狗狗稀有度大于母亲狗狗，交换之~')

        return (father, mother)

    # 查询满足繁育条件的狗狗双亲
    # 如果双亲上架状态条件不满足，则处理使之符合条件
    def prepare_parents(self, father_rare_num, father_price, mother_rare_num, from_private_collection,
                        father_price_dic):
        while True:
            try:
                if from_private_collection:
                    father, mother = self.get_parents_from_private_collection()
                    if not father or not mother:
                        logger.warn('没有可用的狗狗，请使用其他方式选择繁殖')
                        return

                    father_price = father_price_dic[father['rareAmount']]
                    logger.warn('父亲狗狗上架繁育价格为：{0}'.format(father_price))
                else:
                    father, mother = self.get_parents(father_rare_num, mother_rare_num)

                if not father or not mother:
                    logger.warn('无满足条件的繁育双亲， 一分钟后重试')
                    self.random_sleep(60, 90)
                    continue

                # 未上架繁育，将其上架
                if father['shelfStatus'] == 0:
                    logger.info('父亲狗狗{0}处于未上架繁育状态，将其上架'.format(father['petId']))
                    shelf = Shelf(self.user)
                    shelf_success = shelf.shelf(father['petId'], father_price)
                    if not shelf_success:
                        continue

                    # 等待3分钟避免错误：专属分享，3分钟后可购买
                    time.sleep(3 * 60)
                # 出售中，将其下架然后上架繁育
                elif father['shelfStatus'] == 1:
                    logger.info('父亲狗狗{0}处于售卖中, 将其下架， 三分钟后再挂出繁育'.format(father['petId']))
                    sale = Sale(self.user)
                    sale.unsale(father['petId'])

                    # 3分钟后再挂出繁育，避免上下架过频繁
                    time.sleep(3 * 60)

                    logger.info('挂出繁育父亲狗狗{0}'.format(father['petId']))
                    shelf = Shelf(self.user)
                    shelf_success = shelf.shelf(father['petId'], father_price)
                    if not shelf_success:
                        continue
                # 出售中，将其下架
                if mother['shelfStatus'] == 1:
                    logger.info('母亲狗狗{0}处于出售状态，将其下架然'.format(mother['petId']))
                    sale = Sale(self.user)
                    sale.unsale(mother['petId'])
                # 挂出繁育中，将其下架
                elif mother['shelfStatus'] == 2:
                    logger.info('母亲狗狗{0}处于挂出繁育状态，将其下架'.format(mother['petId']))
                    shelf = Shelf(self.user)
                    shelf.off_shelf(mother['petId'])

                # 再次获取狗狗双亲信息，保证信息是最新的
                father = self.get_pet_info_on_market(father['petId'])
                mother = self.get_pet_info_on_market(mother['petId'])

                return (father, mother)
            except:
                traceback.print_exc()
                self.random_sleep(30, 60)

    # 狗狗内部繁殖，直到达到当日最大交易次数为止
    def breed_until_max_trade_times(self, father_rare_num, father_price, mother_rare_num, from_private_collection,
                                    father_price_dic):
        while True:
            try:
                father, mother = self.prepare_parents(father_rare_num, father_price, mother_rare_num,
                                                      from_private_collection, father_price_dic)
                response = self.breed(father, mother)

                # 10018：您今日交易次数已超限，明天再试试吧
                if response['errorNo'] == '10018':
                    return

                self.random_sleep(10, 30)
            except:
                self.random_sleep(10, 30)
                traceback.print_exc()


if __name__ == '__main__':
    breed = Breed(user)
    # 方式一：
    # 从所有狗狗中选择繁殖
    # logger.warn('繁殖方式： 从所有狗狗中选择繁殖')
    # breed.breed_until_max_trade_times(4, 500, 5, False, None)

    # 方式二：
    # 从珍藏狗狗中选择繁殖
    # 上架价格字典，稀有属性数量作为key， 价格作为value
    # logger.warn('繁殖方式： 从珍藏狗狗中选择繁殖')
    price_dic = {0: 500, 1: 500, 2: 500, 3: 800, 4: 1000, 5: 10000, 6: 1000000, 7: 1000000, 8: 100000000}
    breed.breed_until_max_trade_times(None, None, None, True, price_dic)

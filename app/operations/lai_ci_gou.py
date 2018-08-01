#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
import random
import requests
import app.logger.logger as logger
from app.config.user import user


class LaiCiGou:
    RARE_AMOUNT_DIC = {0: '普通', 1: '普通', 2: '稀有', 3: '卓越', 4: '史诗', 5: '史诗', 6: '神话', 7: '神话', 8: '传说'}

    def __init__(self, user):
        self.user = user

        self.headers_template = {
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6',
            'Content-Type': 'application/json',
            'Cookie': self.user.cookie,
            'Host': 'pet-chain.baidu.com',
            'Origin': 'https://pet-chain.baidu.com',
            'Referer': 'https://pet-chain.baidu.com/chain/dogMarket?appId=1&tpl=',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        }

        self.deal_type = {1: '出生', 2: '繁育', 3: '交易'}

        self.rare_degree_dic = {0: '普通', 1: '稀有', 2: '卓越', 3: '史诗', 4: '神话', 5: '传说'}

        self.rare_amount_dic = {0: '普通', 1: '普通', 2: '稀有', 3: '卓越', 4: '史诗', 5: '史诗', 6: '神话', 7: '神话', 8: '传说'}

        self.attributes_names = ['体型', '花纹', '眼睛', '眼睛色', '嘴巴', '肚皮色', '身体色', '花纹色']

        self.shelf_status = {0: '未上市', 1: '在售', 2: '待繁育'}

        # 每日签到 2018年6月14日，百度关闭此功能
        # self.sign()

    # 每日签到
    def sign(self):
        url = 'https://pet-chain.baidu.com/data/user/sign'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/personal?appId=1&tpl='
        data = {
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        print(r.content)
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            logger.fail('签到失败：{0}'.format(response['errorMsg']))
            return

        sign_amount = response['data']['signAmount']
        total_sign_times = response['data']['totalSignTimes']
        total_sign_amount = response['data']['totalSignAmount']
        if response['data']['isSigned']:
            logger.suc('已签到过，获得{0}微，签到次数{1} 累计{2}微'.format(sign_amount, total_sign_times, total_sign_amount))
        else:
            logger.suc('签到成功，获得{0}微，签到次数{1} 累计{2}微'.format(sign_amount, total_sign_times, total_sign_amount))

    # 分页获取狗狗数据
    def _get_pets_data(self, page_no, page_size, page_total, total_count):
        url = 'https://pet-chain.baidu.com/data/user/pet/list'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/personal'
        data = {
            "pageNo": page_no,
            "pageSize": page_size,
            "pageTotal": page_total,
            "totalCount": total_count,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 获取狗总数
    def get_pets_count(self):
        return self._get_pets_data(1, 10, -1, 0)['totalCount']

    # 分页获取狗狗
    def get_pets(self, page_no, page_size, page_total, total_count):
        return self._get_pets_data(page_no, page_size, page_total, total_count)['dataList']

    # 分页获取狗宝宝数据
    def _get_baby_pets_data(self, page_no, page_size, page_total, total_count):
        url = 'https://pet-chain.baidu.com/data/breed/parentbox/list'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/personal?appId=1&tpl='
        data = {
            "pageNo": page_no,
            "pageSize": page_size,
            "pageTotal": page_total,
            "totalCount": total_count,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 获取狗宝宝总数
    def get_baby_pets_count(self):
        return self._get_baby_pets_data(1, 10, -1, 0)['totalCount']

    # 分页获取狗宝宝
    def get_baby_pets(self, page_no, page_size, page_total, total_count):
        return self._get_baby_pets_data(page_no, page_size, page_total, total_count)['dataList']

    # 获取空闲狗狗数据
    def _get_idle_pets_data(self, page_no, page_size):
        url = 'https://pet-chain.baidu.com/data/breed/petList'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/chooseMyDog?appId=1&tpl='
        data = {
            "pageNo": page_no,
            "pageSize": page_size,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 获取空闲狗狗总数
    def get_idle_pets_count(self):
        return self._get_idle_pets_data(1, 10)['totalCount']

    # 分页获取空闲狗狗
    def get_idle_pets(self, page_no, page_size):
        return self._get_idle_pets_data(page_no, page_size)['dataList']

    # 获取市场上的狗狗信息
    def get_pet_info_on_market(self, pet_id):
        url = 'https://pet-chain.baidu.com/data/pet/queryPetById'
        headers = self.headers_template
        headers[
            'Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=market&petId=' + pet_id + '&validCode=&appId=1&tpl='
        data = {
            "petId": pet_id,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 获取自己狗狗的详细信息
    def get_pet_info_in_center(self, pet_id):
        url = 'https://pet-chain.baidu.com/data/pet/queryPetByIdWithAuth'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        data = {
            "petId": pet_id,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 获取自己狗宝宝的详细信息
    def get_baby_pet_info(self, pet_id):
        url = 'https://pet-chain.baidu.com/data/breed/detail'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/babyDetail?petId=' + pet_id
        data = {
            "petId": pet_id,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 统计属性中的稀有属性数量
    @staticmethod
    def get_rare_amount(attributes):
        amount = 0
        for attribute in attributes:
            if attribute['rareDegree'] == '稀有':
                amount = amount + 1

        return amount

    # 获取狗宝宝双亲信息
    def get_baby_parents(self, pet_id):
        url = 'https://pet-chain.baidu.com/data/breed/detail'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/babyDetail?petId=' + pet_id
        data = {
            "petId": pet_id,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        father = response['data']['fatherInfo']
        mother = response['data']['matherInfo']  # 次字段应该是百度拼写错误，应该为motherInfo
        return father, mother

    # 随机sleep一段时间再试，防止百度数据分析
    def random_sleep(self, min, max):
        interval = random.randint(min, max)
        logger.warn('随机暂停 {0} 秒'.format(interval))
        time.sleep(interval)

    def get_pets_on_sale(self, condition):
        url = 'https://pet-chain.baidu.com/data/market/queryPetsOnSale'
        headers = self.headers_template
        r = requests.post(url, headers=headers, data=json.dumps(condition))
        response = json.loads(r.content)
        pets = response['data']['petsOnSale']
        return pets


if __name__ == '__main__':
    lai_ci_gou = LaiCiGou(user)
    # total = lai_ci_gou.get_pets_count()
    # log(total)
    total = lai_ci_gou.get_idle_pets_count()
    logger.info(total)

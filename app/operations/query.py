#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
import traceback
import matplotlib.pyplot as plt
import numpy as np
import app.logger.logger as logger
from pylab import mpl
from scipy.interpolate import spline
from datetime import datetime
from app.config.user import user
from app.operations.lai_ci_gou import LaiCiGou


class Query(LaiCiGou):
    def __init__(self, user):
        super(Query, self).__init__(user)

        self.lowest_price_pets = []

        if not os.path.exists('charts'):
            os.makedirs('charts')
            logger.info('创建文件夹：' + 'charts')

    def get_pets_with_condition(self, rare_degree):
        url = 'https://pet-chain.baidu.com/data/market/queryPetsOnSale'
        headers = self.headers_template
        data = {
            "pageNo": 1,
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

    def draw_chart(self):
        fig = plt.gcf()
        fig.set_size_inches(18.5, 4.8)

        mpl.rcParams['font.sans-serif'] = ['SimHei']  # SimHei是黑体的意思

        plt.xlabel('时间')
        plt.ylabel('价格')
        plt.title('史诗狗低价走势图')

        x, y = [], []
        i = 2
        for pet in self.lowest_price_pets:
            y.append(float(pet['price']))  # + random.randint(1, 1000)
            # x.append(pet['x'])
            second = time.mktime(time.strptime(pet['time'], '%Y-%m-%d %H:%M:%S'))
            # print(second)
            # x.append(float(second)/float(1000000))
            # @x.append(second)
            x.append(i)
            i = i + 1

        T = np.array(x)
        y_new = np.array(y)
        x_new = np.linspace(T.min(), T.max(), 10000)  # 300 represents number of points to make between T.min and T.max
        price_smooth = spline(T, y_new, x_new)
        plt.plot(x_new, price_smooth)

        # plt.plot_date(x, y)
        # plt.plot_date(x,y, xdate=True, linestyle='-', color='green', marker='.')
        # plt.xticks(np.arange(min(x), max(x) + 1, 1.0))

        # plt.plot(x, y, linestyle='-', color='green', marker='.')
        # plt.xticks(np.arange(min(x), max(x) + 1, 1.0))
        # plt.show()
        plt.savefig('./charts/' + str(len(self.lowest_price_pets)))
        plt.close()

    # 购买符合条件的狗狗，直到达到当日最大交易次数为止
    def query_lowest_price_pet(self, rare_degree, max_generation):
        i = 1
        while True:
            try:
                pets = self.get_pets_with_condition(rare_degree)
                lowest_pet = pets[0]

                for pet in pets:
                    if float(lowest_pet['amount']) > float(pet['amount']):
                        lowest_pet = pet
                pet = {
                    'petId': lowest_pet['petId'],
                    'generation': lowest_pet['generation'],
                    'price': lowest_pet['amount'],
                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'x': datetime.now().strftime("%H:%M:%S")
                }

                self.lowest_price_pets.append(pet)

                # if len(self.lowest_price_pets) == 0:
                #     self.lowest_price_pets.append(pet)
                # else:
                #     last_lowest_price_pet = self.lowest_price_pets[len(self.lowest_price_pets) - 1]
                #     if last_lowest_price_pet['petId'] != pet['petId']:
                #         self.lowest_price_pets.append(pet)

                logger.info('最低价狗狗： petId {0}, 代数 {1}, 价格 {2}'.format(pet['petId'], pet['generation'], pet['price']))

                if i % 100 == 0:
                    self.draw_chart()
                i = i + 1
                time.sleep(5)
            except:
                traceback.print_exc()
                time.sleep(5)


if __name__ == '__main__':
    query = Query(user)
    query.query_lowest_price_pet(3, 2)

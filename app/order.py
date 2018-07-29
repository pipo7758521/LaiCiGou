#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import json
import time
import pymongo
from datetime import datetime
import app.db.mongo as mongo
import app.logger.logger as logger
from app.config.user import user
from app.operations.lai_ci_gou import LaiCiGou


class Order(LaiCiGou):
    def __init__(self, user, clear=True):
        super(Order, self).__init__(user)

        self.status = {
            1: "已卖出",
            2: "已买入",
            3: "繁育收入",
            4: "繁育支出"
        }

        self.txnStatus = {
            0: "上链中",
            1: "上链中",
            2: "成功",
            3: "失败",
            4: "失败"
        }

        if (clear):
            # 查询保存前先清掉所有数据
            logger.info('强制更新数据，清除所有记录')
            mongo.orders.delete_many({})

    # 获取当前微积分总数
    def _get_latest_calculus(self):
        url = 'https://pet-chain.baidu.com/data/user/get'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/personal?appId=1&tpl='
        data = {
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return float(response['data']['amount'])

    # 获取账号交易历史记录数据
    def _get_order_data(self, page_no, page_size, page_total, total_count):
        url = 'https://pet-chain.baidu.com/data/user/order/list'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/personal?appId=1&tpl='
        data = {
            "pageNo": page_no,
            "pageSize": page_size,
            "pageTotal": page_total,
            "totalCount": total_count,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 获取交易历史记录总数
    def _get_order_count(self):
        return self._get_order_data(1, 10, -1, 0)['totalCount']

    # 分页获取交易历史记录数据
    def _get_order_list(self, page_no, page_size, page_total, total_count):
        return self._get_order_data(page_no, page_size, page_total, total_count)['dataList']

    # 获取最早的交易记录日期
    def get_oldest_order_trans_date(self):
        for order in mongo.orders.find({'userId': self.user.id, 'txnStatus': 2}).sort(
                [("transDate", pymongo.ASCENDING)]):
            return order['transDate']

    # 获取最后的交易记录日期
    def get_latest_order_trans_date(self):
        for order in mongo.orders.find({'userId': self.user.id, 'txnStatus': 2}).sort(
                [("transDate", pymongo.DESCENDING)]):
            return order['transDate']

    # 保存交易记录简略信息
    def _save_order(self, order, current_amount):
        mongo.orders.insert({
            "userId": self.user.id,
            "amount": order['amount'],
            "type": order['status'],
            'txnStatus': order['txnStatus'],
            'currentAmount': current_amount,
            "transDate": order['transDate']}
        )

    # 获取所有交易历史记录数据
    def _get_save_all_orders(self, from_date=None):
        today = datetime.now().strftime("%Y-%m-%d")
        page_size = 10
        total = self._get_order_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            orders = self._get_order_list(page_no, page_size, pages, total)
            for order in orders:
                if from_date and order['transDate'] == from_date:
                    return

                if order['transDate'] == today:
                    current_amount = self._get_latest_calculus()
                    self._save_order(order, current_amount)
                else:
                    self._save_order(order, 0.0)
                logger.info('保存订单：{0} {1} {2} 微积分 状态 {3}'.format(order['transDate'], self.status[order['status']],
                                                                 order['amount'],
                                                                 self.txnStatus[order['txnStatus']]))
            time.sleep(1)

    # 获取所有交易历史记录数据
    def must_have_all_orders(self):
        count = mongo.orders.find({'userId': self.user.id}).count()
        if count == 0:
            self._get_save_all_orders()
        else:
            latest_record_date = self.get_latest_order_trans_date()
            print(latest_record_date)
            self._get_save_all_orders(from_date=latest_record_date)


if __name__ == '__main__':
    order = Order(user, clear=False)
    order.must_have_all_orders()

#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import traceback
import app.logger.logger as logger
from app.operations.shelf import Shelf
from app.operations.breed import Breed
from app.operations.sale import Sale
from app.operations.buy import Buy
from app.config.user import user
from app.config.user import users
from app.config.cfg import ACCOUNT_0
from app.config.cfg import ACCOUNT_1
from app.config.cfg import ACCOUNT_2
from app.config.cfg import ACCOUNT_3


def sale():
    logger.info('启动卖出定时任务')
    sale = Sale(user)
    try:
        sale.sale_all(100, 0)
        sale.sale_all(100, 1)
    except:
        traceback.print_exc()
    logger.info('卖出定时任务执行完成')


def shelf():
    logger.info('启动挂出繁育定时任务')
    try:
        shelf = Shelf(user)
        rare_num_price_dic = {0: 100, 1: 100, 2: 100, 3: 100, 4: 500}
        # rare_num_price_dic = {0: 100, 1: 100, 2: 100, 3: 100, 4: 500}
        # 按稀有属性数量批次挂出繁育，时间上会成倍增加，如不需按稀有数量批次上架请使用shelf_by_rare_num_once
        # shelf.shelf_by_rare_nums(rare_num_price_dic)
        # 按稀有属性数量一次性挂出繁育所有的狗
        shelf.shelf_by_rare_nums_once(rare_num_price_dic)
    except:
        traceback.print_exc()
    logger.info('挂出繁育定时任务执行完成')


def shelf_multiple_users():
    while True:
        try:
            for user in users:
                if user.name == ACCOUNT_0 or user.name == ACCOUNT_1:
                    continue
                logger.suc('当前账号：{0}'.format(user.name))
                shelf = Shelf(user)
                rare_num_price_dic = {0: 100, 1: 100, 2: 100, 3: 100, 4: 500}
                shelf.shelf_by_rare_nums_once(rare_num_price_dic)
        except:
            time.sleep(60)
            traceback.print_exc()


def breed():
    logger.info('启动内部繁育定时任务')
    breed = Breed(user)
    breed.breed_until_max_trade_times(4, 500, 4, False, None)
    logger.info('内部繁育定时任务执行完成')


def breed_multiple_users():
    for user in users:
        if user.name == ACCOUNT_1:
            continue
        logger.suc('当前账号：{0}'.format(user.name))
        breed = Breed(user)
        if user.name == ACCOUNT_2:
            breed.breed_until_max_trade_times(3, 100, 3, False, None)
        else:
            breed.breed_until_max_trade_times(4, 500, 5, False, None)


def buy():
    logger.info('启动购买定时任务')
    buy = Buy(user)
    # 购买天使狗 价格不高于200
    # buy.buy_angel_pets_until_max_trade_times(200)
    # 购买卓越狗 价格不高于100， 代数不高于2代，数量不超过100条
    buy.buy_pets_until_max_trade_times(100, 2, 2, 100)
    # 购买史诗狗 价格不高于2500， 代数不高于2代，数量不超过5条
    buy.buy_pets_until_max_trade_times(2500, 3, 2, 5)
    logger.info('购买定时任务执行完成')

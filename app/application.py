#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
import json
import time
import math
import threading
import pymongo
from urllib.parse import unquote
import app.db.mongo as mongo
import app.logger.logger as logger
from bson import ObjectId
from app.config.user import get_user_from_db
from app.utils.time import greater_than_half_a_day
from flask import render_template
from flask import Flask, request
from app.order import Order
from app.operations.counter import Counter
from app.operations.lai_ci_gou import LaiCiGou
from app.pet_collector import Collector

app = Flask(__name__)

from enum import Enum


class Operation(Enum):
    TREASURE_UP = '珍藏'
    CANCEL_TREASURE_UP = '取消珍藏'
    COLLECT = '收藏'
    CANCEL_COLLECT = '取消收藏'


class LaiCiGouWebManager():
    def __init__(self):
        pass

    def show_user_profile(username):
        return 'User %s' % username

    def render_html_template(self, name, data=None):
        return render_template(name, data=data)

    def _save_page_cache_data(self, page_name: str, data: dict) -> dict:
        doc = {'name': page_name, 'data': data, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        mongo.page_caches.delete_many({'name': page_name})
        mongo.page_caches.insert(doc)
        save_data = mongo.page_caches.find_one({'name': page_name})

        return save_data

    def _create_save_home_data(self):
        total_amount = mongo.pets.find({}).count()
        children_amount = mongo.pets.find({'fatherId': {'$ne': None}}).count()
        recognized_babies_amount = mongo.recognized_babies.find({}).count()
        converted_id_amount = mongo.converted_ids.find({}).count()
        twins_amount = mongo.twins.find({"petAmount": {'$gt': 1}}).count()

        data = {
            'total_amount': total_amount,
            'children_amount': children_amount,
            'recognized_babies_amount': recognized_babies_amount,
            'converted_id_amount': converted_id_amount,
            'twins_amount': twins_amount

        }
        saved_data = self._save_page_cache_data('home page', data)
        logger.suc('首页数据统计完成')
        return saved_data

    def home_data(self):
        page_name = 'home page'
        data = mongo.page_caches.find_one({'name': page_name})
        if not data:
            logger.warn('无首页数据，重新统计数据')
            data = self._create_save_home_data()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if greater_than_half_a_day(now, data['timestamp']):
            logger.warn('首页数据已经超过半天，开启线程重新统计最新数据')
            t = threading.Thread(target=self._create_save_home_data, name='LoopThread')
            t.start()

        return data['data']

    def _create_save_attributes_summary_data(self):
        rare_degrees = ['普通', '稀有', '卓越', '史诗', '神话', '传说']
        rare_amounts = {0: '无', 1: '1 稀', 2: '2 稀', 3: '3 稀', 4: '4 稀', 5: '5 稀', 6: '6 稀', 7: '7 稀', 8: '8 稀'}
        attributes_names = ['体型', '花纹', '眼睛', '眼睛色', '嘴巴', '肚皮色', '身体色', '花纹色']

        data = {'results': []}

        # 按稀有度统计狗狗数据
        pets_data = {'text': '狗狗（稀有度）', 'data': []}
        for rare_degree in rare_degrees:
            count = mongo.pets.find({'rareDegree': rare_degree}).count()
            pets_data['data'].append({'name': rare_degree, 'value': count})

        data['results'].append(pets_data)

        # 按稀有属性数量统计勾过数据
        rare_amount_data = {'text': '狗狗（稀有数）', 'data': []}
        for rare_amount in rare_amounts:
            count = mongo.pets.find({'rareAmount': rare_amount}).count()
            rare_amount_data['data'].append({'name': rare_amounts[rare_amount], 'value': count})

        data['results'].append(rare_amount_data)

        # 统计所有属性数据
        for attribute_name in attributes_names:
            attributes_data = {'text': attribute_name, 'data': []}
            for attribute_data in mongo.attributes.find({'name': attribute_name}):
                name = attribute_data['value'] if not attribute_data['rareDegree'] else '{0}({1})'.format(
                    attribute_data['value'],
                    attribute_data['rareDegree'])

                attributes_data['data'].append({'name': name, 'value': attribute_data['amount']})
            data['results'].append(attributes_data)

        saved_data = self._save_page_cache_data('attributes info page', data)
        logger.suc('属性信息页数据统计完成')
        return saved_data

    def get_pets_attributes_summary_data(self):
        page_name = 'attributes info page'
        data = mongo.page_caches.find_one({'name': page_name})
        if not data:
            logger.warn('无属性信息页数据，重新统计数据')
            data = self._create_save_attributes_summary_data()
        else:
            data.pop('_id')

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if greater_than_half_a_day(now, data['timestamp']):
            logger.warn('属性信息页数据已经超过半天，开启线程重新统计最新数据')
            t = threading.Thread(target=self._create_save_attributes_summary_data,
                                 name='_create_save_attributes_summary_data')
            t.start()

        return json.dumps(data['data'])

    def _days_between_dates(self, date1, date2):
        date_time1 = datetime.strptime(date1, '%Y-%m-%d')
        date_time2 = datetime.strptime(date2, '%Y-%m-%d')
        return (date_time1 - date_time2).days

    def _create_save_asset_data(self, user):
        status = {1: "已卖出", 2: "已买入", 3: "繁育收入", 4: "繁育支出"}
        txnStatus = {0: "上链中", 1: "上链中", 2: "成功", 3: "失败", 4: "失败"}

        # 检查交易信息数据是完整的
        order = Order(user, clear=False)
        order.must_have_all_orders()

        oldest_date = order.get_oldest_order_trans_date()
        latest_date = order.get_latest_order_trans_date()
        days = self._days_between_dates(latest_date, oldest_date)

        current_amount = 0
        dates, incomes, expends, totals = [], [], [], []
        from_date = datetime.strptime(oldest_date, '%Y-%m-%d')
        for day in range(days + 1):
            date = (from_date + timedelta(days=day)).strftime('%Y-%m-%d')
            income, expend, amount = 0, 0, 0
            for order in mongo.orders.find({'transDate': date, 'txnStatus': 2}):
                amount = float(order['amount'])
                if order['type'] == 1 or order['type'] == 3:
                    income = round(income + amount, 2)
                if order['type'] == 2 or order['type'] == 4:
                    expend = round(expend + amount, 2)
                if date == latest_date:
                    current_amount = order['currentAmount']
            dates.append(date)
            incomes.append(income)
            expends.append(expend)

        # 根据最新的微积分总数和每天交易记录反推过去每天的微积分总数（有误差，因为交易记录不包含每天签到和初始赠送记录）
        total_of_one_day = current_amount
        totals.append(round(total_of_one_day))
        for i in range(len(dates) - 1):
            j = len(dates) - 1 - i
            margin = incomes[j] - expends[j]
            total_of_one_day = total_of_one_day - margin
            totals.append(round(total_of_one_day))

        data = {'useId': user.id,
                'dates': dates,
                'incomes': incomes,
                'expends': expends,
                'totals': totals[::-1],  # totals[::-1] 列表反转
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

        mongo.user_asset_caches.delete_many({'useId': user.id})
        mongo.user_asset_caches.insert(data)
        save_data = mongo.user_asset_caches.find_one({'useId': user.id})
        logger.suc(f'账户 {user.name} 交易数据统计完成')

        return save_data

    def get_asset_data(self):
        user_name = request.form['userName']
        user = get_user_from_db(user_name)
        if not user:
            return json.dumps({'error': '没有配置该账号'})

        data = mongo.user_asset_caches.find_one({'useId': user.id})
        if not data:
            logger.warn(f'无账户 {user.name} 的交易统计数据，需重新统计')
            data = self._create_save_asset_data(user)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if greater_than_half_a_day(now, data['timestamp']):
            logger.warn(f'账户 {user.name} 的交易统计数据已过期半天，重新统计')
            t = threading.Thread(target=self._create_save_asset_data, args=(user,),
                                 name='_create_save_breed_info_data')
            t.start()

        data.pop('_id')
        return json.dumps(data)

    def _create_save_breed_info_data(self):
        data = {}
        for childRareAmount in range(9):
            father_mother_list, children = [], []
            total = 0
            for fatherRareAmount in range(9):
                for motherRareAmount in range(9):
                    key = str(fatherRareAmount) + '-' + str(motherRareAmount)
                    info = mongo.breed_info.find_one(
                        {'childRareAmount': childRareAmount, 'fatherRareAmount': fatherRareAmount,
                         'motherRareAmount': motherRareAmount})
                    if info:
                        child_amount = info['childAmount']

                    else:
                        child_amount = 0

                    total = total + child_amount
                    father_mother_list.append(key)
                    children.append(child_amount)

            data[str(childRareAmount)] = {'fatherMother': father_mother_list, 'childrenAmount': children,
                                          'childrenTotal': total}

        saved_data = self._save_page_cache_data('breed info page', data)
        logger.suc('繁殖信息页数据统计完成')
        return saved_data

    def get_breed_info(self):
        page_name = 'breed info page'
        data = mongo.page_caches.find_one({'name': page_name})
        if not data:
            logger.warn('无繁殖信息页数据，重新统计数据')
            data = self._create_save_breed_info_data()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if greater_than_half_a_day(now, data['timestamp']):
            logger.warn('繁殖信息页数据已经超过半天，开启线程重新统计最新数据')
            t = threading.Thread(target=self._create_save_breed_info_data,
                                 name='_create_save_breed_info_data')
            t.start()

        return json.dumps(data['data'])

    # 将原始属性数组数据结构转换为有序的对象
    def convert_attributes(self, attributes):
        order_attributes = ['体型', '花纹', '眼睛', '眼睛色', '嘴巴', '肚皮色', '身体色', '花纹色']
        results = []
        for order_attribute_name in order_attributes:
            for attribute in attributes:
                if order_attribute_name == attribute['name']:
                    rare_degree = attribute['rareDegree'] if attribute['rareDegree'] else ''
                    results.append({'name': order_attribute_name, 'value': attribute['value'], 'rare': rare_degree})

                    break

        return results

    def get_baby_attributes(self):
        from app.config.user import user
        counter = Counter(user)
        pet_id = request.form['petId']
        baby_details = counter.get_baby_details(pet_id)
        rare_amount = str(baby_details['attributes']).count('稀有')

        father, mother = counter.get_baby_parents(pet_id)
        father = counter.get_pet_info_on_market(father['petId'])
        mother = counter.get_pet_info_on_market(mother['petId'])

        father.pop('father')
        father.pop('mother')
        mother.pop('father')
        mother.pop('mother')

        father_rare_amount = counter.get_rare_amount(father['attributes'])
        mother_rare_amount = counter.get_rare_amount(mother['attributes'])

        father['attributes'] = self.convert_attributes(father['attributes'])
        mother['attributes'] = self.convert_attributes(mother['attributes'])

        father['rareAmount'] = father_rare_amount
        mother['rareAmount'] = mother_rare_amount

        cursor = mongo.breed_info.find({'fatherRareAmount': father_rare_amount, 'motherRareAmount': mother_rare_amount})

        less_or_equal_amount, total = 0, 0
        for info in cursor:
            total = total + info['childAmount']
            if info['childRareAmount'] <= rare_amount:
                less_or_equal_amount = less_or_equal_amount + info['childAmount']

        lucky_percentage = "%.2f%%" % (less_or_equal_amount / total * 100)

        baby_details['name'] = baby_details['petName']
        baby_details['rareAmount'] = rare_amount
        baby_details['rareDegree'] = counter.rare_amount_dic[rare_amount]
        baby_details['coolingInterval'] = '0天'
        baby_details['father'] = father
        baby_details['mother'] = mother
        baby_details['luckyPercentage'] = lucky_percentage

        baby_details.pop('petName')

        mongo.recognized_babies.insert({'petId': pet_id})
        return json.dumps(baby_details)

    def convert_id(self):
        shortId = request.form['shortId']
        pet = mongo.pets.find_one({'id': shortId})
        if pet:
            petId = pet['petId']
            mongo.converted_ids.insert({'shortId': shortId})
        else:
            petId = None
        return json.dumps({'petId': petId})

    # 获取孪生狗总页数，每页大小为10
    def get_twins_pages(self):
        page_size = 10
        count = mongo.twins.find({"petAmount": {'$gt': 1}}, no_cursor_timeout=True).sort(
            [("rareAmount", pymongo.DESCENDING)]).count()

        return json.dumps({'pages': math.ceil(count / page_size)})

    # 分页获取孪生狗数据，每页10条
    def get_twins_of_page(self):
        page_size = 10
        page_number = int(request.form['pageNo'])

        cursor = mongo.twins.find({"petAmount": {'$gt': 1}}, no_cursor_timeout=True).sort(
            [("rareAmount", pymongo.DESCENDING)]).skip(page_size * (page_number - 1)).limit(page_size)

        documents = []
        for doc in cursor:
            doc['id'] = str(doc['_id'])
            doc.pop('_id')
            doc['rareDegree'] = LaiCiGou.RARE_AMOUNT_DIC[doc['rareAmount']]
            documents.append(doc)

        return json.dumps({'documents': documents})

    # 获取孪生狗详细数据
    def get_twins_details(self):
        id = request.form['id']
        twins_doc = mongo.twins.find_one({'_id': ObjectId(id)})

        pet_ids = twins_doc['petIds']

        results = {}
        pets = []
        from app.config.user import user
        lai_ci_gou = LaiCiGou(user)
        for petId in pet_ids:
            pet = {}
            pet_info = lai_ci_gou.get_pet_info_on_market(petId)
            pet['id'] = pet_info['id']
            pet['petId'] = pet_info['petId']
            pet['desc'] = pet_info['desc']
            pet['petUrl'] = pet_info['petUrl']
            pet['rareDegree'] = pet_info['rareDegree']
            pet['generation'] = pet_info['generation']
            pet['coolingInterval'] = pet_info['coolingInterval']
            pet['bgColor'] = pet_info['bgColor']

            pets.append(pet)

        results['petAmount'] = twins_doc['petAmount']
        results['rareDegree'] = LaiCiGou.RARE_AMOUNT_DIC[twins_doc['rareAmount']]
        results['rareAmount'] = twins_doc['rareAmount']
        results['attributes'] = self.convert_attributes(twins_doc['attributes'])
        results['petUrl'] = twins_doc['petUrl']
        results['pets'] = pets

        return json.dumps(results)

    # 查找指定的狗狗的孪生狗
    def query_twins(self):
        from app.config.user import user
        petId = request.form['petId']
        des_pet = mongo.pets.find_one({'petId': petId})
        if not des_pet:
            collector = Collector(user)
            collector.query_save_pet_and_ancestors(petId)
            des_pet = mongo.pets.find_one({'petId': petId})

        amount = mongo.pets.find({'attributes': des_pet['attributes']}).count()
        if amount < 2:
            return json.dumps({'info': '你的狗狗独一无二，没有孪生兄弟'})
        else:
            cursor = mongo.pets.find({'attributes': des_pet['attributes']})
            pet_ids = []
            for doc in cursor:
                pet_ids.append(doc['petId'])

        results = {}
        pets = []

        lai_ci_gou = LaiCiGou(user)
        for petId in pet_ids:
            pet = {}
            pet_info = lai_ci_gou.get_pet_info_on_market(petId)
            pet['id'] = pet_info['id']
            pet['petId'] = pet_info['petId']
            pet['desc'] = pet_info['desc']
            pet['petUrl'] = pet_info['petUrl']
            pet['rareDegree'] = pet_info['rareDegree']
            pet['generation'] = pet_info['generation']
            pet['coolingInterval'] = pet_info['coolingInterval']
            pet['bgColor'] = pet_info['bgColor']

            pets.append(pet)

        results['petAmount'] = len(pets)
        results['rareDegree'] = LaiCiGou.RARE_AMOUNT_DIC[des_pet['rareAmount']]
        results['rareAmount'] = des_pet['rareAmount']
        results['attributes'] = self.convert_attributes(des_pet['attributes'])
        results['petUrl'] = des_pet['petUrl']
        results['pets'] = pets

        return json.dumps(results)

    def query_attributes(self):
        names = ['体型', '花纹', '眼睛', '眼睛色', '嘴巴', '肚皮色', '身体色', '花纹色']
        results = []
        for name in names:
            cursor = mongo.attributes.find({'name': name})
            values = ['全部']
            for doc in cursor:
                if doc['rareDegree']:
                    value = '{0} {1}'.format(doc['value'], doc['rareDegree'])
                else:
                    value = doc['value']
                values.append(value)
            results.append({'value': '全部', 'name': name, 'values': values})
        return json.dumps(results)

    # 获取按属性查询的狗狗总页数
    # def get_pet_pages(self):
    #     page_size = 10
    #
    #     market_status = request.form['marketStatus']
    #     attributes = request.form.to_dict()
    #
    #     ids = list()
    #     for i in range(8):
    #         name = attributes['attributes[{0}][name]'.format(i)]
    #         value = attributes['attributes[{0}][value]'.format(i)].replace('稀有', '').replace(' ', '')
    #         if value != '全部':
    #             doc = mongo.attributes.find_one({'name': name, 'value': value})
    #             ids.append(doc['intId'])
    #
    #     query = {'aIds':{'$all':ids}}
    #
    #     # 当没有指定查询属性（查询属性为空）时，直接从官网查询（速度更快），设置最大页数为200
    #     if len(ids) == 0:
    #         pages = 200
    #     else:
    #         if market_status == '在售':
    #             from app.config.user import user
    #             lai_ci_gou = LaiCiGou(user)
    #
    #             count = 0
    #             cursor = mongo.pets.find(query)
    #             # TODO： 一直查找在售的狗狗，统计其数量，此处需要更好的解决方案
    #             for doc in cursor:
    #                 pet_info = lai_ci_gou.get_pet_info_on_market(doc['petId'])
    #                 if pet_info['amount'] != '0.00':
    #                     count = count + 1
    #         else:
    #             count = mongo.pets.find(query).count()
    #
    #         pages = math.ceil(count / page_size)
    #
    #     return json.dumps({'pages': pages})

    def get_pet_pages(self):
        page_size = 10
        query = []

        user_name = unquote(request.form['userName'])
        pet_type = request.form['petType']
        attributes = request.form.to_dict()

        for i in range(8):
            name = attributes['attributes[{0}][name]'.format(i)]
            value = attributes['attributes[{0}][value]'.format(i)].replace('稀有', '').replace(' ', '')
            if value != '全部':
                query.append({'attributes': {'$elemMatch': {'name': name, 'value': value}}})

        #  用户名为'query'表示不是查具体的用户，一般游客查询
        if user_name == 'query' or pet_type == '全部' or pet_type == '在售':
            query = {} if len(query) == 0 else {'$and': query}
        else:
            query = {'user': user_name} if len(query) == 0 else {'user': user_name, '$and': query}

        count = 0
        if pet_type == '全部':
            # 当没有指定查询属性（查询属性为空）时，直接从官网查询（速度更快），设置最大页数为200
            count = 200 * page_size if len(query) == 0 else mongo.pets.find(query).count()
        elif pet_type == '在售':
            from app.config.user import user
            lai_ci_gou = LaiCiGou(user)

            count = 0
            cursor = mongo.pets.find(query)
            # TODO： 一直查找在售的狗狗，统计其数量，此处需要更好的解决方案
            for doc in cursor:
                pet_info = lai_ci_gou.get_pet_info_on_market(doc['petId'])
                if pet_info['shelfStatus'] == 1:
                    count = count + 1
        elif pet_type == '收藏待购买':
            page_size = 100
            count = mongo.public_collection.find(query).count()
        elif pet_type == '我的狗狗':
            page_size = 100
            count = mongo.my_pets.find(query).count()
        elif pet_type == '我的珍藏':
            page_size = 100
            count = mongo.private_collection.find(query).count()

        pages = math.ceil(count / page_size)

        return json.dumps({'pages': pages})

    # 分页查询获取狗狗
    # def query_pets_of_page(self):
    #     page_number = int(request.form['pageNo'])
    #     market_status = request.form['marketStatus']
    #     attributes = request.form.to_dict()
    #
    #     ids = list()
    #     for i in range(8):
    #         name = attributes['attributes[{0}][name]'.format(i)]
    #         value = attributes['attributes[{0}][value]'.format(i)].replace('稀有', '').replace(' ', '')
    #         if value != '全部':
    #             doc = mongo.attributes.find_one({'name': name, 'value': value})
    #             ids.append(doc['intId'])
    #
    #     query = {'aIds': {'$all': ids}}
    #
    #     page_size, pets = 10, []
    #     from app.config.user import user
    #     lai_ci_gou = LaiCiGou(user)
    #
    #     # 当没有指定查询属性（查询属性为空）时，直接从官网查询（速度更快）
    #     if len(ids) == 0:
    #         condition = {
    #             "pageNo": page_number,
    #             "pageSize": 10,
    #             "lastAmount": "",
    #             "lastRareDegree": "",
    #             "filterCondition": "{}",
    #             "querySortType": "CREATETIME_ASC",
    #             "petIds": [],
    #             "requestId": int(time.time() * 1000),
    #             "appId": 1,
    #             "tpl": "",
    #             "type": 1
    #         }
    #         pets_on_sale = lai_ci_gou.get_pets_on_sale(condition)
    #         for pet in pets_on_sale:
    #             pet.pop('birthType')
    #             pet.pop('mutation')
    #             pet.pop('petType')
    #             pet.pop('validCode')
    #             pet.pop('incubateTime')
    #             pet.pop('isCooling')
    #             pet['rareDegree'] = lai_ci_gou.rare_degree_dic[pet['rareDegree']]
    #             pet['amount'] = '{0} {1}'.format(pet['amount'], '微')
    #             pets.append(pet)
    #     else:
    #         if market_status == '在售':
    #             # TODO： 效率问题：此处需要更好的解决方案
    #             cursor = mongo.pets.find(query)
    #             skip = page_size * (page_number - 1)
    #             for doc in cursor:
    #                 doc.pop('_id')
    #                 doc.pop('attributes')
    #                 doc.pop('fatherId')
    #                 doc.pop('motherId')
    #                 doc.pop('rareAmount')
    #                 pet_info = lai_ci_gou.get_pet_info_on_market(doc['petId'])
    #                 if pet_info['amount'] == '0.00':
    #                     continue
    #
    #                 skip = skip - 1
    #                 if skip <= 0:
    #                     doc['amount'] = '{0} {1}'.format(pet_info['amount'], '微')
    #                     doc['coolingInterval'] = pet_info['coolingInterval']
    #                     doc['desc'] = pet_info['desc']
    #                     pets.append(doc)
    #                     if len(pets) == page_size:
    #                         break
    #         else:
    #             cursor = mongo.pets.find(query).skip(page_size * (page_number - 1)).limit(page_size)
    #             for doc in cursor:
    #                 doc.pop('_id')
    #                 doc.pop('attributes')
    #                 doc.pop('fatherId')
    #                 doc.pop('motherId')
    #                 doc.pop('rareAmount')
    #                 pet_info = lai_ci_gou.get_pet_info_on_market(doc['petId'])
    #                 if pet_info['amount'] == '0.00':
    #                     doc['amount'] = '未上市交易'
    #                 else:
    #                     doc['amount'] = '{0} {1}'.format(pet_info['amount'], '微')
    #                 doc['coolingInterval'] = pet_info['coolingInterval']
    #                 doc['desc'] = pet_info['desc']
    #                 pets.append(doc)
    #
    #     return json.dumps({'pets': pets})

    # 分页查询获取狗狗
    def query_pets_of_page(self):
        query = []

        user_name = unquote(request.form['userName'])
        page_number = int(request.form['pageNo'])
        pet_type = request.form['petType']
        attributes = request.form.to_dict()

        for i in range(8):
            name = attributes['attributes[{0}][name]'.format(i)]
            value = attributes['attributes[{0}][value]'.format(i)].replace('稀有', '').replace(' ', '')
            if value != '全部':
                query.append({'attributes': {'$elemMatch': {'name': name, 'value': value}}})

        #  用户名为'query'表示不是查具体的用户，一般游客查询
        if user_name == 'query' or pet_type == '全部' or pet_type == '在售':
            query = {} if len(query) == 0 else {'$and': query}
        else:
            query = {'user': user_name} if len(query) == 0 else {'user': user_name, '$and': query}

        if pet_type == '在售' or pet_type == '全部':
            collection = mongo.pets
        elif pet_type == '收藏待购买':
            collection = mongo.public_collection
        elif pet_type == '我的狗狗':
            collection = mongo.my_pets
        elif pet_type == '我的珍藏':
            collection = mongo.private_collection
        else:
            collection = mongo.pets

        page_size, pets = 10, []
        from app.config.user import user
        lai_ci_gou = LaiCiGou(user)

        if pet_type == '全部':
            if len(query) == 0:  # 当没有指定查询属性（查询属性为空）时，直接从官网查询（速度更快）
                condition = {
                    "pageNo": page_number,
                    "pageSize": 10,
                    "lastAmount": "",
                    "lastRareDegree": "",
                    "filterCondition": "{}",
                    "querySortType": "CREATETIME_ASC",
                    "petIds": [],
                    "requestId": int(time.time() * 1000),
                    "appId": 1,
                    "tpl": "",
                    "type": 1
                }
                pets_on_sale = lai_ci_gou.get_pets_on_sale(condition)
                for pet in pets_on_sale:
                    pet.pop('birthType')
                    pet.pop('mutation')
                    pet.pop('petType')
                    pet.pop('validCode')
                    pet.pop('incubateTime')
                    pet['rareDegree'] = lai_ci_gou.rare_degree_dic[pet['rareDegree']]

                    pet['amount'] = '{0} {1}'.format(pet['amount'], '微')

                    is_collected = mongo.public_collection.find_one({'user': user_name, 'petId': pet['petId']})
                    if is_collected:
                        pet['operation'] = Operation.CANCEL_COLLECT.value
                    else:
                        pet['operation'] = Operation.COLLECT.value
                    pets.append(pet)
            else:
                cursor = collection.find(query).skip(page_size * (page_number - 1)).limit(page_size)
                for doc in cursor:
                    doc.pop('_id')
                    doc.pop('attributes')
                    doc.pop('fatherId')
                    doc.pop('motherId')
                    doc.pop('rareAmount')
                    pet_info = lai_ci_gou.get_pet_info_on_market(doc['petId'])

                    doc['rareDegree'] = '{0}{1}'.format(doc['rareDegree'],
                                                        lai_ci_gou.get_rare_amount(pet_info['attributes']))

                    if pet_info['shelfStatus'] == 1:
                        doc['amount'] = '{0} {1}'.format(pet_info['amount'], '微')
                    else:
                        doc['amount'] = '未上市交易'
                    doc['coolingInterval'] = pet_info['coolingInterval']
                    doc['desc'] = pet_info['desc']

                    is_collected = mongo.public_collection.find_one({'user': user_name, 'petId': doc['petId']})
                    if is_collected:
                        doc['operation'] = Operation.CANCEL_COLLECT.value
                    else:
                        doc['operation'] = Operation.COLLECT.value
                    pets.append(doc)
        if pet_type == '在售':
            # TODO： 效率问题：此处需要更好的解决方案
            cursor = collection.find(query)
            skip = page_size * (page_number - 1)
            for doc in cursor:
                doc.pop('_id')
                doc.pop('attributes')
                doc.pop('fatherId')
                doc.pop('motherId')
                doc.pop('rareAmount')
                pet_info = lai_ci_gou.get_pet_info_on_market(doc['petId'])
                if pet_info['shelfStatus'] != 1:
                    continue

                skip = skip - 1
                if skip <= 0:
                    doc['amount'] = '{0} {1}'.format(pet_info['amount'], '微')
                    doc['coolingInterval'] = pet_info['coolingInterval']
                    doc['desc'] = pet_info['desc']
                    doc['rareDegree'] = '{0}{1}'.format(doc['rareDegree'],
                                                        lai_ci_gou.get_rare_amount(pet_info['attributes']))

                    is_collected = mongo.public_collection.find_one({'user': user_name, 'petId': doc['petId']})
                    if is_collected:
                        doc['operation'] = Operation.CANCEL_COLLECT.value
                    else:
                        doc['operation'] = Operation.COLLECT.value

                    pets.append(doc)
                    if len(pets) == page_size:
                        break
        elif pet_type == '收藏待购买' or pet_type == '我的狗狗' or pet_type == '我的珍藏':
            page_size = 100
            cursor = collection.find(query).skip(page_size * (page_number - 1)).limit(page_size)
            for doc in cursor:
                doc.pop('_id')
                doc.pop('attributes')
                doc.pop('fatherId')
                doc.pop('motherId')
                doc.pop('rareAmount')

                pet_info = lai_ci_gou.get_pet_info_on_market(doc['petId'])
                doc['isCooling'] = pet_info['isCooling']

                doc['rareDegree'] = '{0}{1}'.format(doc['rareDegree'],
                                                    lai_ci_gou.get_rare_amount(pet_info['attributes']))

                status = lai_ci_gou.shelf_status[pet_info['shelfStatus']]
                if pet_info['shelfStatus'] != 0:
                    doc['amount'] = '{0} {1}{2}'.format(status, pet_info['amount'], '微')
                else:
                    doc['amount'] = status

                doc['coolingInterval'] = pet_info['coolingInterval']
                doc['desc'] = pet_info['desc']

                if pet_type == '收藏待购买':
                    is_collected = mongo.public_collection.find_one({'user': user_name, 'petId': doc['petId']})
                    if is_collected:
                        doc['operation'] = Operation.CANCEL_COLLECT.value
                    else:
                        doc['operation'] = Operation.COLLECT.value
                else:
                    is_collected = mongo.private_collection.find_one({'user': user_name, 'petId': doc['petId']})
                    if is_collected:
                        doc['operation'] = Operation.CANCEL_TREASURE_UP.value
                    else:
                        doc['operation'] = Operation.TREASURE_UP.value

                pets.append(doc)

        return json.dumps({'pets': pets})

    def collect(self):
        user_name = unquote(request.form['userName'])
        user = get_user_from_db(user_name)
        if not user:
            return json.dumps({'status': 1, 'info': '没有配置该账号'})

        pet_type = request.form['petType']
        operation = request.form['operation']
        pet_id = int(request.form['petId'])

        if pet_type == '在售' or pet_type == '全部' or pet_type == '收藏待购买':
            src_collection = mongo.pets
            des_collection = mongo.public_collection
        elif pet_type == '我的狗狗' or pet_type == '我的珍藏':
            src_collection = mongo.my_pets
            des_collection = mongo.private_collection
        else:
            src_collection = mongo.pets
            des_collection = mongo.public_collection

        feature_operation = ''
        if operation == Operation.COLLECT.value:
            pet = src_collection.find_one({'petId': str(pet_id)})
            pet.pop('_id')

            if not des_collection.find_one({'user': user_name, 'petId': str(pet_id)}):
                pet['user'] = user_name
                des_collection.insert(pet)

            feature_operation = Operation.CANCEL_COLLECT.value
        elif operation == Operation.TREASURE_UP.value:
            pet = src_collection.find_one({'user': user_name, 'petId': str(pet_id)})
            pet.pop('_id')

            if not des_collection.find_one({'user': user_name, 'petId': str(pet_id)}):
                pet['user'] = user_name
                des_collection.insert(pet)

            feature_operation = Operation.CANCEL_TREASURE_UP.value
        elif operation == Operation.CANCEL_COLLECT.value:
            des_collection.delete_one({'petId': str(pet_id)})
            feature_operation = Operation.COLLECT.value
        elif operation == Operation.CANCEL_TREASURE_UP.value:
            des_collection.delete_one({'petId': str(pet_id)})
            feature_operation = Operation.TREASURE_UP.value

        return json.dumps({'status': 0, 'featureOperation': feature_operation})

    def update_my_pets(self):
        user_name = unquote(request.form['userName'])
        user = get_user_from_db(user_name)
        if not user:
            return json.dumps({'info': '没有配置该账号'})

        counter = Counter(user)

        counter.update_my_pets()

        return json.dumps({'info': '更新完成'})


server = LaiCiGouWebManager()


@app.route('/')
def home_page():
    data = server.home_data()
    return server.render_html_template('home.html', data)


@app.route('/user/<username>')
def show_user_profile():
    return server.show_user_profile()


@app.route('/pie/')
def pie_page():
    return server.render_html_template('pie.html')


@app.route("/pie/getData", methods=['POST'])
def get_pets_attributes_summary_data():
    return server.get_pets_attributes_summary_data()


@app.route('/asset/')
def asset_page():
    return server.render_html_template('asset.html')


@app.route("/asset/getAssetData", methods=['POST'])
def get_asset_data():
    return server.get_asset_data()


@app.route('/breed/')
def breed_info_page():
    return server.render_html_template('breedInfo.html')


@app.route("/breed/getBreedInfo", methods=['POST'])
def get_breed_info():
    return server.get_breed_info()


@app.route('/recognise/')
def recognise_page():
    return server.render_html_template('recogniseBaby.html')


@app.route("/recognise/getBabyAttributes", methods=['POST'])
def get_baby_attributes():
    return server.get_baby_attributes()


@app.route('/idConvert/')
def id_convert_page():
    return server.render_html_template('idConvert.html')


@app.route("/idConvert/convertId", methods=['POST'])
def convert_id():
    return server.convert_id()


@app.route('/twins/')
def twins_page():
    return server.render_html_template('twins.html')


@app.route('/twins/getPages', methods=['POST'])
def get_twins_pages():
    return server.get_twins_pages()


@app.route("/twins/getTwins", methods=['POST'])
def get_twins():
    return server.get_twins_of_page()


@app.route('/twinsDetails/<id>')
def twins_details_page(id):
    return server.render_html_template('twinsDetails.html')


@app.route("/twinsDetails/getDetails", methods=['POST'])
def get_twins_details():
    return server.get_twins_details()


@app.route('/queryTwins/')
def query_twins_page():
    return server.render_html_template('queryTwins.html')


@app.route("/queryTwins/queryTwins", methods=['POST'])
def query_twins():
    return server.query_twins()


@app.route('/pretty/<username>')
def pretty_page(username):
    return server.render_html_template('pretty.html', username)


@app.route("/pretty/queryAttributes", methods=['POST'])
def query_attributes():
    return server.query_attributes()


@app.route("/pretty/getPages", methods=['POST'])
def get_pet_pages():
    return server.get_pet_pages()


@app.route("/pretty/queryPetsOfPage", methods=['POST'])
def query_pets_of_page():
    return server.query_pets_of_page()


@app.route("/pretty/collect", methods=['POST'])
def collect():
    return server.collect()


@app.route("/pretty/updateMyPets", methods=['POST'])
def update_my_pets():
    return server.update_my_pets()


if __name__ == '__main__':
    pass

#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import json
import time
import app.logger.logger as logger
from app.config.user import user
from app.operations.lai_ci_gou import LaiCiGou
from app.attr_parser import AttributeSvgParser
from app.db.mongo import my_pets


class Counter(LaiCiGou):
    def __init__(self, user):
        super(Counter, self).__init__(user)

        self.types = []

        self.attribute_svg_parser = AttributeSvgParser(user, clear=False)

    # 获取狗狗历史记录数据
    def _get_pet_history_data(self, pet_id, page_no, page_size):
        url = 'https://pet-chain.baidu.com/data/pet/history'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/trace'
        data = {
            "pageNo": page_no,
            "pageSize": page_size,
            "petId": pet_id,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 获取狗狗历史记录数量
    def get_pet_histories_count(self, pet_id):
        return self._get_pet_history_data(pet_id, 1, 10)['totalCount']

    # 获取狗狗历史记录
    def get_pet_histories(self, pet_id, page_no, page_size):
        return self._get_pet_history_data(pet_id, page_no, page_size)['dataList']

    # 按稀有等级统计狗狗数量
    def count_pets_amount_by_rare_degree(self):
        rare_degree_data, rare_degree_amount_data = {}, {}
        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                rare_degree = self.rare_degree_dic[pet['rareDegree']]
                if rare_degree in rare_degree_data:
                    rare_degree_data[rare_degree] = rare_degree_data[rare_degree] + 1
                else:
                    rare_degree_data[rare_degree] = 1

                info = self.get_pet_info_on_market(pet['petId'])
                rare_amount = self.get_rare_amount(info['attributes'])
                key = str(rare_amount) + '稀'
                if key in rare_degree_amount_data:
                    rare_degree_amount_data[key] = rare_degree_amount_data[key] + 1
                else:
                    rare_degree_amount_data[key] = 1

            sorted_rare_degree_amount_data = self.attribute_svg_parser.svg.ordered(rare_degree_amount_data)
            logger.info('第{0}页时：{1} {2}'.format(page_no, rare_degree_data, sorted_rare_degree_amount_data))
            time.sleep(5)

    def get_attribute_value(self, attributes, name):
        for attribute in attributes:
            if attribute['name'] == name:
                return attribute['value']

    # 对比狗狗属性信息，归类保存到self.types数据集
    def check_attributes(self, info):
        for exist_type in self.types:
            flag = True
            for attribute_name in self.attributes_names:
                exist_value = self.get_attribute_value(exist_type['attributes'], attribute_name)
                value = self.get_attribute_value(info['attributes'], attribute_name)
                if exist_value != value:
                    flag = False
                    break

            if flag:
                exist_type['petIds'].append(info['petId'])
                logger.info('有相同类型的狗狗')
                return

        logger.info('没有相同类型的狗狗')
        t = {
            'petIds': [info['petId']],
            'attributes': info['attributes']
        }
        self.types.append(t)

    # 按属性统计狗狗，所有属性完全相同的才算是同一类狗狗
    # 此方法主要是为了统计出双胞胎、三胞胎...狗狗
    def sort_pets_by_attributes(self):
        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            logger.info('第{0}页：'.format(page_no))
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                info = self.get_pet_info_on_market(pet['petId'])
                self.check_attributes(info)
            time.sleep(5)
        logger.info(self.types)

    # 统计指定稀有属性数量的狗狗
    def get_pets_of_rare_degree(self, rare_num):
        pets_list = []
        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                pet_info = self.get_pet_info_on_market(pet['petId'])
                pet_rare_num = self.get_rare_amount(pet_info['attributes'])

                if pet_rare_num == rare_num:
                    pets_list.append({'petId': pet['petId'], 'isCooling': pet['isCooling']})

            logger.info('第{0}页时：{1}'.format(page_no, pets_list))
            time.sleep(5)

    # 获取狗宝宝基本信息数据
    def _query_baby_data(self, pet_id):
        page_size = 10

        info = self.get_baby_pet_info(pet_id)
        father_id = info['fatherInfo']['petId']
        total = self.get_pet_histories_count(father_id)
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            histories = self.get_pet_histories(father_id, page_no + 1, page_size)
            for history in histories:
                if history['type'] == 2 and history['child']['petId'] == pet_id:
                    return history['child']
        return None

    # 查询获取单只狗宝宝的稀有度
    def get_baby_rage_degree(self, pet_id):
        data = self._query_baby_data(pet_id)
        if data:
            return data['rareDegree']
        else:
            return None

    # 识别单只狗宝宝的详细属性（有误差）
    def get_baby_attribute_details(self, pet_id):
        data = self._query_baby_data(pet_id)
        if data:
            return self.attribute_svg_parser.predict_one_pet_svg_url(data['petUrl'])
        else:
            return ''

    # 识别单只狗宝宝的属性信息（有误差），与其他信息合并返回
    def get_baby_details(self, pet_id):
        data = self._query_baby_data(pet_id)
        attributes_info = self.attribute_svg_parser.predict_one_pet_svg_url_api(data['petUrl'])
        data['attributes'] = attributes_info
        return data

    # 查询统计所有狗宝宝的稀有度
    def query_babies_rage_degree(self):
        page_size, summary, details = 10, {}, {}
        total = self.get_baby_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            babies = self.get_baby_pets(page_no + 1, page_size, pages, total)
            for baby in babies:
                baby_id = baby['petId']

                rare_degree = self.get_baby_rage_degree(baby_id)
                details[baby_id] = self.rare_degree_dic[rare_degree]
                rare_degree = self.rare_degree_dic[rare_degree]
                logger.info('狗蛋：{0} 稀有度：{1}'.format(baby_id, rare_degree))

                if rare_degree in summary:
                    summary[rare_degree] = summary[rare_degree] + 1
                else:
                    summary[rare_degree] = 1

                attributes_details = self.get_baby_attribute_details(baby_id)
                logger.info('狗蛋 {0} 详细属性识别：{1}'.format(baby_id, attributes_details))

                time.sleep(5)

        logger.info('概况：{0}'.format(summary))
        logger.info('详细：{0}'.format(details))

    # 保存狗狗到myPets数据表
    def save_my_pet(self, pet_info):
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
            'user': self.user.name
        }
        my_pets.insert(pet)

    # 统计并保存当前账号下的所有狗狗信息
    def save_my_pets(self):
        my_pets.delete_many({})
        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        index = 0
        for page_no in range(pages):
            page_no = page_no + 1
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                pet_info = self.get_pet_info_on_market(pet['petId'])
                self.save_my_pet(pet_info)
                index = index + 1
                logger.info('保存第{0}条狗狗：{1}'.format(index, pet_info['petId']))


if __name__ == '__main__':
    counter = Counter(user)
    # 按稀有等级统计狗狗数量
    # counter.count_pets_amount_by_rare_degree()
    # 按属性统计狗狗，所有属性完全相同的才算是同一类狗狗
    # 此方法主要是为了统计出双胞胎、三胞胎...狗狗
    # counter.sort_pets_by_attributes()
    # 统计指定稀有属性数量的狗狗
    # counter.get_pets_of_rare_degree(5)
    # 查询统计狗宝宝稀有级别
    counter.query_babies_rage_degree()
    # 统计所有拥有的狗狗到myPets数据表
    #counter.save_my_pets()

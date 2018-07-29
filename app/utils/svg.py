#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import json
import xmltodict
import re
import copy
import app.db.mongo as mongo
import app.logger.logger as logger
from app.config.user import user
from app.operations.lai_ci_gou import LaiCiGou


class Svg(LaiCiGou):
    def __init__(self, user):
        super(Svg, self).__init__(user)

    # 获取svg xml数据
    def get_pet_svg(self, pet_id):
        pet = self.get_pet_info_on_market(pet_id)
        return requests.get(pet['petUrl']).content.decode('utf-8')

    # 获取svg xml数据
    def get_pet_svg_xml(self, pet_url):
        return requests.get(pet_url).content.decode('utf-8')

    # 获取体型
    def get_body_shape(self, svg_json):
        body_shape = None
        new_svg_json = copy.deepcopy(svg_json)
        for node in new_svg_json['svg']['g']:
            if node['@id'] == 'mask':
                body_shape = node
        return body_shape

    # 获取身体色
    def get_body_color(self, svg_json):
        body_color = None
        new_svg_json = copy.deepcopy(svg_json)
        for node in new_svg_json['svg']['g']:
            if node['@id'] == 'body':
                body_color = node['g']['rect']['@fill']
        return body_color

    # 获取花纹
    def get_pattern(self, svg_json):
        # pattern 节点下面依次为花纹和肚皮色
        # 花纹构造较复杂，不易区分，采用穷举特征值的方式判断
        new_svg_json = copy.deepcopy(svg_json)
        pattern = None
        for node in new_svg_json['svg']['g']:
            if node['@id'] == 'pattern':
                node_str = json.dumps(node)
                # 鱼纹特征值：
                pattern_1 = "M197.9,381.5q1.88-.74,3.75-1.44l9.82-3.7c2.89-1.1,6.21-2.78,9.36-3.46a4.91,4.91,0,0,1,2.79.09,1.44,1.44,0,0,1,.89,1.57c-.23,2-3,4.2-4.86,6-2.27,2.17-4.68,4.29-7.28,6.34-2,1.58-4.14,3.12-6.4,4.58Z"
                # 斑马纹特征值：
                pattern_2 = "M502.33,335.08a151.07,151.07,0,0,1-15.05,4.07c-13.31,2.79-28.61,6-42.28,4.92,25.63,2.13,53.69.69,82-4.21,10.57-1.83,45.11-15.55,45.11-15.55L565.4,309s-29.87,13.55-37.48,16.54C519.41,328.87,511,332.28,502.33,335.08Z"
                # 耀斑特征值：
                pattern_3 = "M213.89,348.69c-.53,1.67-.95,3.36-1.63,5s-1.29,3.68-.61,5.6A10.12,10.12,0,0,0,214.5,363a35,35,0,0,0,3.59,2.9,3.46,3.46,0,0,0,2.28.82,2.62,2.62,0,0,0,1.24-.6,20.67,20.67,0,0,0,6-7.67,10,10,0,0,0,1.29-6.31c-.63-3.15-3.6-4.52-6.87-5.52a14.84,14.84,0,0,0-3.71-.76c-2-.09-4.42.84-4.37,2.76"
                # 两道杠特征值：
                pattern_4 = "M225.5,310.37c-3-1.41-6.42-1.34-9.66-.8-10.47,1.76-22.5,9.07-27.73,18.3-3.21,5.67-1.18,7.54-.89,14,.21,4.72.8,5.52,1.06,11.07.16,3.27-.9,5.65,1.78,7.54,4.85-3,8.16-8.94,10.59-14.09A41.13,41.13,0,0,1,220.05,327c4.25-2,9.54-4.12,10.24-8.77C230.77,315,228.47,311.77,225.5,310.37Z"
                # 八字纹特征值：
                pattern_5 = "M348.18,92.92c11.09-4.18,21.41,1,30.77,6.67a129.47,129.47,0,0,1,36.11,33.23c9.51,12.82,16.21,27.29,23.55,41.38.36.71.73,1.42,1.11,2.12.75,1.44-6.79,7.19-7.8,7.93a21.15,21.15,0,0,1-9.2,3.71c-8,1.35-16.19-.17-23.73-2.74a91.74,91.74,0,0,1-37.57-24.84c-11.13-12.1-20.73-26.88-23.71-43.14a32.05,32.05,0,0,1-.23-12.11A16.23,16.23,0,0,1,348.18,92.92Z"
                # 奶牛特征值：
                pattern_6 = "M384.05,219.12c3.34,3,7.31,5.4,11.72,6.06,5.17.77,10.43-1,14.92-3.63,19.84-11.72,20-35.18,14.83-55.26-4-15.32-9.67-31.33-20.23-43.6-12.33-14.34-30-19.83-48.55-17.73-3.3.37-6.78,1.06-9.16,3.37-3.24,3.14-3.42,8.23-3,12.73,1.11,12.44,5,24.44,8.95,36.28,4.79,14.29,9.75,28.58,16.53,42C373.69,206.63,378,213.74,384.05,219.12Z"
                # 散羽纹特征值：
                pattern_7 = "M224.65,337.33s7.32-8.78,3.88-19.34C228.53,318,221.09,327.67,224.65,337.33Z"
                # 霸气点特征值：
                pattern_8 = "M389.21,109.75a38.1,38.1,0,0,0-9.78-2.63c-7.56-1-18.32-.79-24.8,4.08a18.1,18.1,0,0,0-7.58,14.54c0,12.71,4.6,26.33,7.61,38.62,4.65,19,9.3,39,20.12,55.55,7.14,10.94,24.86,25.33,39,21.07C433,235.15,436.14,193.84,432.9,178,428.15,154.87,410.42,118.49,389.21,109.75Z"
                # 峡谷纹特征值：
                pattern_9 = "M463.35,410.47a10.31,10.31,0,0,0-1.64-3.79,15.21,15.21,0,0,0-6.27-4.05c-2.31-.86-4.91-1.05-7.32-1.69-.9-.23-2.9-.63-3.48-1.44-.13-.19-.45-1.09-.17-1.19a89.16,89.16,0,0,1-22.93,4.92c.19-2.28-.1-4.51.08-6.09.73-6.3-8,17.9-13.58,13.45C398.7,403.1,395.12,390,392.81,398c-1.6,5.48-1.49,5.24-1.5,10.91,0,5.11.5,13,3.82,17.17,1.61,2,4.37,4.91,6.62,6.15,5.45,3,11.06,3.2,17.29,3.2,5,0,10.48-1.29,13.54-5.27.47-.62,2.43-3.74,2.5-4.52.19-2.09-3.58-3.56-5.47-4.48-2.6-1.26-5.14-1.41-5.94-4.18-.43-1.52-1.35-2.8-1.46-4.38,0-.69-.51-4.46-.75-8.36a8,8,0,0,1-.25,6.64c-.23.4-.91,1.59-.55,1.87a8.42,8.42,0,0,1,.53,2.66c7,.22,13.87,1,20.86.84,3.7-.11,7.4-.37,11.08-.79,2.65-.3,5.31-.64,8-1C462.23,414.25,463.58,411.87,463.35,410.47Z"
                # 逆鳞特征值：
                pattern_10 = "M452.2,315a10.59,10.59,0,0,0,4.79-3.93,9.23,9.23,0,0,0,1.6-5.73,41.53,41.53,0,0,1-3.94,3.62,16.43,16.43,0,0,1-4,2.36,30.14,30.14,0,0,1-4.62,1.5c-1.65.41-3.39.77-5.33,1.21a11,11,0,0,0,5.55,1.92A13,13,0,0,0,452.2,315Z"
                # 冰凌特征值：
                pattern_11 = "M1,442.46c1.37,2.94,19.68,6,22.77,7s6.15-.27,9-1.43a323.08,323.08,0,0,1,142.75-22.27c2.15.15,4.45.29,6.3-.81s2.7-2.9,3.59-4.69q4.77-9.58,9.53-19.16c1.63-3.27,6-5.8,5.77-9.45a20.34,20.34,0,0,0-2-8.57c-11.34-23.45-10.71-37.68-12.14-56.56-.88-11.62,1.34-25.07,3.9-35.71,2.42-10-30.86-23.15-37-26-20.63-9.66-42.69-16.83-65.49-19.13-13.29-1.35-26.29-3.87-38.81-8.64-12.31-4.7-34-10.42-45.71-1.08-2.73,2.19-2.28,8.74-1.85,32.39"

                if pattern_1 in node_str:
                    pattern = 1
                elif pattern_2 in node_str:
                    pattern = 2
                elif pattern_3 in node_str:
                    pattern = 3
                elif pattern_4 in node_str:
                    pattern = 4
                elif pattern_5 in node_str:
                    pattern = 5
                elif pattern_6 in node_str:
                    pattern = 6
                elif pattern_7 in node_str:
                    pattern = 7
                elif pattern_8 in node_str:
                    pattern = 8
                elif pattern_9 in node_str:
                    pattern = 9
                elif pattern_10 in node_str:
                    pattern = 10
                elif pattern_11 in node_str:
                    pattern = 11
                else:
                    pattern = 0  # 无花纹
        return pattern

    # 获取花纹色
    def get_pattern_color(self, svg_json):
        # pattern 节点下面依次为花纹和肚皮色
        pattern_color = None
        new_svg_json = copy.deepcopy(svg_json)
        for node in new_svg_json['svg']['g']:
            if node['@id'] == 'pattern':
                str = json.dumps(node)
                colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', str)
                pattern_color = colors[0]
        return pattern_color

    # 获取嘴巴
    def get_nose_mouth(self, svg_json):
        nose_mouth = None
        new_svg_json = copy.deepcopy(svg_json)
        for node in new_svg_json['svg']['g']:
            if node['@id'] == 'nose-mouth':
                # nose_mouth = node['path']

                # 采用穷举特征值的方式判断
                nose_mouth_str = json.dumps(node)
                # 美滋滋
                nose_mouth_1 = "M342.46,246.45c-.41.22-2.32-.19-2.89,0a1,1,0,0,0-.52,1,14.81,14.81,0,0,0,.4,4.35,12.51,12.51,0,0,0-2.61-3.47,3.5,3.5,0,0,0-2.79-1.15c-1.22.19-2.07,1.53-3.4,1.18a3.47,3.47,0,0,1-.36-.08,57.36,57.36,0,0,1,3.34,6,8,8,0,0,0,.83,1.91,6,6,0,0,0,1.35,1.49,5.81,5.81,0,0,0,3.73,1.3,5,5,0,0,0,3.57-1.48,5.6,5.6,0,0,0,1.51-3.64,14.85,14.85,0,0,0-.67-4.13,16,16,0,0,0-1.28-3.22Z"
                # 北极熊
                nose_mouth_2 = "M306.43,199.51c-5.65,5.54-13.34,22.4-15.88,29.93-6.32,18.74-8.52,30.57-6.62,54,1.35,16.76,8.74,24.32,24.95,32,13.57,6.41,37.06,6.76,51.37,0,7.66-3.62,17.75-11.13,20.51-19.14,8.25-24,4-33.61-2.69-58-4.69-17-12.84-29.66-21.61-40.42-10-12.31-14.47-15.83-28.84-12.15-6.26,1.6-15.65,8.8-20.44,13.14C306.92,199,306.68,199.27,306.43,199.51Z"
                # 甜蜜蜜
                nose_mouth_3 = "M350.23,246a22.34,22.34,0,0,1-3.27.9,8.46,8.46,0,0,1-3.27-.18,9.18,9.18,0,0,1-3.09-1.27,7.16,7.16,0,0,1-2.36-2.38,6.94,6.94,0,0,1-.62-1.42,9.57,9.57,0,0,0,3.66-2.19,53.56,53.56,0,0,0,5-5.91c5.86-7.2,15.45-19.85,7.51-29.1C350,200,343.5,199,338,199.12a66.31,66.31,0,0,0-22.51,4.33l-.09.05a1.19,1.19,0,0,0-.22.08c-4.78,2.41-9.32,7-8.23,12.82,1.2,6.41,8,11.94,12.62,16,3.25,2.83,7.4,6.88,11.81,8.66a11.89,11.89,0,0,0,3.14.84,7.48,7.48,0,0,0,2.28-.07,12.14,12.14,0,0,1-.29,1.19,10.23,10.23,0,0,1-1.6,3.2,9.31,9.31,0,0,1-5.94,3.36,17.83,17.83,0,0,1-7.19-.3,13.28,13.28,0,0,1-6.5-3.37,8.23,8.23,0,0,0,2.61,2.87,14.46,14.46,0,0,0,3.51,1.77,15.89,15.89,0,0,0,7.87.71,12.32,12.32,0,0,0,2.82-.89c.85.88,1.76,1.68,2.66,2.49,1.05,1,2.13,1.9,3.11,2.9a10,10,0,0,1,.68.78,6.13,6.13,0,0,0,.79.82,6.64,6.64,0,0,0,1.95,1.15,6.51,6.51,0,0,0,4.48.11,5.7,5.7,0,0,0,3.34-3,6.16,6.16,0,0,0,.16-4.47,11.25,11.25,0,0,0-1.52-2.74l.37-.07c.3-.06.6-.12.9-.21a11.81,11.81,0,0,0,1.81-.56,8.41,8.41,0,0,0,3.24-2.18,9.14,9.14,0,0,0,1.81-3.35,17.18,17.18,0,0,0,.72-3.59c-1.1,2.16-2,4.42-3.61,5.9A8.68,8.68,0,0,1,350.23,246Zm-14-37.34-2-1c-1.1-.52-.61-2,.3-2.34a14.44,14.44,0,0,1,9.38-.41c1.75.51,3.75,1.42,3.3,3.62a5.47,5.47,0,0,1-4.5,3.73C340.07,212.44,338.28,209.68,336.19,208.61Zm12.38,42.73a5.41,5.41,0,0,1-.19,3.9,4.89,4.89,0,0,1-2.88,2.54,5.68,5.68,0,0,1-3.92,0,5.94,5.94,0,0,1-1.73-1,5.87,5.87,0,0,1-.7-.71c-.24-.29-.49-.57-.74-.83-1.42-1.42-3-2.64-4.5-3.91h0c-.1,0-.14-.12-.22-.16a4.61,4.61,0,0,1-1.23-1,7.16,7.16,0,0,0,.66-.36,8.68,8.68,0,0,0,2.91-2.87,9.73,9.73,0,0,0,1.33-3.78.66.66,0,0,1,0-.14l0-.47c.05.17.11.34.17.52a2.5,2.5,0,0,0,.09.25,7.44,7.44,0,0,0,2.29,3,12.29,12.29,0,0,0,1.13.75,10.31,10.31,0,0,0,5.91,1.4A11.93,11.93,0,0,1,348.57,251.34Z"
                # 达利胡
                nose_mouth_4 = "M306.4,233.29l-.22.51-.18.45c-.11.3-.21.6-.34.89a17.64,17.64,0,0,1-.81,1.7,12.54,12.54,0,0,1-4.8,5.22,9.5,9.5,0,0,1-3.24,1.1,11.84,11.84,0,0,1-3.51-.08,4.06,4.06,0,0,1-.83-.17c-.25-.08-.52-.13-.77-.22a5.82,5.82,0,0,1-1.37-.79,6.29,6.29,0,0,1-1.15-1.1,8,8,0,0,1-.78-1.41,7.54,7.54,0,0,1-.49-1.57,7.76,7.76,0,0,1-.06-1.67,6.43,6.43,0,0,1,1-3.12c.08-.12.14-.24.22-.35l.29-.31a5.48,5.48,0,0,1,.58-.6,6.6,6.6,0,0,1,1.45-.92,4.57,4.57,0,0,1,.81-.37l.87-.24c.14,0,.29-.09.44-.12l.43-.06.44-.05h.43a3.75,3.75,0,0,1,1.63.38,4.37,4.37,0,0,1,1.29,1.18,8.15,8.15,0,0,1,1.21,3.65,7.58,7.58,0,0,0-.48-4,4.46,4.46,0,0,0-3.48-2.62l-.56-.09h-1.11c-.18,0-.36.05-.54.07l-1.08.17a7.12,7.12,0,0,0-1.06.32,7.89,7.89,0,0,0-3.67,2.62,8.15,8.15,0,0,0-1.75,4.23,9.1,9.1,0,0,0,.52,4.56,9.5,9.5,0,0,0,1.1,2.09,9,9,0,0,0,1.68,1.69,8.68,8.68,0,0,0,2,1.22c.37.15.76.24,1.13.35a5,5,0,0,0,1.12.25,14.87,14.87,0,0,0,4.42,0,11.57,11.57,0,0,0,4.23-1.56,14.14,14.14,0,0,0,5.46-6.65c.28-.65.53-1.31.74-2,.12-.33.19-.67.29-1l.13-.49.13-.42a7.2,7.2,0,0,1,1.76-3.07,13,13,0,0,1,6.78-3.45A12,12,0,0,0,309,229.8,8.83,8.83,0,0,0,306.4,233.29Z"
                # 大胡子
                nose_mouth_5 = "M361.93,304.22a40.62,40.62,0,0,1,3.69,9.25,32.5,32.5,0,0,1,1.09,10,28.16,28.16,0,0,1-1.22,7c.94-.4,1.88-.84,2.78-1.31a33.14,33.14,0,0,0,5.12-3.27,32.58,32.58,0,0,0,8-9.07,36.91,36.91,0,0,0,4.43-11.47,60.07,60.07,0,0,0,1.23-12.54,44.83,44.83,0,0,1,.64,8.36,21.71,21.71,0,0,1,4.89,4.1,12.15,12.15,0,0,1,1.77,2.62l.08-.11a25.11,25.11,0,0,0,2.45-5.9,40.39,40.39,0,0,0,1.32-6.67c-.26-.49-.54-1-.85-1.46a15.93,15.93,0,0,1,2.55,2.93,25.91,25.91,0,0,1,1.88,3.43,35.8,35.8,0,0,1,1.36,3.67c0,.12.07.25.11.38l.71-1.45c.57-1.54,1.32-3,1.84-4.55a49.08,49.08,0,0,0,2.38-9.42,37.41,37.41,0,0,0,.06-9.69,29,29,0,0,0-2.85-9.46,19.44,19.44,0,0,1,3.58,5.76h0a21.12,21.12,0,0,1,3.61.54,34.7,34.7,0,0,1,4.56,1.49,45.09,45.09,0,0,1,4.33,2.05c.53.28,1,.59,1.55.89a48.63,48.63,0,0,0-1-5.12,32.4,32.4,0,0,0-2.83-7.41,28.07,28.07,0,0,0-2.14-3.33,24.78,24.78,0,0,0-2.68-2.94,21.28,21.28,0,0,0-6.89-4.32,16.48,16.48,0,0,1,8,3c.41.28.8.6,1.19.91.73-.13,1.46-.27,2.19-.35a29.66,29.66,0,0,1,3-.23,32,32,0,0,1,6,.33,31.13,31.13,0,0,1,5.9,1.43,27.11,27.11,0,0,1,2.8,1.1,49.94,49.94,0,0,0-8.27-13.81,45.43,45.43,0,0,0-6.88-6.56c-1.23-1-2.56-1.88-3.88-2.77s-2.73-1.64-4.16-2.35a68.43,68.43,0,0,0-18.19-6.23,94.94,94.94,0,0,0-14-1.74c-.27,1.15-.58,2.32-1,3.5-6.48,19.83-28.21,40.19-43.87,41.1-.52,0-1,.05-1.58.05-15.46,0-37.36-12.51-48.72-28.07a44.82,44.82,0,0,1-5.42-9.56,117.07,117.07,0,0,0-12.57,4.44,72.2,72.2,0,0,0-17.07,9.82,37.91,37.91,0,0,0-6.84,6.85,30.84,30.84,0,0,0-4.65,8.32,29.93,29.93,0,0,0-1.58,9.35l.05,2.4.28,2.39c.05.39.09.8.15,1.19l0,.23c.21-.28.42-.54.64-.81a21.72,21.72,0,0,1,3.33-3.24,16.6,16.6,0,0,1,4.09-2.35,14.57,14.57,0,0,1,4.65-1l1.45-.1-.17,1.45a37.19,37.19,0,0,0-.17,5.5,39,39,0,0,0,.61,5.51,25.27,25.27,0,0,0,1.6,5.25,18.45,18.45,0,0,0,2.08,3.43,17.92,17.92,0,0,1,.25-1.79,16.23,16.23,0,0,1,.95-3.21,11.64,11.64,0,0,1,1.72-2.85,8.87,8.87,0,0,1,2.61-2,2.83,2.83,0,0,0-.28.2,6.31,6.31,0,0,1,.63-.34,36.56,36.56,0,0,1,2.68-11.74,33.12,33.12,0,0,0-1.37,5.87,40.24,40.24,0,0,0-.49,6A39.29,39.29,0,0,0,265,297.51a36.32,36.32,0,0,0,2.11,5.54,39,39,0,0,0,2.9,5.16,47.12,47.12,0,0,0,5.71,7c.05-.86.13-1.72.25-2.58a34.78,34.78,0,0,1,1.1-5.31,26.28,26.28,0,0,1,2.05-5.1,19.57,19.57,0,0,1,3.31-4.53l2.47-2.52-.06,3.61a49,49,0,0,0,1.27,11.65,39.22,39.22,0,0,0,4.19,10.88,27.7,27.7,0,0,0,7.58,8.6,28.51,28.51,0,0,0,8.75,4.28c0-1.59,0-3.16.09-4.74.11-2.21.3-4.41.61-6.61a43.94,43.94,0,0,1,1.4-6.55,19,19,0,0,1,3.05-6.21l.76-.94.82.83a34.91,34.91,0,0,1,5.28,6.85,22.78,22.78,0,0,1,1.84,4,13.07,13.07,0,0,1,.71,3.59,7.92,7.92,0,0,0,1.57-.42,9.2,9.2,0,0,0,2.13-1.21,11.72,11.72,0,0,0,3.17-3.86,20.71,20.71,0,0,0,1.78-4.83,31.93,31.93,0,0,0,.77-4.26c-.2-.21-.39-.44-.6-.65a44,44,0,0,0-5.45-4.79,28.47,28.47,0,0,1,6.37,3.76,29.39,29.39,0,0,1,5.32,5.31,23.53,23.53,0,0,1,3.69,6.7l.61,1.84c.15.64.26,1.28.38,1.91.06.32.13.64.17,1l0,.46a47.6,47.6,0,0,0,10.8-8.76l1.32-1.55c.42-.53.79-1.09,1.19-1.64a13.37,13.37,0,0,0,1.12-1.69,16.56,16.56,0,0,0,1-1.78l.89-1.85c.29-.62.46-1.29.71-1.93l.36-1c.1-.33.16-.67.24-1l.05-.21a25.18,25.18,0,0,0,.43-2.53,53.33,53.33,0,0,0-2.91-5.28A41.71,41.71,0,0,1,361.93,304.22Z"
                # 长舌头
                nose_mouth_6 = "M349.68,228.05c3-3.48,6.9-10.44,5.84-15.41-.94-4.37-8.86-3.19-12.12-3.27-5.53-.14-11-.11-16.57-.14-4.93,0-10.93-1.21-15.76-.23-6,3.54,7.41,20.47,9.69,22.26C329.5,238.16,342.48,236.45,349.68,228.05Z"
                # 小獠牙
                nose_mouth_7 = "M302.92,246.24l-.23-.25c.05.14.1.27.16.41.33.93.66,1.79,1,2.76a29.56,29.56,0,0,1,.75,2.87,52.82,52.82,0,0,1,.77,5.79l.44,5.77h0l8.26-4a88.09,88.09,0,0,0-7.21-9.1Q304.91,248.36,302.92,246.24Z"
                # 三瓣
                nose_mouth_8 = "M337.25,252.72c2.78-6,10.95-8.6,18.39-3-2.85,14-9.36,40.17-18.39,40.17,12.34,0,20.88-48.35,20.88-48.35s-8.63-6.74-13-11.42a46.27,46.27,0,0,1-4.21-5.49c-.88-1.32-1.75-2.72-2.56-4.11a53.64,53.64,0,0,1-2.76-5.31,14.23,14.23,0,0,1-1.26-4c-.33,3.79-1.82,6.85-3.8,10.72-.22.43-.45.86-.68,1.28-.46.85-.94,1.69-1.43,2.51a153,153,0,0,1-11.16,15.77s.58,3.13,1.62,7.81C324.47,247.42,331.18,247.28,337.25,252.72Z"
                # 熊出没
                nose_mouth_9 = "M377.12,230.72c-1.23-8.8-11.21-15.68-44.66-15.18-37.64.57-50.92,13.2-50.11,26.48s-.74,81.65,53.83,79.11S380.06,251.68,377.12,230.72Z"
                # 撇嘴
                nose_mouth_10 = "M373.78,247.87c-4.5,1.35-8.88,3-13.24,4.76s-8.58,3.8-12.77,5.88q-7.47,3.84-14.63,8.21l-.27-8.91.45,0a14.7,14.7,0,0,0,3.35-.36c8.25-1.87,18.48-9.31,20.57-17.39a10.77,10.77,0,0,0-3.61-11.25c-8.44-7.55-30.56-5.5-40.8-.48-5.87,2.88-6.92,6.06-6.77,8.22.31,4.29,4.76,10.32,11.08,15a31.42,31.42,0,0,0,12.72,5.91l.33,11c-2.21,1.4-4.4,2.82-6.56,4.3a191.42,191.42,0,0,0-22,17.26c7.63-5.36,15.41-10.44,23.31-15.31,4-2.4,7.93-4.8,12-7s8.09-4.49,12.23-6.56a227,227,0,0,1,25.4-11.09c4.36-1.52,8.76-3,13.24-4.12s9-2.08,13.64-2.8a92.43,92.43,0,0,0-14,1.36A123.63,123.63,0,0,0,373.78,247.87Z"
                # 地包天
                nose_mouth_11 = "M367.82,297.69a93,93,0,0,1-30.44,6.94,85.46,85.46,0,0,1-31-4.14,84.26,84.26,0,0,1-14.33-6.2,76.27,76.27,0,0,1-9.36-6.1c2.4,2.63,4.45,5.77,6.92,8.16,3.8,3.67,8.49,6.2,13.19,8.53,10.57,5.23,22.35,8.58,34.23,7.63a75.58,75.58,0,0,0,31.11-9.9A110.77,110.77,0,0,0,382.3,293c4.34-3.43,7.86-8,12.62-10.87l-1.35.8A112.58,112.58,0,0,1,367.82,297.69Z"
                # 小虎牙
                nose_mouth_12 = "M383.86,243.77a1.5,1.5,0,0,0,0-3,1.5,1.5,0,0,0,0,3Z"
                # 樱桃
                nose_mouth_13 = "M323.72,231.05h0s3.54,4.22,12.43,4.29c8,.06,11.84-4.4,12.56-5.32l.13-.18C337.8,225.8,325.41,230.38,323.72,231.05Z"
                # 橄榄
                nose_mouth_14 = "M324.62,208.1c.12,4.83,1.89,11.79,6.53,14.49,6.3,3.67,8.8-4.66,9.22-9.46.38-4.38.61-10-1.67-13.87-2.48-4.27-7.49-3.87-10.58-.73C325.59,201.09,324.81,204.63,324.62,208.1Z"
                # 呆萌
                nose_mouth_15 = "M356.12,201.53c-2.73-4.53-5.58-9.51-9-13.56-8.86-10.47-21.9-7.39-30,2.09a99.56,99.56,0,0,0-6.35,8.83c-3.13,5.22-6.84,14-4.22,19.93,4.81,10.84,19.11,11,28.82,8.52,3.7-.93,7.6-1.12,11.37-1.63,2.06-.28,4.7-.28,6.62-1.14,2.51-1.11,4.31-4.81,5.35-7.31C361.18,211.22,359.25,206.71,356.12,201.53Z"

                if nose_mouth_1 in nose_mouth_str:
                    nose_mouth = 1
                elif nose_mouth_2 in nose_mouth_str:
                    nose_mouth = 2
                elif nose_mouth_3 in nose_mouth_str:
                    nose_mouth = 3
                elif nose_mouth_4 in nose_mouth_str:
                    nose_mouth = 4
                elif nose_mouth_5 in nose_mouth_str:
                    nose_mouth = 5
                elif nose_mouth_6 in nose_mouth_str:
                    nose_mouth = 6
                elif nose_mouth_7 in nose_mouth_str:
                    nose_mouth = 7
                elif nose_mouth_8 in nose_mouth_str:
                    nose_mouth = 8
                elif nose_mouth_9 in nose_mouth_str:
                    nose_mouth = 9
                elif nose_mouth_10 in nose_mouth_str:
                    nose_mouth = 10
                elif nose_mouth_11 in nose_mouth_str:
                    nose_mouth = 11
                elif nose_mouth_12 in nose_mouth_str:
                    nose_mouth = 12
                elif nose_mouth_13 in nose_mouth_str:
                    nose_mouth = 13
                elif nose_mouth_14 in nose_mouth_str:
                    nose_mouth = 14
                elif nose_mouth_15 in nose_mouth_str:
                    nose_mouth = 15
        return nose_mouth

    # 获取肚皮色
    def get_tummy_color(self, svg_json):
        tummy_color = None
        new_svg_json = copy.deepcopy(svg_json)
        for node in new_svg_json['svg']['g']:
            if node['@id'] == 'pattern':
                if type(node['g']['g']) == list:
                    for e in node['g']['g']:
                        if '@fill' in e['path']:
                            tummy_color = e['path']['@fill']
                else:
                    tummy_color = node['g']['g']['path']['@fill']
        return tummy_color

    # 获取眼睛色
    def get_eye_color(self, svg_json):
        eye_color = None
        new_svg_json = copy.deepcopy(svg_json)
        for node in new_svg_json['svg']['g']:
            if node['@id'] == 'eye':
                for e in node['g']:
                    if e['@id'] == 'eye-color2':
                        str = json.dumps(e)
                        colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', str)
                        eye_color = colors[0]
                        return eye_color
        return eye_color

    # 获取眼睛
    def get_eye_shape(self, svg_json):
        eye_shape = None
        new_svg_json = copy.deepcopy(svg_json)
        for node in new_svg_json['svg']['g']:
            if node['@id'] == 'eye':
                for e in node['g']:
                    if e['@id'] == 'eye-shape':
                        # eye_shape = e['path']
                        # return eye_shape

                        # 采用穷举特征值的方式判断
                        eye_shape_str = json.dumps(e)
                        # 小严肃
                        eye_shape_1 = "M372.8,156.6a2.39,2.39,0,0,1,.28-.49,9.85,9.85,0,0,0-2.52,1,5.43,5.43,0,0,0-1.77,1.58c.95.15,2.38.36,4.14.57a2,2,0,0,1-.21-.47,1.11,1.11,0,0,0,.88-1.08A1.13,1.13,0,0,0,372.8,156.6Z"
                        # 小杀气
                        eye_shape_2 = "M368.14,174.13a32.24,32.24,0,0,0,14.41,8.44A33.17,33.17,0,0,1,368.14,174.13Z"
                        # 白眉斗眼
                        eye_shape_3 = "M295.23,123.9c-21.73-17.81-51.73-12-72.06,4.87-11.71,10.13-20.83,23.9-22.35,39.61-1.28,13.09,2.59,26.27,9.6,37.28,12.38,19.45,36.52,33.94,59.91,27.1,20.91-6.12,35.23-26.45,41.18-46.49C318.07,164.16,313.73,139.06,295.23,123.9Zm16.09,44.39c3.12,13.14-4,29.29-15.05,36.62-11.44,7.59-25.45,6.31-36.15-1.92-11.83-9.09-12.9-22.85-8.48-36.31a1.66,1.66,0,0,1,.15-.33c5.3-13,20-19.08,33.33-17.46a40.23,40.23,0,0,1,4.79.88c7-2,15.58,1.56,16.61,9.36A21.23,21.23,0,0,1,311.32,168.29Z"
                        # 小鄙视
                        eye_shape_4 = "M436.34,147.2c-10.89-11.41-23.95-17.74-35-20a42.19,42.19,0,0,0-11.79-.86c-29.86,2.45-37.87,25.17-41.29,34.87-1.63,4.64-1.49,8.41.36,9.85,2.15,1.67,6.75.46,12.31-3.25,7.45-5,21.81-6.11,32.55-6.18,12.35-.09,24.26,1.18,28.78,2.1,1.15.24,2.39.53,3.66.82,5.66,1.32,12.7,2.95,16.07.6a5.61,5.61,0,0,0,2.2-4.2C444.55,157.91,441.55,152.65,436.34,147.2Z"
                        # 小对眼
                        eye_shape_5 = "M295.89,123.07c-21.73-17.81-51.73-12-72.06,4.87-11.71,10.13-20.83,23.9-22.36,39.62-1.27,13.08,2.6,26.27,9.61,37.28,12.38,19.45,36.51,33.94,59.91,27.09,20.91-6.11,35.23-26.44,41.18-46.49C318.73,163.33,314.39,138.24,295.89,123.07ZM312,167.47c3.12,13.13-4,29.28-15.05,36.62-11.44,7.58-25.45,6.3-36.15-1.92-11.83-9.09-12.9-22.85-8.48-36.32a1.57,1.57,0,0,1,.15-.32c5.3-13,19.95-19.08,33.33-17.47a40.23,40.23,0,0,1,4.79.88c7-1.95,15.58,1.56,16.61,9.37A21.23,21.23,0,0,1,312,167.47Z"
                        # 小可爱
                        eye_shape_6 = "M297.13,125.51c-15.9-15-34.94-17.68-52.69-4.19-.06,0-.1.09-.15.13l-.16.1c-32.2,24.89-13.28,88.73,29.73,85.92,17.9-1.17,30.39-17.56,35.77-33.3C315.69,156.47,310.67,138.3,297.13,125.51Zm1.7,11.07c-.37,4.7-3.28,9.51-8.6,8.16-6.66-1.69-8.92-10.67-3.13-14.72-13.93-.19-27.77,8.58-26.34,24,1.35,14.55,17.51,25.42,31.5,20.72,13.7-4.61,18.18-24.79,11.11-36.67a40,40,0,0,1,5.14,29.08c-3.19,14.68-12.89,31-27.86,36-18.76,6.22-38.12-7.82-45.61-24.45-8.06-17.9-4.86-42.48,11.14-54.91,13.4-10.41,29.23-10.55,43-.84a49.54,49.54,0,0,1,13.22,13.66,13.15,13.15,0,0,0-3.88-3.77A11.87,11.87,0,0,1,298.83,136.58Z"
                        # 小海盗
                        eye_shape_7 = "M420,192.85a46.83,46.83,0,0,0,19.9-20.34c8.37-17,4.19-36.87-10.93-48.47-2.69-1.4-5.08-3.35-7.81-4.73a57.25,57.25,0,0,0-13.79-4.85c-8.82-1.87-17.25-1-25.07,3.61-14.63,8.64-18.83,25.57-15.31,41.4,3.33,14.93,13.11,31.35,28.48,36.16a27.23,27.23,0,0,0,3,.76A34.2,34.2,0,0,0,420,192.85Zm-26.34-15.24c-11.38.59-16.79-10.33-18.41-20.36a44.34,44.34,0,0,1-.51-5c-.3-7.3,2.38-13.24,7.29-16.52a9,9,0,0,0-.43,3.91c.41,4.09,2.62,8.82,7.42,8.37,4.1-.38,7.16-3.89,7.81-7.77a1.5,1.5,0,0,0,.07-.44,1.39,1.39,0,0,0,0-.46,7.59,7.59,0,0,0-3.6-6.3c.26,0,.52,0,.78,0,12.33,1.17,22.05,8.79,21.92,21.78a1.93,1.93,0,0,1,0,.34,1.74,1.74,0,0,1-.05.34C414.59,166.59,405.14,177,393.61,177.61Z"
                        # 小颓废
                        eye_shape_8 = "M232.2,185.18c6.52,12.52,18.21,24.54,33.43,23.53,17.63-1.17,31.58-20.12,38.41-36,2.84-6.61,3.9-15.26,4.72-22.4-2.6,11.05-7.33,21.83-15.12,30.1a42,42,0,0,1-24,13c-10,1.47-20.23-2-28.93-6.67l-.84-.46q-3.09-1.71-6-3.69c-.9-.61-3.29-1.92-4.23-2.45Z"
                        # 小新
                        eye_shape_9 = "M312.54,138.57c-1.24-.42-6.63-.89-14.56-1.27-.59,5.6-10.78,19.12-25.61,18.19-13-.81-19.14-14.78-20.67-18.9-18.22.28-28,1.27-30,2.33-.18,2.3,1.34,9.19,6.7,15.73s16.29,14.63,36.77,14.63c28.46,0,41.06-16.94,44.25-22.13C312.36,142.4,312.73,139.32,312.54,138.57Z"
                        # 小脾气
                        eye_shape_10 = "M283.59,193.7a34.78,34.78,0,0,1-7.82,4.17,16.67,16.67,0,0,1,3.65,1.65,21.2,21.2,0,0,1,4.1,3.21c.05.05.1.11.16.16.73-.94,1.45-1.88,2.17-2.83l3.07-4a18.09,18.09,0,0,1-3.78-1.41A17.18,17.18,0,0,1,283.59,193.7Z"
                        # 小头晕
                        eye_shape_11 = "M289.33,118.08c-7.82-4.63-16.25-5.49-25.07-3.61a56.83,56.83,0,0,0-13.79,4.85c-2.74,1.38-5.12,3.33-7.81,4.73-15.12,11.6-19.3,31.46-10.94,48.47,7.69,15.62,26.58,28.71,44.44,23.12,15.37-4.81,25.15-21.23,28.47-36.16C308.16,143.65,304,126.72,289.33,118.08ZM262.26,189c-9.47,1.85-17-6.57-18.21-15.24a1.62,1.62,0,0,1-.05-.4,1.39,1.39,0,0,1,0-.46,16.55,16.55,0,0,1,17.43-15.77,5.68,5.68,0,0,1,1.57-.87,1.14,1.14,0,0,1,1.27-.13,1.34,1.34,0,0,1,.49.32l4.7,3.45c.7.52,1.52.95,1.59,1.92,0,.11,0,.23,0,.35a15.9,15.9,0,0,1,3,10C273.89,179.25,269.86,187.48,262.26,189Z"
                        # 小惊讶
                        eye_shape_12 = "M305.64,165.74A35.81,35.81,0,0,0,302.39,115a36.06,36.06,0,0,0-23.85-9c-.79,0-1.58,0-2.38.08a36.13,36.13,0,0,0-33.83,38.21A35.59,35.59,0,0,0,254.53,169a36.39,36.39,0,0,0,51.11-3.27ZM283,152c-3.37.22-6.49-5.66-7-13.13s1.87-13.7,5.24-13.91c2.32-.15,4.53,2.6,5.83,6.76-2.45,1.13-4.19,2.73-3.57,4.46.52,1.47,2.42,1.74,4.66,1.33,0,.19,0,.38.05.58C288.73,145.57,286.38,151.8,283,152Z"
                        # 黑老大
                        eye_shape_13 = "M399,132.29c-.4-4.85-25.25-7.51-47.46-7.58a58.06,58.06,0,0,0,9,1.38c-4,0-15.83.26-27.37.54,2.63,4,11.8,16.45,24.71,17.21C373.23,144.74,399.43,137.73,399,132.29Z"
                        # 小傻子
                        eye_shape_14 = "M292.42,122.51c-7.41-5.22-16.44-9.14-25.66-8a23.3,23.3,0,0,0-6.34,1.77,26.45,26.45,0,0,1,4-1.27,6.69,6.69,0,0,1,4.67,6.47c.15.09-.61,2.49-.47,2.59,2.78,1.83-.58,4.15,1.16,7.37,7.06,13.09-1.89,10.66-11.93,16.55-4.15,2.43-2.64,4-6.92,3.84-6.23-.28-12.06-1.08-16.51-6.78-.1-.13-.35,12.73-.44,12.59a49.9,49.9,0,0,0,4.25,20.57c7.49,16.64,26.85,30.68,45.61,24.46,15-5,24.67-21.28,27.85-36C315.5,149.37,306.53,132.45,292.42,122.51Z"
                        # 小纠结
                        eye_shape_15 = "M265.06,168.79c-11.41.64-22.76,2.13-34.16,2.7q-2.9.15-5.8.23h-.18a70.27,70.27,0,0,0,7.39,9.78,44.73,44.73,0,0,0,9.93,8.2,36.87,36.87,0,0,0,11.85,4.55,43.94,43.94,0,0,0,12.7.48,56.61,56.61,0,0,0,6.33-1,39.8,39.8,0,0,0,17-8.1,33.06,33.06,0,0,0,8.16-9.47,53.41,53.41,0,0,0,4.24-9.78l-17.57,1.2Z"
                        # 白眉斗眼
                        eye_shape_16 = "M444.44,127.47c-22.48-20.29-60.06-25.66-81.28-.71-16.45,20.6-17.87,51.3-7.19,74.86,10.79,23.79,36.25,38.16,62.16,32.38,23.25-5.19,41.58-24.61,45.83-47.95C467.84,164.77,460.58,142,444.44,127.47Zm17.49,50.33a58,58,0,0,1-33.47,49.53,51.87,51.87,0,0,1-65.66-19.41c-14.71-22.92-14.78-57.43,2.48-79,18.67-21.95,49.9-18.94,71.71-3.55C453.74,137.14,463,157.45,461.93,177.8Z"

                        if eye_shape_1 in eye_shape_str:
                            eye_shape = 1
                        elif eye_shape_2 in eye_shape_str:
                            eye_shape = 2
                        elif eye_shape_3 in eye_shape_str:
                            eye_shape = 3
                        elif eye_shape_4 in eye_shape_str:
                            eye_shape = 4
                        elif eye_shape_5 in eye_shape_str:
                            eye_shape = 5
                        elif eye_shape_6 in eye_shape_str:
                            eye_shape = 6
                        elif eye_shape_7 in eye_shape_str:
                            eye_shape = 7
                        elif eye_shape_8 in eye_shape_str:
                            eye_shape = 8
                        elif eye_shape_9 in eye_shape_str:
                            eye_shape = 9
                        elif eye_shape_10 in eye_shape_str:
                            eye_shape = 10
                        elif eye_shape_11 in eye_shape_str:
                            eye_shape = 11
                        elif eye_shape_12 in eye_shape_str:
                            eye_shape = 12
                        elif eye_shape_13 in eye_shape_str:
                            eye_shape = 13
                        elif eye_shape_14 in eye_shape_str:
                            eye_shape = 14
                        elif eye_shape_15 in eye_shape_str:
                            eye_shape = 15
                        elif eye_shape_16 in eye_shape_str:
                            eye_shape = 16
        return eye_shape

    def ordered(self, obj):
        if isinstance(obj, dict):
            return sorted((k, self.ordered(v)) for k, v in obj.items())
        if isinstance(obj, list):
            return sorted(self.ordered(x) for x in obj)
        else:
            return obj

    def _compare_body_shape(self, pet_id1, pet_id2):
        xml1 = self.get_pet_svg(pet_id1)
        svg_json1 = xmltodict.parse(xml1)

        shape1 = self.get_body_shape(svg_json1)
        logger.info(json.dumps(shape1))

        xml2 = self.get_pet_svg(pet_id2)
        svg_json2 = xmltodict.parse(xml2)

        shape2 = self.get_body_shape(svg_json2)
        logger.info(json.dumps(shape2))

        return self.ordered(shape1) == self.ordered(shape2)

    def get_xmls(self):
        # names = ['眼睛', '嘴巴']
        names = ['嘴巴']
        for name in names:
            for attribute in mongo.attributes.find({"name": name}):
                pet = mongo.pets.find_one(
                    {"attributes": {"$elemMatch": {"name": name, "value": attribute['value']}}})
                xml = self.get_pet_svg_xml(pet['petUrl'])
                print('{0} {1}'.format(name, attribute['value']))
                print(xml)


if __name__ == '__main__':
    svg = Svg(user)
    logger.info(svg._compare_body_shape('2000528696277494352', '2000526840851553075'))
    svg.get_xmls()

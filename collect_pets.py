#!/usr/bin/python
# -*- coding: utf-8 -*-
from app.config.user import user
from app.pet_collector import Collector

collector = Collector(user)
# 按稀有度无限循环查询和保存狗狗
collector.get_save_pets_forever()

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json


def load_json(file_name):
    father_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + os.path.sep + ".")
    with open(os.path.join(father_path, file_name), 'rb') as file:
        return json.loads(file.read().decode())

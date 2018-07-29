#!/usr/bin/python
# -*- coding: utf-8 -*-
import platform
import app.db.mongo as mongo
import app.logger.logger as logger
from app.config.util import load_json
from app.config.cfg import ACCOUNT

os = platform.system()


class User():
    def __init__(self, name=None, secret=None, cookie=None):
        self.id = ''
        self.name = name
        self.secret = secret
        self.cookie = cookie


def _to_object(users_json_list):
    users = []
    for user_json in users_json_list:
        user = User()
        user.__dict__ = user_json
        users.append(user)
    return users


def get_users():
    if os == "Windows":
        users = load_json('user.json')['users']
    else:
        cursor = mongo.users.find({})
        users = list()
        for doc in cursor:
            doc['id'] = doc['_id']
            doc.pop('_id')
            users.append(doc)

    return _to_object(users)


def get_user(users_name):
    users = get_users()
    for user in users:
        if user.name == users_name:
            return user
    return None


def force_insert_into_db(users):
    mongo.users.delete_many({})
    for user in users:
        user_dic = {}
        user_dic.update(user.__dict__)
        mongo.users.insert(user_dic)


def get_user_from_db(user_name):
    document = mongo.users.find_one({'name': user_name})
    if not document:
        return None

    document['id'] = str(document['_id'])
    document.pop('_id')
    user = User()
    user.__dict__ = document

    return user


if os == "Windows":
    force_insert_into_db(get_users())

users = get_users()
user = get_user(ACCOUNT)

logger.suc('当前账号：{0}'.format(user.name))

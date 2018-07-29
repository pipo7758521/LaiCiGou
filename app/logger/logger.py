#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime


class ConsoleColors:
    SUCCESS = '\033[32m'
    WARNING = '\033[93m'
    ERROR = '\033[31m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


def info(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('>> {0}: {1}'.format(t, msg))


def suc(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('>> {0}: {1}{2}{3}'.format(t, ConsoleColors.SUCCESS, msg, ConsoleColors.ENDC))


def warn(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('>> {0}: {1}{2}{3}'.format(t, ConsoleColors.WARNING, msg, ConsoleColors.ENDC))


def err(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('>> {0}: {1}{2}{3}'.format(t, ConsoleColors.ERROR, msg, ConsoleColors.ENDC))


def fail(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('>> {0}: {1}{2}{3}'.format(t, ConsoleColors.FAIL, msg, ConsoleColors.ENDC))

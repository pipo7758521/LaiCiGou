#!/usr/bin/python
# -*- coding: utf-8 -*-
import schedule
import time

from tasks import sale
from tasks import shelf
from tasks import shelf_multiple_users

if __name__ == '__main__':
    # 下面任务为串行执行，如需并行需用多线程对任务再次封装
    # schedule.every().hours.do(sale)
    # schedule.every().hours.do(shelf)
    #
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    shelf_multiple_users()

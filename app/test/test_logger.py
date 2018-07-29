import sys
print(sys.path)

sys.path.append("..")

import logger.logger as logger


def test():
    logger.info('info: No active formats remain. Continue?')
    logger.suc('success: No active formats remain. Continue?')
    logger.warn('warning: No active formats remain. Continue?')
    logger.err('error: No active formats remain. Continue?')
    logger.fail('fail: No active formats remain. Continue?')


test()

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys
import os.path
from PIL import Image
import numpy as np

from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

import tensorflow as tf
import app.captcha_crack.captcha_model as captcha

import base64
from io import BytesIO
import app.logger.logger as logger
import app.captcha_crack.config as config

IMAGE_WIDTH = config.IMAGE_WIDTH
IMAGE_HEIGHT = config.IMAGE_HEIGHT

CHAR_SETS = config.CHAR_SETS
CLASSES_NUM = config.CLASSES_NUM
CHARS_NUM = config.CHARS_NUM

FLAGS = None

# 当前文件所在目录
CUR_PATH = os.path.split(os.path.realpath(__file__))[0]
checkpoint_dir = CUR_PATH + '/captcha_train'


class Crack:
    @staticmethod
    def _one_hot_to_texts(recog_result):
        texts = []
        for i in range(recog_result.shape[0]):
            index = recog_result[i]
            texts.append(''.join([CHAR_SETS[i] for i in index]))
        return texts

    @staticmethod
    def _input_data(base64_image_str):
        batch_size = 1
        images = np.zeros([batch_size, IMAGE_HEIGHT * IMAGE_WIDTH], dtype='float32')

        image = Image.open(BytesIO(base64.b64decode(base64_image_str)))
        image_gray = image.convert('L')
        image_resize = image_gray.resize(size=(IMAGE_WIDTH, IMAGE_HEIGHT))
        image.close()
        input_img = np.array(image_resize, dtype='float32')
        input_img = np.multiply(input_img.flatten(), 1. / 255) - 0.5
        images[0, :] = input_img

        return images

    @staticmethod
    def predict(base64_image_str):
        with tf.Graph().as_default(), tf.device('/cpu:0'):
            input_images = Crack._input_data(base64_image_str)
            images = tf.constant(input_images)
            logits = captcha.inference(images, keep_prob=1)
            result = captcha.output(logits)
            saver = tf.train.Saver()
            sess = tf.Session()
            # log(checkpoint_dir)
            saver.restore(sess, tf.train.latest_checkpoint(checkpoint_dir))
            # log(tf.train.latest_checkpoint(checkpoint_dir))
            recog_result = sess.run(result)
            sess.close()
            text = Crack._one_hot_to_texts(recog_result)

            return text[0]


def main(_):
    img_str = r'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'
    text = Crack.predict(img_str)
    logger.info(text)  # JNWx


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--checkpoint_dir',
        type=str,
        default='./captcha_train',
        help='Directory where to restore checkpoint.'
    )
    parser.add_argument(
        '--captcha_dir',
        type=str,
        default='./data/test_data',
        help='Directory where to get captcha images.'
    )
    FLAGS, unparsed = parser.parse_known_args()
    tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)

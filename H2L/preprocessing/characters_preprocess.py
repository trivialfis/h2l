#!/usr/bin/env python3
#
# Copyright © 2017, 2018 Fis Trivial <ybbs.daans@hotmail.com>
#
# This file is part of H2L.
#
# H2L is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# H2L is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with H2L.  If not, see <http://www.gnu.org/licenses/>.
#

import os
from random import shuffle, randint
from skimage import exposure
import cv2
from .reform import randomReform
from ..normalization import image_utils
from ..evaluator import h2l_debug
# from configuration import characterRecognizerConfig as config
from tqdm import tqdm
import numpy as np
from multiprocessing import Pool

SOURCE = '../resource/pngs'
# SOURCE = '../resource/splited'
TRAINING = '../resource/training'
VALIDATION = '../resource/validation'
TRAIN_RATIO = 0.9
CPUS = 6
####
LIMIT = 200
####
# LIMIT = 2000

debugger = h2l_debug.h2l_debugger()


def binarize_inv(image):
    result = cv2.threshold(
        image, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return result


def load_images():
    symbols = os.listdir(SOURCE)
    debugger.display('Total classes: ', len(symbols))
    bar = tqdm(total=len(symbols), unit='symbol')
    all_images = {}
    for sym in symbols:
        path = os.path.join(SOURCE, sym)
        images_name = os.listdir(path)
        shuffle(images_name)
        images_path = [os.path.join(path, img) for img in images_name]
        images = [cv2.imread(img, 0) for img in images_path]
        images = [binarize_inv(img) for img in images]
        kernel = np.ones((3, 3), np.uint8)
        # images = [cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        #           for img in images]
        images = [cv2.dilate(img, kernel=kernel, iterations=1)
                  for img in images]
        all_images[sym] = images
        bar.update(1)
    return all_images


def clean(all_images):
    result = {}
    for k, v in all_images.items():
        result[k] = v[:LIMIT] if len(v) > LIMIT else v
    return result


def generate(all_images):

    print('Generate')
    result = {}
    di_kernel = np.ones((2, 2), np.uint8)
    for k, v in all_images.items():
        length = len(v)
        ori_length = length
        result[k] = v
        while length < 2*LIMIT:
            index = randint(0, ori_length-1)
            image = v[index].copy()
            image = randomReform(v[index], binarizing=False)
            image = cv2.erode(image, di_kernel, iterations=1)
            result[k].append(image)
            length += 1
        ####
        # remove_edges only for collected
        # result[k] = [image_utils.remove_edges(image, escape=0.1)
        #              for image in result[k]]
        ####

        ####
        # Dilate only for pngs
        result[k] = [
            cv2.dilate(
                image, di_kernel, iterations=1
            )
            for image in result[k]
        ]
        # di_kernel = np.ones((2, 2), np.uint8)
        # result[k] = [
        #     # cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, di_kernel)
        #     cv2.morphologyEx(img, cv2.MORPH_TOPHAT, di_kernel)
        #     for img in result[k]
        # ]
        # result[k] = [
        #     cv2.dilate(
        #         image, di_kernel, iterations=2
        #     )
        #     for image in result[k]
        # ]
        ####

        ####
        # erode only for collected
        # result[k] = [
        #     cv2.erode(
        #         image, di_kernel, iterations=1
        #     )
        #     for image in result[k]
        # ]
        ####
    return result


def save_images(all_images):

    def save(data, target):
        low_contrast = 0
        for symbol, images in data.items():
            path = os.path.join(target, symbol)
            if not os.path.exists(path):
                os.mkdir(path)
            index = 0
            for image in images:
                filename = os.path.join(path, str(index) + 'a.png')
                low_contrast += 1 if exposure.is_low_contrast(image) else 0
                index += 1
                cv2.imwrite(filename=filename, img=image)
        return low_contrast

    print('Save')
    low_contrast = 0
    if not os.path.exists(TRAINING):
        os.mkdir(TRAINING)
    if not os.path.exists(VALIDATION):
        os.mkdir(VALIDATION)
    for k, v in all_images.items():
        training_images = v[:int(len(v)*TRAIN_RATIO)]
        try:
            low_contrast += save({k: training_images}, TRAINING)
        except ValueError:
            debugger.display(type({k: training_images}),
                             len({k: training_images}))
        validation_images = v[int(len(v)*TRAIN_RATIO):]
        low_contrast += save({k: validation_images}, VALIDATION)
    return low_contrast


def subprocess(images):
    images = generate(images)
    low_contrast = save_images(images)
    debugger.display('Low contrast: ', low_contrast)


def start():
    print('Load')
    all_images = load_images()
    print('Clean')
    all_images = clean(all_images)
    all_images = list(all_images.items())

    size = len(all_images) // CPUS
    tasks = []
    for i in range(CPUS-1):
        tasks.append(dict(all_images[size*i:size*(i+1)]))
    tasks.append(dict(all_images[(CPUS-1)*size:]))
    # tasks = [dict(all_images[size*i:size*(i+1)]) for i in range(CPUS)]
    pool = Pool(processes=CPUS)
    pool.map(subprocess, tasks)

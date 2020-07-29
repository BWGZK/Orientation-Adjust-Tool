import tensorflow as tf
from skimage import transform
import numpy as np
import copy
import os
import sys

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class auto:
    def __init__(self):
        self.slices = 6
        self.imgSize = 256
        self.channels = [0.6, 0.8, 1.0]
        self.saveName = "tfrecord"
        self.directs = ["000", "001", "010", "011", "100", "101", "110", "111"]
        self.direct = ""

        head = tf.keras.Sequential()
        head.add(tf.keras.layers.Conv2D(32, (3, 3), input_shape=(self.imgSize, self.imgSize, 3)))
        head.add(tf.keras.layers.BatchNormalization())
        head.add(tf.keras.layers.Activation('relu'))
        head.add(tf.keras.layers.MaxPooling2D(pool_size=(2, 2)))
        head.add(tf.keras.layers.Conv2D(32, (3, 3)))
        head.add(tf.keras.layers.BatchNormalization())
        head.add(tf.keras.layers.Activation('relu'))
        head.add(tf.keras.layers.MaxPooling2D(pool_size=(2, 2)))
        head.add(tf.keras.layers.Conv2D(64, (3, 3)))
        head.add(tf.keras.layers.BatchNormalization())
        head.add(tf.keras.layers.Activation('relu'))
        head.add(tf.keras.layers.MaxPooling2D(pool_size=(2, 2)))
        average_pool = tf.keras.Sequential()
        average_pool.add(tf.keras.layers.AveragePooling2D())
        average_pool.add(tf.keras.layers.Flatten())
        average_pool.add(tf.keras.layers.Dense(8, activation='softmax'))
        self.model_C0 = tf.keras.Sequential([head, average_pool])
        self.model_C0.compile(optimizer=tf.keras.optimizers.Adam(),
                           loss='categorical_crossentropy', metrics=['accuracy'])
        self.model_C0.load_weights(resource_path("./data/orientation_C0.h5"))

        self.model_T2 = tf.keras.Sequential([head, average_pool])
        self.model_T2.compile(optimizer=tf.keras.optimizers.Adam(),
                           loss='categorical_crossentropy', metrics=['accuracy'])
        self.model_T2.load_weights(resource_path("./data/orientation_T2.h5"))

        self.model_LGE = tf.keras.Sequential([head, average_pool])
        self.model_LGE.compile(optimizer=tf.keras.optimizers.Adam(),
                           loss='categorical_crossentropy', metrics=['accuracy'])
        self.model_LGE.load_weights(resource_path("./data/orientation_LGE.h5"))

    # def __del__(self):
    #     print("finished")


    def predict(self, img, name):
        if name == "C0":
            self.preProcess(img, 6)
            self.model = self.model_C0
            # self.model.load_weights(resource_path("./data/orientation_C0.h5"))
        if name == "LGE":
            self.preProcess(img, 10)
            self.model = self.model_LGE
            # self.model.load_weights(resource_path("./data/orientation_LGE.h5"))
        if name == "T2":
            self.preProcess(img, 3)
            self.model  = self.model_T2
            # self.model.load_weights(resource_path("./data/orientation_T2.h5"))
        dataSet = self.get_batched_dataset()
        raw = self.model.predict(dataSet)
        predictions = np.array(raw).tolist()
        resultDic = dict()
        for i in range(self.slices):
            prediction = predictions[i]
            key = prediction.index(max(prediction))
            direct = self.directs[key]
            if direct in resultDic.keys():
                resultDic[direct] += 1
            else:
                resultDic[direct] = 1
        self.direct, count = sorted(list(resultDic.items()), key=lambda x: x[1], reverse=True)[0]
        return self.direct

    def adjust(self, img):
        target = img
        if self.direct == "":
            return 0, False
        os.remove("./"+self.saveName)
        if self.direct == "000":
            target = img  # 000 Target[x,y,z]=Source[x,y,z]
        if self.direct == "001":
            target = np.fliplr(img)  # 001 Target[x,y,z]=Source[sx-x,y,z]
        if self.direct == "010":
            target = np.flipud(img)  # 010 Target[x,y,z]=Source[x,sy-y,z]
        if self.direct == "011":
            target = np.flipud(np.fliplr(img))  # 011 Target[x,y,z]=Source[sx-x,sy-y,z]
        if self.direct == "100":
            target = img.transpose((1, 0, 2))  # 100 Target[x,y,z]=Source[y,x,z]
        if self.direct == "101":
            # 101 Target[x,y,z]=Source[sx-y,x,z] 110 Target[x,y,z]=Source[y,sy-x,z]
            # target = np.fliplr(img.transpose((1, 0, 2)))
            target = np.flipud(img.transpose((1, 0, 2)))
        if self.direct == "110":
            # 110 Target[x,y,z]=Source[y,sy-x,z] 101 Target[x,y,z]=Source[sx-y,x,z]
            # target = np.flipud(img.transpose((1, 0, 2)))
            target = np.fliplr(img.transpose((1, 0, 2)))
        if self.direct == "111":
            target = np.flipud(np.fliplr(img.transpose((1, 0, 2))))  # 111 Target[x,y,z]=Source[sx-y,sy-x,z]
        return target, True

    def preProcess(self, img, slices):
        self.slices = slices
        if min(img.shape) < self.slices:
            self.slices = min(img.shape)
        start = int((min(img.shape) - self.slices)/ 2)
        end = start + self.slices
        new_target = np.zeros((self.imgSize, self.imgSize, self.slices))
        for i in range(start, end, 1):
            data = self.histogram_equalization(img[:, :, i])
            new_target[:, :, i - start] = np.array(transform.resize(data, (self.imgSize, self.imgSize)))

        results = []
        for i in range(self.slices):
            result = np.zeros((self.imgSize, self.imgSize, len(self.channels)))
            for j in range(len(self.channels)):
                new_slice = copy.deepcopy(new_target[:, :, i])
                mask = self.channels[j] * new_slice.max()
                new_slice = np.where((new_slice >= mask), mask, new_slice)
                result[:, :, j] = new_slice / mask
            result = result.astype(np.uint8)
            results.append(result.tostring())
        with tf.io.TFRecordWriter(self.saveName) as writer:
            for result in results:
                features = self.create_features(result)
                writer.write(features.SerializeToString())

    def histogram_equalization(self, image, number_bins=256):
        image_histogram, bins = np.histogram(image.flatten(), number_bins, density=True)
        cdf = image_histogram.cumsum()
        cdf = 255 * cdf / cdf[-1]
        image_equalized = np.interp(image.flatten(), bins[:-1], cdf)
        return image_equalized.reshape(image.shape)

    def _bytes_feature(self, value):
        if isinstance(value, type(tf.constant(0))):
            value = value.numpy()
        return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

    def create_features(self, image_string):
        feature = {
            'image_raw': self._bytes_feature(image_string),
        }
        return tf.train.Example(features=tf.train.Features(feature=feature))

    def read_tfrecord(self, example):
        features = {
            'image_raw': tf.io.FixedLenFeature([], tf.string),
        }
        example = tf.io.parse_single_example(example, features)
        img = tf.io.decode_raw(example["image_raw"], tf.uint8)
        img = tf.cast(img, tf.float32)
        img = tf.reshape(img, (256, 256, 3))
        return img

    def get_batched_dataset(self):
        option_no_order = tf.data.Options()
        option_no_order.experimental_deterministic = False

        dataset = tf.data.Dataset.list_files(self.saveName)
        dataset = dataset.with_options(option_no_order)
        dataset = dataset.interleave(tf.data.TFRecordDataset, cycle_length=16, num_parallel_calls=10)
        dataset = dataset.map(self.read_tfrecord, num_parallel_calls=10)

        dataset = dataset.cache()
        dataset = dataset.shuffle(10)
        dataset = dataset.batch(1, drop_remainder=True)
        dataset = dataset.prefetch(10)
        return dataset

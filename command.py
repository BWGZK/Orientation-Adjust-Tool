import argparse
import time

from SimpleITK import GetArrayFromImage, ReadImage, WriteImage, GetImageFromArray
import os
import datetime
import numpy as np
import auto_adjust
from multiprocessing import Process


class command_run():
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-k', '--keep_header', help="don't adjust header", nargs='?', default='False', const="True")
        parser.add_argument('-f', '--batch_process', help="process files in a folder", nargs='?', default='False',
                            const="True")
        parser.add_argument('file_path', help='the open file path', type=str)
        parser.add_argument('-o', '--save_path', type=str, help="specify save path", nargs='?', default="")
        parser.add_argument('-c', '--type', type=str, help="specify MRI Image Type", nargs='?',
                            choices=["C0", "T2", "LGE"],
                            default="")
        args = parser.parse_args()
        self.piplines(args)

    def piplines(self, args):
        save_path = args.save_path
        if args.save_path == "":
            if args.batch_process == "True":
                components = [s for s in args.file_path.split("\\") if len(s) > 0]
                file_dir = "\\".join(components[0:-2])
                file_name = args.file_path.split("\\")[-1]
                new_file_name = file_name + "_adjusted"
                save_path = os.path.join(file_dir, new_file_name)
                if os.path.exists(save_path):
                    new_file_name = file_name + str(datetime.datetime.now())[0:9]
                    save_path = os.path.join(file_dir, new_file_name)

            else:
                file_path_flag = False
                components = [s for s in args.file_path.split("\\") if len(s) > 0]
                file_dir = "\\".join(components[0:-2])
                if ".nii.gz" in args.file_path:
                    new_file_name = args.file_path.replace(".nii.gz", "_adjusted.nii.gz")
                    save_path = os.path.join(file_dir, new_file_name)
                    if os.path.exists(save_path):
                        new_file_name = args.file_path.replace(".nii.gz",
                                                               "_adjusted_" + str(datetime.datetime.now()) + ".nii.gz")
                        save_path = os.path.join(file_dir, new_file_name)
                    file_path_flag = True
                if not file_path_flag and ".nii" in args.file_path:
                    new_file_name = args.file_path.replace(".nii", "_adjusted.nii")
                    save_path = os.path.join(file_dir, new_file_name)
                    if os.path.exists(save_path):
                        new_file_name = args.file_path.replace(".nii",
                                                               "_adjusted_" + str(datetime.datetime.now()) + ".nii")
                        save_path = os.path.join(file_dir, new_file_name)
                    file_path_flag = True
                if not file_path_flag and ".mha" in args.file_path:
                    new_file_name = args.file_path.replace(".mha", "_adjusted.mha")
                    save_path = os.path.join(file_dir, new_file_name)
                    if os.path.exists(save_path):
                        new_file_name = args.file_path.replace(".mha",
                                                               "_adjusted_" + str(datetime.datetime.now()) + ".mha")
                        save_path = os.path.join(file_dir, new_file_name)
                    file_path_flag = True
        else:
            file_path_flag = True

        if args.batch_process == "True" and not os.path.exists(save_path):
            os.makedirs(save_path)

        if args.batch_process == "True":
            file_paths = []
            for walkpath, subdirs, subfiles in os.walk(args.file_path):
                # supported format: ".nii.gz" ".mha" ".nii"
                subfiles = [s for s in subfiles if ".nii.gz" in s or ".mha" in s or ".nii" in s]
                for subfile in subfiles:
                    file_path = os.path.join(walkpath, subfile)
                    file_paths.append(file_path)
            p_list = []
            for file_path in file_paths:
                p = Process(target=self.wrapper, args=(args, save_path, file_path))
                p_list.append(p)
            for p in p_list:
                p.start()
                p.join()
            print('all files are processed.')

            if len(file_paths) == 0:
                print(
                    "Sorry, the folder not contain supported files, only the following formats are supported: nii.gz, mha, nii")
        else:
            if file_path_flag:
                print("save to: ", save_path)
                self.pipline(args, args.file_path, save_path)
            else:
                print("Sorry, only the following formats are supported: nii.gz, mha, nii")

    def wrapper(self, args, save_path, file_path):
        subfile = file_path.split("\\")[-1]
        self.pipline(args, file_path, os.path.join(save_path, subfile))

    def pipline(self, args, file_path, save_path):
        self.setUpParams(args, file_path, save_path)
        self.openfiles()
        self.predict()
        self.adjust()
        self.saveAs()
        # if os.path.exists(self.saveName):
        #     os.remove(self.saveName)
        time.sleep(1)

    def setUpParams(self, args, file_path, save_path):
        if args.keep_header == "True":
            self.keep_header = True
        else:
            self.keep_header = False
        self.save_path = save_path
        self.file_path = file_path
        self.name = args.type
        self.batch_process = args.batch_process

        self.imgIndex = 0
        self.imgDim = 1
        self.adjust_imgIndex = 0
        self.adjust_imgDim = 6
        self.img = np.zeros((1, 1, 1))
        self.adjust_img = np.zeros((1, 1, 1))
        self.direct = 1
        self.auto = auto_adjust.auto()
        self.adjusted = False
        self.isOpen = False
        self.predicted = False
        self.Orientation_predicted = ""
        self.saveName = "tfrecord"

    def openfiles(self):
        if self.file_path == "":
            return
        if self.name == "":
            if "T2" in self.file_path.split("/")[-1]:
                self.name = "T2"
            if "LGE" in self.file_path.split("/")[-1]:
                self.name = "LGE"
            if "C0" in self.file_path.split("/")[-1]:
                self.name = "C0"
            if self.name == "":
                self.name = "C0"

        itk_img = ReadImage(self.file_path)
        img = GetArrayFromImage(itk_img)
        self.spacing = itk_img.GetSpacing()
        self.direction = itk_img.GetDirection()
        # print("img:", self.file_path, "direction:", self.direction)
        self.origin = itk_img.GetOrigin()
        minDim = list(img.shape).index(min(img.shape))
        if minDim == 0:
            self.img = np.zeros((img.shape[1], img.shape[2], min(img.shape)))
            for i in range(min(img.shape)):
                self.img[:, :, i] = self.showRoate(img[i, :, :])
        if minDim == 1:
            self.img = np.zeros((img.shape[0], img.shape[2], min(img.shape)))
            for i in range(min(img.shape)):
                self.img[:, :, i] = img[:, i, :]
        if minDim == 2:
            self.img = img
        self.imgDim = self.img.shape[2]
        if self.imgDim >= 3:
            self.imgIndex = int(self.imgDim / 2 + 1)
        else:
            self.imgIndex = int(self.imgDim / 2)

        self.adjusted = False
        self.predicted = False
        self.isOpen = True

    def orientation_adjust(self):
        direction = np.reshape(np.array(list(self.direction)), (3, 3))
        if self.Orientation_predicted == "000":
            direction = direction  # 000 Target[x,y,z]=Source[x,y,z]
        if self.Orientation_predicted == "001":
            direction = np.fliplr(direction)  # 001 Target[x,y,z]=Source[sx-x,y,z]
        if self.Orientation_predicted == "010":
            direction = np.flipud(direction)  # 010 Target[x,y,z]=Source[x,sy-y,z]
        if self.Orientation_predicted == "011":
            direction = np.flipud(np.fliplr(direction))  # 011 Target[x,y,z]=Source[sx-x,sy-y,z]
        if self.Orientation_predicted == "100":
            direction = direction.transpose((1, 0, 2))  # 100 Target[x,y,z]=Source[y,x,z]
        if self.Orientation_predicted == "101":
            # 101 Target[x,y,z]=Source[sx-y,x,z] 110 Target[x,y,z]=Source[y,sy-x,z]
            # target = np.fliplr(img.transpose((1, 0, 2)))
            direction = np.flipud(direction.transpose((1, 0, 2)))
        if self.Orientation_predicted == "110":
            # 110 Target[x,y,z]=Source[y,sy-x,z] 101 Target[x,y,z]=Source[sx-y,x,z]
            # target = np.flipud(img.transpose((1, 0, 2)))
            direction = np.fliplr(direction.transpose((1, 0, 2)))
        if self.Orientation_predicted == "111":
            direction = np.flipud(
                np.fliplr(direction.transpose((1, 0, 2))))  # 111 Target[x,y,z]=Source[sx-y,sy-x,z]
        direction = tuple(np.reshape(direction, (9,)).tolist())
        return direction

    def saveAs(self):
        # set files
        if self.isOpen:
            if self.adjusted or self.Orientation_predicted == "000":
                savePath = self.save_path
                save_img = np.zeros((self.adjust_img.shape[2], self.adjust_img.shape[0], self.adjust_img.shape[1]))
                for i in range(self.adjust_img.shape[2]):
                    save_img[i, :, :] = self.showRoate(self.adjust_img[:, :, i])
                reply = self.keep_header
                if reply:
                    direction = self.direction
                else:
                    direction = self.orientation_adjust()
                img_save = GetImageFromArray(save_img)
                img_save.SetDirection(direction)
                img_save.SetOrigin(self.origin)
                img_save.SetSpacing(self.spacing)
                WriteImage(img_save, savePath)

    def predict(self):
        if self.isOpen:
            self.Orientation_predicted = self.auto.predict(self.img, self.name)
            self.adjusted = False
            if self.Orientation_predicted == "000":
                self.adjust_img = self.img

    def adjust(self):
        if self.isOpen:
            if not self.adjusted:
                if not self.predicted:
                    self.predict()
                self.adjust_img, predicted = self.auto.adjust(self.img)
                if not predicted:
                    self.predict()
                    self.adjust_img, predicted = self.auto.adjust(self.img)
                self.img = self.adjust_img
                self.adjusted = True
            else:
                pass

    def showRoate(self, img):
        if self.name == "C0" or self.name == "LGE":
            target = np.flipud(np.fliplr(img))
        if self.name == "T2":
            target = np.fliplr(img)
        return target


if __name__ == '__main__':
    p = Process(target=command_run)
    p.start()
    p.join()

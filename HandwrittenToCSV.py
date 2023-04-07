from PIL import Image
import numpy as np
import os
import csv


def createfilelist(mydir, fileformat='.PNG'):
    filelist = []
    print(mydir)
    for root, dirs, files in os.walk(mydir, topdown=False):
        for name in files:
            if name.endswith(fileformat):
                fullname = os.path.join(root, name)
                filelist.append(fullname)
    return filelist


myFileList = createfilelist('hw')
labellist = [[int(x[3])] for x in myFileList]

with open("img_labels.csv", 'a') as f:
    writer = csv.writer(f)
    for x in labellist:
        writer.writerow(x)


for file in myFileList:
    img_file = Image.open(file)
    width, height = img_file.size
    file_format = img_file.format
    mode = img_file.mode
    img_grey = img_file.convert('L')
    value = np.asarray(img_grey.getdata(), dtype=int).reshape((img_grey.size[1], img_grey.size[0]))
    value = value.flatten()

    with open("img_pixels.csv", 'a') as f:
        writer = csv.writer(f)
        writer.writerow(value)

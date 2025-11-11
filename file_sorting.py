# File sorting
# Description: I used Windows File History to backup a bunch of files on both my laptop and my PC
# BUT on my laptop I have over 200,000 folders of files that had names replaced by numbers and/or
# UTC dates because the names were too long. This is extremely frustrating as I have no idea what
# these files are. This code is an attempt to sort these files and remove whatever is unnecessary

import os
import shutil

SORT_FOLDER = 'E:/FileHistory/jeffr/QUICKSILVER/Data/$OF/'
NEW_DIR = 'E:/FileHistory/jeffr/QUICKSILVER/Data/Sorting_OF/'
if not os.path.isdir(NEW_DIR):
    os.mkdir(NEW_DIR)
# os.mkdir(SORT_FOLDER + 'NEW_FOLDER/')
# print(os.listdir(path=SORT_FOLDER))
dirs = os.listdir(path=SORT_FOLDER)
for dir in dirs:
    os.chdir(SORT_FOLDER + dir + '/')
    files = os.listdir('.')
    for file in files:
        if not os.path.isfile(NEW_DIR + file):
            shutil.copy(SORT_FOLDER + dir + '/' + file, NEW_DIR + file)
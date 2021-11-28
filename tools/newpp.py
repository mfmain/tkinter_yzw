#!/usr/bin/python

import os, sys, time, shutil
import exifread as exif
import argparse
# import tkinter as tk
# from tkinter.filedialog import askdirectory
# from tkinter_yzw.tk_tree import TkYzwFrameTree


class CSTA:
    def __init__(self):
        self.total = 0
        self.moved = 0
        self.removed = 0
        self.failed = 0
        self.ignored = 0

    def show(self):
        print("\ttotal:", self.total)
        print("\t移动:", self.moved)
        print("\t删除:", self.removed)
        print("\t忽略:", self.ignored)
        print("\t失败:", self.failed)


def opt_parse(argv):
    parser = argparse.ArgumentParser(description='gather photoes')
    parser.add_argument('srcdir',                  type=str,                  help='source dir')
    parser.add_argument('dstdir',                  type=str,                  help='target dir')
    parser.add_argument('cmpdir',                  type=str,                  help='compare dir')
    parser.add_argument("-v", "--verbose",         action="count", default=0, help="increase output verbosity")
    parser.add_argument("-n", "--dryrun",          action="store_true",       help="dry run")
    parser.add_argument("-k", "--keepsame",        action="store_true",       help="keep source if dst exists")
    parser.add_argument("-r", "--depth",           action="store_true",       help="no recursive")
    parser.add_argument("-c", "--content_compare", action="store_true",       help="compare whole content")
    return parser.parse_args(argv)


def t_filetime(filepath):
    state = os.stat(filepath)
    return time.strftime("%Y-%m-%d", time.localtime(state[-2]))


# filename without path
def t_filename(filename):
    if filename[:4] == 'VID_' and filename[-4:] == '.3gp':
        return filename[4:8] + '-' + filename[8:10] + '-' + filename[10:12]
    if filename[:4] == 'IMG_' and filename[-4:] == '.jpg':
        return filename[4:8] + '-' + filename[8:10] + '-' + filename[10:12]
    return None


def get_exif(filepath):
    with open(filepath, 'rb') as fd:
        return exif.process_file(fd)


def t_exif(exif, k):
    t = exif.get(k, None)
    if t: return str(t).replace(":", "-")[:10]
    return None


def move_photo_fd(srcdir, filename, dstpdir, t, tn):
    dstdir = dstpdir + "\\" + t
    filenamed = os.path.join(dstdir, filename)
    filename = os.path.join(srcdir, filename)  # full path filename
    print("\tmove %s %s %s" % (filename, dstdir, tn), end=" ")
    if is_same(filename, filenamed):
        print("same")
        if not opt.dryrun and not opt.keepsame: os.remove(filename)
        if not opt.keepsame: sta.removed += 1
        return

    if not opt.dryrun:
        if not os.path.exists(dstdir): os.mkdir(dstdir)
        try:
            shutil.move(filename, dstdir)
            sta.moved += 1
            # shutil.copy2(filename, dstdir)  # 用copy2会保留图片的原始属性
            # os.remove(filename)
            print("")
        except:
            sta.failed += 1
            print("failed")
    else:
        sta.moved += 1
        print("")


def move_photo_dd(srcdir, dstdir):
    for root, dirs, files in os.walk(srcdir, True):
        print ("目录" + root)
        for filename in files:
            sta.total += 1
            filepath = os.path.join(root, filename)
            e = filename[-4:].lower() # _, e = os.path.splitext(filename)
            if e.lower() not in ('.jpg','.png', '.3gp', '.mp4'):
                print("\t%s ignored" % filepath)
                sta.ignored += 1
                continue
            filepath = os.path.join(root, filename)
            exif = get_exif(filepath)
            tn = '原始时间'
            t = t_exif(exif, 'EXIF DateTimeOriginal')
            if not t:
                tn = '图片时间'
                t = t_exif(exif, 'Image DateTime')
            if not t:
                tn = '文件名时间'
                t = t_filename(filename)
            if not t:
                tn = '文件时间戳'
                t = t_filetime(filepath)
            move_photo_fd(root, filename, dstdir, t, tn)
        if not opt.depth: break # 不遍历子目录


def fc(fn1, fn2, bs = 102400):
    try:
        with open(fn1, "rb") as f1, open(fn2, "rb") as f2:
            while True:
                try:
                    b1 = f1.read(bs)
                    b2 = f2.read(bs)
                except:
                    return False
                if not b1 and not b2: return True
                # print("#", len(b1), len(b2))
                if b1 != b2: return False
    except FileNotFoundError:
        return False


def is_same(fn1, fn2):
    try: st1 = os.stat(fn1)
    except: return False
    try: st2 = os.stat(fn2)
    except: return False
    # print(st1.st_ino, st2.st_ino)
    if st1.st_ino == st2.st_ino:
        print(" idential file, abort!")
        exit(1)
    if opt.content_compare: return fc(fn1, fn2)
    if st1.st_size == st2.st_size: return True
    return False


# class Ui:
#     def __init__(self):
#         self.root = tk.Tk()
#         self.root.title("newpp")
#         self.root.geometry('800x800+200+200')  # yscroll=True时需要设，否则窗口很小
#         fr = tk.Frame(self.root)
#
#
#
#         column_list = [("", 180), (",w", "100,w+")]
#         ui_tree = TkYzwFrameTree(self.root, column_list, scroll="xy", height=10)
#         # show="tree" 无抬头栏；  show="headings" 有抬头
#         self.ui_tree = ui_tree
#         # ui_tree.wx.column('#0', stretch="no", minwidth=0, width=0)
#
#         # for path in ["状态", "当前任务", "已完成任务"][::-1] :
#         #     self.ui_tree.easy_item(path, text=path, open=True, tags="h1")
#         #
#         # self.ui_tree.easy_item("状态/连接信息", value="xxx")
#         ui_tree.pack(side="top", fill="both", expand=1)
#
#         self.on_timer()


if __name__=="__main__":
    sta = CSTA()
    opt = opt_parse(sys.argv[1:])
    if opt.verbose: print(opt)
    move_photo_dd(opt.srcdir, opt.dstdir)
    sta.show()

    # input("OK")

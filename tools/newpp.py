# coding： gbk

USAGE = """
USAGE: newpp.py [options] <src> <dst>:
  依次使用"原始时间", "图片时间", "文件名中的时间", "文件时间戳"的优先级提取src目录下的图片文件的"目标文件夹"
  如果f"dst/{目的文件夹}"下, 已经存在同名文件, 则进行比较, 相同则归类到"same"分支下面
  -t, --todir 另行指定拷贝和移动的目标文件夹
  -k, --keepsame 如果目标文件已存在仍然保留源文件
  -r, --depth 遍历子目录
  -c, --content_compare 逐字节对比src和dst下同名文件是否相同, 默认只要文件大小相同就认为相同
  -v, --verbose 打印详细日志
  -n, --dryrun 不实际执行拷贝和移动操作 
"""

# DEBUGME:
#    --todir E:\w\newpp2 J:\DCIM\100CANON \\192.168.1.111\e\w\newpp
#    --todir \\192.168.1.111\e\w\newpp.to J:\DCIM\100CANON \\192.168.1.111\e\w\newpp

import os, sys, time, shutil
import exifread as exif
import argparse
import threading
import traceback
from collections import defaultdict
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter_yzw.tk_tree import TkYzwFrameTree
from tkinter_yzw.tk_mainui import TkYzwMainUi, TkYzwMainUiApp
import win32api
import subprocess
# from PIL import Image
# import cv2


def img_show(fn):
    win32api.ShellExecute(0, 'open', fn, None, '.', 0)


# def img_show_pil(fn):
#     im = Image.open(fn)
#     im.show()
#
#
# def img_show_cv2(fn):
#     img = cv2.imread(fn)
#     cv2.imshow("Image", img)


def img_show_os(fn):
    # os.execv(r"C:\Program Files (x86)\XnView\xnview.exe", ("xnview.exe", fn))
    # os.system(fr'"C:\Program Files (x86)\XnView\xnview.exe" "{fn}"')
    win32api.ShellExecute(0, 'open', r"C:\Program Files (x86)\XnView\xnview.exe", fn, '', 1)


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
    parser.error = lambda msg: (print(USAGE), sys.exit(1))
    parser.add_argument('srcdir',                  type=str,                  help='compare srcdir')
    parser.add_argument('dstdir',                  type=str,                  help='compare dstdir')
    parser.add_argument('-t', "--todir",           type=str,                  help='copy/move to dir')
    parser.add_argument("-v", "--verbose",         action="count", default=0, help="increase output verbosity")
    parser.add_argument("-n", "--dryrun",          action="store_true",       help="dry run")
    parser.add_argument("-k", "--keepsame",        action="store_true",       help="keep source if dst exists")
    parser.add_argument("-r", "--depth",           action="store_true",       help="recursive")
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


class PhotoItem:
    def __init__(self, root:str, filename:str):
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

        self.srcdir = root            # 源目录
        self.filename = filename      # 文件名，不带目录
        self.filepath_src = filepath  # 源文件名，全路径
        self.tn = tn                  # 图片按时间的分类
        self.t = t                    # 图片的日期，用于新建子目录
        self.dstdir = opt.dstdir + "\\" + t   # 用于比较的目的目录
        self.filepath_dst = os.path.join(self.dstdir, filename)
        self.todir = opt.todir  + "\\" + t    # 用于拷贝或移动的目的目录
        self.filepath_to = os.path.join(self.todir, filename)


def iter_srcdir(srcdir):
    """generator, 遍历源图片"""
    for root, dirs, files in os.walk(srcdir, True):
        print ("目录" + root)
        for filename in files:
            sta.total += 1
            e = filename[-4:].lower() # _, e = os.path.splitext(filename)
            if e.lower() not in ('.jpg','.png', '.3gp', '.mp4'):
                # print(f"\t{root} {filename} ignored")
                sta.ignored += 1
                continue
            #move_photo_fd(filepath, filename, t, tn)
            yield PhotoItem(root, filename)
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


class MainUi(TkYzwMainUi):
    def __init__(self):
        super().__init__(title="newpp", geometry='800x500+200+200')
        w = TkYzwFrameTree(self.root, column_list=[("源文件,w", "300,w"), ("目的文件夹,w", "100,w+")], scroll="xy", height=10,
                                 command=lambda iid, event: self.on_callback("tree_command", iid, event))
        w.pack(side="top", fill="both", expand=1)
        self.ui_tree = w
        self.ui_tree.bind("<Button-3>", lambda event: self.on_callback("tree_menu", event))

        self.ui_tree.easy_insert("", "原始时间", index="end", open=True, tags="h1")
        self.ui_tree.easy_insert("", "图片时间", index="end", open=True, tags="h1")
        self.ui_tree.easy_insert("", "文件名时间", index="end", open=True, tags="h1")
        self.ui_tree.easy_insert("", "文件时间戳", index="end", open=True, tags="h1")
        self.ui_tree.easy_insert("", "same", index="end", open=False, tags="h1")


class MainApp(TkYzwMainUiApp):
    def __init__(self, mainui:TkYzwMainUi):
        super().__init__(mainui)
        self.d_tn_cnt = defaultdict(int)
        self.d_iid_pi = dict()
        threading.Thread(target=self.main_newpp, args=(), daemon=True).start()

    def main_newpp(self):
        for pi in iter_srcdir(opt.srcdir):
            # dstdir = opt.dstdir + "\\" + pi.t
            # filepath_dst = os.path.join(dstdir, pi.filename)
            if is_same(pi.filepath_src, pi.filepath_dst):
                pi.tn = "same"
            self.d_tn_cnt[pi.tn] += 1
            iid = f"{pi.tn}/{pi.filepath_src}"
            self.d_iid_pi[iid] = pi
            mainui.ui_tree.easy_item(pi.tn, text=f"{pi.tn}({self.d_tn_cnt[pi.tn]})")
            # mainui.ui_tree.easy_insert(pi.tn, pi.filepath_src, value=(pi.dstdir,))
            mainui.ui_tree.easy_item(iid, value=(pi.dstdir,))
        print("done")

    def on_ui_tree_command(self, iid, event):
        print(f"on_ui_tree_command: iid={iid}, event={event}")
        try:
            tn, filepath_src = iid.split("/", maxsplit=1)
            print(f"open {repr(filepath_src)}")
        except:
            return

        print("img_show", filepath_src)
        img_show(filepath_src)

    def on_ui_tree_menu(self, event):
        mainui = self.mainui
        # print(f"on_ui_tree_menu: event={event}")
        a_iid = mainui.ui_tree.wx.selection()
        # print(a_iid)
        if not a_iid: return
        menubar = tk.Menu(self.mainui.ui_tree)
        menubar.add_command(label="copy to", command=lambda : mainui.on_callback("tree_copy_to", a_iid))
        menubar.add_command(label="move to", command=lambda: mainui.on_callback("tree_move_to", a_iid))
        menubar.add_command(label="delete", command=lambda: mainui.on_callback("tree_delete", a_iid))
        menubar.add_command(label="explorer", command=lambda: mainui.on_callback("tree_explorer", a_iid[0]))
        menubar.post(event.x_root, event.y_root)

    def _gen_fastcopy_srcfile(self, a_iid):
        f = open("newpp_fastcopy.txt", "w", encoding="gbk")
        for iid in a_iid:
            _, fn = iid.split("/", maxsplit=1)
            print(fn, file=f)
        f.close()

    def do_fastcopy(self, cmd:str, a_iid):
        # C:\Users\yzw\FastCopy\FastCopy.exe
        # https://fastcopy.jp/help/fastcopy_eng.htm#cmdline
        #    /cmd=diff
        #    /cmd=move
        #    /cmd=delete
        #    /auto_close	Close automatically after execution is finished with no errors.
        #    /estimate	Estimate complete time.(to disable, /estimate=FALSE)
        #    /no_exec
        self._gen_fastcopy_srcfile(a_iid)
        fastcopycmd = fr'C:\Users\yzw\FastCopy\FastCopy.exe /cmd={cmd} /estimate /no_exec /srcfile=newpp_fastcopy.txt'
        if opt.todir:
            fastcopycmd += f' /to={opt.todir}\\'
        else:
            fastcopycmd += f' /to={opt.dstdir}\\'
        subprocess.call(fastcopycmd)

    def on_ui_tree_copy_to(self, a_iid):
        print("on_ui_tree_copy_to", a_iid)
        # self.do_fastcopy("diff", a_iid)
        for iid in a_iid:
            pi = self.d_iid_pi[iid]
            print(f"copy {pi.filepath_src} {pi.todir}")
            if not os.path.exists(pi.todir): os.mkdir(pi.todir)
            try:
                shutil.copy2(pi.filepath_src, pi.todir)  # 用copy2会保留图片的原始属性
            except:
                traceback.print_exc()

    def on_ui_tree_move_to(self, a_iid):
        print("on_ui_tree_move_to", a_iid)
        # self.do_fastcopy("move", a_iid)
        for iid in a_iid:
            pi = self.d_iid_pi[iid]
            print(f"move {pi.filepath_src} {pi.todir}")
            if not os.path.exists(pi.todir): os.mkdir(pi.todir)
            try:
                shutil.move(pi.filepath_src, pi.todir)
            except OSError as e:
                # Destination path  already exists
                print(e)

            mainui.ui_tree.delete(iid)

    def on_ui_tree_delete(self, a_iid):
        print("on_ui_tree_delete", a_iid)
        # self.do_fastcopy("delete", a_iid)
        for iid in a_iid:
            pi = self.d_iid_pi[iid]
            print(f"del {pi.filepath_src}")
            os.unlink(pi.filepath_src)
            mainui.ui_tree.delete(iid)

    def on_ui_tree_explorer(self, iid):
        print("on_ui_tree_explorer", iid)
        tn, fn = iid.split("/", maxsplit=1)
        subprocess.call(fr'explorer /select,"{fn}"')

    def on_mainq(self, msgtype, *argv):
        print(f"{msgtype} {argv}")


if __name__=="__main__":
    sta = CSTA()
    opt = opt_parse(sys.argv[1:])
    # opt.dryrun = 1

    # main_newpp(opt.srcdir, opt.dstdir)

    mainui = MainUi()
    mainq = mainui.mainq
    mainapp = MainApp(mainui)
    mainui.run()

    sta.show()

# coding: gbk

# pyinstaller -F -w --exclude numpy ulogview.py
# DEBUG_ARG: -f ulogview_sample.log -l d:\^\ulogview.log
#            -f D:\tx\src\frpy\py\robot_rmf_7808.log


import sys
import os
import time
import queue
import socket
import threading
import argparse
import tkinter as tk
from tkinter_yzw.tk_tree import TkYzwFrameTree


class MyGlobals():
    def __init__(self):
        self.q = queue.Queue()
        self.addr_cnt = 0  # len(d_addr_rootpath)
        self.d_addr_rootpath = dict()

    def root_path_get(self, addr):
        """  根据来源地址addr决定根路径是谁， rootpath_是rootpath加上目录分隔符/, 这个冗余仅仅是为了性能优化 """
        rootpath, rootpath_ = self.d_addr_rootpath.get(addr, (None, None))
        if rootpath is None:
            self.addr_cnt += 1
            rootpath  = "[%d]" % self.addr_cnt
            rootpath_ = rootpath + '/'
            self.d_addr_rootpath[addr] = (rootpath, rootpath_)
        return rootpath, rootpath_


def q_nonblock_polling(q):
    a = []
    while 1:
        try:
            x = q.get(block=False)  # x = (addr, msg)
            a.append(x)
        except queue.Empty:
            return a


class ThreadInputFile(threading.Thread):
    """ 从文件中读取,转发到queue """
    def __init__(self, q:queue.Queue, fn:str, encoding="gbk", polltv=0.3):
        threading.Thread.__init__(self)
        self.daemon = True
        self.q = q
        self.fn = fn
        self.encoding = encoding
        self.polltv = polltv

    def run(self):
        fn = self.fn
        file = open(fn, "rb")
        encoding = self.encoding
        polltv = self.polltv
        line = b""
        st = os.stat(self.fn)
        # st_ino = st.st_ino
        st_size = 0
        while True:
            line_ = file.readline()
            print("readline %r" % line_)
            if line_:
                line += line_
                if line[-1] == 10:  # b"\n"
                    msg = line.decode(encoding).rstrip()  # strip tailing \r\n
                    if log: print(msg, file=log, flush=True)
                    self.q.put((fn, msg))
                    line = b""
                    continue

            # read nothing
            st = os.stat(self.fn)
            if st.st_size < st_size or st.st_nlink < 1:
                print("file rewinded, reopen it")
                file = open(fn, "rb")
                line = b""
            st_size = st.st_size
            time.sleep(args.polltv)


class ThreadInputUdp(threading.Thread):
    """ 接收UDP,转发到queue """
    def __init__(self, q:queue.Queue, host:str, port:int, encoding="gbk"):
        threading.Thread.__init__(self)
        self.daemon = True
        self.q = q
        self.encoding = encoding
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))

    def run(self):
        encoding = self.encoding
        while True:
            data, addr = self.sock.recvfrom(8192)
            # print(addr, data)
            msg = data.decode(encoding)
            if log: print(msg, file=log, flush=True)
            self.q.put((addr, msg))


class Ui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ulogview")
        self.root.geometry('800x800+200+200') # yscroll=True时需要设，否则窗口很小
        fr = tk.Frame(self.root)

        column_list = [("", 180), (",w", "100,w+")]
        ui_tree = TkYzwFrameTree(self.root, column_list, scroll="xy", height=10)
        # show="tree" 无抬头栏；  show="headings" 有抬头
        self.ui_tree = ui_tree
        # ui_tree.wx.column('#0', stretch="no", minwidth=0, width=0)

        # for path in ["状态", "当前任务", "已完成任务"][::-1] :
        #     self.ui_tree.easy_item(path, text=path, open=True, tags="h1")
        #
        # self.ui_tree.easy_item("状态/连接信息", value="xxx")
        ui_tree.pack(side="top", fill="both", expand=1)

        self.on_timer()


    def on_timer(self):
        for addr, x in q_nonblock_polling(g.q):
            rootpath, rootpath_ = g.root_path_get(addr)
            if self.ui_tree.treecmd(rootpath, rootpath_, x): continue
            action, x_ = x[0], x[1:]
            if action == 't':
                # title for rootpath
                g.d_addr_rootpath[addr] = (x_, x_ + '/')
            else:
                pass

        self.root.after(100, self.on_timer)


def _getopt():
    argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description='ulogview')
    parser.add_argument('-f', '--file', type=str, default="", help='load from logfile')
    parser.add_argument('-u', '--udp', type=int, default=17878, help='listen on udp port')
    parser.add_argument('-l', '--log', type=str, default="", help='write to logfile')
    parser.add_argument('--source_encoding', type=str, default="gbk", help='source(file/udp) encoding')
    parser.add_argument('--log_encoding', type=str, default="gbk", help='write logfile encoding')
    parser.add_argument('--polltv', type=float, default=0.3, help='write logfile encoding')

    return parser.parse_args(argv)


args = _getopt()
print(args)
g = MyGlobals()
if args.log:
    log = open(args.log, "w", encoding=args.log_encoding)
else:
    log = None

if args.file:
    # D:\tx\src\frpy\py\robot_rmf_7808.log
    # ulogview_sample.log
    ThreadInputFile(g.q, fn=args.file, encoding=args.source_encoding).start()
else:
    ThreadInputUdp(g.q, host="0.0.0.0", port=args.udp, encoding=args.source_encoding).start()


ui = Ui()
ui.root.mainloop()

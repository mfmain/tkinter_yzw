# coding: gbk

# pyinstaller -F -w --exclude numpy ulogd.py

import sys
import time
import queue
import socket
import threading
import tkinter as tk
from tkinter_yzw.tk_tree import TkYzwFrameTree
import win32clipboard
import win32con


def clip_copy(msg):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_TEXT, msg.encode("gbk"))
    win32clipboard.CloseClipboard()


class MyGlobals():
    def __init__(self):
        self.q = queue.Queue()
        self.addr_cnt = 0  # len(d_addr_rootpath)
        self.d_addr_rootpath = dict()

    def root_path_get(self, addr):
        rootpath, rootpath_ = self.d_addr_rootpath.get(addr, (None, None))
        if rootpath is None:
            self.addr_cnt += 1
            rootpath  = "[%d]" % self.addr_cnt
            rootpath_ = rootpath + '/'
            self.d_addr_rootpath[addr] = (rootpath, rootpath_)
        return rootpath, rootpath_


def list_get(a:list, i:int, default:any):
    if i < 0 or i >= len(a):
        return default
    else:
        return a[i]


def q_nonblock_polling(q):
    a = []
    while 1:
        try:
            x = q.get(block=False)  # x = (addr, msg)
            a.append(x)
        except queue.Empty:
            return a


class ThreadUdp2Queue(threading.Thread):
    """ ����UDP,ת����queue """
    def __init__(self, q:queue.Queue, host:str, port:int):
        threading.Thread.__init__(self)
        self.daemon = True
        self.q = q
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))

    def run(self):
        while True:
            data, addr = self.sock.recvfrom(8192)
            print(addr, data)
            self.q.put((addr, data.decode("gbk")))


class Ui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ulogd")
        self.root.geometry('800x500+200+200') # yscroll=Trueʱ��Ҫ�裬���򴰿ں�С
        fr = tk.Frame(self.root)

        column_list = [("", 120), (",w", "100,w+")]
        ui_tree = TkYzwFrameTree(self.root, column_list, scroll="xy", height=10)
        # show="tree" ��̧ͷ����  show="headings" ��̧ͷ
        self.ui_tree = ui_tree
        # ui_tree.wx.column('#0', stretch="no", minwidth=0, width=0)

        # for path in ["״̬", "��ǰ����", "���������"][::-1] :
        #     self.ui_tree.easy_item(path, text=path, open=True, tags="h1")
        #
        # self.ui_tree.easy_item("״̬/������Ϣ", value="xxx")
        ui_tree.pack(side="top", fill="both", expand=1)
        ui_tree.bind("x", self.on_key_x)
        ui_tree.bind("X", self.on_key_X)
        ui_tree.bind("<Control-c>", self.on_key_ctrl_c)

        self.on_timer()

    def on_key_X(self, _):
        self.ui_tree.do_clear()

    def on_key_x(self, _):
        self.ui_tree.do_deltree_selected()

    def on_key_ctrl_c(self, _):
        a = self.ui_tree.wx.selection()
        a_msg = []
        for iid in a:
            values = self.ui_tree.wx.item(iid, 'values')
            a_msg.append("%s: %s" % (iid, ','.join(values)))
        clip_copy('\n'.join(a_msg))

    def on_timer(self):
        for addr, x in q_nonblock_polling(g.q):
            # t title            # ����root�ڵ���ʾ���ı�
            # X                  # clear all
            # xaaa/bbb           # deltree aaa/bbb

            # rxxx/yyy msg       # ����·��xxx/yyy��msg, ���������,�����
            # Rxxx/yyy msg       # R,r����������r��ͷ������,R��β������,�����÷���ͬ

            # ixxx yyy:text msg  # ��·��xxx��������ӽڵ�yyy, ð�ź���Ϊ�ڵ�����ʾ���ı�(��ȱʡʹ��yyy)
            # Ixxx yyy:text msg  # I, i����������i��ͷ������,I��β������,�����÷���ͬ
            # ixxx yyy      msg  # ��·��xxx��������ӽڵ�yyy, �ڵ�����ʾ���ı�Ϊyyy
            # ixxx :text    msg  # ��·��xxx������������ڵ�(ϵͳ�Զ��ṩ), ð�ź���Ϊ�ڵ�����ʾ���ı�
            # ixxx :<ts>    msg  # ��·��xxx������������ڵ�(ϵͳ�Զ��ṩ), �ڵ�����ʾʱ���

            # �߼�����:
            # `<exec_source_code>  # ֱ�ӵ���self.ui_tree.<exec_source_code>
            # `easy_inert(path, _iid, index=0...)

            rootpath, rootpath_ = g.root_path_get(addr)
            action, x_ = x[0], x[1:]
            if action == 'r':
                a = x_.split(maxsplit=1)
                relpath = a[0]
                if relpath == '.':
                    self.ui_tree.easy_item(rootpath, values=(list_get(a, 1, ""),))
                else:
                    self.ui_tree.easy_item(rootpath_ + relpath, values=(list_get(a, 1, ""),))
            elif action == 'R':
                a = x_.split(maxsplit=1)
                self.ui_tree.easy_item(rootpath_+a[0], index="end", values=(list_get(a, 1, ""),))
            elif action == 'i':
                a = x_.split(maxsplit=2)
                iid_text = list_get(a, 1, "").split(":")
                _iid = list_get(iid_text, 0, "")
                text = list_get(iid_text, 1, "")
                if text == '<ts>': text = time.strftime("%H:%M:%S")
                if not text: text = _iid
                if not _iid: _iid = None
                values = (list_get(a, 2, ""),)
                self.ui_tree.easy_insert(rootpath_+a[0], _iid=_iid, text=text, values=values)
            elif action == 'I':
                a = x_.split(maxsplit=2)
                iid_text = list_get(a, 1, "").split(":")
                _iid = list_get(iid_text, 0, "")
                text = list_get(iid_text, 1, "")
                if text == '<ts>': text = time.strftime("%H:%M:%S")
                if not text: text = _iid
                if not _iid: _iid = None
                values = (list_get(a, 2, ""),)
                self.ui_tree.easy_insert(rootpath_+a[0], index="end", _iid=_iid, text=text, values=values)
            elif action == 'X':
                self.ui_tree.do_clear()
            elif action == 'x':
                if x_ == '.':
                    self.ui_tree.do_deltree(rootpath)
                else:
                    self.ui_tree.do_deltree(rootpath_ + x_)
            elif action == 't':
                # title for rootpath
                g.d_addr_rootpath[addr] = (x_, x_ + '/')
            elif action == '`':
                try:
                    exec("self.ui_tree." + x_)
                except:
                    pass
            else:
                pass

        self.root.after(100, self.on_timer)


if len(sys.argv) < 2:
    # print("Usage: %s listen_port" % sys.argv[0])
    listen_port = 17878
else:
    listen_port = int(sys.argv[1])

g = MyGlobals()
ThreadUdp2Queue(g.q, host="0.0.0.0", port=listen_port).start()
ui = Ui()
ui.root.mainloop()
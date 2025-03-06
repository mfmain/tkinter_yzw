# coding: gbk

# py3xcli & pyinstaller -F -w --exclude numpy ulogview.py & copy dist\ulogview.exe d:\s\bin /y
# py3xcli & pyinstaller -F --exclude numpy ulogview.py & copy dist\ulogview.exe d:\s\bin\ulogview_cons.exe /y
# DEBUG_ARG: -f ulogview_sample.log -l d:\^\ulogview.log
#            -f D:\tx\src\frpy\py\robot_rmf_7808.log
#            -u 17878 缺省


import sys
import os
import time
import queue
import socket
import threading
import argparse
import tkinter as tk
from tkinter_yzw.tk_tree import TkYzwFrameTree
from tkinter.messagebox import showinfo

# if sys.platform == 'win32':
#     CRLF = b'\r\n'
#     CRLFLEN = 2
# else:
#     CRLF = b'\n'
#     CRLFLEN = 1

# windows下也可能通过sshfs读取linux文件, 我糊涂了, 所以不要区分CRLF为妙
CRLF = b'\n'
CRLFLEN = 1


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
        self.split_lines_buf = b""

    def split_lines(self, bufnew:bytes):
        self.split_lines_buf += bufnew
        rra = []
        pstart = 0
        while 1:
            npos = self.split_lines_buf.find(CRLF, pstart)  # index?
            if npos < 0:
                self.split_lines_buf = self.split_lines_buf[pstart:]
                return rra
            else:
                rra.append(self.split_lines_buf[pstart:npos])
                pstart = npos + CRLFLEN

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
            buf = file.read()
            if buf:
                print(f"read {len(buf)}")
                a_line = self.split_lines(buf)
                for line in a_line:
                    # print(line)
                    # msg = line.rstrip().decode(encoding)
                    msg = line.decode(encoding)  # 没有strip掉\r也行, 提高点性能
                    if log: print(msg, file=log, flush=True)
                    self.q.put((fn, msg))

            # read nothing
            st = os.stat(self.fn)
            if st.st_size < st_size or st.st_nlink < 1:
                print("file rewinded, reopen it")
                file = open(fn, "rb")
                self.split_lines_buf = b""
            st_size = st.st_size
            time.sleep(sysarg.polltv)


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


class MainUi:
    def __init__(self, title="ulogview"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry('800x800+200+200') # yscroll=True时需要设，否则窗口很小
        fr = tk.Frame(self.root)

        column_list = [(",w", "180,w"), (",w", "100,w+")]
        ui_tree = TkYzwFrameTree(self.root, column_list, scroll="xy", height=10)  # , dnd="move"
        # show="tree" 无抬头栏；  show="headings" 有抬头
        self.ui_tree = ui_tree
        # ui_tree.wx.column('#0', stretch="no", minwidth=0, width=0)

        # for path in ["状态", "当前任务", "已完成任务"][::-1] :
        #     self.ui_tree.easy_item(path, text=path, open=True, tags="h1")
        #
        # self.ui_tree.easy_item("状态/连接信息", value="xxx")
        ui_tree.pack(side="top", fill="both", expand=1)

        menu = tk.Menu(ui_tree.wx, tearoff=0)
        menu.add_command(label="Delete", command=self.context_menu_delete)
        menu.add_command(label="Find", command=self.context_menu_find)
        ui_tree.wx.bind("<Button-3>", lambda event: menu.post(event.x_root, event.y_root))
        self.context_menu = menu

        self.on_timer()

    def context_menu_delete(self):
        tree = self.ui_tree.wx
        selected_item = tree.selection()
        if selected_item:
            tree.delete(selected_item)

    def context_menu_find_next(self, what:str, with_node:int, with_content:int):
        tree = self.ui_tree.wx
        current_item = tree.selection()
        if not current_item:
            current_item = tree.get_children()[0]
        else:
            current_item = current_item[0]

        while current_item:
            # 尝试找到第一个子节点
            first_child = tree.get_children(current_item)
            if first_child:
                current_item = first_child[0]
            else:
                # 如果没有子节点，尝试找到下一个兄弟节点
                next_item = tree.next(current_item)
                if next_item:
                    current_item = next_item
                else:
                    # 如果没有下一个兄弟节点，尝试找到父节点的下一个兄弟节点
                    parent_item = tree.parent(current_item)
                    while parent_item:
                        next_parent = tree.next(parent_item)
                        if next_parent:
                            current_item = next_parent
                            break
                        parent_item = tree.parent(parent_item)
                    else:
                        # 如果没有父节点的下一个兄弟节点，结束搜索
                        current_item = None

            if current_item:
                found = False
                if with_node:
                    item_text = tree.item(current_item, "text")
                    found = item_text and what.lower() in item_text.lower()
                if not found and with_content:
                    item_values = tree.item(current_item, "values")
                    found = item_values and any(what.lower() in value.lower() for value in item_values)

                if found:
                    tree.selection_set(current_item)
                    tree.focus(current_item)
                    tree.see(current_item)
                    break

        if not current_item:
            print("No more matching items found.")
            showinfo("Search", "No more matching items found.")

    def context_menu_find(self):
        tree = self.ui_tree.wx
        selected_item = tree.selection()
        if selected_item:
            # 创建一个简单的编辑对话框
            find_dialog = tk.Toplevel()
            find_dialog.title("Find")

            wx_what_entry = tk.Entry(find_dialog)
            wx_what_entry.pack(side="top")

            fr = tk.Frame(find_dialog)
            wxv_check1 = tk.IntVar(value=1)
            tk.Checkbutton(fr, text="node", variable=wxv_check1).pack(side="left")
            wxv_check2 = tk.IntVar(value=0)
            tk.Checkbutton(fr, text="content", variable=wxv_check2).pack(side="left")
            fr.pack(side="top")

            search_button = tk.Button(find_dialog, text="Search",
                                    command=lambda: self.context_menu_find_next(wx_what_entry.get(), wxv_check1.get(), wxv_check2.get()))
            search_button.pack(side="top")
            wx_what_entry.focus_set()

    def on_timer(self):
        for addr, x in q_nonblock_polling(g.q):
            rootpath, rootpath_ = g.root_path_get(addr)
            if self.ui_tree.treecmd(x, rootpath, rootpath_): continue
            action, x_ = x[0], x[1:]
            if action == 't':
                # title for rootpath
                g.d_addr_rootpath[addr] = (x_, x_ + '/')
            else:
                pass

        self.root.after(100, self.on_timer)


class _DebugmeSplitLines:
    def __init__(self):
        self.gen_line_buf = b""

    def split_lines(self, bufnew:bytes):
        self.gen_line_buf += bufnew
        rra = []
        pstart = 0
        while 1:
            npos = self.gen_line_buf.find(b'\n', pstart)  # index?
            if npos < 0:
                self.gen_line_buf = self.gen_line_buf[pstart:]
                return rra
            else:
                rra.append(self.gen_line_buf[pstart:npos])
                pstart = npos + 1

    def test1(self):
        a = self.split_lines(b"111\n222\n333\n444")
        print(a)
        a = self.split_lines(b"aaa\nbbb\nccc\nddd")
        print(a)
        a = self.split_lines(b"AAA")
        print(a)
        a = self.split_lines(b"111\n222")
        print(a)
        a = self.split_lines(b"aaa\nbbb\n")
        print(a)
        a = self.split_lines(b"ccc\n")
        print(a)

    def test2(self):
        f = open(r"c:\s\log\xxx.log", "rb")
        t1 = time.perf_counter()
        while 1:
            buf = f.read(10000)
            if not buf: break
            a = self.split_lines(buf)
            print(len(a))

        t2 = time.perf_counter()
        print(t2 - t1)


def _getopt():
    argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description='ulogview')
    parser.add_argument('-f', '--file', type=str, default="", help='load from logfile')
    parser.add_argument('-u', '--udp', type=int, default=17878, help='listen on udp port')
    parser.add_argument('-l', '--log', type=str, default="", help='write to logfile')
    parser.add_argument("-n", "--with_lineno", action="store_true", default=False, help="parse lineno")
    parser.add_argument('--source_encoding', type=str, default="gbk", help='source(file/udp) encoding')
    parser.add_argument('--log_encoding', type=str, default="gbk", help='write logfile encoding')
    parser.add_argument('--polltv', type=float, default=0.3, help='write logfile encoding')

    return parser.parse_args(argv)


sysarg = _getopt()
print(sysarg)
g = MyGlobals()
if sysarg.log:
    log = open(sysarg.log, "w", encoding=sysarg.log_encoding)
else:
    log = None

if sysarg.file:
    # D:\tx\src\frpy\py\robot_rmf_7808.log
    # ulogview_sample.log
    ThreadInputFile(g.q, fn=sysarg.file, encoding=sysarg.source_encoding).start()
    mainui = MainUi(title=sysarg.file)

else:
    ThreadInputUdp(g.q, host="0.0.0.0", port=sysarg.udp, encoding=sysarg.source_encoding).start()
    mainui = MainUi(title=sysarg.udp)


mainui.root.mainloop()

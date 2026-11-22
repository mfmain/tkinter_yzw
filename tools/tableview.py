# coding: gbk

import sys, os, time
from datetime import date
import win32clipboard
import win32con
import pprint
import traceback

import sys
import os
import time
import queue
import socket
import threading
import argparse
import tkinter as tk
import tkinter_yzw as tky
from tkinter_yzw.tk_table import *

import yaml
import redis


class DictObj:
    def __init__(self, d:dict):
        if d is not None:
            self.__dict__ = d.copy()


def date_from_str(ymd: str):
    y = int(ymd[:4])
    m = int(ymd[4:6])
    d = int(ymd[6:8])
    return date(y,m,d)


def clip_copy(msg):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_TEXT, msg.encode("gbk"))
    win32clipboard.CloseClipboard()

#
# class Obj:
#     def __init__(self):
#         pass


class MainUi(tky.TkYzwMainUi):
    def __init__(self, layout):
        d_locals['mainui'] = self
        super().__init__(title="mainui demo", layout=layout)  #, geometry='800x500+200+200'
        self.root.bind("<Control-k>", lambda ev:self.on_callback("control_k", ev))

        # fr = tk.Frame(self.root)
        # fr.pack(side="top", expand=1, fill="both")
        #
        # w = tk.Label(fr, text="double click me", font="微软雅黑 28 bold", fg='red', bg='blue', wraplength=160)  # anchor='w' justify='left' 多行对齐方式
        # w.pack(side="left", fill="both", expand=1)
        # w.bind("<Double-1>", lambda event: self.on_callback("label_double1", event))

        self.a_ui_f = []
        self.a_ui_v = []

        for code in yaml_exec_init:
            if not code: continue
            try:
                exec(code, globals(), d_locals)
            except:
                print(f"exec_init {code}")
                traceback.print_exc()

        fr = tk.Frame(self.root)
        # tk.Button(fr, text="确定", command=self.on_ok, bg="#d0e0d0").pack(side="left")
        # tk.Button(fr, text="退出", command=self.root.destroy, bg="#d0e0d0").pack(side="left")
        # tk.Button(fr, text="hide", command=self.on_hide, bg="#d0e0d0").pack(side="right")

        fr.pack(side="top", fill='x', expand=0)

        self.ui_table = table = self.load_table_from_yaml(self.root)
        self.ui_title = 'f' + repr(yaml_option.get("title", "tableview"))

        # table.cell_hide(("第1行","信息"))
        # table.cell_hide(("第10行", "来源"))

        self.st_hide = False

        table.pack(side="top", fill="both", expand=1)

        self.on_COPY_signal = False
        self.root.bind("<Control-c>", self.on_COPY)

    def on_COPY(self, e):
        self.on_COPY_signal = True

    def layout_wx(self, table, cell):
        # d_locals['self'] = self
        # d_locals['table'] = table
        d_locals['cell'] = cell  # cell> {'f': '{bias.IH02_B}', 'style': 'labelka', 'columnspan': 3}

        x = cell.get('uiv', None)
        if x is not None:
            del cell['uiv']
            uiv = eval(x, globals(), d_locals)
        else:
            uiv = None

        if "f" in cell:
            if "style" in cell:
                style = cell['style']
                uix = tk.Label(table, **d_style.get(style, {}))
                self.a_ui_f.append((uix, 'f' + repr(cell['f']), {}))
                del cell['style']
            else:
                uix = tk.Label(table)
                self.a_ui_f.append((uix, 'f' + repr(cell['f']), {}))
            del cell['f']
        elif "v" in cell:
            if "style" in cell:
                style = cell['style']
                uix = tk.Label(table, **d_style.get(style, {}))
                self.a_ui_v.append((uix, cell['v'], {}))
                del cell['style']
            else:
                uix = tk.Label(table)
                self.a_ui_v.append((uix, cell['v'], {}))
            del cell['v']

        elif 'label' in cell:
            if "style" in cell:
                style = cell['style']
                uix = tk.Label(table, text=cell['label'], **d_style.get(style, {}))
                del cell['style']
            else:
                uix = tk.Label(table, text=cell['label'])
            del cell['label']
        elif 'uix' in cell:
            try:
                uix = eval(cell['uix'], globals(), d_locals)
                del cell['uix']
            except:
                traceback.print_exc()
        else:
            uix = None

        return uix, uiv

    def load_table_from_yaml(self, root):
        tb = yaml_table
        rows = tb['rows']
        del tb['rows']
        style = tb.get("style", None)
        table = TkYzwTable(root, **d_style.get(style, {}))
        d_locals['table'] = table

        for a_cell in rows:
            # a_cell: 一行中的cell列表
            for cell in a_cell:
                # cell: 单个cell
                if isinstance(cell, list):
                    # 这个cell中含有多个widget
                    ui = tk.Frame(table)
                    uiv = []
                    for wx in cell:
                        # wx: cell中的单个widget
                        subui, subuiv = self.layout_wx(ui, wx)
                        subui.pack(side="left", expand=1, fill="both")
                        uiv.append(subuiv)
                    # 整个cell的选项,比如columnspan,需要加在最后一个wx上
                    table.add_cell(TkYzwTableCell(ui, uiv), **wx)
                else:
                    # 这个cell只有单个widget
                    ui, uiv = self.layout_wx(table, cell)
                    table.add_cell(TkYzwTableCell(ui, uiv), **cell)
            table.add_row()
        return table

    def on_setting(self):
        dlg = UiSetting(self.root)
        dlg.run()

    def on_timer(self):
        self.root.title(eval(self.ui_title))
        a_copy = []

        for code in yaml_exec_pre:
            try:
                exec(code, globals(), d_locals)
            except:
                print("exec failed: %s" % code)
                traceback.print_exc()
        for ui, f, vo in self.a_ui_f:
            try:
                ui['text'] = eval(f, globals(), d_locals)
            except:
                print("eval failed: %s" % f)
                ui['text'] = f
            a_copy.append(ui['text'])
        for ui, v, vo in self.a_ui_v:
            try:
                ui['text'] = eval(v, globals(), d_locals)
            except:
                # print("eval failed: %s" % v)
                ui['text'] = v
            a_copy.append(ui['text'])
        for code in yaml_exec_post:
            try:
                exec(code, globals(), d_locals)
            except:
                print("exec failed: %s" % code)
                traceback.print_exc()
        if self.on_COPY_signal:
            msgy = pprint.pformat(d_locals)
            clip_copy(",".join(a_copy))
            self.on_COPY_signal = False


class MainApp(tky.TkYzwMainUiApp):
    def __init__(self, mainui: tky.TkYzwMainUi):
        super().__init__(mainui, idle_timers=[yaml_option_interval])
        # threading.Thread(target=thproc_timer, args=(), daemon=True).start()

    def on_ui_control_k(self, ev):
        # ev: <KeyPress event state=Control|Mod1 keysym=k keycode=75 char='\x0b' x=404 y=-48>
        print("on_ui_control_k", ev)

    def on_ui_label_double1(self, event):
        print(f"on_ui_label_double1: event={event}")

    def on_ui_option1(self, v):
        print(f"on_ui_option1 {v}")

    def on_ui_spinbox1(self):
        v = mainui.uiv_spinbox1.get()
        print(f"on_ui_spinbox1 {v}")

    def on_ui_check1(self):
        v = mainui.uiv_check1.get()
        print(f"on_ui_check1 {v}")

    def on_ui_radio1(self, v:int):
        print(f"on_ui_radio1 {v}")

    def on_ui_start(self):
        # entry1 = mainui.uiv_entry1.get()
        d = mainui.getall_uiv()
        print(f"on_ui_start {self.ss.frid_task}: {d}")

    def on_ui_stop(self):
        print(f"on_ui_stop")

    def on_mainq(self, msgtype, *argv):
        if msgtype == 'timer':
            self.on_timer(*argv)
        else:
            print(f"{msgtype} {argv}")

    def on_idle(self):
        # print("mainq idle")
        pass

    def on_idle_timer(self, cycle:float):
        # print(f"mainq idle_timer {cycle}")
        mainui.on_timer()

    def on_timer(self, count):
        print(f"thread generated timer {count}")


def load_textfile(fn:str, encodings=None):
    if encodings is None: encodings = ['gbk', 'utf8']
    for encoding in encodings:
        try:
            with open(fn, encoding=encoding) as f:
                return f.read()
        except:
            continue

    return None


def add_style(name, **d):
    d_style[name] = d


def FrRedis(host:str, charset='gb18030', errors='replace', decode_responses=True, socket_timeout=None, socket_connect_timeout=None, **ka):
    a = host.split(":")
    host = a[0]
    if len(a) > 1: ka["port"] = int(a[1])
    if len(a) > 2: ka['db'] = int(a[2])

    k = frozenset([('host', host),
         ('charset', charset),
         ('errors', errors),
         ('decode_responses', decode_responses),
         ('socket_timeout', socket_timeout),
         ('socket_connect_timeout', socket_connect_timeout),
         ] + list(ka.items()))
    rd = redis.Redis(host=host, charset=charset, errors=errors, decode_responses=decode_responses,
                     socket_timeout=socket_timeout, socket_connect_timeout=socket_connect_timeout, **ka)

    return rd


if __name__ == '__main__':
    yaml_all = yaml.load(load_textfile(sys.argv[1]), Loader=yaml.FullLoader)

    yaml_option = yaml_all.get("option", dict())
    yaml_option_interval = yaml_option.get("interval", 1)
    yaml_option_layout = yaml_option.get("layout", None)
    yaml_style = yaml_all.get("style", dict())
    yaml_exec_init = yaml_all.get('exec_init', [])
    yaml_exec_pre = yaml_all.get('exec_pre', [])
    yaml_exec_post = yaml_all.get('exec_post', [])
    yaml_table = yaml_all['table']

    d_style = yaml_style
    d_locals = dict()

    for code in yaml_exec_init:
        try:
            print(code)
            exec(code, globals(), d_locals)
        except:
            traceback.print_exc()

    mainui = MainUi(yaml_option_layout)
    mainq = mainui.mainq
    mainapp = MainApp(mainui)
    mainui.run()
    print("bye")
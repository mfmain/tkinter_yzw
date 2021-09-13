
import tkinter as tk
from collections import deque


class TkYzwFrameIndexedListbox(tk.Frame):
    def __init__(self, master, dict_index:dict, index_home=['help', 'todo'], command=None, *a, **ka):
        super().__init__(master, *a, **ka)
        self.cb_command = command
        self.dict_index = dict_index
        self.index_home = index_home
        self.history = deque(maxlen=16)

        fr = tk.Frame(self); fr.pack(side="top", fill="x")
        self.ui_label = tk.Label(fr, text="key:")
        self.ui_label.bind("<Double-Button-1>", self.on_index_double_click)
        self.ui_label.bind("<Button-1>", self.on_label_click)
        self.ui_label.pack(side="left")

        self.uiv_entry = tk.StringVar()
        self.ui_entry = tk.Entry(fr, width=4, textvariable=self.uiv_entry)
        self.ui_entry.bind("<KeyRelease>", self.on_key)
        self.ui_entry.pack(side="left", fill="x", expand=1)

        self.uiv_star = '>'  # '>'=起始匹配 '*'=模糊匹配
        self.ui_star = tk.Label(fr, text=self.uiv_star)
        self.ui_star.pack(side="right")
        self.ui_star.bind("<1>", self.on_star)

        self.uiv_lstbox = tk.StringVar()
        self.ui_lstbox = tk.Listbox(self, listvariable = self.uiv_lstbox, height=28, width=36)
        self.ui_lstbox.pack(side="top", fill="both", expand=1)
        self.ui_lstbox.bind("<ButtonRelease-1>", self.on_sel)

        self.index_cur = index_home
        self.on_key(None)
        self.ui_entry.focus_set()

    def on_label_click(self, event):
        """
        点击index标签
        """
        print(self.history)
        if len(self.history) < 1: return
        k = self.history.pop()
        print("pop", k)
        self.uiv_entry.set(k)
        self.on_key(None)

    def on_index_double_click(self, event):
        """
        双击index标签
        """
        pass

    def on_star(self, event):
        """
        点击星号标签
        """
        if self.uiv_star == '*': self.uiv_star = '>'
        else:                 self.uiv_star = '*'
        self.ui_star.config(text=self.uiv_star)
        self.on_key(None)

    def lookup_dict(self, s:str):
        if not s:
            return self.index_home
        cnt = 0
        a = []
        s = s.lower()
        for k in self.dict_index:
            k_ = k.lower()
            if self.uiv_star == '*':
                if k_.find(s) < 0: continue
            else:
                if not k_.startswith(s): continue
            a.append(k)
            cnt += 1
            if cnt >= 50: break
        return sorted(a)

    def on_key(self, _):
        """
        用户输入新的key
        """

        k = self.ui_entry.get()
        if _ is not None and k:
            if self.history:
                lastk = self.history[-1]
                if k.startswith(lastk):
                    self.history[-1] = k
                elif not lastk.startswith(k):
                    self.history.append(k)
                else:
                    pass
            else:
                self.history.append(k)
        print(self.history)

        self.index_cur = self.lookup_dict(k)
        self.ui_lstbox.delete(0, tk.END)
        self.ui_lstbox.insert(0, *self.index_cur)
        self.ui_lstbox.select_set(0)
        self.on_sel()

    def on_sel(self, _=None):
        """
        用户选择列表中的项目
        """
        sel = self.ui_lstbox.curselection()
        if not sel: return
        i = sel[0]
        k = self.index_cur[i]
        if self.cb_command is not None:
            self.cb_command(k)
        else:
            print("on_sel_key:", k)

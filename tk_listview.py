# coding: utf-8

import tkinter as tk
import tkinter.ttk as ttk
from collections import OrderedDict


class TkYzwFrameListview(tk.Frame):
    def __init__(self, parent, column_list:tuple, width_list:tuple, maxrows:int = 0, move_on_update=False, yscroll=False, **ak):
        """
        :param column_list: [heading,anchor] #> "<name>,<anchor>" # ["时间", "来源", "分类", "信息,w"]
        :type column_list:  list[str]
        :param width_list: #> "50:100,w+"  # "<minwidth>:<width>, <anchor><stretch>"
        :type width_list:  list[int or str]
        :param maxrows: 正数限制行数，满后删最旧补新; 负数限制行数,满后不操作; 0不限制行数
        :param move_on_update: 当进行更新时，移动该行到首行
        :param yscroll: 卷滚条
        :param height: 初始的窗口行数
        """

        super().__init__(parent)
        self.move_on_update = move_on_update

        if maxrows > 0:
            self.maxrows = maxrows     #type: int
            self.drop_on_full = False  # 满了删旧补新
            self.ordered = True        # iids需要是OrderedDict来记录新旧次序
        elif maxrows < 0:
            self.maxrows = -maxrows   #type: int
            self.drop_on_full = True  # 满了弃新
            self.ordered = False      # iids是普通dict
        else:
            self.maxrows = 0           # 不限制行数，不会满
            self.drop_on_full = True   # no full at all
            self.ordered = None        # 根本不需要iids

        if self.ordered:
            self.iids = OrderedDict()  #type: OrderedDict [str, int]
        else:
            self.iids = {}             #type: dict [str, int]

        if column_list:
            ak['show'] = 'headings'
        else:
            ak['show'] = 'tree'
            column_list = ["c%d"%(i+1) for i in range(len(width_list))]

        fr = self
        tree = ttk.Treeview(fr, columns=["c%d"%(i+1) for i in range(len(column_list))], **ak)
        self.wx = tree         #type: ttk.Treeview

        # 配置抬头行 column_list
        style = ttk.Style()
        style.configure("Treeview", foreground='black')
        style.configure("Treeview.Heading", foreground='black', font="微软雅黑 11 bold")

        ANCHORS = ('n', 's', 'w', 'e', 'nw', 'sw', 'ne', 'se', 'ns', 'ew', 'nsew', 'center')

        for i, c in enumerate(column_list):
            a = c.rsplit(",", maxsplit=1)
            if len(a) > 1 and a[1] in ANCHORS:
                tree.heading('c%d'%(i+1), text=a[0], anchor=a[1])
            else:
                tree.heading('c%d'%(i+1), text=c, anchor='center')

        # 配置内容行width_list
        for i, width in enumerate(width_list):  # tk.W
            #> "50:100,w+"  # "<minwidth>:<width>, <anchor><stretch>"
            minwidth = 1
            stretch = 0
            anchor = "center"
            if type(width) is str:
                if width.endswith("+"):
                    stretch = 1
                    width = width[:-1]
                a = width.rsplit(",", maxsplit=1)
                if len(a) > 1 and a[1] in ANCHORS:
                    width = a[0]
                    anchor = a[1]
                a = width.split(":", maxsplit=1)
                if len(a) > 1:
                    minwidth = int(a[0])
                    width = a[1]
                width = int(width)

            tree.column('c%d'%(i+1), minwidth=minwidth, width=width, stretch=stretch, anchor=anchor)

        # tree.column('c3', width=100,stretch=1, anchor='w')

        # 配置tag
        tree.tag_configure('oddrow', background='#eeeeff')
        tree.tag_configure('bold', font="微软雅黑 10 bold")
        tree.tag_configure('blue', foreground='blue')
        tree.tag_configure('red', foreground='red')
        tree.tag_configure('grey', foreground='grey')

        # 卷滚条
        if yscroll:
            vbar = ttk.Scrollbar(tree, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vbar.set)
            vbar.pack(side="right", fill="y")

        tree.pack(fill="both", expand=1)

    def insert(self, v, index=0, iid=None, move=False, **ka):
        """
        :param v: values
        :param index: 0=第一个，1=第二个, ... "end"=最后一个
        :param iid:
        :param move:
        :return: iid，插入失败返回None
        """

        if self.maxrows == 0:
            # 不限制行数, 此时iids=None
            try:
                iid = self.wx.insert("", index, iid, values=v, **ka)  # parent=="" top-level
            except:
                try:
                    self.wx.item(iid, values=v, **ka)
                    if self.move_on_update: self.wx.move(iid, "", index)  # parent=""
                except:
                    pass
            return iid

        # 限制行数
        if iid in self.iids:
            # iid已经存在，则更新
            self.wx.item(iid, values=v, **ka)
            if self.move_on_update: self.wx.move(iid, "", index) # parent=""
            return iid

        # iid不存在，需要插入
        if len(self.iids) < self.maxrows:
            # maxrows未满
            iid = self.wx.insert("", index, iid, values=v, **ka)  # parent=="" top-level
            self.iids[iid] = 1
            return

        # iid不存在，maxrows满
        if self.drop_on_full:  return None

        if iid is None:
            print("TkListview.insert 必须提供iid:  maxrows=%d ordered=%r"%(self.maxrows, self.ordered))
            return None

        # 删除最老的，此时iids应为OrderedDict
        self.iids: OrderedDict
        iid_oldest, _ = self.iids.popitem(False)  # False=FIFO, True=LIFO
        self.wx.delete(iid_oldest)
        iid = self.wx.insert("", index, iid, values=v, **ka)  # parent=="" top-level
        self.iids[iid] = 1
        return iid

    def clear(self):
        for i in self.wx.get_children(): self.wx.delete(i)
        if self.ordered:
            self.iids = OrderedDict() #type: dict [str, int]
        else:
            self.iids = {} #type: dict [str, int]


if __name__ == '__main__':
    import time

    class Ui:
        # 把UI相关的控件及其变量都封装在一起
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("tk_listview demo")
            self.root.geometry('600x500+200+200') # yscroll=True时需要设，否则窗口很小
            fr = tk.Frame(self.root)
            self.uiv_iid = tk.IntVar(value=1)
            tk.Entry(fr, width=4, textvariable=self.uiv_iid).pack(side="left")
            tk.Button(fr, text="添加", command=self.on_insert, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="GO",   command=self.on_go, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="清空", command=self.on_clear, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="退出", command=self.root.destroy, bg="#d0e0d0").pack(side="left")
            fr.pack(side="top")

            column_list = ("时间", "来源", "分类", "信息,w")
            width_list = (100, 100, "50:100,w", "100,w+")

            # 测试方案： 改变maxrows, move_on_update
            #               (0, True), (0, False), (5, True), (5, False), (-5, True), (-5, False)
            ui_listview = TkYzwFrameListview(self.root, column_list, width_list, maxrows=0, move_on_update=False, yscroll=True, height=10)
            self.ui_listview = ui_listview

            ui_listview.wx.column('#0', stretch="no", minwidth=0, width=0)

            # ui_listview.wx.heading('c4', text='信息', anchor='w')   使用,w后缀实现
            # ui_listview.wx.column('c4', width=100, stretch=1, anchor='w')  使用,w+后缀实现

            ui_listview.wx.bind("<Double-1>", self.on_tree_d1)
            ui_listview.pack(side="top", fill="both", expand=1)

        def on_insert(self):
            sel = self.ui_listview.wx.selection()
            if not sel:
                index = 0
            else:
                index = self.ui_listview.wx.index(sel[0])
            iid = self.uiv_iid.get()
            t = time.strftime("%H%M%S")
            v = (t, iid, "x%d"%iid, "this is a very simple demo row %d"%iid )
            self.ui_listview.insert(v, index=index, iid="myiid%d"%iid)
            self.uiv_iid.set(iid+1)

        def on_go(self):
            tree = self.ui_listview.wx
            print("selected:")
            for i, item in enumerate(tree.selection()):
                print("    [%d]"%i, tree.item(item, "values"))
            print("all:")
            for i, item in enumerate(self.ui_listview.iids):
                print("    [%d]"%i, tree.item(item, "values"))

        def on_clear(self):
            self.ui_listview.clear()

        def on_tree_d1(self, event):
            tree = self.ui_listview.wx
            sel = tree.selection()
            if not sel:
                print("no sel")
                return
            item = sel[0]
            print("you clicked on ", tree.item(item, "values"))
            rowiid = tree.identify_row(event.y)  # > iid I001 I002 I003 ...
            column = tree.identify_column(event.x)  # > #1 #2 #3 ...
            rowindex = tree.index(rowiid)
            colindex = int(column[1:])
            print("    row=[%d]%s"%(rowindex,rowiid), "col=[%d]%s"%(colindex,column), tree.set(rowiid))
            print("   ---", tree.set(rowiid, "c%d"%colindex))
            tree.set(rowiid, "c%d"%colindex, value="xxx")
            # tree.set(rowiid, column='c2', value="xxx")

    ui = Ui()
    ui.root.mainloop()


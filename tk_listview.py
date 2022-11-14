# coding: utf-8

import tkinter as tk
import tkinter.ttk as ttk
from collections import OrderedDict


class TkYzwFrameListview(tk.Frame):
    def __init__(self, master, column_list, on_cell=None, on_select=None, on_heading=None, scroll="", maxrows:int=0, movetop_on_update=False, **ak):
        """
        :param column_list: [("tag", 120), ("desc,w", "100,w+"), ...("列名,列名anchor", "列宽,内容行anchor")] 不包含树节点"#0"
        :param on_cell: 双击某个单元格时调用，同时on_select也会被调用
        :param on_select: 选择时调用(单击某行单选, 按shift片选, 按ctrl多选)
        :param on_heading： 单击抬头时调用
        :param maxrows: 正数限制行数，满后删最旧补新; 负数限制行数,满后不操作; 0不限制行数
        :param movetop_on_update: 当进行更新时，移动该行到首行
        :param kw:
            show="tree" 无抬头栏；  show="headings" 有抬头  # 无抬头无法拉伸单列的列宽
        """

        self.cb_command = on_cell
        self.cb_on_select = on_select
        self.movetop_on_update = movetop_on_update

        a_coltext = [x[0] for x in column_list]
        a_width = [x[1] for x in column_list]
        a_keyfunc = [x[2] if len(x) > 2 else None for x in column_list]

        super().__init__(master, **ak)
        self.master = master

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

        fr = self
        tree = ttk.Treeview(fr, columns=["c%d"%(i+1) for i in range(len(a_coltext))], **ak)
        self.wx = tree         #type: ttk.Treeview

        # 配置抬头行 a_coltext
        style = ttk.Style()
        style.configure("Treeview", foreground='black')
        style.configure("Treeview.Heading", foreground='black', font="微软雅黑 11 bold")

        tree.column('#0', stretch="no", minwidth=0, width=0)  # 不显示树节点#0
        ANCHORS = ('n', 's', 'w', 'e', 'nw', 'sw', 'ne', 'se', 'ns', 'ew', 'nsew', 'center')
        for i, coltext in enumerate(a_coltext):
            colname = 'c%d' % (i+1)
            a = coltext.rsplit(",", maxsplit=1)  # a> [text, anchor]
            text=a[0]
            anchor = a[1] if len(a) > 1 and a[1] in ANCHORS else "center"
            keyfunc = a_keyfunc[i]
            tree.heading(colname, text=text, anchor=anchor, command=lambda i=i, kf=keyfunc: self._sort_column(i, False, kf))

        # 配置内容行width_list
        for i, width in enumerate(a_width):  # tk.W
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

        tree.bind("<Double-1>", self._on_tree_double1)      # double click
        # tree.bind("<ButtonRelease-1>", self.on_tree_release1)  # single click, 不能使用<Button-1>,会取到鼠标点击前的状态
        # tree.bind("<<TreeviewSelect>>", self.on_tree_select)  # 一定能取到selection, 不会"index out of range"
        tree.bind("<<TreeviewSelect>>", self.__on_tree_select)
        tree.bind("<B1-Motion>", self._on_tree_b1_motion, add='+')

        # 卷滚条
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(0, weight=1)
        tree.grid(row=0, column=0, sticky="nsew")

        if 'y' in scroll:
            ysb = ttk.Scrollbar(fr, orient='vertical', command=tree.yview)
            tree.configure(yscroll=ysb.set)
            ysb.grid(row=0, column=1, sticky='ns')

        if 'x' in scroll:
            xsb = ttk.Scrollbar(fr, orient='horizontal', command=tree.xview)
            tree.configure(xscroll=xsb.set)
            xsb.grid(row=1, column=0, sticky='ew')

        self.bind("x", self.on_key_x)
        self.bind("X", self.on_key_X)
        self.bind("<Control-c>", self.on_key_ctrl_c)
        self.bind("<Control-a>", self.on_key_ctrl_a)

    def _sort_column(self, coli, reverse, keyfunc):
        # keyfunc 返回一个用于排序的key
        cn = "c%d" % (coli + 1)
        tv = self.wx
        a_chiid = tv.get_children('')  # 第一级子节点
        if keyfunc:
            a = [(keyfunc(tv.set(iid, cn)), iid) for iid in a_chiid]  # 这里的.set()没有提供value参数,实际效果是get
        else:
            a = [(tv.set(iid, cn), iid) for iid in a_chiid]  # 这里的.set()没有提供value参数,实际效果是get
        a.sort(reverse=reverse)
        for index, (val, iid) in enumerate(a): tv.move(iid, '', index)
        tv.heading(cn, command=lambda: self._sort_column(coli, not reverse, keyfunc))

    def bind(self, sequence, func):
        self.wx.bind(sequence, func)

    def on_key_X(self, _):
        self.do_clear()

    def on_key_x(self, _):
        self.do_deltree_selected()

    def on_key_ctrl_c(self, _):
        a = self.wx.selection()
        a_msg = []
        for iid in a:
            text = self.wx.item(iid, 'text')
            values = self.wx.item(iid, 'values')
            a_msg.append("%s: %s" % (text, ','.join(values)))
        clip_copy('\n'.join(a_msg))

    def on_key_ctrl_a(self, _):
        a_iid = self.iter_children("")
        self.wx.selection_set(a_iid)

    def __on_tree_select(self, event):
        if self.cb_on_select:
            iids = self.wx.selection()  # type: tuple
            if iids: self.cb_on_select(iids[0], event)

    def _on_tree_double1(self, event):
        if self.cb_command:
            iids = self.wx.selection()  # type: tuple
            if iids: self.cb_command(iids[0], event)

    def _on_tree_b1_motion(self, event):
        tv = event.widget
        newindex = tv.index(tv.identify_row(event.y))

        a_iid = tv.selection()
        print("_on_tree_b1_motion selection: ", a_iid)
        for iid in a_iid: tv.move(iid, '', newindex)

    def dump_selection(self):
        print("dump_selection:")
        iids = self.wx.selection()  # type: tuple  # 刚启动时,未选择任何东西,返回空tuple
        for i, iid in enumerate(iids):
            print('  [%d] iid=%s text=%s' % (i, iid, self.wx.item(iid, 'text')))

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
                    if self.movetop_on_update: self.wx.move(iid, "", index)  # parent=""
                except:
                    pass
            return iid

        # 限制行数
        if iid in self.iids:
            # iid已经存在，则更新
            self.wx.item(iid, values=v, **ka)
            if self.movetop_on_update: self.wx.move(iid, "", index) # parent=""
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

            column_list = [("时间", 100), ("来源", 100, int), ("分类","50:100,w", lambda x: int(x[1:])), ("信息,w", "100,w+")]

            # 测试方案： 改变maxrows, movetop_on_update
            #           (0, True), (0, False), (5, True), (5, False), (-5, True), (-5, False)
            ui_listview = TkYzwFrameListview(self.root, column_list, maxrows=0, movetop_on_update=False, scroll="y")
            self.ui_listview = ui_listview

            ui_listview.wx.column('#0', stretch="no", minwidth=0, width=0)  # 不显示树节点#0

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
            v = (t, int(iid), "x%d"%iid, "this is a very simple demo row %d"%iid )
            self.ui_listview.insert(v, index=index, iid="ylv%d"%iid)
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


# coding: utf-8

from typing import Union
from collections import defaultdict
import tkinter as tk


class TkYzwTableCell(tk.Frame):
    """ 单元格 """
    def __init__(self, uix:tk.Widget, uiv=None):
        self.uix = uix
        self.uiv = uiv  #type:  Union(tk.Variable, list[tk.Variable])
        self.rowi = -1
        self.coli = -1
        self.gridopt = dict()


class TkYzwTable(tk.Frame):
    """ 表格
        布局方式:
            cell 单元格可以是任意tk控件
            add_cell(cell)在当前行的最后一列添加一个单元格cell
            add_row 开始新的一行
        访问方式:
            d_cellkey_cell[cellkey]  通过cellkey来访问命名单元格
            d_rowi_a_cells[0] 返回第一行的单元格列表
            d_coli_a_cells[0] 返回第一列的单元格列表
    """
    def __init__(self, parent, bd=3, relief="groove", bg="#b0b0cc", **ak):
        super().__init__(parent, bd=bd, relief=relief, bg=bg, **ak)
        self.d_cellkey_cell = dict()           #type: dict[any, TkYzwTableCell]
        self.d_rowi_a_cells = dict()
        self.d_coli_a_cells = dict()
        self.loc_next_rowi = 0
        self.loc_next_coli = 0

    def get_cell(self, cellkey) -> TkYzwTableCell:
        cell = self.d_cellkey_cell.get(cellkey, None)
        return cell

    def add_cell(self, cell:TkYzwTableCell, cellkey=None, rowspan=1, columnspan=1, sticky="nesw", padx=1, pady=1, **gridopt):
        coli = self.loc_next_coli
        self.loc_next_coli += columnspan
        if cell is None: return

        if cellkey is not None:
            self.d_cellkey_cell[cellkey] = cell

        rowi = self.loc_next_rowi
        if cell.uix:
            cell.uix.grid(row=rowi, column=coli, rowspan=rowspan, columnspan=columnspan, sticky=sticky, padx=padx, pady=pady, **gridopt)
        if rowi not in self.d_rowi_a_cells:
            self.rowconfigure(rowi, weight=1)
            self.d_rowi_a_cells[rowi] = []
        if coli not in self.d_coli_a_cells:
            self.columnconfigure(coli, weight=1)
            self.d_coli_a_cells[coli] = []

        self.d_rowi_a_cells[rowi].append(cell)
        self.d_coli_a_cells[coli].append(cell)
        cell.rowi = rowi
        cell.coli = coli
        gridopt.update({"sticky": sticky, "padx": padx, "pady": pady})
        cell.gridopt = gridopt
        return cell

    def add_row(self):
        self.loc_next_rowi += 1
        self.loc_next_coli = 0

    def cell_hide(self, cellkey):
        cell = self.d_cellkey_cell.get(cellkey, None)
        if cell is None: return
        cell.uix.grid_forget()  # ['state'] = 'disabled'
        cell.uix = tk.Label(self, text="")
        cell.uix.grid(row=cell.rowi, column=cell.coli, **cell.gridopt)

    def row_hide(self, rowi:int):
        a_cells = self.d_rowi_a_cells.get(rowi, [])
        if not a_cells: return

        for cell in a_cells:
            cell.uix.grid_forget()  # ['state'] = 'disabled'
        self.rowconfigure(rowi, weight=0)

    def row_show(self, rowi:int):
        a_cells = self.d_rowi_a_cells.get(rowi, [])
        if not a_cells: return

        for cell in a_cells:
            cell.uix.grid(row=cell.rowi, column=cell.coli, **cell.gridopt)
        self.rowconfigure(rowi, weight=1)


if __name__ == '__main__':
    class Ui:  # 把UI相关的控件及其变量都封装在一起
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("tk_sheet demo")
            # self.root.geometry('600x500+200+200')
            fr = tk.Frame(self.root)
            tk.Button(fr, text="确定", command=self.on_ok, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="退出", command=self.root.destroy, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="hide", command=self.on_hide, bg="#d0e0d0").pack(side="right")

            fr.pack(side="top", fill='x', expand=0)

            self.ui_table = table = TkYzwTable(self.root)

            table.add_cell(TkYzwTableCell(tk.Label(table, text="test")), columnspan=3)
            table.add_cell(TkYzwTableCell(tk.Label(table, text="test2")))
            table.add_cell(TkYzwTableCell(tk.Label(table, text="test3")))
            table.add_row()

            a_colname = ["时间", "来源", "分类", "信息"]
            table.add_cell(TkYzwTableCell(tk.Label(table, text="行权价")))
            for colname in a_colname:
                table.add_cell(TkYzwTableCell(tk.Label(table, text=colname)))
            table.add_row()

            for rowname in ["第%d行" % (x + 1) for x in range(16)]:
                table.add_cell(TkYzwTableCell(tk.Label(table, text=rowname)))
                for colname in a_colname:
                    uiv = tk.StringVar(value="%r,%r"%(rowname, colname))
                    ui = tk.Entry(table, textvariable=uiv, relief="flat")
                    table.add_cell(TkYzwTableCell(ui, uiv), cellkey=(rowname, colname))
                table.add_row()

            table.cell_hide(("第1行","信息"))
            table.cell_hide(("第10行", "来源"))

            self.st_hide = False

            table.pack(side="top", fill="both", expand=1)

        def on_ok(self):
            for cellkey, cell in self.ui_table.d_cellkey_cell.items():
                if cell.uiv: print(cellkey, cell.uiv.get())

        def on_hide(self):
            print("on_hide", self.st_hide)
            if self.st_hide:
                cell = self.ui_table.d_cellkey_cell[("第13行", "信息")]
                self.ui_table.row_show(cell.rowi)
                self.st_hide = False
            else:
                cell = self.ui_table.d_cellkey_cell[("第13行", "信息")]
                self.ui_table.row_hide(cell.rowi)
                self.st_hide = True


    ui = Ui()
    ui.root.mainloop()


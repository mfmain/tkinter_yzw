# coding: utf-8

import tkinter as tk


class TkYzwSheetCell:
    def __init__(self, row:int, column:int, ui:tk.Widget, uiv:tk.Variable, grid_orig_row=0, grid_orig_column=0):
        self.rowi_grid = row + grid_orig_row         # 绝对,等同grid.row,从0开始编号
        self.coli_grid = column + grid_orig_column   # 绝对,等同grid.column,从0开始编号

        self.rowi = row      # 相对索引,第一行显示的是表头(col_list),其rowi=0
        self.coli = column   # 相对索引,每行的第一列显示的是rowname,其coli=0
        # 所以纯数据部分(不含rowname,colname)第一行第一列的cell: rowi=1, coli=1
        self.ui = ui
        self.uiv = uiv


class TkYzwSheetRow:
    def __init__(self, rowi:int, rowname:str, col_list:list, grid_orig_row=0):
        self.rowi_grid = rowi + grid_orig_row  # 绝对, 等同grid.column
        self.rowi = rowi  # 相对索引,第一行显示的是表头(col_list),其rowi=0
        self.rowname = rowname
        self.col_list = col_list
        self.d_coli_cell = dict()     #type: dict[int, TkYzwSheetCell]  # 相对索引
        self.d_colname_cell = dict()  #type: dict[str, TkYzwSheetCell]


class TkYzwSheetAny(tk.Frame):
    def __init__(self, parent, row_list:str, col_list:str, title=None, on_title=None, bg="#b0b0cc"):
        super().__init__(parent)
        self["bd"] = 3 # border
        self["relief"] = "groove"
        self["bg"] = bg

        self.col_list = col_list  # 从第一列开始的表头, ["A", "B", "C", ...], 对应的coli=[0, 1, 2,...]
        self.row_list = []  # 从表头下面那行开始的每一行的第一个cell放的文本, 对应的rowi=[rowi_start+1, rowi_start+2, ...]
        self.rowi_max = 0  # 最大的相对索引号

        # self.option_add('*Font', '微软雅黑 8')
        if title:
            w = tk.Label(self, text=title, font="微软雅黑 10 bold"); w.grid(row=0, column=0, columnspan=10, sticky="we")
            if on_title: w.bind("<Double-Button-1>", on_title)
            self.rowi_start = 1
        else:
            self.rowi_start = 0

        self.d_rowi = dict()     #type: dict[int, TkYzwSheetRow]  # 相对索引
        self.d_rowname = dict()  #type: dict[str, TkYzwSheetRow]

        sheetrow = TkYzwSheetRow(0, "", col_list, grid_orig_row=self.rowi_start)
        sheetrow.d_coli_cell = dict()
        sheetrow.d_colname_cell = dict()
        for i, colname in enumerate(col_list):
            if i > 0:  self.columnconfigure(i, weight=1)
            cell = TkYzwSheetCell(0, i, tk.Label(self, text=colname), None, grid_orig_row=self.rowi_start)
            cell.ui.grid(row=cell.rowi_grid, column=cell.coli_grid, sticky="nsew", padx=1, pady=1)
            cell.ui.bind("<Double-1>", lambda e, x=colname: self.on_double1_heading(x))
            sheetrow.d_colname_cell[colname] = cell  # 可以用colname索引
            sheetrow.d_coli_cell[i] = cell        # 也可以用coli索引, 从0开始编号
        self.d_rowi[0]  = sheetrow   # 使用rowi索引

        for rowname in row_list:
            self.append_row(rowname)

    def append_row(self, rowname:str=""):
        self.rowi_max += 1
        if not rowname: rowname = str(self.rowi_max)
        self.row_list.append(rowname)
        rowi相对 = self.rowi_max
        rowi绝对 = self.rowi_start + rowi相对
        self.rowconfigure(rowi绝对, weight=1)
        sheetrow = TkYzwSheetRow(rowi相对, rowname, self.col_list, grid_orig_row=self.rowi_start)
        sheetrow.d_coli_cell = dict()
        sheetrow.d_colname_cell = dict()
        for cellcoli, colname in enumerate(self.col_list):
            if cellcoli == 0:
                cell = TkYzwSheetCell(rowi相对, 0, tk.Label(self, text=str(rowname)), None, grid_orig_row=self.rowi_start)
                cell.ui.bind("<Double-1>", lambda e, x=rowname: self.on_double1_row(x))
            else:
                uiv = self.on_cell_uiv(rowi相对, rowname, cellcoli, colname)
                cell = TkYzwSheetCell(rowi相对, cellcoli, self.on_cell_ui(rowi相对, rowname, cellcoli, colname, uiv), uiv,
                                      grid_orig_row=self.rowi_start)
                self.last_uiv = cell.uiv
            cell.ui.grid(row=cell.rowi_grid, column=cell.coli_grid, sticky='nesw', padx=1, pady=1)
            sheetrow.d_colname_cell[colname] = cell
            sheetrow.d_coli_cell[cellcoli] = cell
        self.d_rowname[rowname] = sheetrow
        self.d_rowi[rowi相对] = sheetrow
        return sheetrow

    def remove_row(self, rowname:str):
        row = self.d_rowname.get(rowname, None)
        if row is None: return
        for cell in row.d_colname_cell.values():
            cell.ui.grid_forget()
            cell.ui.destroy()
        self.rowconfigure(row.rowi_grid, weight=0)

        self.row_list.remove(rowname)
        del self.d_rowi[row.rowi]
        del self.d_rowname[row.rowname]

    def get_cell(self, rowname:str, colname:str):
        row = self.d_rowname.get(rowname)
        if row is None: return None
        cell = row.d_colname_cell.get(colname)
        return cell

    def cell_hide(self, rowname, colname):
        sheetrow = self.d_rowname[rowname]
        cell = sheetrow.d_colname_cell[colname]
        cell.ui.grid_forget()  # ['state'] = 'disabled'
        cell.ui = tk.Label(self, text="")
        cell.ui.grid(row=cell.rowi_grid, column=cell.coli_grid, sticky='nesw', padx=1, pady=1)

    def row_hide(self, rowname):
        sheetrow = self.d_rowname[rowname]
        for cell in sheetrow.d_colname_cell.values():
            cell.ui.grid_forget()  # ['state'] = 'disabled'
        self.rowconfigure(sheetrow.rowi_grid, weight=0)

    def row_show(self, rowname):
        sheetrow = self.d_rowname[rowname]
        for cell in sheetrow.d_colname_cell.values():
            cell.ui.grid(row=cell.rowi_grid, column=cell.coli_grid, sticky='nesw', padx=1, pady=1)
        self.rowconfigure(sheetrow.rowi_grid, weight=1)

    def get_by_row_col(self, all=False):
        a = []
        for rowname in self.row_list:
            for colname in self.col_list[1:]:
                sheetrow = self.d_rowname[rowname]
                cell = sheetrow.d_colname_cell[colname]
                uiv = cell.uiv
                if all:
                    a.append((colname, rowname, uiv.get()))
                else:
                    v = uiv.get()
                    if v: a.append((colname, rowname, v))
        return a

    def get_by_col_row(self, all=False):
        a = []
        for colname in self.col_list[1:]:
            for rowname in self.row_list:
                sheetrow = self.d_rowname[rowname]
                cell = sheetrow.d_colname_cell[colname]
                uiv = cell.uiv
                if all:
                    a.append((colname, rowname, uiv.get()))
                else:
                    v = uiv.get()
                    if v: a.append((rowname, colname, v))
        return a

    def on_cell_uiv(self, rowi:int, rowname:str, coli:int, colname:str):
        # print("on_cell_uiv: ", coli, colname)
        return tk.IntVar(value=1)

    def on_cell_ui(self, rowi:int, rowname:str, coli:int, colname:str, uiv:tk.Variable):
        # uiv: from on_cell_uiv's return value
        return tk.Checkbutton(self, variable=uiv)

    def on_double1_heading(self, colname:str):
        pass

    def on_double1_row(self, rowname:str):
        pass


class TkYzwSheetCheck(TkYzwSheetAny):
    def on_cell_uiv(self, rowi:int, rowname:str, coli:int, colname:str):
        return tk.IntVar(value=0)

    def on_cell_ui(self, rowi:int, rowname:str, coli:int, colname:str, uiv:tk.Variable):
        return tk.Checkbutton(self, variable=uiv)

    def on_double1_heading(self, colname:str):
        if colname not in self.col_list[1:]: return
        oldv = None
        for row in self.row_list:
            sheetrow = self.d_rowname[row]
            cell = sheetrow.d_colname_cell[colname]
            ui, uiv = cell.ui, cell.uiv
            if ui.winfo_ismapped():
                if oldv is None: oldv = uiv.get()
                uiv.set(not oldv)

    def on_double1_row(self, rowname:str):
        oldv = None
        for col in self.col_list[1:]:
            sheetrow = self.d_rowname[rowname]
            cell = sheetrow.d_colname_cell[col]
            ui, uiv = cell.ui, cell.uiv
            if ui.winfo_ismapped():
                if oldv is None: oldv = uiv.get()
                uiv.set(not oldv)


class TkYzwSheetEntry(TkYzwSheetAny):
    def on_cell_uiv(self, rowi:int, rowname:str, coli:int, colname:str):
        # 返回cell的值
        return tk.StringVar(value="%d(%r) %d(%r)"%(rowi, rowname, coli, colname))

    def on_cell_ui(self, rowi:int, rowname:str, coli:int, colname:str, uiv:tk.Variable):
        # 返回cell的控件
        return tk.Entry(self, textvariable=uiv, relief="flat")


if __name__ == '__main__':
    import time
    class Ui:  # 把UI相关的控件及其变量都封装在一起
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("tk_sheet demo")
            # self.root.geometry('600x500+200+200')
            fr = tk.Frame(self.root)
            # tk.Button(fr, text="添加", command=self.on_insert, bg="#d0e0d0").pack(side="left")
            # tk.Button(fr, text="清空", command=self.on_clear, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="确定", command=self.on_ok, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="退出", command=self.root.destroy, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="hide", command=self.on_hide, bg="#d0e0d0").pack(side="right")

            fr.pack(side="top", fill='x')

            fr = TkYzwSheetCheck(self.root, ["第%d行" % (x+1) for x in range(16)], ["行权价", "时间", "来源", "分类", "信息"])
            # fr = TkYzwSheetEntry(self.root, ["第%d行"%x for x in range(16)], ["行权价", "时间", "来源", "分类", "信息"])
            self.frsel = fr
            fr.pack(side="top", expand=tk.YES, fill='both')
            fr.cell_hide("第1行","信息")
            fr.cell_hide("第10行", "来源")
            self.st_hide = False

        def on_ok(self):
            a = self.frsel.get_by_row_col()
            a2 = self.frsel.get_by_col_row()
            print(a)
            print(a2)

        def on_hide(self):
            print("on_hide", self.st_hide)
            if self.st_hide:
                self.frsel.row_show("第13行")
                self.st_hide = False
            else:
                self.frsel.row_hide("第13行")
                self.st_hide = True


    ui = Ui()
    ui.root.mainloop()


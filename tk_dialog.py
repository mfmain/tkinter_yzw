# coding: gbk
import tkinter as tk


class TkYzwDialog(tk.Toplevel):
    def __init__(self, master_, title=None, modal=True, transient=True, *la, **ka):
        super().__init__(master_, *la, **ka)
        self.master_ = master_
        if title is not None:
            self.title(title)

        master = self.master  # 如果master_是空, tk会自动分配一个root给self.master
        if master_ is None and modal:
            master.withdraw()
            transient = False
        if transient: self.transient(master)
        self.modal = modal
        if modal: self.grab_set()

        #self.geometry("400x300")
        x,y = master.winfo_pointerxy()
        # self.geometry("+%d+%d"%(x-200,y-100))
        self.geometry("+%d+%d" % (x, y))

        self.result = None

    def close(self, result):
        self.result = result
        self.destroy()

    def on_ok(self):
        self.destroy()
        self.result = self.collect_uiv()

    def on_cancel(self):
        self.destroy()
        self.result = None

    def collect_uiv(self):
        d = dict()
        for uiv in self.__dict__:
            if uiv.startswith("uiv_"):
                k = uiv[4:]
                wx = getattr(self, uiv)
                d[k] = wx.get()
        return d

    def run(self):
        # only necessary for modal
        if self.modal:
            self.master.wait_window(self)
            if self.master_ is None:
                self.master.destroy()
            return self.result
        else:
            return None


if __name__ == '__main__':

    def main_连续三个modal():

        class DlgDemo(TkYzwDialog):
            def __init__(self, master, *la, **ka):
                super().__init__(master, *la, **ka)

                self.uiv_entry = tk.IntVar(value=1)
                tk.Entry(self, width=4, textvariable=self.uiv_entry, justify="center").pack(fill="both", expand=0)

                fr = tk.Frame(self)
                fr.pack(side="top", pady=5, fill="both")
                tk.Button(fr, text="确认", command=self.on_ok).pack(side="left", fill="both", expand=1)
                tk.Button(fr, text="取消", command=self.on_cancel).pack(side="left", fill="both", expand=1)

        dlg = DlgDemo(None, modal=True)
        result = dlg.run()
        print(result)

        dlg = DlgDemo(None, modal=True)
        result = dlg.run()
        print(result)

        dlg = DlgDemo(None, modal=True)
        result = dlg.run()
        print(result)

    def main_listview():
        from tk_listview import TkYzwFrameListview
        class DlgDemo(TkYzwDialog):
            def __init__(self, master, a_col, a_row):
                super().__init__(master, modal=True)

                # a_col = [("股票", 100), ("价格", 100, int), ("数量", "50:100,w")]
                lv = TkYzwFrameListview(self, a_col, scroll="y")
                lv.pack(side="top", fill="x")
                for x in a_row: lv.insert(x, index='end')

                fr = tk.Frame(self)
                fr.pack(side="top", pady=5, fill="both")
                tk.Button(fr, text="确认", command=self.on_ok).pack(side="left", fill="both", expand=1)
                tk.Button(fr, text="取消", command=self.on_cancel).pack(side="left", fill="both", expand=1)

        a_col = [("股票", 100), ("价格", 100, float), ("数量", "50:100,w", int)]
        a_row = [
            ("dsfsd", 2.3, 100),
            ("dsfsd2", 2.1, 1200),
            ("dsfsd3", 2.9, 130),
            ("dsfsd4", 2.4, 1400),
        ]
        dlg = DlgDemo(None, a_col, a_row)
        result = dlg.run()
        print(result)


    main_listview()
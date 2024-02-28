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
    class DlgDemo(TkYzwDialog):
        def __init__(self, master, *la, **ka):
            super().__init__(master, *la, **ka)

            self.uiv_entry = tk.IntVar(value=1)
            tk.Entry(self, width=4, textvariable=self.uiv_entry, justify="center").pack(fill="both", expand=0)

            fr = tk.Frame(self)
            fr.pack(side="top", pady=5, fill="both")
            tk.Button(fr, text="确认", command=self.on_确认).pack(side="left", fill="both", expand=1)
            tk.Button(fr, text="取消", command=self.on_取消).pack(side="left", fill="both", expand=1)

        def on_确认(self):
            self.destroy()
            self.result = self.collect_uiv()

        def on_取消(self):
            self.destroy()
            self.result = None

    dlg = DlgDemo(None, modal=True)
    result = dlg.run()
    print(result)

    dlg = DlgDemo(None, modal=True)
    result = dlg.run()
    print(result)

    dlg = DlgDemo(None, modal=True)
    result = dlg.run()
    print(result)

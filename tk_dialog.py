
import tkinter as tk


class TkYzwDialog(tk.Toplevel):
    def __init__(self, master, title=None, modal=True, *la, **ka):
        super().__init__(master, *la, **ka)
        if title is not None:
            self.title(title)
        self.transient(master)
        self.modal = modal
        if modal: self.grab_set()
        self.master = master

        #self.geometry("400x300")
        x,y = master.winfo_pointerxy()
        # self.geometry("+%d+%d"%(x-200,y-100))
        self.geometry("+%d+%d" % (x, y))

        self.result = None

    def close(self, result):
        self.result = result
        self.destroy()

    def run(self):
        if self.modal:
            self.wait_window(self)
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
            self.result = self.uiv_entry.get()

        def on_取消(self):
            self.destroy()
            self.result = None

    root = tk.Tk()
    dlg = DlgDemo(root)
    result = dlg.run()
    print(result)



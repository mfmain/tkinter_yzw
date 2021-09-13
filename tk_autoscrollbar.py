

# http://effbot.org/zone/tkinter-autoscrollbar.htm
# http://effbot.org/zone/tkinter-scrollbar-patterns.htm

import tkinter as tk


class _AutoScrollbar_pack(tk.Scrollbar):
    def set(self, lo, hi):
        # print("_AutoScrollbar set(%r,%r)"%(lo, hi))
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            if self.cget("orient") == tk.HORIZONTAL:
                self.pack(fill=tk.X, side=tk.BOTTOM)
            else:
                self.pack(fill=tk.Y, side=tk.RIGHT)
        tk.Scrollbar.set(self, lo, hi)


class _AutoScrollbar(tk.Scrollbar):
    def set(self, lo, hi):
        # print("_AutoScrollbar set(%r,%r)" % (lo, hi))
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)


class TkYzwFrameAutoScroll(tk.Frame):
    """"
    给不支持滚动的控件使用,即Text,Canvas,Listbox,Entry之外的控件
    """
    def __init__(self, master=None, scroll="xy", **kw):
        """
        :param master: canvas's parent
        """

        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        scrollcommand = dict()
        xbar, ybar = None, None
        if 'x' in scroll:
            self.ui_xbar = xbar = _AutoScrollbar(master, orient=tk.HORIZONTAL)
            xbar.grid(row=1, column=0, sticky="ew")
            scrollcommand["xscrollcommand"] = xbar.set
        if 'y' in scroll:
            self.ui_ybar = ybar = _AutoScrollbar(master)
            ybar.grid(row=0, column=1, sticky="ns")
            scrollcommand["yscrollcommand"] = ybar.set

        self.ui_canvas = canvas = tk.Canvas(master, **scrollcommand)
        canvas.grid(row=0, column=0, sticky="nsew")

        if xbar: xbar.config(command=canvas.xview)
        if ybar: ybar.config(command=canvas.yview)

        super().__init__(canvas, **kw)

    def update_scrollregion(self):
        """
        should be call when self packed
        """
        self.ui_canvas.create_window(0, 0, anchor=tk.NW, window=self)  # 相当于self.pack()
        self.update_idletasks()   # to update bbox
        self.ui_canvas.config(scrollregion=self.ui_canvas.bbox("all"))


def enable_autoscroll(cls, master_, scroll="xy", *a, **ka):
    """
    cls: Text,Canvas,Listbox,Entry
    """
    master = tk.Frame(master_, bd=2, relief="sunken")
    master.columnconfigure(0, weight=1)
    master.rowconfigure(0, weight=1)

    xbar, ybar = None, None
    if 'x' in scroll:
        xbar = _AutoScrollbar(master, orient=tk.HORIZONTAL)
        xbar.grid(row=1, column=0, sticky="ew")
        ka["xscrollcommand"] = xbar.set
    if 'y' in scroll:
        ybar = _AutoScrollbar(master)
        ybar.grid(row=0, column=1, sticky="ns")
        ka["yscrollcommand"] = ybar.set

    obj = cls(master, **ka)
    obj.grid(row=0, column=0, sticky="nsew")

    if xbar: xbar.config(command=obj.xview)
    if ybar: ybar.config(command=obj.yview)
    obj.pack = master.pack
    obj.grid = master.grid
    obj.place = master.place
    obj.pack_forget = master.pack_forget
    obj.grid_forget = master.grid_forget
    obj.place_forget = master.place_forget()
    return obj


def at_enable_autoscroll(xy="xy"):
    def modified_cls(cls):
        def cls_init(master, *a, **ka):
            return enable_autoscroll(cls, master, scroll=xy, *a, **ka)
        return cls_init
    return modified_cls


# xvar only when wrap="none"
@at_enable_autoscroll()
class TextAutoScroll(tk.Text): pass


@at_enable_autoscroll()
class CanvasAutoScroll(tk.Canvas): pass


@at_enable_autoscroll()
class ListboxAutoScroll(tk.Listbox): pass


@at_enable_autoscroll()
class EntryAutoScroll(tk.Entry): pass


if __name__ == '__main__':
    def debugme_1():
        root = tk.Tk()
        frame = TkYzwFrameAutoScroll(root, bg="red")
        label = tk.Label(frame, text="text", font=("Arial", "512"))
        label.pack(fill="both", expand=1)

        frame.update_scrollregion()

        root.mainloop()


    def debugme_2():
        root = tk.Tk()
        text = enable_autoscroll(tk.Text, root, wrap="none")  # type: tk.Text
        text.pack(fill="both", expand=1)
        root.mainloop()


    def debugme_3():
        root = tk.Tk()
        text = TextAutoScroll(root, wrap="none")
        text.pack(fill="both", expand=1)
        root.mainloop()


    debugme_3()

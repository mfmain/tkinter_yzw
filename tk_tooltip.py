
import tkinter as tk
from tkinter_yzw.tk_autoscrollbar import at_enable_autoscroll


class TkYzwTooltip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, on_tooltip, *la, **ka):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.id = None
        self.tw = None
        self.widget = widget
        self.on_tooltip = on_tooltip
        self.on_tooltip_la = la
        self.on_tooltip_ka = ka
        widget.bind("<Enter>", lambda e: self.enter(e, widget))
        widget.bind("<Leave>", lambda e: self.leave(e, widget))
        widget.bind("<ButtonPress>", lambda e: self.leave(e, widget))

    def enter(self, e, w):
        self.schedule(w)

    def leave(self, e, w):
        self.unschedule(w)
        self.hidetip()

    def schedule(self, w):
        self.unschedule(w)
        self.id = w.after(self.waittime, lambda: self.showtip(w))

    def unschedule(self, w):
        id = self.id
        self.id = None
        if id:
            w.after_cancel(id)

    def showtip(self, w):
        x = y = 0
        x, y, cx, cy = w.bbox("insert")
        x += w.winfo_rootx() + 35
        y += w.winfo_rooty() + 10
        # creates a toplevel window
        self.tw = tk.Toplevel(w)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))

        text = self.on_tooltip(*self.on_tooltip_la, **self.on_tooltip_ka)

        label = tk.Label(self.tw, text=text, justify='left',
                       background="yellow", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
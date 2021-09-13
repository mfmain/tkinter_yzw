# coding: gbk


import tkinter


class TkYzwWidgetSizer:
    def __init__(self, widget, sizeable=True, moveable=True):
        self.widget = widget
        self.sizeable = sizeable
        self.moveable = moveable
        self.widget_cursor_old = self.widget["cursor"]
        self.x_start_drag = 0
        self.y_start_drag = 0

        self.widget.bind("<Button1-Motion>", self.on_button1_motion_move)  # drag 左键拖动

        if moveable:
            self.widget.bind("<Button-1>", self.on_button1_press)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        if sizeable:
            self.widget.bind("<Motion>", self.on_motion)  # hover 鼠标在控件上移动（非拖动）

    def on_button1_press(self, event):
        self.x_start_drag = event.x
        self.y_start_drag = event.y

    def on_button1_motion_move(self, event):
        # The mouse is moved, with mouse button 1 being held down
        if not self.moveable: return
        self.widget["cursor"] = "hand2"
        x = self.widget.winfo_x() + event.x - self.x_start_drag
        y = self.widget.winfo_y() + event.y - self.y_start_drag
        self.widget.place_configure(x=x, y=y, anchor="nw")

    def on_button1_release(self, event):
        self.widget["cursor"] = self.widget_cursor_old

    def on_motion(self, event):
        # The user moved the mouse pointer entirely within a widget.
        w = int(self.widget.place_info()["width"])
        h = int(self.widget.place_info()["height"])
        b_left = 1 <= event.x <= 3
        b_right = 1 <= w - event.x <= 3
        b_top = 1 <= event.y <= 3
        b_bottom = 1 <= h - event.y <= 3

        if b_top and b_left:
            self.widget["cursor"] = "top_left_corner"
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_size_topleft)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        elif b_top and b_right:
            self.widget["cursor"] = "top_right_corner"
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_size_topright)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        elif b_bottom and b_left:
            self.widget["cursor"] = "bottom_left_corner"
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_size_bottomleft)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        elif b_bottom and b_right:
            self.widget["cursor"] = "bottom_right_corner"
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_size_bottomright)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        elif b_right:
            self.widget["cursor"] = "right_side"
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_size_right)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        elif b_bottom:
            self.widget["cursor"] = "bottom_side"
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_size_bottom)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        elif b_left:
            self.widget["cursor"] = "left_side"
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_size_left)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        elif b_top:
            self.widget["cursor"] = "top_side"
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_size_top)
            self.widget.bind("<ButtonRelease-1>", self.on_button1_release)

        else:
            # 拖动并非发生在边缘，这里实现moveable功能
            self.widget["cursor"] = self.widget_cursor_old
            self.widget.bind("<Button1-Motion>", self.on_button1_motion_move)

    def on_button1_motion_size_topleft(self, event):
        x = self.widget.winfo_x() + int(self.widget.place_info()["width"])
        y = self.widget.winfo_y() + int(self.widget.place_info()["height"])
        w = int(self.widget.place_info()["width"]) - event.x
        h = int(self.widget.place_info()["height"]) - event.y
        self.widget.place_configure(x=x, y=y, width=w, height=h, anchor="se")

    def on_button1_motion_size_topright(self, event):
        # w0 = int(self.widget.place_info()["width"])
        h0 = int(self.widget.place_info()["height"])
        x = self.widget.winfo_x()
        y = self.widget.winfo_y() + h0
        w = event.x
        h = h0 - event.y
        self.widget.place_configure(x=x, y=y, width=w, height=h, anchor="sw")

    def on_button1_motion_size_bottomleft(self, event):
        w0 = int(self.widget.place_info()["width"])
        # h0 = int(self.widget.place_info()["height"])
        x = self.widget.winfo_x() + w0
        y = self.widget.winfo_y()
        w = w0 - event.x
        h = event.y
        self.widget.place_configure(x=x, y=y, width=w, height=h, anchor="ne")

    def on_button1_motion_size_bottomright(self, event):
        # w0 = int(self.widget.place_info()["width"])
        # h0 = int(self.widget.place_info()["height"])
        x = self.widget.winfo_x()
        y = self.widget.winfo_y()
        w = event.x
        h = event.y
        self.widget.place_configure(x=x, y=y, width=w, height=h, anchor="nw")

    def on_button1_motion_size_top(self, event):
        x = self.widget.winfo_x()
        y = self.widget.winfo_y() + int(self.widget.place_info()["height"])
        h = int(self.widget.place_info()["height"]) - event.y
        self.widget.place_configure(x=x, y=y, height=h, anchor="sw")

    def on_button1_motion_size_bottom(self, event):
        x = self.widget.winfo_x()
        y = self.widget.winfo_y()
        h = event.y
        self.widget.place_configure(x=x, y=y, height=h, anchor="nw")

    def on_button1_motion_size_left(self, event):
        x = self.widget.winfo_x() + int(self.widget.place_info()["width"])
        y = self.widget.winfo_y()
        w = int(self.widget.place_info()["width"]) - event.x
        self.widget.place_configure(x=x, y=y, width=w, anchor="ne")

    def on_button1_motion_size_right(self, event):
        x = self.widget.winfo_x()
        y = self.widget.winfo_y()
        w = event.x
        self.widget.place_configure(x=x, y=y, width=w, anchor="nw")


if __name__ == '__main__':

    root = tkinter.Tk()

    btn1 = tkinter.Button(root, text="btn1")
    btn1.place(x=50, y=50, width=100, height=100)
    TkYzwWidgetSizer(btn1, sizeable=True, moveable=True)

    root.mainloop()

# coding: gbk

# 通过队列的方式，实现ui模块和主循环的分离，以保证ui模块独立性，逻辑上比虚函数方式要清晰
# 界面处于前台主线程，mainloop单独一个后台线程，每一个事件源一个后台线程
# 前台主线程（界面）的callback只是将请求发送到q中就返回了，其他输入源（比如timer）都可以单独搞一个线程，也是将请求发到q就不管了
# mainloop是后台主控线程，所有的请求都在这里排队执行（单线程）
#     所有callback和timer串行排队执行，谁也不能打断谁，所以可以省去资源竞争的加锁操作


import queue
import traceback
import tkinter as tk


mainq = queue.Queue()  # 主消息队列


class MainUi_:
    self = None  # ready mark
    def __init__(self, title=None, font='微软雅黑 9', icon_fn="", bg=None, geometry=None, topmost=False, layout=None, enable_on_idle=False):
        self.root = tk.Tk()
        self.title = title
        if title: self.root.title(title)
        self.root.option_add('*Font', font)  # '微软雅黑 9 bold'
        if bg: self.root.option_add('*Background', bg)  #  root["bg"] = bg
        if topmost: self.root.wm_attributes("-topmost", 1)
        if icon_fn and os.path.exists(icon_fn): self.root.iconbitmap(icon_fn)

        self.layout_fn = ""
        if layout:
            self.root.protocol("WM_DELETE_WINDOW", self.do_exit)
            if isinstance(layout, str):
                self.layout_fn = layout
                self.layout = yaml_load(g_.fn_app_layout, False, encoding="utf-8")
            elif isinstance(layout, dict):
                self.layout = layout

            geometry = self.layout.get("geometry", None)  #>  'geometry':'405x427+531+450'
            if geometry: self.root.geometry(geometry)

        else:
            self.layout = dict()

        self.self = self  # ready
        self.enable_on_idle = enable_on_idle
        self.after_id = None

    def after(self, ms:int, func):
        self.after_id = self.root.after(ms, func)

    def on_idle(self):
        pass

    def on_root_destroy(self):
        pass

    def on_save_layout(self, f):
        pass

    def do_exit(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        if self.layout_fn:
            with open(g_.fn_app_layout, "w") as f:
                print("geometry:", self.root.winfo_geometry(), file=f)
                self.on_save_layout(f)

        self.on_root_destroy()
        self.root.destroy()

    def on_callback(self, callbackid, widget, *la, **ka):
        # print(f"MainUi.on_callback {time.time()} a={widget, la, ka}")
        mainq.put(("ui", [callbackid, widget, la, ka]))

    def run(self):
        if self.enable_on_idle:
            while True:
                tk.update_idletasks()  # 只更新屏幕,不处理event和callback
                tk.update()  # 绝不能从callback中调用update
                self.on_idle()
        else:
            self.root.mainloop()

    def mainui_dispatch(self, msga: tuple, ui_dispatcher:dict):
        callbackid, widget, la, ka = msga
        # print(f"mainui_dispatch id={callbackid} widget={widget} la={la} ka={ka}")
        func = ui_dispatcher.get(callbackid, None)
        if func is not None:
            func(widget, *la, **ka)


if __name__ == '__main__':

    def thproc_timer():
        while True:
            mainq.put(("timer", None))
            time.sleep(5)


    class MainUi(MainUi_):
        def __init__(self, *la, **ka):
            super().__init__(*la, **ka)
            fr = self.root
            w = tk.Label(fr, text="clickme", font="微软雅黑 28 bold");
            w.pack(side="top", fill="both", expand=1)
            w.bind("<Double-1>",
                   lambda *la, **ka: self.on_callback("demo_bind", w, *la, **ka))

            opm_list = ['Python', 'PHP', 'CPP', 'C', 'Java', 'JavaScript', 'VBScript']
            self.uiv_opm = tk.StringVar(value=opm_list[0])
            w = tk.OptionMenu(fr, self.uiv_opm, *opm_list,
                              command=lambda *la, **ka: self.on_callback("demo_command", w, *la, **ka))
            w.pack(side="top", padx=10, pady=5)
            self.uix_opm = w

            w = tk.Button(fr, text="exit", fg="red",
                          command=lambda *la, **ka: self.on_callback("exit", w, *la, **ka))
            w.pack(side="top", padx=10, pady=5)


    class MainApp():
        def __init__(self):
            threading.Thread(target=self.thproc_mainloop, args=(), daemon=True).start()
            threading.Thread(target=thproc_timer, args=(), daemon=True).start()
            self.ui_dispatcher = {
                "demo_bind": self.on_ui_demo_bind,
                "demo_command": self.on_ui_demo_command,
                "exit": self.on_ui_exit
            }

        def on_ui_demo_bind(self, *la, **ka):
            print(f"demo_bind: la={la} ka={ka}")
            widget, event, *_ = la
            print(f"    widget={widget} event={event}")

        def on_ui_demo_command(self, *la, **ka):
            print(f"demo_command: la={la} ka={ka}")
            widget, *_ = la
            print(f"    widget={widget}")

        def on_ui_exit(self, *la, **ka):
            mainui.do_exit()

        def thproc_mainloop(self):
            while 1:
                try:
                    msgtype, msga = mainq.get(block=True)
                except:
                    traceback.print_exc()
                    continue
                if msgtype == 'ui':
                    mainui.mainui_dispatch(msga, self.ui_dispatcher)
                elif msgtype == 'timer':
                    print("timer")
                else:
                    print(f"unhandled {msgtype} {msga}")


if __name__ == '__main__':
    import threading
    import time

    mainui = MainUi()
    mainapp = MainApp()
    mainui.run()
    print("bye")
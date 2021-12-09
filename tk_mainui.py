# coding: gbk

# 通过队列的方式，实现ui模块和主循环的分离，以保证ui模块独立性，逻辑上比虚函数方式要清晰
# 界面处于前台主线程，mainloop单独一个后台线程，每一个事件源一个后台线程
# 前台主线程（界面）的callback只是将请求发送到q中就返回了，其他输入源（比如timer）都可以单独搞一个线程，也是将请求发到q就不管了
# mainloop是后台主控线程，所有的请求都在这里排队执行（单线程）
#     所有callback和timer串行排队执行，谁也不能打断谁，所以可以省去资源竞争的加锁操作


import os
import chardet
import queue
import traceback
import yaml
import threading
import tkinter as tk


def _yaml_load(fn, encoding=None, default=None):
    if default is None:
        default = dict()

    if os.path.exists(fn):
        bcontent = open(fn, "rb").read()
        if encoding is None:
            encoding = chardet.detect(bcontent)['encoding']
        yml = yaml.load(bcontent.decode(encoding), Loader=yaml.FullLoader)  # throw exception
        return default if yml is None else yml
    else:
        return default


class TkYzwMainUi:
    self = None  # ready mark

    def __init__(self, title=None, font='微软雅黑 9', icon_fn="", bg=None, geometry=None, topmost=False, layout=None, mainq=None):
        """
        param mainq:
            如果传入空，将生成一个self.mainq，供外部引用
        param layout:
            str:  如果是字符串类型，将解释为文件名，并启动layout的自动保存机制
            dict: layout参数字典

        removed param enable_on_idle=None, idletimers=None

        # param enable_on_idle：None or float
        #     experimental feature: 每次idle时sleep的时间
        #     缺省为None，即不启用idle机制，即便重载了self.on_idle，也不会被调用
        #     enable_on_idle指定为0.01，则每秒最多调用100次，取决是界面的复杂程度，依次类推，0.001则最多调用1000次
        #     注意self.on_idle执行期间，界面将得不到响应，所以必须尽快完成，禁止阻塞
        # param timers：None or list of float
        #     experimental feature: 如果没有打开enable_on_idle，会自动打开enable_on_idle=0.01
        #     定时器时长列表，单位为秒，浮点数，
        #     该定时器，基于idle的lazy判断，所以不保证实时性和精度，不补足错过的次数，精度依赖enable_on_idle指定的时间
        #     要实现精确的定时器，可自行构造一个独立的线程发送定时器消息给q
        """
        self.root = tk.Tk()
        if mainq is None:
            self.mainq = queue.Queue()  # 主消息队列
        else:
            self.mainq = mainq

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
                self.layout = _yaml_load(open(self.layout_fn, "r", encoding="gbk"), {})
            elif isinstance(layout, dict):
                self.layout = layout

            if geometry is None:
                geometry = self.layout.get("geometry", None)  #>  'geometry':'405x427+531+450'

        else:
            self.layout = dict()

        if geometry:
            self.root.geometry(geometry)

        # if isinstance(idletimers, list) and len(idletimers) > 0:
        #     if enable_on_idle is None: enable_on_idle = 0.01
        #     t = time.time()
        #     self.a_timercycle = idletimers
        #     self.a_timerlast = [t] * len(idletimers)
        # else:
        #     self.a_timercycle = []
        #
        # self.enable_on_idle = enable_on_idle
        self.after_id = None

        self.root_destroyed = False
        self.self = self  # ready

    def after(self, ms:int, func):
        self.after_id = self.root.after(ms, func)

    def on_idle(self):
        pass

    def on_root_destroy(self):
        pass

    def on_save_layout(self, f):
        pass

    def do_exit(self, *la, **ka):
        # *la, **ka to accept mainui_dispatch's calling convention
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        if self.layout_fn:
            with open(g_.fn_app_layout, "w") as f:
                print("geometry:", self.root.winfo_geometry(), file=f)
                self.on_save_layout(f)

        self.on_root_destroy()
        try:
            self.root.destroy()  # destory all widgets
        except RuntimeError:
            # main thread is not in main loop:
            pass
        self.root.quit()  # quit mainloop even if destroy() failed
        self.root_destroyed = True

    def on_callback(self, callbackid, *la, **ka):
        self.mainq.put(("ui", callbackid, la, ka))

    # def run(self):
    #     if self.enable_on_idle:
    #         # 这里将构造一个死循环，主线程CPU 100%，谨慎打开这个功能
    #         while not self.root_destroyed:
    #             self.root.update_idletasks()  # 只更新屏幕,不处理event和callback
    #             self.root.update()  # 绝不能从callback中调用update
    #             self.mainq.put(("idle"))
    #
    #             time.sleep(self.enable_on_idle)
    #             t = time.time()
    #             for i, cycle in enumerate(self.a_timercycle):
    #                 if t - self.a_timerlast[i] > cycle:
    #                     self.a_timerlast[i] = t
    #                     self.mainq.put(("idletimer", cycle))
    #     else:
    #         self.root.mainloop()

    def run(self):
        self.root.mainloop()

    def mainui_dispatch(self, msga: tuple, ui_dispatcher:dict):
        callbackid, widget, la, ka = msga
        # print(f"mainui_dispatch id={callbackid} widget={widget} la={la} ka={ka}")
        func = ui_dispatcher.get(callbackid, None)
        if func is not None:
            func(widget, *la, **ka)


class TkYzwMainUiApp:
    def __init__(self, mainui:TkYzwMainUi, enable_idle=None, idle_timers=None):
        self.mainui = mainui
        self.mainq = mainui.mainq
        threading.Thread(target=self.thproc_mainloop, args=(enable_idle, idle_timers), daemon=True).start()
        # self.ui_dispatcher = {
        #     "demo_bind": self.on_ui_demo_bind,
        #     "demo_command": self.on_ui_demo_command,
        #     "exit": self.on_ui_exit
        # }

    def on_ui_exit(self, *la, **ka):
        self.mainui.do_exit()

    def thproc_mainloop(self, enable_idle=None, idletimers=None):
        mainq = self.mainq

        if isinstance(idletimers, list) and len(idletimers) > 0:
            if enable_idle is None: enable_idle = 0.01
            t = time.time()
            a_timercycle = idletimers
            a_timerlast = [t] * len(idletimers)
        else:
            a_timercycle = []

        while 1:
            try:
                msgtype, *argv = mainq.get(block=True, timeout=enable_idle)
            except queue.Empty:
                # timeout
                self.on_idle()
                t = time.time()
                for i, cycle in enumerate(a_timercycle):
                    if t - a_timerlast[i] > cycle:
                        a_timerlast[i] = t
                        self.on_idle_timer(cycle)
                continue
            except:
                traceback.print_exc()
                continue

            if msgtype == 'ui':
                callbackid, la, ka = argv
                # mainui.mainui_dispatch(argv[0], self.ui_dispatcher)
                func = getattr(self, f"on_ui_{callbackid}")
                if func: func(*la, **ka)
            elif msgtype == 'idletimer':
                self.on_idle_timer(argv[0])
            else:
                self.on_mainq(msgtype, *argv)

    def on_mainq(self, msgtype, *argv):
        print(f"{msgtype} {msga}")

    def on_idle(self):
        # print("idle")
        pass

    def on_idle_timer(self, cycle:float):
        print(f"idle_timer {cycle}")


if __name__ == '__main__':

    def thproc_timer():
        while True:
            mainq.put(("timer", None))
            time.sleep(5)


    class MainUi(TkYzwMainUi):
        def __init__(self):
            super().__init__(title="mainui demo", geometry='800x500+200+200')
            fr = self.root
            w = tk.Label(fr, text="clickme", font="微软雅黑 28 bold");
            w.pack(side="top", fill="both", expand=1)
            w.bind("<Double-1>", lambda event: self.on_callback("demo_bind_double1", event))

            opm_list = ['Python', 'PHP', 'CPP', 'C', 'Java', 'JavaScript', 'VBScript']
            self.uiv_opm = tk.StringVar(value=opm_list[0])
            w = tk.OptionMenu(fr, self.uiv_opm, *opm_list, command=lambda v: self.on_callback("demo_command_option_menu", v))
            w.pack(side="top", padx=10, pady=5)
            self.uix_om = w

            w = tk.Button(fr, text="exit", fg="red",
                          command=lambda: self.on_callback("exit"))
            w.pack(side="top", padx=10, pady=5)
        #     self.on_idle_cnt = 0
        #
        # def on_idle(self):
        #     self.on_idle_cnt += 1
        #     # print(f"on_idle {self.on_idle_cnt}")

    class MainApp(TkYzwMainUiApp):
        def __init__(self, mainui:TkYzwMainUi, enable_idle=None, idle_timers=None):
            super().__init__(mainui, enable_idle, idle_timers)
            threading.Thread(target=thproc_timer, args=(), daemon=True).start()

        def on_ui_demo_bind_double1(self, event):
            print(f"on_ui_demo_bind_double1: event={event}")

        def on_ui_demo_command_option_menu(self, v):
            print(f"on_ui_demo_command_option_menu {v}")

        def on_mainq(self, msgtype, *argv):
            if msgtype == 'timer':
                # print(f"timer {mainui.on_idle_cnt}")
                print(f"timer")
            else:
                print(f"{msgtype} {msga}")


    import threading
    import time

    mainui = MainUi()
    mainq = mainui.mainq
    mainapp = MainApp(mainui, idle_timers=[0.5, 3])
    mainui.run()
    print("bye")
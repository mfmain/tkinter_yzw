# coding: gbk

# ͨ�����еķ�ʽ��ʵ��uiģ�����ѭ���ķ��룬�Ա�֤uiģ������ԣ��߼��ϱ��麯����ʽҪ����
# ���洦��ǰ̨���̣߳�mainloop����һ����̨�̣߳�ÿһ���¼�Դһ����̨�߳�
# ǰ̨���̣߳����棩��callbackֻ�ǽ������͵�q�оͷ����ˣ���������Դ������timer�������Ե�����һ���̣߳�Ҳ�ǽ����󷢵�q�Ͳ�����
# mainloop�Ǻ�̨�����̣߳����е������������Ŷ�ִ�У����̣߳�
#     ����callback��timer�����Ŷ�ִ�У�˭Ҳ���ܴ��˭�����Կ���ʡȥ��Դ�����ļ�������


import os
import chardet
import queue
import traceback
import yaml
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

    def __init__(self, title=None, font='΢���ź� 9', icon_fn="", bg=None, geometry=None, topmost=False, layout=None, mainq=None, enable_on_idle=False):
        """
        param mainq:
            �������գ�������һ��self.mainq�����ⲿ����
        param layout:
            str:  ������ַ������ͣ�������Ϊ�ļ�����������layout���Զ��������
            dict: layout�����ֵ�
        param enable_on_idle��
            �����True�����ṩ�ص�����self.on_idle����Ϊ�Ḷ��һ���Ĵ��ۣ�����ȱʡΪFalse
            ���ΪFalse������������self.on_idle��Ҳ���ᱻ����
            ע��self.on_dileִ���ڼ䣬���潫�ò�����Ӧ�����Ա��뾡����ɣ���ֹ����
        """
        self.root = tk.Tk()
        if mainq is None:
            self.mainq = queue.Queue()  # ����Ϣ����
        else:
            self.mainq = mainq

        self.title = title
        if title: self.root.title(title)
        self.root.option_add('*Font', font)  # '΢���ź� 9 bold'
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
        self.root.destroy()

    def on_callback(self, callbackid, widget, *la, **ka):
        # print(f"MainUi.on_callback {time.time()} a={widget, la, ka}")
        self.mainq.put(("ui", [callbackid, widget, la, ka]))

    def run(self):
        if self.enable_on_idle:
            while True:
                tk.update_idletasks()  # ֻ������Ļ,������event��callback
                tk.update()  # �����ܴ�callback�е���update
                self.on_idle()
        else:
            self.root.mainloop()

    def mainui_dispatch(self, msga: tuple, ui_dispatcher:dict):
        callbackid, widget, la, ka = msga
        # print(f"mainui_dispatch id={callbackid} widget={widget} la={la} ka={ka}")
        func = ui_dispatcher.get(callbackid, None)
        if func is not None:
            func(widget, *la, **ka)


class TkYzwMainUiApp:
    def __init__(self):
        threading.Thread(target=self.thproc_mainloop, args=(), daemon=True).start()
        # self.ui_dispatcher = {
        #     "demo_bind": self.on_ui_demo_bind,
        #     "demo_command": self.on_ui_demo_command,
        #     "exit": self.on_ui_exit
        # }

    def on_ui_exit(self, widget, *la, **ka):
        mainui.do_exit()

    def thproc_mainloop(self):
        while 1:
            try:
                msgtype, *argv = mainq.get(block=True)
            except:
                traceback.print_exc()
                continue
            if msgtype == 'ui':
                callbackid, widget, la, ka = argv[0]
                # mainui.mainui_dispatch(argv[0], self.ui_dispatcher)
                func = getattr(self, f"on_ui_{callbackid}")
                if func: func(widget, *la, **ka)
            else:
                self.on_mainq(msgtype, *argv)

    def on_mainq(self, msgtype, *argv):
        print(f"{msgtype} {msga}")


if __name__ == '__main__':

    def thproc_timer():
        while True:
            mainq.put(("timer", None))
            time.sleep(5)


    class MainUi(TkYzwMainUi):
        def __init__(self, *la, **ka):
            super().__init__(*la, **ka)
            fr = self.root
            w = tk.Label(fr, text="clickme", font="΢���ź� 28 bold");
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


    class MainApp(TkYzwMainUiApp):
        def __init__(self):
            super().__init__()
            threading.Thread(target=thproc_timer, args=(), daemon=True).start()

        def on_ui_demo_bind(self, widget, *la, **ka):
            print(f"demo_bind: widget={widget}, la={la} ka={ka}")
            event, *_ = la
            print(f"    event={event}")

        def on_ui_demo_command(self, widget, *la, **ka):
            print(f"demo_command: widget={widget}, la={la} ka={ka}")

        def on_mainq(self, msgtype, *argv):
            if msgtype == 'timer':
                print("timer")
            else:
                print(f"{msgtype} {msga}")


if __name__ == '__main__':
    import threading
    import time

    mainui = MainUi()
    mainq = mainui.mainq
    mainapp = MainApp()
    mainui.run()
    print("bye")
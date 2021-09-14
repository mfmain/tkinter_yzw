
# 参考ttk.notebook


import tkinter as tk
import tkinter.ttk as ttk


class _Page:
    def __init__(self, index:int, pagename:str):
        self.index = index
        self.pagename = pagename
        self.frame = None


class TkYzwFramePages(tk.Frame):
    """
    类型属性页,可通过pagename切换Frame
    """
    def __init__(self, master, pagenames:list, page_current=0, *a, **ka):
        super().__init__(master, *a, **ka)

        if not 0 <= page_current < len(pagenames): raise Exception("bad page_current")
        # 因为没有Listbox,所以用只读的Combobox代替, w.current永远返回数组下标,不会返回负数

        self.a_page = [_Page(i, x) for i, x in enumerate(pagenames)]  #type: list[_Page]
        self.d_page = { x.pagename: x for x in self.a_page }          #type: dict[str, _page]
        self.page_current = page_current

        for page in self.a_page:
            page.frame = tk.Frame(self)
            # page.pack_info = frame.pack_info()
            if page.index == page_current:
                page.frame.pack(fill="both", expand=1)

    def page_switch(self, to):
        """
        to: 切换到索引为to(int)或键值为to(str)的页面去
        """
        if isinstance(to, str):
            page = self.d_page[to]
            to = page.index
        if self.page_current == to: return
        self.a_page[self.page_current].frame.pack_forget()
        self.page_current = to
        self.a_page[to].frame.pack(fill="both", expand=1)
        # self.a_page[current].frame.pack(page.pack_info))

    def __getitem__(self, i):
        if isinstance(i, str):
            return self.d_page[i].frame

        if isinstance(i, slice):
            start, stop = i.start, i.stop
            if start is None: start = 0
            if stop is None: stop = len(self.a_page)
            return [x.frame for x in self.a_page][start:stop]
        else:
            return self.a_page[i].frame


class TkYzwSelectList(tk.Frame):
    def __init__(self, master, pagenames:list, page_current=0, command=None, **ak):
        super().__init__(master, **ak)
        self.uiv_pagename = tk.StringVar(value=pagenames[page_current])
        self.ui_pagename = w = ttk.Combobox(self, values=pagenames, textvariable=self.uiv_pagename, state="readonly", justify="center")
        w.pack(fill="both", expand=1)
        w.bind('<<ComboboxSelected>>', self.__on_pagename)
        w.current(page_current)
        self.cb_on_command = command

    def __on_pagename(self, event):
        if event:
            w = event.widget
            w.selection_clear()

        current = self.ui_pagename.current()  # 新的current
        self.cb_on_command(current)


class TkYzwSelectOptionMenu(tk.Frame):
    def __init__(self, master, pagenames:list, page_current=0, command=None, **ak):
        super().__init__(master, **ak)
        self.uiv_pagename = tk.StringVar(value=pagenames[page_current])
        self.ui_pagename = w = tk.OptionMenu(self, self.uiv_pagename, *pagenames, command=self.__on_command)
        w.pack(fill="both", expand=1)
        self.cb_on_command = command

    def __on_command(self, event):
        pagename = self.uiv_pagename.get()
        self.cb_on_command(pagename)


if __name__ == '__main__':
    class Ui:
        def __init__(self):
            self.root = root = tk.Tk()

            pagenames = ['page1', 'page2', 'page3']
            self.ui_pages = TkYzwFramePages(root, pagenames, 1)
            self.ui_sel = TkYzwSelectList(root, pagenames, 1, command=self.ui_pages.page_switch)      # Listbox风格
            #self.ui_sel = TkYzwSelectOptionMenu(root, pagenames, 1, command=self.ui_pages.page_switch)  # OptionMenu风格

            page1 = self.ui_pages['page1']
            tk.Label(page1, text="Page1", font="微软雅黑 10").pack()
            page2 = self.ui_pages['page2']
            tk.Label(page2, text="Page2", font="微软雅黑 20").pack()
            page3 = self.ui_pages['page3']
            tk.Label(page3, text="Page3", font="微软雅黑 30").pack()

            self.ui_sel.pack(side='top', fill='none', expand=0)
            self.ui_pages.pack(side='top', fill='both', expand=1)

    ui = Ui()
    ui.root.mainloop()
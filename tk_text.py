
import tkinter as tk
from tkinter_yzw.tk_autoscrollbar import at_enable_autoscroll


@at_enable_autoscroll()
class TkYzwText(tk.Text):
    def __init__(self, *a, **ka):
        super().__init__(*a, **ka)

        # fontname = 'Verdana'
        fontname = '微软雅黑'
        self.tag_config("h1", font=(fontname, 24, 'bold'))
        self.tag_config("h2", font=(fontname, 20, 'bold'))
        self.tag_config("h3", font=(fontname, 16, 'bold'))

        self.tag_config("red", foreground="red")
        self.tag_config("green", foreground="green")
        self.tag_config("blue", foreground="blue")
        self.tag_config("grey", foreground="grey")

        self.tag_configure('groove', relief="groove", borderwidth=2)

        self.tag_config("hyper", foreground="blue", underline=1, font=(fontname, 12, 'bold'))
        self.tag_config("help", foreground="blue", font=(fontname, 14))
        self.tag_config("consolas", font=("Consolas", 11))

    def mark_input_prev(self, markname:str):
        istart, iend = self.tag_prevrange(markname, tk.CURRENT + '+1c')  # 查找当前处于哪个tag<y>，返回该区间
        return self.get(istart, iend)  # 返回该区间的文本

    def mark_input_next(self, markname:str):
        istart, iend = self.tag_nextrange(markname, tk.CURRENT + '+1c')  # 查找当前处于哪个tag<y>，返回该区间
        return self.get(istart, iend)  # 返回该区间的文本

    def tag_input(self, tagname:str):
        ranges = self.tag_ranges(tagname)
        if not ranges:
            return None
        else:
            istart, iend, *_ = ranges
            return self.get(istart, iend)  # 返回该区间的文本

    def tag_output(self, tagname:str, output:str):
        """输出到指定tag处"""
        ranges = self.tag_ranges(tagname)
        if not ranges:
            # self.insert("end", output, tagname)
            pass
        else:
            istart, iend, *_ = ranges
            self.delete(istart, iend)
            self.insert(istart, output, tagname)

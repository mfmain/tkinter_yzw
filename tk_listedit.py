# coding: utf8

# see https://stackoverflow.com/questions/14459993/tkinter-listbox-drag-and-drop-with-python
# there are samples for selectmode MULTIPLE


import tkinter as tk
from tk_dialog import TkYzwDialog


class _DlgItemEditor(TkYzwDialog):
    def __init__(self, master, itemtext="", title=None, **ka):
        super().__init__(master, title=title, **ka)

        self.uiv_edit1 = tk.StringVar(value=itemtext)
        tk.Entry(self, textvariable=self.uiv_edit1).pack(fill="both", expand=0)

        fr = tk.Frame(self); fr.pack(side="top", pady=5, fill="both")

        tk.Button(fr, text="OK", command=self.on_OK).pack(side="left", fill="both", expand=1)
        tk.Button(fr, text="CANCEL", command=self.on_CANCEL).pack(side="left", fill="both", expand=1)

    def on_OK(self):
        self.destroy()
        self.result = self.uiv_edit1.get()

    def on_CANCEL(self):
        self.destroy()
        self.result = None


class TkYzwListedit(tk.Listbox):
    def __init__(self, master, items=None, cls_item_editor=None, **kw):
        if items is None:
            items = []
        if cls_item_editor is None:
            cls_item_editor = _DlgItemEditor
        self.cls_item_editor = cls_item_editor

        kw['selectmode'] = tk.SINGLE
        if "listvariable" not in kw: kw['listvariable'] = tk.Variable()
        tk.Listbox.__init__(self, master, kw)
        self.var = self.cget('listvariable')
        self.curIndex = None

        for x in items:
            self.insert(tk.END, x)
        self.insert(tk.END, "+")

        self.bind('<Button-1>', self.setCurrent)
        self.bind('<B1-Motion>', self.shiftSelection)
        self.bind('<Double-Button-1>', self.on_double1)
        self.bind('<KeyPress>', self.on_key)

    def setCurrent(self, event):
        self.curIndex = self.nearest(event.y)

    def shiftSelection(self, event):
        i = self.nearest(event.y)
        if i < self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i+1, x)
            self.curIndex = i
        elif i > self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i-1, x)
            self.curIndex = i

    def on_layout_save(self):
        var = self.cget('listvariable')
        a = list(self.getvar(var))
        a.remove('+')
        return a

    def on_double1(self, ev):
        # edit item
        print("edit %r"%ev)
        a_sel = self.curselection()
        print(f"curselection {a_sel}")
        if not a_sel: return
        sel = a_sel[0]
        text = self.get(sel)
        print(f"get {text}")
        if text == '+':
            dlg = self.cls_item_editor(self.master)
            result = dlg.run()
            if result:
                self.insert(sel, result)
        else:
            dlg = self.cls_item_editor(self, itemtext=text)
            result = dlg.run()
            if result:
                self.delete(sel)
                self.insert(sel, result)

    def on_key(self, ev):
        print("on_key %r"%ev)
        a_sel = self.curselection()
        print(f"curselection {a_sel}")
        if ev.keysym == "Delete":
            for sel in a_sel:
                text = self.get(sel)
                if text != '+':
                    self.delete(sel)


if __name__ == '__main__':
    class Ui:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("tk_listedit demo")

            items = ["111", "2222", "33333"]
            self.uix_le = TkYzwListedit(self.root, items=items)
            self.uix_le.pack()

            fr = tk.Frame()
            fr.pack(side="top", fill='x')
            tk.Button(fr, text="OK", command=self.on_ok, bg="#d0e0d0").pack(side="left")
            tk.Button(fr, text="EXIT", command=self.root.destroy, bg="#d0e0d0").pack(side="left")

        def on_ok(self):
            a = self.uix_le.on_layout_save()
            print(a)

    ui = Ui()
    ui.root.mainloop()
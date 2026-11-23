# UI as an Independent Module: As Simple as Using print, Interacting with an Event-Driven MainApp

`tkinter_yzw` 是一个以 tkinter 为底座的个人工具库，核心主张就是标题里那句话：
**把 UI 做成独立模块，工作线程与事件驱动的主程序交互像用 print 一样简单**。

- **主循环框架**（tk_mainui）：所有事件（UI 回调、线程间消息、定时器、idle）串行进一个 `mainq` 队列统一分发，
  工作线程只需 `mainq.put(("事件类型", 数据))`，回调函数里无需任何锁。
- **一套实用控件**：树、平铺表、grid 表格、表单、类型属性页、tooltip、自动滚动条等，多为 `tk.Frame` 子类，内聚自包。
- **每个模块自带 demo**：进入包目录直接 `python tk_xxx.py` 就能跑，demo 就是用法文档。
- **配套工具**：tlgview（treecmd 协议日志/UDP 可视化器）、tableview（YAML 驱动的数据表格）、newpp（照片归档）。

开发环境为 Windows + Python 3（tkinter 自带）；无额外主题/插件机制，源码即全部。

## 安装

```bash
pip install -r requirements.txt
```

- 包本身仅需 `sortedcontainers`（tk_tree 兄弟节点排序）和 `PyYAML`（tk_mainui 窗口布局存取）
- tools/ 额外需 `pywin32`、`redis`、`exifread`（见各工具说明）

作为包引用：`import tkinter_yzw as tky`（`__init__.py` 已导出全部控件）。

## 快速开始：主循环 + 工作线程

最推荐的骨架（精简自 tk_mainui.py 自带 demo）：

```python
import time, threading
import tkinter as tk
from tkinter_yzw import TkYzwMainUi, TkYzwMainUiApp

class MainUi(TkYzwMainUi):                     # UI 壳：窗口/字体/布局存取
    def __init__(self):
        super().__init__(title="demo", geometry="800x500+200+200")
        w = tk.Label(self.root, text="double click me", font="微软雅黑 28 bold")
        w.pack(fill="both", expand=1)
        w.bind("<Double-1>", lambda e: self.on_callback("demo_double1", e))
        tk.Button(self.root, text="exit", fg="red",
                  command=lambda: self.on_callback("exit")).pack()

class MainApp(TkYzwMainUiApp):                 # 主循环：串行分发所有事件
    def __init__(self, mainui, *la, **ka):
        super().__init__(mainui, *la, **ka)
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):                          # 工作线程：print 式上报，无锁
        while True:
            self.mainq.put(("tick", 123))
            time.sleep(5)

    def on_mainq(self, msgtype, *argv):        # mainq 自定义事件的去处
        print(f"on_mainq {msgtype} {argv}")

    def on_ui_demo_double1(self, event):       # on_callback("demo_double1") 自动路由到这里
        print("double click!", event)

mainui = MainUi()
mainapp = MainApp(mainui, timers=[1], enable_idle=0.1, idle_timers=[0.5, 3])
mainapp.run()
```

约定：

- UI 事件：控件回调里调 `mainui.on_callback("id", *args)`，主循环类实现 `on_ui_id(*args)` 接收
- 工作线程：`mainq.put((类型, 数据))` → `on_mainq(类型, *数据)`；`("exit",)` 停主循环
- 定时：`timers=[秒,…]` → `on_mainq_timer(tvsec)`；`enable_idle`/`idle_timers` → `on_idle()`/`on_idle_timer(cycle)`
- 窗口几何等布局可经 `on_save_layout` 存入 yaml，下次启动自动恢复

## 控件一览

| 模块 | 主要类 | 说明 |
|---|---|---|
| tk_mainui | `TkYzwMainUi` / `TkYzwMainUiApp` / `TkYzwTimer` | 主循环框架：mainq 事件串行化、UI 回调自动路由、定时器/idle、布局存取 |
| tk_tree | `TkYzwFrameTree` | 树控件：统一的列规格语法、路径式 iid（easy_*系列）、sorted_key 兄弟排序、拖拽（dnd）、**treecmd 协议**（见下文）；附 `FrameTaskTree` 任务列表示例 |
| tk_listview | `TkYzwFrameListview` | 平铺表（行情监控类）：maxrows FIFO/满则丢弃、movetop_on_update 更新置顶、点击表头按 keyfunc 排序、拖拽重排；可用 `wx.column('#0', width=0)` 隐接树列变纯表格 |
| tk_table | `TkYzwTable` | grid 布局表格：cellkey 定位单元格，cell_hide/row_hide 收起单元格/整行后布局自动补位 |
| tk_sheet | `TkYzwSheet*` 系列 | 表单式表格（较早）：单元格是 Entry/Check/自定义控件，按 rowname/colname 寻址，配套取值接口 |
| tk_listedit | `TkYzwListedit` | 可编辑列表控件（弹窗编辑，配 TkYzwDialog） |
| tk_dialog | `TkYzwDialog` | 模态对话框模板：on_ok/on_cancel 先取结果再销毁 |
| tk_pages | `TkYzwFramePages` / `TkYzwSelectList` / `TkYzwSelectOptionMenu` | 类型属性页（按 pagename 切换 Frame）+ 两种选择控件 |
| tk_index | `TkYzwFrameIndexedListbox` | 字典索引导航框：输入过滤（`>` 起始匹配 / `*` 模糊）、历史回退 |
| tk_text | `TkYzwText` | Text 增强：预设 h1/h2/h3、四色、hyper、consolas 等 tag；tag_input/tag_output 往 tag 占位区写内容；自动滚动 |
| tk_tooltip | `TkYzwTooltip` | 任意控件的悬停提示 |
| tk_autoscrollbar | `TkYzwFrameAutoScroll` / `enable_autoscroll` / `at_enable_autoscroll` | 卷轴条自动隐现；装饰器给 Text/Canvas/Listbox/Entry 注入自动滚动行为 |
| tk_sizer | `TkYzwWidgetSizer` | 给 place() 定位的控件加上鼠标拖拽移动、边缘拖拽缩放 |

tk_tree 与 tk_listview 共享同一套列规格语法但各司其职：层级树/协议走 tree，平铺行走 listview，二者不互相依赖。

## tools

### tlgview — treecmd 协议日志/UDP 可视化器

```bash
python tools/tlgview.py tools/tlgview_sample.tlg   # 回放文件（允许 backtick 执行）
python tools/tlgview.py -u 17878                   # 监听 udp 127.0.0.1:17878（禁用 backtick 执行）
```

把每行 treecmd 协议渲染成一棵实时刷新的树；每个 UDP 来源地址各自一棵根。常用参数：
`-H` 监听地址（0.0.0.0 对外开放）、`-l` 转写日志、`--source_encoding/--log_encoding`、
`--with_lineno`、`--polltv`。文件头有 pyinstaller 打单文件 exe 的一行命令。

### tableview — YAML 驱动的数据表格

`python tools/tableview.py tableview.yaml`：表/列/单元格样式全部由 yaml 声明，数据源为 redis，
支持选中单元格拷贝到剪贴板（win32）。配套 `tableview.yaml`、`tableview_layout.yaml`。

### newpp — 照片归档

```bash
python tools/newpp.py [options] <srcdir> <dstdir>
```

按“原始时间 → 照片 EXIF 时间 → 文件名时间 → 文件时间戳”优先级提取目标目录名归档；
目标已存在同名文件时比较内容，相同则归入 `same` 分支（exifread 提取拍摄时间）。

## treecmd 协议（日志扩展名 `.tlg`，播放器 `tools/tlgview.py`）

`TkYzwFrameTree.treecmd(cmd, rootpath, rootpath_)`（见 tk_tree.py）是一个“面向树的 print”协议：
每行一条命令，首字符是命令字母，其余是参数。`tools/tlgview.py` 把 `.tlg` 文件或 UDP
每个来源地址的每一行送进同一棵树。

- 参数里的路径都是相对路径，内部自动前缀 `rootpath_`；`.` 表示“本来源根节点”，r/R/i/I/x/z/t 通用。
- 来源寻址：UDP 模式每个来源地址自动得到根节点 `[1]`、`[2]`…；`t title` 只重命名**本来源**的根。文件模式 = 单来源。
- 返回值：True = 本行已识别（空行也返回 True，静默吞掉）；False = 未识别，交给宿主处理（tlgview 直接忽略，即不认识的行不进树）。
- 健壮性：缺参数的裸命令（如单独一个 `r`）按未识别处理；单行处理出错打印 traceback 后继续，不会停死刷新。

```text
t title               # 设置本来源根节点显示文本（t 后必须有空格；t紧跟路径是 tag 命令，注意区分）
X                     # 清空全部
xaaa/bbb              # 删除子树 aaa/bbb
xaaa/bbb/             # 末尾斜杠：只删后代保留自身；x. = 本来源根
rxxx/yyy msg          # 设置路径 xxx/yyy 的 msg（右栏），缺失则自动创建全部上级；已存在则只更新 msg
Rxxx/yyy msg          # 同 r，但需要创建时插在末尾（r 插在头部）
ixxx yyy msg          # 在 xxx 下插入子节点 yyy，显示文本 = yyy
ixxx yyy:text msg     # …显示文本 = text（text 不能含冒号，会被截断）
ixxx :text msg        # 匿名节点：iid 由系统分配（I001、I002…），不参与去重
ixxx :<ts>  msg       # 匿名节点显示接收时间 HH:MM:SS（只对实时接收有意义，回放文件无意义）
ixxx :<seq> msg       # 匿名节点显示自增序号（每个父节点单独计数）
Ixxx yyy:text:sk msg  # 同 i 但插在末尾；第三段 sorted_key 参与排序（排序时忽略插入位置）
zxxx/yyy 0            # 折叠（取 vim 的 z）；1 展开，认 True/False，其它值一律按展开处理
txxx/yyy tag1 tag2    # 设置 tag（整体覆盖）。h1,h2,h3,red,green,blue,grey 由 tlgview 配置
`<code>               # 高级：等于执行 self.<code>，见下方
```

命名 vs 匿名：命名节点的 iid 就是路径本身，重复插入同名节点 = 更新（text/values 被覆盖，不报错）；
要“累积记录”用匿名节点 `ixxx :text`，i 往头插、I 往尾插。

高级命令 backtick：

- 整行按 `exec("self." + 命令)` 执行，执行环境里可用局部变量 `rootpath`/`rootpath_`，例如：
  `` `easy_item(rootpath_+"Usage", tags=["h1","blue"]) ``（见 tools/tlgview_sample.tlg）
- 受类属性 `treecmd_allow_exec` 门控（默认 True）：tlgview 文件模式保持开启，UDP 模式置 False
  （不执行，仅打印该行）。不可信输入必须关闭。
- 执行失败只打印 traceback，不影响后续行。

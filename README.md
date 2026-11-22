# UI as an Independent Module: As Simple as Using print, Interacting with an Event-Driven MainApp

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

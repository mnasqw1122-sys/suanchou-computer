# -*- coding: utf-8 -*-
"""
算 筭 操 作 系 统  v3
============================================================
「不需要显示算筭码——就像现代系统不显示二进制一样。」

用户看到的是：
  算术结果 → 大号数字，像计算器
  识字结果 → 大字 + 含义 + 笔画分解动画
  校字结果 → 两字并列对比，差异高亮
  序列输出 → 卡片式排列，一目了然

运行：py suan_os.py  或  双击 suan_os.exe
"""
import sys, os, tkinter as tk
from tkinter import ttk, scrolledtext
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber
from suanchou_zupu import (
    SuanChouZupuAssembler, ZUPU_TABLE, ZUPU_CATEGORIES, TIANGAN, ZUPU_MEANING
)
from suanchou_vm import SuanChouVM
from stroke_dictionary import StrokeDictionary, Character
from extended_strokes import EXTENDED_STROKE_DATA


# ═══════════════════════════════════════════════════════════════
# 应用级渲染器 —— 用户看到的是有意义的结果，不是算筭码
# ═══════════════════════════════════════════════════════════════

class AppRenderer:
    """只渲染有意义的结果，不渲染算筭码"""

    @staticmethod
    def title(canvas, text, y, color="#e94560"):
        canvas.create_text(450, y, text=text, fill=color,
                           font=("Microsoft YaHei", 14, "bold"), anchor="center")

    @staticmethod
    def subtitle(canvas, text, y, color="#8b949e"):
        canvas.create_text(450, y, text=text, fill=color,
                           font=("Microsoft YaHei", 10), anchor="center")

    @staticmethod
    def big_result(canvas, text, y, color="#3fb950", size=48):
        return canvas.create_text(450, y, text=text, fill=color,
                                   font=("Microsoft YaHei", size, "bold"),
                                   anchor="center")

    @staticmethod
    def char_card(canvas, char_obj, x, y, highlight=False):
        """画一个汉字卡片：大字 + 含义"""
        w, h = 180, 120
        bg = "#161b22"
        border = "#e94560" if highlight else "#30363d"

        canvas.create_rectangle(x, y, x + w, y + h, fill=bg, outline=border, width=2)
        canvas.create_text(x + w / 2, y + 35, text=char_obj.char,
                           fill="#e6edf3", font=("Microsoft YaHei", 32, "bold"))
        canvas.create_text(x + w / 2, y + 70, text=char_obj.meaning.split("；")[0],
                           fill="#8b949e", font=("Microsoft YaHei", 10))
        canvas.create_text(x + w / 2, y + 95,
                           text=f"{char_obj.pinyin}  {char_obj.stroke_count}画  {char_obj.category}",
                           fill="#484f58", font=("Microsoft YaHei", 8))

    @staticmethod
    def compare_cards(canvas, char_a, char_b, y, diff_bits, common_bits):
        """两个字并排对比"""
        # 两个卡片并排
        AppRenderer.char_card(canvas, char_a, 180, y)
        AppRenderer.char_card(canvas, char_b, 540, y)

        # 连接线 + 比较结果
        cy = y + 140
        canvas.create_line(360, y + 60, 540, y + 60, fill="#30363d", width=1, dash=(4, 4))
        canvas.create_text(450, cy, text=f"差异 {diff_bits} 位  ·  共同 {common_bits} 位",
                           fill="#79c0ff", font=("Microsoft YaHei", 11, "bold"))

        # 语义标签
        tags_a = "、".join(char_a.semantic_tags[:3]) if char_a.semantic_tags else "无"
        tags_b = "、".join(char_b.semantic_tags[:3]) if char_b.semantic_tags else "无"
        common_tags = set(char_a.semantic_tags) & set(char_b.semantic_tags)
        tag_text = ""
        if common_tags:
            tag_text = f"共同标签：「{'」「'.join(common_tags)}」"

        return cy + 30, tag_text

    @staticmethod
    def sequence_cards(canvas, values, y, title=""):
        """画一行数值卡片"""
        if title:
            AppRenderer.title(canvas, title, y - 30)
        x = max(80, 450 - len(values) * 45)
        for i, v in enumerate(values):
            cx = x + i * 90
            bg = "#161b22"
            canvas.create_rectangle(cx, y, cx + 78, y + 72, fill=bg, outline="#30363d", width=1)
            canvas.create_text(cx + 39, y + 25, text=str(v),
                               fill="#3fb950", font=("Consolas", 16, "bold"))
            canvas.create_text(cx + 39, y + 52, text=f"#{i+1}",
                               fill="#484f58", font=("Microsoft YaHei", 7))
        return y + 90

    @staticmethod
    def paint_chars(canvas, char_objects, y):
        """画多个已识别的字"""
        n = len(char_objects)
        x_start = 450 - n * 110
        for i, co in enumerate(char_objects):
            AppRenderer.char_card(canvas, co, x_start + i * 220, y, highlight=(i == 0))
        return y + 140


# ═══════════════════════════════════════════════════════════════
# 算筭操作系统 v3
# ═══════════════════════════════════════════════════════════════

class SuanChouOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("算筭操作系统  SuanChou OS v3")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0d1117")
        self.root.minsize(950, 600)

        self.char_data = {}
        self._init_char_data()

        # 计算字符在 VM 内存中的地址（按字典插入顺序）
        self.char_addr = {}
        addr = 32
        for cn in self.char_data:
            self.char_addr[cn] = addr
            addr += 1

        AD = self.char_addr  # 简写

        self.programs = {
            "日月校.suan": (
                f"取 甲, #{AD['日']}\n取 乙, #{AD['月']}\n"
                "校 甲, 乙\n印 甲\n印 辛\n停",
                "比较「日」和「月」的笔画差异"
            ),
            "阶乘.suan": (
                "载 甲, #1\n载 乙, #5\n载 丙, #1\n"
                "乘阶：\n乘 甲, 乙\n减 乙, 丙\n比 乙, 丙\n"
                "大 #乘阶\n乘 甲, 乙\n印 甲\n停",
                "计算 5! = 120"
            ),
            "倒计时.suan": (
                "载 甲, #9\n载 乙, #1\n"
                "循环：\n印 甲\n减 甲, 乙\n比 甲, 乙\n"
                "大 #循环\n印 甲\n停",
                "从 9 倒数到 1"
            ),
            "累加.suan": (
                "载 甲, #0\n载 乙, #5\n载 丙, #1\n"
                "循环：\n加 甲, 乙\n减 乙, 丙\n比 乙, 丙\n"
                "大 #循环\n加 甲, 乙\n印 甲\n停",
                "计算 5+4+3+2+1 = 15"
            ),
            "识字.suan": (
                f"取 甲, #{AD['日']}\n识 甲\n"
                f"取 甲, #{AD['月']}\n识 甲\n"
                f"取 甲, #{AD['木']}\n识 甲\n印 甲\n停",
                "识别多个汉字：日、月、木"
            ),
            "计算器.suan": (
                "； ╔══════════════════════════════════════╗\n"
                "； ║  算筭计算器                        ║\n"
                "； ║  修改下面数字然后运行，即可计算    ║\n"
                "； ╚══════════════════════════════════════╝\n"
                "\n"
                "载 甲, #38   ； 被加数\n"
                "载 乙, #17   ； 加数\n"
                "加 甲, 乙    ； 甲 = 38 + 17\n"
                "印 甲        ； 输出：55\n"
                "\n"
                "载 甲, #100  ； 被减数\n"
                "载 乙, #36   ； 减数\n"
                "减 甲, 乙    ； 甲 = 100 - 36\n"
                "印 甲        ； 输出：64\n"
                "\n"
                "载 甲, #12   ； 被乘数\n"
                "载 乙, #8    ； 乘数\n"
                "乘 甲, 乙    ； 甲 = 12 × 8\n"
                "印 甲        ； 输出：96\n"
                "\n"
                "载 甲, #99   ； 被除数\n"
                "载 乙, #7    ； 除数\n"
                "除 甲, 乙    ； 甲 = 商, 辛 = 余数\n"
                "印 甲        ； 输出商：14\n"
                "印 辛        ； 输出余数：1\n"
                "\n"
                "载 甲, #1    ； 阶乘起始\n"
                "载 乙, #6    ； 计算 6!\n"
                "载 丙, #1\n"
                "乘阶：\n"
                "乘 甲, 乙\n"
                "减 乙, 丙\n"
                "比 乙, 丙\n"
                "大 #乘阶\n"
                "乘 甲, 乙\n"
                "印 甲        ； 输出：720\n"
                "\n"
                "停",
                "多功能计算器：加减乘除 + 阶乘"
            ),
            "图形演示.suan": (
                "； ╔══════════════════════════════════════╗\n"
                "； ║  图形演示 — 纯算筭字谱程序         ║\n"
                "； ║  输出直接在画布上渲染               ║\n"
                "； ╚══════════════════════════════════════╝\n"
                "\n"
                "； — 绘制大号数字 —\n"
                "载 甲, #42    ； 甲 = 42\n"
                "绘数 甲      ； 画布上绘制大号 42\n"
                "\n"
                "载 甲, #99\n"
                "载 乙, #7\n"
                "除 甲, 乙    ； 99÷7 = 14 余 1\n"
                "绘框 甲, 辛 ； 框内显示 14 和 1\n"
                "\n"
                "； — 阶乘 —\n"
                "载 甲, #1\n"
                "载 乙, #5\n"
                "载 丙, #1\n"
                "乘阶：\n"
                "乘 甲, 乙\n"
                "减 乙, 丙\n"
                "比 乙, 丙\n"
                "大 #乘阶\n"
                "乘 甲, 乙\n"
                "绘数 甲      ； 绘制 120\n"
                "\n"
                f"； — 绘制汉字卡片 —\n"
                f"取 甲, #{AD['木']}\n"
                "绘字 甲      ； 画「木」字卡片\n"
                f"取 甲, #{AD['日']}\n"
                "绘字 甲      ； 画「日」字卡片\n"
                "\n"
                "停",
                "图形演示：数字/汉字卡片/信息框"
            ),
            "图形计算器.suan": (
                "； ╔══════════════════════════════════════╗\n"
                "； ║  图形计算器 — 纯算筭字谱程序        ║\n"
                "； ║  点击按钮即可计算                    ║\n"
                "； ╚══════════════════════════════════════╝\n"
                "\n"
                "； — 初始化 —\n"
                "清屏\n"
                "载 甲, #0    ； 甲 = 当前数字\n"
                "载 乙, #0    ； 乙 = 暂存数\n"
                "载 丁, #0    ； 丁 = 运算符 (0=无)\n"
                "载 辛, #0    ； 辛 = 0 用于比较\n"
                "\n"
                "； — 绘制按钮 —\n"
                "； 第0行：运算符\n"
                "载 甲, #0     ； 位置 0\n"
                "载 乙, #10    ； 标签+\n"
                "置键 甲, 乙   ； 按钮(0,0) = +\n"
                "载 甲, #1     ； 位置 1\n"
                "载 乙, #11    ； 标签-\n"
                "置键 甲, 乙   ； 按钮(0,1) = -\n"
                "载 甲, #2     ； 位置 2\n"
                "载 乙, #12    ； 标签×\n"
                "置键 甲, 乙   ； 按钮(0,2) = ×\n"
                "载 甲, #3     ； 位置 3\n"
                "载 乙, #13    ； 标签÷\n"
                "置键 甲, 乙   ； 按钮(0,3) = ÷\n"
                "\n"
                "； 第1行：7 8 9 C\n"
                "载 甲, #10    ； (1,0)\n"
                "载 乙, #7\n"
                "置键 甲, 乙\n"
                "载 甲, #11    ； (1,1)\n"
                "载 乙, #8\n"
                "置键 甲, 乙\n"
                "载 甲, #12    ； (1,2)\n"
                "载 乙, #9\n"
                "置键 甲, 乙\n"
                "载 甲, #13    ； (1,3)\n"
                "载 乙, #15    ； C=15\n"
                "置键 甲, 乙\n"
                "\n"
                "； 第2行：4 5 6 ⌫\n"
                "载 甲, #20\n"
                "载 乙, #4\n"
                "置键 甲, 乙\n"
                "载 甲, #21\n"
                "载 乙, #5\n"
                "置键 甲, 乙\n"
                "载 甲, #22\n"
                "载 乙, #6\n"
                "置键 甲, 乙\n"
                "载 甲, #23\n"
                "载 乙, #16    ； ⌫=16\n"
                "置键 甲, 乙\n"
                "\n"
                "； 第3行：1 2 3 =\n"
                "载 甲, #30\n"
                "载 乙, #1\n"
                "置键 甲, 乙\n"
                "载 甲, #31\n"
                "载 乙, #2\n"
                "置键 甲, 乙\n"
                "载 甲, #32\n"
                "载 乙, #3\n"
                "置键 甲, 乙\n"
                "载 甲, #33\n"
                "载 乙, #14    ； ==14\n"
                "置键 甲, 乙\n"
                "\n"
                "； 第4行：0 .\n"
                "载 甲, #40\n"
                "载 乙, #0\n"
                "置键 甲, 乙\n"
                "载 甲, #42\n"
                "载 乙, #17    ； .=17\n"
                "置键 甲, 乙\n"
                "\n"
                "； 初始显示\n"
                "载 甲, #0\n"
                "绘文 甲       ； 显示 0\n"
                "\n"
                "； ===== 主循环 =====\n"
                "再试：\n"
                "待触          ； 等待点击\n"
                "触值 戊       ； 戊 = 点击值\n"
                "\n"
                "； 判断：戊 < 10 → 数字\n"
                "载 丙, #10\n"
                "比 戊, 丙\n"
                "大 #管符       ； 戊 >= 10 → 运算符/命令\n"
                "\n"
                "； == 数字处理 ==\n"
                "； 甲 = 甲*10 + 戊\n"
                "载 丙, #10\n"
                "乘 甲, 丙     ； 甲 *= 10\n"
                "加 甲, 戊     ； 甲 += 新数字\n"
                "绘文 甲       ； 显示\n"
                "跳 #再试\n"
                "\n"
                "； == 运算符/命令处理 ==\n"
                "管符：\n"
                "载 丙, #10\n"
                "比 戊, 丙\n"
                "等 #按加       ； 戊=10 → +\n"
                "载 丙, #11\n"
                "比 戊, 丙\n"
                "等 #按减       ； 戊=11 → -\n"
                "载 丙, #12\n"
                "比 戊, 丙\n"
                "等 #按乘       ； 戊=12 → ×\n"
                "载 丙, #13\n"
                "比 戊, 丙\n"
                "等 #按除       ； 戊=13 → ÷\n"
                "载 丙, #14\n"
                "比 戊, 丙\n"
                "等 #按等       ； 戊=14 → =\n"
                "载 丙, #15\n"
                "比 戊, 丙\n"
                "等 #按清       ； 戊=15 → C\n"
                "载 丙, #16\n"
                "比 戊, 丙\n"
                "等 #按退       ； 戊=16 → ⌫\n"
                "跳 #再试\n"
                "\n"
                "； == + ==\n"
                "按加：\n"
                "载 乙, 甲     ； 保存当前数\n"
                "载 丁, #10    ； 操作 = +\n"
                "载 甲, #0     ； 甲 归零等新数\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "按减：\n"
                "载 乙, 甲\n"
                "载 丁, #11    ； 操作 = -\n"
                "载 甲, #0\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "按乘：\n"
                "载 乙, 甲\n"
                "载 丁, #12    ； 操作 = ×\n"
                "载 甲, #0\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "按除：\n"
                "载 乙, 甲\n"
                "载 丁, #13    ； 操作 = ÷\n"
                "载 甲, #0\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "； == = ==\n"
                "按等：\n"
                "载 丙, #10\n"
                "比 丁, 丙\n"
                "等 #做加       ； 丁=10 → +\n"
                "载 丙, #11\n"
                "比 丁, 丙\n"
                "等 #做减       ； 丁=11 → -\n"
                "载 丙, #12\n"
                "比 丁, 丙\n"
                "等 #做乘       ； 丁=12 → ×\n"
                "载 丙, #13\n"
                "比 丁, 丙\n"
                "等 #做除       ； 丁=13 → ÷\n"
                "跳 #再试\n"
                "\n"
                "做加：\n"
                "加 乙, 甲     ； 乙 = 乙 + 甲\n"
                "载 甲, 乙     ； 甲 = 结果\n"
                "载 丁, #0     ； 操作清除\n"
                "绘文 甲       ； 显示\n"
                "跳 #再试\n"
                "\n"
                "做减：\n"
                "减 乙, 甲     ； 乙 = 乙 - 甲\n"
                "载 甲, 乙\n"
                "载 丁, #0\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "做乘：\n"
                "乘 乙, 甲     ； 乙 = 乙 × 甲\n"
                "载 甲, 乙\n"
                "载 丁, #0\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "做除：\n"
                "除 乙, 甲     ； 乙 = 乙÷甲, 辛=余\n"
                "载 甲, 乙\n"
                "载 丁, #0\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "； == C ==\n"
                "按清：\n"
                "载 甲, #0\n"
                "载 乙, #0\n"
                "载 丁, #0\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "； == ⌫ ==\n"
                "按退：\n"
                "载 丙, #10\n"
                "除 甲, 丙     ； 甲÷10 去掉个位\n"
                "绘文 甲\n"
                "跳 #再试\n"
                "\n"
                "停\n",
                "纯算筭字谱图形计算器"
            ),
        }

        self._build_ui()
        self._open("阶乘.suan")

    def _init_char_data(self):
        dic = StrokeDictionary()
        for cn, data in EXTENDED_STROKE_DATA.items():
            if cn in dic._characters:
                obj = dic._characters[cn]
            else:
                obj = Character(
                    char=cn, stroke_sequence=data["strokes"],
                    meaning=data["meaning"], radical=data["radical"],
                    category=data["category"], semantic_tags=data["tags"],
                    pinyin=data["pinyin"],
                )
            if obj._encoded is None:
                obj.encode()
            self.char_data[cn] = obj

    def _build_ui(self):
        # 顶栏
        top = tk.Frame(self.root, bg="#161b22", height=40)
        top.pack(fill=tk.X, side=tk.TOP)
        top.pack_propagate(False)
        tk.Label(top, text="算筭操作系统", font=("Microsoft YaHei", 14, "bold"),
                 fg="#e94560", bg="#161b22").pack(side=tk.LEFT, padx=16, pady=6)

        # 工具栏
        bar = tk.Frame(self.root, bg="#0d1117", height=32)
        bar.pack(fill=tk.X, side=tk.TOP)
        bb = {"font": ("Microsoft YaHei", 9), "bd": 0, "relief": tk.FLAT,
              "padx": 14, "pady": 4, "cursor": "hand2"}
        tk.Button(bar, text="▶  运行", fg="white", bg="#e94560",
                  activebackground="#c23152", command=self._run, **bb).pack(
            side=tk.LEFT, padx=4, pady=2)
        tk.Button(bar, text="✚ 新建", fg="#c9d1d9", bg="#21262d",
                  activebackground="#30363d", command=self._new, **bb).pack(
            side=tk.LEFT, padx=2, pady=2)
        tk.Button(bar, text="指令集", fg="#c9d1d9", bg="#21262d",
                  activebackground="#30363d", command=self._show_isa, **bb).pack(
            side=tk.LEFT, padx=2, pady=2)
        tk.Button(bar, text="计算器", fg="#c9d1d9", bg="#21262d",
                  activebackground="#30363d", command=self._calculator, **bb).pack(
            side=tk.LEFT, padx=2, pady=2)
        self.status_lbl = tk.Label(bar, text="  就绪", fg="#8b949e", bg="#0d1117",
                                    font=("Microsoft YaHei", 9), anchor="w")
        self.status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # 主区域
        main = tk.Frame(self.root, bg="#0d1117")
        main.pack(fill=tk.BOTH, expand=True)

        # 左侧：文件列表
        sidebar = tk.Frame(main, bg="#0d1117", width=160)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="程序", font=("Microsoft YaHei", 10, "bold"),
                 fg="#e94560", bg="#0d1117", anchor="w").pack(fill=tk.X, padx=10, pady=(8, 4))
        self.file_list = tk.Listbox(sidebar, bg="#0d1117", fg="#e6edf3",
                                     font=("Microsoft YaHei", 9),
                                     selectbackground="#e94560",
                                     highlightthickness=0, bd=0)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 8))
        for name in self.programs:
            self.file_list.insert(tk.END, name)
        self.file_list.bind("<<ListboxSelect>>", lambda e: (
            sel := self.file_list.curselection(),
            self._open(self.file_list.get(sel[0])) if sel else None
        ))

        # 中间：编辑器
        mid = tk.Frame(main, bg="#0d1117", width=320)
        mid.pack(side=tk.LEFT, fill=tk.Y)
        mid.pack_propagate(False)
        lbl_frame = tk.Frame(mid, bg="#0d1117")
        lbl_frame.pack(fill=tk.X)
        tk.Label(lbl_frame, text="  源码", font=("Microsoft YaHei", 10, "bold"),
                 fg="#e94560", bg="#0d1117").pack(side=tk.LEFT, padx=6, pady=(4, 2))
        self.file_label = tk.Label(lbl_frame, text="", fg="#484f58", bg="#0d1117",
                                    font=("Microsoft YaHei", 9))
        self.file_label.pack(side=tk.RIGHT, padx=6)

        self.editor = scrolledtext.ScrolledText(
            mid, bg="#0d1117", fg="#e6edf3", insertbackground="#e94560",
            font=("Microsoft YaHei", 10), wrap=tk.NONE, bd=0, undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        for tag, kw in [
            ("comment", {"foreground": "#8b949e"}),
            ("keyword", {"foreground": "#ff7b72"}),
            ("register", {"foreground": "#79c0ff"}),
            ("label", {"foreground": "#d2a8ff"}),
        ]:
            self.editor.tag_configure(tag, **kw)
        self.editor.bind("<KeyRelease>", self._highlight)

        # 右侧：图形输出
        right = tk.Frame(main, bg="#161b22")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(right, text="  输出", font=("Microsoft YaHei", 10, "bold"),
                 fg="#e94560", bg="#161b22", anchor="w").pack(fill=tk.X, padx=8, pady=(4, 0))
        self.canvas = tk.Canvas(right, bg="#0d1117", bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    def _open(self, name):
        content, _ = self.programs[name]
        self.current_file = name
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", content)
        self._highlight()
        self.file_label.config(text=name)
        self.status_lbl.config(text=f"  已加载「{name}」")
        self._clear_output()

    def _new(self):
        name = "未命名.suan"
        self.programs[name] = ("； 新程序\n\n停\n", "")
        self.file_list.insert(tk.END, name)
        self._open(name)

    def _highlight(self, event=None):
        for tag in ("comment", "keyword", "register", "label"):
            self.editor.tag_remove(tag, "1.0", tk.END)
        lines = self.editor.get("1.0", tk.END).split("\n")
        for ln, lt in enumerate(lines, 1):
            line = lt.strip()
            if not line: continue
            for cc in ["；", ";"]:
                cp = line.find(cc)
                if cp >= 0:
                    self.editor.tag_add("comment", f"{ln}.{cp}", f"{ln}.end")
                    line = line[:cp]
            if line.endswith("：") or line.endswith(":"):
                self.editor.tag_add("label", f"{ln}.0", f"{ln}.end")
                continue
            words = line.replace(",", " ").replace("#", " ").split()
            col = 0
            for w in words:
                idx = lt.find(w, col)
                if idx >= 0:
                    s, e = f"{ln}.{idx}", f"{ln}.{idx + len(w)}"
                    if w in ZUPU_TABLE: self.editor.tag_add("keyword", s, e)
                    elif w in TIANGAN: self.editor.tag_add("register", s, e)
                col = idx + len(w) if idx >= 0 else col + 1

    def _clear_output(self):
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, 900, 500))

    def _load_chars_to_vm(self, vm):
        """加载所有汉字到VM内存（使用预计算的地址）"""
        for cn, obj in self.char_data.items():
            if obj._encoded is None: obj.encode()
            val = sum(1 << j for j, b in enumerate(obj._encoded._bits) if b.is_on)
            addr = self.char_addr[cn]
            vm.memory[addr] = CountingRodNumber(val, obj.bits)

    # ═══════════════════════════════════════════════════════════
    # 核心：编译 → 执行 → 应用级渲染
    # ═══════════════════════════════════════════════════════════
    def _run(self):
        content = self.editor.get("1.0", tk.END)
        lines = [l.rstrip() for l in content.split("\n")]

        # 加载字符数据
        vm = SuanChouVM()
        self._load_chars_to_vm(vm)

        asm = SuanChouZupuAssembler()
        insts, errs = asm.assemble(lines)

        self._clear_output()
        y = 15
        AppRenderer.title(self.canvas, "程序执行结果", y)
        y += 35

        if errs:
            self.canvas.create_text(450, 220, text="编译错误", fill="#f85149",
                                     font=("Microsoft YaHei", 18, "bold"),
                                     anchor="center")
            for i, e in enumerate(errs):
                self.canvas.create_text(450, 260 + i * 20, text=e,
                                         fill="#f85149", font=("Microsoft YaHei", 9),
                                         anchor="center")
            return

        # 执行
        self.status_lbl.config(text=f"  编译成功：{len(insts)} 条 —— 执行中…")
        self.root.update_idletasks()

        vm.load_program(insts)
        vm.run(trace=False)

        count = vm.instruction_count
        self.status_lbl.config(text=f"  执行完成：{count} 条指令")

        # ═════════════════════════════════════════════════════
        # 判断程序类型 → 选择渲染方式
        # ═════════════════════════════════════════════════════

        # 图形程序：用了 绘数/绘字/绘棒/绘框 的，走图形渲染
        is_graphics = ("绘数" in content or "绘字" in content or
                       "绘棒" in content or "绘框" in content)
        if is_graphics and vm.draw_commands:
            self._render_graphics(vm.draw_commands)
            return

        # 交互程序
        if vm.interactive_mode == "calculator":
            self._render_interactive_calculator(vm)
            return
        if vm.interactive_mode == "waiting":
            self._render_interactive_program(vm)
            return

        is_char = ("识" in content or "校" in content or "合" in content or
                   "交" in content or "显" in content or "签" in content)
        is_sequence = ("循环" in content or "乘阶" in content) and "印" in content and not is_char
        is_calculator = ("被加数" in content or "被减数" in content or "被乘数" in content or
                         "被除数" in content or "算筭计算器" in content)

        output_values = []
        for out in vm.output_rods:
            if "(" in out:
                val = out.split("(")[1].replace(")", "").strip()
                try:
                    output_values.append(int(val))
                except:
                    output_values.append(out)

        char_hits = []
        for out in vm.output:
            if "->" in out and "「" in out:
                cn = out.split("「")[1].split("」")[0]
                if cn in self.char_data:
                    char_hits.append(self.char_data[cn])

        # ── 渲染：汉字识别 ──
        if char_hits:
            y += 10
            AppRenderer.title(self.canvas, "— 识字结果 —", y, "#d2a8ff")
            y += 30
            x0 = 450 - len(char_hits) * 110
            for i, co in enumerate(char_hits):
                if i < 4:  # 最多显示4个
                    AppRenderer.char_card(self.canvas, co, x0 + i * 220, y,
                                           highlight=(i == 0))
            y += 140

        # ── 渲染：计算器模式 ──
        if is_calculator and output_values:
            y += 10
            AppRenderer.title(self.canvas, "— 算筭计算器 —", y, "#3fb950")
            y += 35

            # 解析源码中的注释，获取操作信息
            ops = []
            raw_lines = content.split("\n")
            current_op = None
            for line in raw_lines:
                line = line.strip()
                if not line: continue
                # 找注释行作为标签
                for cc in ["；", ";"]:
                    if cc in line and not line.startswith(cc):
                        comment = line.split(cc)[1].strip()
                        if any(kw in comment for kw in ["甲 =", "输出", "商", "余数"]):
                            current_op = line
                if "被加数" in line or "被减数" in line or "被乘数" in line or "被除数" in line:
                    # 剥离注释
                    for cc in ["；", ";"]:
                        if cc in line:
                            ops.append(line.split(cc)[1].strip())
                            break

            # 格式：前几个 ops 与 output_values 对应
            # 不依赖精确解析——只展示有意义的标签
            calc_items = []
            if "被加数" in content: calc_items.append(("加法", 0))
            if "被减数" in content: calc_items.append(("减法", 1))
            if "被乘数" in content: calc_items.append(("乘法", 2))
            if "被除数" in content:
                calc_items.append(("除法(商)", 3))
                calc_items.append(("除法(余)", 4))

            # 检查是否有阶乘
            has_fact = "乘阶" in content and "阶乘" in content

            # 渲染计算卡片
            card_w, card_h = 190, 80
            cols = min(3, len(calc_items) + (1 if has_fact else 0))
            total_w = cols * (card_w + 15) - 15
            cx_start = 450 - total_w // 2
            col = 0
            row_y = y

            for label, idx in calc_items:
                if idx < len(output_values):
                    val = output_values[idx]
                    if isinstance(val, int):
                        x = cx_start + col * (card_w + 15)
                        # 卡片背景
                        self.canvas.create_rectangle(x, row_y, x + card_w, row_y + card_h,
                                                      fill="#161b22", outline="#30363d", width=1)
                        # 标签
                        self.canvas.create_text(x + card_w // 2, row_y + 20,
                                                 text=label, fill="#8b949e",
                                                 font=("Microsoft YaHei", 9))
                        # 结果
                        self.canvas.create_text(x + card_w // 2, row_y + 52,
                                                 text=str(val), fill="#3fb950",
                                                 font=("Consolas", 22, "bold"))
                        col += 1
                        if col >= cols:
                            col = 0
                            row_y += card_h + 15
            if col > 0:
                row_y += card_h + 15

            # 阶乘结果单独显示
            if has_fact and len(output_values) > len(calc_items):
                fact_val = output_values[-1] if isinstance(output_values[-1], int) else output_values[len(calc_items)]
                if isinstance(fact_val, int):
                    x = cx_start
                    self.canvas.create_rectangle(x, row_y, x + card_w, row_y + card_h,
                                                  fill="#161b22", outline="#e94560", width=2)
                    self.canvas.create_text(x + card_w // 2, row_y + 20,
                                             text="阶乘", fill="#e94560",
                                             font=("Microsoft YaHei", 9))
                    self.canvas.create_text(x + card_w // 2, row_y + 52,
                                             text=str(fact_val), fill="#3fb950",
                                             font=("Consolas", 22, "bold"))
                    row_y += card_h + 15

            y = row_y + 20

        if is_sequence and output_values and not is_calculator:
            y += 10
            clean_vals = [v for v in output_values if isinstance(v, int)]
            if len(clean_vals) > 1:
                AppRenderer.title(self.canvas, "— 输出序列 —", y, "#79c0ff")
                y += 30
                shown = clean_vals[:6] if len(clean_vals) > 6 else clean_vals
                if len(clean_vals) > 6:
                    shown = clean_vals[:3] + ["…"] + clean_vals[-3:]
                x = max(60, 450 - len(shown) * 45)
                for i, sv in enumerate(shown):
                    if sv == "…":
                        self.canvas.create_text(x + i * 90 + 39, y + 36,
                                                 text="···", fill="#484f58",
                                                 font=("Microsoft YaHei", 14))
                    else:
                        bg = "#161b22"
                        self.canvas.create_rectangle(x + i * 90, y, x + i * 90 + 78,
                                                      y + 72, fill=bg, outline="#30363d")
                        self.canvas.create_text(x + i * 90 + 39, y + 25,
                                                 text=str(sv), fill="#3fb950",
                                                 font=("Consolas", 16, "bold"))
                y += 100
            else:
                is_sequence = False  # 只有一个值，不算序列

        # ── 渲染：最终结果 ──
        if output_values and not is_sequence and not is_calculator:
            val = output_values[-1]
            y += 10
            # 如果是字符程序但没命中，也显示一下数值
            if is_char and not char_hits:
                AppRenderer.title(self.canvas, "— 结果 —", y, "#79c0ff")
                y += 25
            AppRenderer.big_result(self.canvas, str(val), y + 20)

        # ── 如果是字符比较程序 ──
        if is_char and len(output_values) >= 2 and not char_hits and not is_sequence and not is_calculator:
            # 可能是一次比较操作：输出差异位和共同位
            diff = output_values[0] if output_values else 0
            com = output_values[1] if len(output_values) > 1 else 0
            y += 10
            self.canvas.create_text(450, y + 20,
                                     text=f"笔画差异 {diff} 位  ·  笔画重合 {com} 位",
                                     fill="#79c0ff", font=("Microsoft YaHei", 14, "bold"),
                                     anchor="center")
            # 画一个简单的条形图
            total_diff_com = diff + com
            if total_diff_com > 0:
                bw, bh = 400, 24
                bx, by = 450 - bw // 2, y + 50
                diff_w = int(bw * diff / total_diff_com)
                com_w = int(bw * com / total_diff_com)
                self.canvas.create_rectangle(bx, by, bx + diff_w, by + bh,
                                              fill="#f85149", outline="")
                self.canvas.create_rectangle(bx + diff_w, by, bx + bw, by + bh,
                                              fill="#3fb950", outline="")
                self.canvas.create_text(bx + diff_w // 2, by + bh // 2,
                                         text=f"差异 {diff}", fill="white",
                                         font=("Microsoft YaHei", 10, "bold"))
                self.canvas.create_text(bx + diff_w + com_w // 2, by + bh // 2,
                                         text=f"重合 {com}", fill="white",
                                         font=("Microsoft YaHei", 10, "bold"))
                y += 60

        # 滚动
        self.canvas.config(scrollregion=(0, 0, 900, max(y + 80, 500)))

    def _render_graphics(self, draw_commands):
        """渲染 .suan 程序的图形输出"""
        AppRenderer.title(self.canvas, "算筭图形程序", 20)
        y = 55
        xc = 450  # center

        for cmd in draw_commands:
            kind = cmd[0]
            if kind == "NUM":
                val = cmd[1]
                # 大号数字
                self.canvas.create_rectangle(xc - 100, y, xc + 100, y + 90,
                                              fill="#161b22", outline="#30363d", width=1)
                self.canvas.create_text(xc, y + 25, text=str(val),
                                         fill="#3fb950", font=("Consolas", 32, "bold"))
                self.canvas.create_text(xc, y + 65, text=f"{val:#b}"[2:],
                                         fill="#8b949e", font=("Consolas", 9))
                y += 110

            elif kind == "CHAR":
                char_obj = cmd[1]
                # 汉字卡片
                w, h = 200, 120
                x = xc - w // 2
                self.canvas.create_rectangle(x, y, x + w, y + h,
                                              fill="#161b22", outline="#e94560", width=2)
                self.canvas.create_text(x + w // 2, y + 35, text=char_obj.char,
                                         fill="#e6edf3", font=("Microsoft YaHei", 36, "bold"))
                self.canvas.create_text(x + w // 2, y + 70, text=char_obj.meaning.split("；")[0],
                                         fill="#8b949e", font=("Microsoft YaHei", 10))
                self.canvas.create_text(x + w // 2, y + 92,
                                         text=f"{char_obj.pinyin}  {char_obj.stroke_count}画",
                                         fill="#484f58", font=("Microsoft YaHei", 8))
                y += 140

            elif kind == "ROD":
                val, rod_str = cmd[1], cmd[2]
                self.canvas.create_text(xc, y + 10, text=f"值: {val}",
                                         fill="#3fb950", font=("Consolas", 13, "bold"))
                y += 30
                self.canvas.create_text(xc, y + 10, text=rod_str,
                                         fill="#79c0ff", font=("Consolas", 13))
                y += 50

            elif kind == "BOX":
                title_val, body_val = cmd[1], cmd[2]
                w, h = 240, 90
                x = xc - w // 2
                self.canvas.create_rectangle(x, y, x + w, y + h,
                                              fill="#161b22", outline="#79c0ff", width=1)
                self.canvas.create_text(x + w // 2, y + 22, text=str(title_val),
                                         fill="#79c0ff", font=("Microsoft YaHei", 12, "bold"))
                self.canvas.create_text(x + w // 2, y + 58, text=str(body_val),
                                         fill="#3fb950", font=("Consolas", 20, "bold"))
                y += 110

        self.canvas.config(scrollregion=(0, 0, 900, max(y + 80, 500)))

    def _render_interactive_program(self, vm):
        """渲染纯 .suan 交互程序 —— OS 只负责画，逻辑全在 .suan 里"""
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or 900
        h = self.canvas.winfo_height() or 600

        # 常量：按钮布局
        BTN_W, BTN_H, GAP = 58, 48, 5
        COLS = 4
        grid_x0 = (w - (BTN_W * COLS + GAP * (COLS - 1))) // 2
        grid_y0 = 180  # 顶部留120给显示区

        btn_map = {}  # (row, col) -> label_value
        self._active_vm = vm

        # 第一遍：渲染所有draw_commands
        for cmd in vm.draw_commands:
            kind = cmd[0]
            if kind == "CLEAR":
                self.canvas.delete("all")

            elif kind == "NUM":
                val = cmd[1]
                self.canvas.create_text(w // 2, 50, text=str(val),
                                         fill="#3fb950", font=("Consolas", 30, "bold"))

            elif kind == "TEXT":
                val = cmd[1]
                self.canvas.create_text(w // 2, 50, text=str(val),
                                         fill="#3fb950", font=("Consolas", 22, "bold"))

            elif kind == "KEY":
                pos, label = cmd[1], cmd[2]
                row, col = pos // 10, pos % 10
                btn_map[(row, col)] = label
                x = grid_x0 + col * (BTN_W + GAP)
                y = grid_y0 + row * (BTN_H + GAP)
                # 确定颜色
                if label >= 10:
                    bg, fg = "#161b22", "#3fb950"  # 运算符绿色
                else:
                    bg, fg = "#21262d", "#e6edf3"
                if label == 14:  # "="
                    bg, fg = "#e94560", "white"
                rect = self.canvas.create_rectangle(x, y, x + BTN_W, y + BTN_H,
                                                     fill=bg, outline="")
                lbl_text = str(label)
                if label == 10: lbl_text = "+"
                elif label == 11: lbl_text = "−"
                elif label == 12: lbl_text = "×"
                elif label == 13: lbl_text = "÷"
                elif label == 14: lbl_text = "="
                elif label == 15: lbl_text = "C"
                elif label == 16: lbl_text = "⌫"
                elif label == 17: lbl_text = "."
                txt = self.canvas.create_text(x + BTN_W // 2, y + BTN_H // 2,
                                               text=lbl_text, fill=fg,
                                               font=("Microsoft YaHei", 15, "bold"))

                def make_handler(l=label):
                    def handler(event):
                        self._active_vm.last_touch_value = l
                        self._active_vm.interactive_mode = None
                        self._resume_vm_execution()
                    return handler
                self.canvas.tag_bind(rect, "<Button-1>", make_handler(label))
                self.canvas.tag_bind(txt, "<Button-1>", make_handler(label))

    def _resume_vm_execution(self):
        """从待触点恢复执行"""
        vm = self._active_vm
        if vm is None: return
        self.status_lbl.config(text="  执行中…")
        self.root.update_idletasks()

        # 从 PC 处恢复执行（PC 已经指向 待触 的下一条指令）
        while vm.pc < len(vm.program):
            inst = vm.program[vm.pc]
            result = vm.decode_execute(inst)
            vm.pc += 1
            if result == "HALT":
                break
            if vm.interactive_mode == "waiting":
                # 又碰到了 待触，重新渲染
                self._render_interactive_program(vm)
                return

        self.status_lbl.config(text=f"  执行完成：{vm.instruction_count} 条指令")
        # 最终渲染
        self.canvas.delete("all")
        for cmd in vm.draw_commands:
            if cmd[0] in ("NUM", "TEXT"):
                self.canvas.create_text(
                    (self.canvas.winfo_width() or 900) // 2, 60,
                    text=str(cmd[1]) if cmd[0] == "TEXT" else f"= {cmd[1]}",
                    fill="#3fb950",
                    font=("Consolas", 28 if cmd[0] == "TEXT" else 24, "bold"))

    def _render_interactive_calculator(self, vm):
        """渲染交互式计算器 —— 在画布上画按钮，可以点击"""
        self.canvas.delete("all")

        # 状态
        state = {"a": "", "op": "", "b": "", "result": ""}
        # 画布元素 ID 引用（用于更新显示）
        ui = {}

        w = self.canvas.winfo_width() or 900
        h = self.canvas.winfo_height() or 600

        # 居中计算器
        cx, cy = w // 2, h // 2 - 20

        # ===== 显示区 =====
        disp_w, disp_h = 260, 80
        disp_x, disp_y = cx - disp_w // 2, cy - 200

        # 公式行
        formula_id = self.canvas.create_text(
            cx, disp_y + 22, text="", fill="#8b949e",
            font=("Microsoft YaHei", 10), anchor="center")
        # 结果行
        result_id = self.canvas.create_text(
            cx, disp_y + 55, text="0", fill="#e6edf3",
            font=("Microsoft YaHei", 26, "bold"), anchor="center")
        disp_bg = self.canvas.create_rectangle(
            disp_x, disp_y, disp_x + disp_w, disp_y + disp_h,
            fill="#161b22", outline="#30363d", width=1)
        self.canvas.tag_lower(disp_bg, formula_id)

        ui["formula"] = formula_id
        ui["result"] = result_id

        # 辅助函数
        def update_display():
            a, op, b, r = state["a"], state["op"], state["b"], state["result"]
            if r:
                self.canvas.itemconfig(formula_id, text=f"{a} {op} {b} =")
                self.canvas.itemconfig(result_id, text=str(r))
            elif b:
                self.canvas.itemconfig(formula_id, text=f"{a} {op}")
                self.canvas.itemconfig(result_id, text=b)
            elif a:
                self.canvas.itemconfig(formula_id, text="")
                self.canvas.itemconfig(result_id, text=a)
            else:
                self.canvas.itemconfig(formula_id, text="")
                self.canvas.itemconfig(result_id, text="0")

        # ===== 按钮布局 =====
        btn_w, btn_h, gap = 58, 48, 5
        grid_x0 = cx - (btn_w * 4 + gap * 3) // 2
        grid_y0 = disp_y + disp_h + 20

        btn_ids = {}  # (row, col) -> rect_id
        btn_colors = {}

        def make_btn(row, col, text, color_bg="#21262d", color_fg="#e6edf3",
                     w=1, h=1, font_size=16):
            x = grid_x0 + col * (btn_w + gap)
            y = grid_y0 + row * (btn_h + gap)
            bw = btn_w * w + gap * (w - 1)
            bh = btn_h * h + gap * (h - 1)
            rect = self.canvas.create_rectangle(x, y, x + bw, y + bh,
                                                 fill=color_bg, outline="",
                                                 tags="calc_btn")
            txt = self.canvas.create_text(x + bw // 2, y + bh // 2,
                                           text=text, fill=color_fg,
                                           font=("Microsoft YaHei", font_size, "bold"),
                                           tags="calc_btn")
            # 绑定点击
            self.canvas.tag_bind(rect, "<Button-1>", lambda e, r=row, c=col: on_click(r, c))
            self.canvas.tag_bind(txt, "<Button-1>", lambda e, r=row, c=col: on_click(r, c))
            btn_ids[(row, col)] = (rect, txt)
            btn_colors[(row, col)] = (color_bg, color_fg)
            return x, y, bw, bh

        # 按钮定义：(row, col, text, width, height, bg, fg, font_size)
        buttons = [
            # 第一行：运算符
            (0, 0, "+", 1, 1, "#161b22", "#3fb950", 16),
            (0, 1, "−", 1, 1, "#161b22", "#3fb950", 16),
            (0, 2, "×", 1, 1, "#161b22", "#3fb950", 16),
            (0, 3, "÷", 1, 1, "#161b22", "#3fb950", 16),
            # 第二行：7 8 9 C
            (1, 0, "7", 1, 1, "#21262d", "#e6edf3", 15),
            (1, 1, "8", 1, 1, "#21262d", "#e6edf3", 15),
            (1, 2, "9", 1, 1, "#21262d", "#e6edf3", 15),
            (1, 3, "C", 1, 1, "#161b22", "#f85149", 12),
            # 第三行：4 5 6 ⌫
            (2, 0, "4", 1, 1, "#21262d", "#e6edf3", 15),
            (2, 1, "5", 1, 1, "#21262d", "#e6edf3", 15),
            (2, 2, "6", 1, 1, "#21262d", "#e6edf3", 15),
            (2, 3, "⌫", 1, 1, "#161b22", "#f85149", 14),
            # 第四行：1 2 3 =
            (3, 0, "1", 1, 1, "#21262d", "#e6edf3", 15),
            (3, 1, "2", 1, 1, "#21262d", "#e6edf3", 15),
            (3, 2, "3", 1, 1, "#21262d", "#e6edf3", 15),
            (3, 3, "=", 1, 1, "#e94560", "white", 18),
            # 第五行：0 .
            (4, 0, "0", 2, 1, "#21262d", "#e6edf3", 15),
            (4, 2, ".", 1, 1, "#21262d", "#e6edf3", 15),
        ]

        # 计算器按钮映射
        btn_map = {}
        for row, col, text, bw, bh, bg, fg, fs in buttons:
            make_btn(row, col, text, bg, fg, bw, bh, fs)
            btn_map[(row, col)] = text

        # 点击回调
        def compute():
            if not state["a"] or not state["op"] or not state["b"]:
                return
            try:
                a = int(float(state["a"]))
                b = int(float(state["b"]))
            except ValueError:
                state["result"] = "错误"
                update_display()
                return
            op = state["op"]

            # 用 VM 计算
            from suanchou_zupu import SuanChouZupuAssembler
            asm = SuanChouZupuAssembler()
            if op == "+":
                src = [f"载 甲, #{a}", f"载 乙, #{b}", "加 甲, 乙", "印 甲", "停"]
            elif op == "−":
                src = [f"载 甲, #{a}", f"载 乙, #{b}", "减 甲, 乙", "印 甲", "停"]
            elif op == "×":
                src = [f"载 甲, #{a}", f"载 乙, #{b}", "乘 甲, 乙", "印 甲", "停"]
            elif op == "÷":
                src = [f"载 甲, #{a}", f"载 乙, #{b}", "除 甲, 乙", "印 甲", "停"]
            else:
                return

            insts, errs = asm.assemble(src)
            if errs: return
            v = SuanChouVM()
            v.load_program(insts)
            v.run(trace=False)
            val = v.registers[0].to_int()
            if op == "÷":
                rem = v.registers[7].to_int()
                state["result"] = f"{val} 余 {rem}"
            else:
                state["result"] = str(val)
            update_display()
            state["a"] = str(val) if op != "÷" else str(val)
            state["op"] = state["b"] = ""

        def on_click(row, col):
            text = btn_map.get((row, col), "")
            if text in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
                d = text
                if state["result"]:
                    state["a"] = d
                    state["op"] = state["b"] = state["result"] = ""
                elif not state["op"]:
                    state["a"] += d
                else:
                    state["b"] += d
                update_display()
            elif text == ".":
                if state["result"]:
                    state["a"] = "0."
                    state["op"] = state["b"] = state["result"] = ""
                elif "." in (state["b"] or state["a"]):
                    return
                elif not state["op"]:
                    state["a"] += "."
                else:
                    state["b"] += "."
                update_display()
            elif text in ("+", "−", "×", "÷"):
                if state["a"]:
                    if state["b"] and not state["result"]:
                        compute()
                    state["op"] = text
                    state["b"] = ""
                    state["result"] = ""
                    update_display()
            elif text == "=":
                if state["a"] and state["op"] and state["b"]:
                    compute()
            elif text == "C":
                state["a"] = state["op"] = state["b"] = state["result"] = ""
                update_display()
            elif text == "⌫":
                if state["b"]:
                    state["b"] = state["b"][:-1]
                elif state["op"]:
                    state["op"] = ""
                elif state["a"]:
                    state["a"] = state["a"][:-1]
                update_display()

        # 底部文案
        self.canvas.create_text(cx, grid_y0 + 5 * (btn_h + gap) + 20,
                                 text="算筭VM 驱动 | 纯 .suan 程序 | —  + | 计算",
                                 fill="#21262d", font=("Microsoft YaHei", 8), anchor="center")

    def _show_isa(self):
        win = tk.Toplevel(self.root)
        win.title("算筭指令集")
        win.geometry("520x540")
        win.configure(bg="#0d1117")
        text = scrolledtext.ScrolledText(win, bg="#0d1117", fg="#e6edf3",
                                          font=("Microsoft YaHei", 10), bd=0)
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        text.tag_configure("cat", foreground="#e94560",
                            font=("Microsoft YaHei", 11, "bold"))
        text.tag_configure("rod", foreground="#3fb950")
        for cat, mn in ZUPU_CATEGORIES.items():
            text.insert(tk.END, f"\n【{cat}】\n", "cat")
            for m in mn:
                code = ZUPU_TABLE[m]
                r = "".join("—" if ((code >> (5 - i)) & 1) else "|" for i in range(6))
                mean = ZUPU_MEANING.get(m, "")
                text.insert(tk.END, f"  {m}  {r}  → {mean}\n")
        text.insert(tk.END, f"\n寄存器：{'  '.join(f'{k}=R{v}' for k, v in TIANGAN.items())}\n")
        text.config(state=tk.DISABLED)

    # ═══════════════════════════════════════════════════════════
    # 图形计算器 — 点按钮，出结果
    # ═══════════════════════════════════════════════════════════
    def _calculator(self):
        win = tk.Toplevel(self.root)
        win.title("算筭计算器")
        win.geometry("340x480")
        win.configure(bg="#0d1117")
        win.resizable(False, False)

        # 显示区
        display_frame = tk.Frame(win, bg="#161b22", height=100)
        display_frame.pack(fill=tk.X, padx=8, pady=8)
        display_frame.pack_propagate(False)

        # 运算公式（小字）
        formula_var = tk.StringVar(value="")
        tk.Label(display_frame, textvariable=formula_var,
                 fg="#8b949e", bg="#161b22", anchor="e",
                 font=("Microsoft YaHei", 10)).pack(fill=tk.X, padx=12, pady=(8, 0))

        # 结果数（大字）
        result_var = tk.StringVar(value="0")
        tk.Label(display_frame, textvariable=result_var,
                 fg="#e6edf3", bg="#161b22", anchor="e",
                 font=("Microsoft YaHei", 28, "bold")).pack(fill=tk.X, padx=12, pady=(0, 8))

        # 计算器状态
        state = {"a": "", "op": "", "b": "", "result": ""}

        def update_display():
            a = state["a"]
            op = state["op"]
            b = state["b"]
            r = state["result"]
            if r:
                formula_var.set(f"{a} {op} {b} =")
                result_var.set(str(r))
                state["result"] = ""
            elif b:
                formula_var.set(f"{a} {op}")
                result_var.set(b)
            elif a:
                formula_var.set("")
                result_var.set(a)
            else:
                formula_var.set("")
                result_var.set("0")

        def press_digit(d):
             """d is int for numbers, str '.' for decimal point"""
             s = str(d)
             if state["result"]:
                 state["a"] = s
                 state["op"] = state["b"] = state["result"] = ""
             elif not state["op"]:
                 if s == "." and "." in state["a"]: return
                 state["a"] += s
             else:
                 if s == "." and "." in state["b"]: return
                 state["b"] += s
             update_display()

        def press_op(op_symbol, op_name):
            if state["a"] and not state["b"]:
                state["op"] = op_symbol
                state["_op_name"] = op_name
            update_display()

        def compute():
            if not state["a"] or not state["op"] or not state["b"]:
                return
            try:
                a = int(float(state["a"]))
                b = int(float(state["b"]))
            except ValueError:
                result_var.set("输入错误")
                return
            op_name = state.get("_op_name", "")

            # 用算筭VM做实际计算
            from suanchou_zupu import SuanChouZupuAssembler
            from suanchou_vm import SuanChouVM

            asm = SuanChouZupuAssembler()

            if op_name == "加":
                src = [f"载 甲, #{a}", f"载 乙, #{b}", "加 甲, 乙", "印 甲", "停"]
            elif op_name == "减":
                src = [f"载 甲, #{a}", f"载 乙, #{b}", "减 甲, 乙", "印 甲", "停"]
            elif op_name == "乘":
                src = [f"载 甲, #{a}", f"载 乙, #{b}", "乘 甲, 乙", "印 甲", "停"]
            elif op_name == "除":
                src = [f"载 甲, #{a}", f"载 乙, #{b}", "除 甲, 乙", "印 甲", "停"]
            else:
                return

            insts, errs = asm.assemble(src)
            if errs:
                result_var.set("错误")
                return

            vm = SuanChouVM()
            vm.load_program(insts)
            vm.run(trace=False)

            val = vm.registers[0].to_int()
            state["result"] = str(val)
            if op_name == "除":
                rem = vm.registers[7].to_int()
                state["result"] = f"{val} 余 {rem}"
            update_display()
            state["a"] = str(val) if op_name != "除" else str(val)
            state["op"] = state["b"] = ""

        def clear():
            state["a"] = state["op"] = state["b"] = state["result"] = ""
            update_display()

        def clear_entry():
            if state["b"]:
                state["b"] = state["b"][:-1]
            elif state["op"]:
                state["op"] = ""
            elif state["a"]:
                state["a"] = state["a"][:-1]
            update_display()

        # 按钮区
        btn_frm = tk.Frame(win, bg="#0d1117")
        btn_frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        btn_cfg = {"font": ("Microsoft YaHei", 14, "bold"), "bd": 0,
                   "activeforeground": "white", "cursor": "hand2"}

        # 数字按钮
        digits_layout = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2),
            ("0", 4, 0),
        ]

        for d, row, col in digits_layout:
             span = 2 if d == "0" else 1
             tk.Button(btn_frm, text=d,
                       fg="#e6edf3", bg="#21262d",
                       activebackground="#30363d",
                       command=lambda x=d: press_digit(int(x) if x != "." else x),
                       **btn_cfg
                       ).grid(row=row, column=col, columnspan=span,
                              sticky="nsew", padx=2, pady=2)

        # 小数点
        tk.Button(btn_frm, text=".",
                  fg="#e6edf3", bg="#21262d", activebackground="#30363d",
                  command=lambda: press_digit(".") if "." not in (
                      state["b"] or state["a"]
                  ) else None,
                  **btn_cfg).grid(row=4, column=2, sticky="nsew", padx=2, pady=2)

        # 运算符按钮
        ops = [
            ("÷", 0, 0, "除"), ("×", 0, 1, "乘"),
            ("−", 0, 2, "减"), ("+", 0, 3, "加"),
        ]
        for sym, row, col, name in ops:
            tk.Button(btn_frm, text=sym,
                      fg="#3fb950", bg="#161b22",
                      activebackground="#30363d",
                      command=lambda s=sym, n=name: press_op(s, n),
                      **btn_cfg).grid(row=row, column=col, columnspan=1,
                                      sticky="nsew", padx=2, pady=2)

        # 等于
        tk.Button(btn_frm, text="=",
                  fg="white", bg="#e94560",
                  activebackground="#c23152",
                  command=compute,
                  **btn_cfg).grid(row=4, column=3, rowspan=1,
                                  sticky="nsew", padx=2, pady=2)

        # 清除按钮
        tk.Button(btn_frm, text="C",
                  fg="#f85149", bg="#161b22",
                  activebackground="#30363d",
                  command=clear,
                  **btn_cfg).grid(row=1, column=3, sticky="nsew", padx=2, pady=2)
        tk.Button(btn_frm, text="⌫",
                  fg="#f85149", bg="#161b22",
                  activebackground="#30363d",
                  command=clear_entry,
                  **btn_cfg).grid(row=2, column=3, sticky="nsew", padx=2, pady=2)

        # 网格权重
        for i in range(5):
            btn_frm.rowconfigure(i, weight=1)
        for i in range(4):
            btn_frm.columnconfigure(i, weight=1)

        # 底部署名
        tk.Label(win, text="算筭VM 驱动  |  — + | 计算",
                 fg="#21262d", bg="#0d1117",
                 font=("Microsoft YaHei", 8)).pack(pady=(0, 6))

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    SuanChouOS().run()

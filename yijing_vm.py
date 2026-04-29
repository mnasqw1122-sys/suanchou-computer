# -*- coding: utf-8 -*-
"""
易象虚拟机 (Yijing Virtual Machine)
============================================
不是冯·诺依曼架构。不是指令流水线。

是卦象的配置与变换。
  初始象 → 变爻 → 之象 → 释象

每一条「指令」不是一个操作，而是一种「变易」。
六十四卦不是查表——是阴阳爻在自组织。

核心概念：
  爻 yao   = 基本态 (阴/阳)
  卦 gua   = 六爻组成的一个整体
  象 xiang = 卦所对应的义理
  变 bian  = 改变其中若干爻
"""


class Yao:
    """爻 —— 最基本的不可再分的状态"""
    def __init__(self, is_yang=True):
        self._yang = is_yang

    @property
    def yang(self): return self._yang

    @property
    def yin(self): return not self._yang

    def bian(self):
        """爻变 —— 阴变阳，阳变阴"""
        return Yao(not self._yang)

    def __str__(self):
        return "—" if self._yang else "--"


def yao_from_str(s):
    """从字符读取爻：阳=(yang)/1, 阴=(yin)/0"""
    return Yao(s in ("yang", "1", "阳", True))


class Gua:
    """
    卦 —— 六爻构成的整体。
    不是一个字，不是一个数。是一个「象」——一种配置状态。
    """
    def __init__(self, yaos=None):
        if yaos is None:
            yaos = [Yao(True) for _ in range(6)]
        self.yaos = yaos[:6]  # 六爻，下往上

    @classmethod
    def from_binary(cls, n):
        """从 0-63 的数字构造卦"""
        yaos = []
        for i in range(6):
            yaos.append(Yao((n >> (5 - i)) & 1))
        return cls(yaos)

    def to_int(self):
        val = 0
        for y in self.yaos:
            val = (val << 1) | (1 if y.yang else 0)
        return val

    def bian(self, index):
        """变一爻 —— 改变第 index 位"""
        new_yaos = list(self.yaos)
        if 0 <= index < 6:
            new_yaos[index] = new_yaos[index].bian()
        return Gua(new_yaos)

    def bian_many(self, indices):
        """变多爻"""
        g = self
        for i in indices:
            g = g.bian(i)
        return g

    def __str__(self):
        return "".join(str(y) for y in reversed(self.yaos))


# 周易六十四卦名
LIUSHISI_GUA = [
    (0, "坤"), (1, "复"), (2, "师"), (3, "临"),
    (4, "谦"), (5, "明夷"), (6, "升"), (7, "泰"),
    (8, "豫"), (9, "震"), (10, "解"), (11, "归妹"),
    (12, "小过"), (13, "丰"), (14, "恒"), (15, "大壮"),
    (16, "比"), (17, "屯"), (18, "坎"), (19, "节"),
    (20, "蹇"), (21, "既济"), (22, "井"), (23, "需"),
    (24, "萃"), (25, "随"), (26, "困"), (27, "兑"),
    (28, "咸"), (29, "革"), (30, "大过"), (31, "夬"),
    (32, "剥"), (33, "颐"), (34, "蒙"), (35, "损"),
    (36, "艮"), (37, "贲"), (38, "蛊"), (39, "大畜"),
    (40, "晋"), (41, "噬嗑"), (42, "未济"), (43, "旅"),
    (44, "否"), (45, "无妄"), (46, "讼"), (47, "履"),
    (48, "观"), (49, "益"), (50, "涣"), (51, "中孚"),
    (52, "渐"), (53, "家人"), (54, "巽"), (55, "小畜"),
    (56, "否"), (57, "同人"), (58, "离"), (59, "大有"),
    (60, "姤"), (61, "鼎"), (62, "未济"), (63, "乾"),
]

GUA_NAMES = {n: name for n, name in LIUSHISI_GUA}
GUA_NUMBERS = {name: n for n, name in LIUSHISI_GUA}


class YijingVM:
    """
    易象虚拟机

    不是处理器。不是一条条执行。
    是「初始象 → 变象操作 → 象成形」。
    """

    def __init__(self):
        # 当前卦象
        self.gua = Gua.from_binary(0)  # 坤卦开始

        # 变换记录
        self.bian_log = []

        # 已确认的象
        self.cheng_gua = None

        # 解释文本
        self.jieshuo = []

    def chu_xiang(self, n):
        """初象 —— 设置初始卦象"""
        self.gua = Gua.from_binary(n & 0x3F)
        self.bian_log.append(("初象", str(self.gua), GUA_NAMES.get(self.gua.to_int(), "?")))

    def bian_yao(self, index):
        """变爻 —— 改变第 index 爻"""
        self.gua = self.gua.bian(index)
        self.bian_log.append(("变爻", index, str(self.gua)))

    def xiang_cheng(self):
        """象成 —— 确定当前卦象，赋予名字和义理"""
        self.cheng_gua = self.gua
        name = GUA_NAMES.get(self.gua.to_int(), f"卦{self.gua.to_int()}")
        self.jieshuo.append(f"象成 → 【{name}】")
        return name

    def yao_yang(self, index):
        """查爻 —— 检查第 index 爻的阴阳"""
        if 0 <= index < 6:
            return self.gua.yaos[index].yang
        return None

    def cha(self):
        """察 —— 检查当前状态"""
        return {
            "象": str(self.gua),
            "数": self.gua.to_int(),
            "名": GUA_NAMES.get(self.gua.to_int(), "未知"),
            "变史": self.bian_log,
            "解说": self.jieshuo,
        }


# ═══════════════════════════════════════════════════════════
#  易象字谱 —— 非翻译的汉字指令
# ═══════════════════════════════════════════════════════════

YI_MNEMONICS = {
    # 这些不是英文翻译。它们没有英文原名。
    # 它们来自《周易》的概念体系。

    "初象": "chu_xiang",   # 初象 → 设定初始卦象
    "变":   "bian_yao",    # 变 → 改变一爻（阴变阳，阳变阴）
    "象成": "xiang_cheng", # 象成 → 卦象确定，释名
    "阴阳": "yao_yang",    # 阴阳 → 查某爻的阴阳状态
    "察":   "cha",         # 察 → 观察当前卦象全貌
}

YI_NAMES = {
    "chu_xiang": "初象",
    "bian_yao": "变",
    "xiang_cheng": "象成",
    "yao_yang": "阴阳",
    "cha": "察",
}


class YijingAssembler:
    """易象汇编器：汉字 → 易象操作"""
    def assemble(self, lines):
        ops = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("；") or line.startswith(";"):
                continue
            if line.endswith("：") or line.endswith(":"):
                continue

            parts = line.replace(",", " ").split()
            if not parts:
                continue

            op_name = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            if op_name not in YI_MNEMONICS:
                ops.append(("错误", f"不识：{op_name}"))
                continue

            func_name = YI_MNEMONICS[op_name]
            ops.append((func_name, args))
        return ops


def run_yijing(source):
    """运行一段易象字谱"""
    asm = YijingAssembler()
    ops = asm.assemble(source)
    vm = YijingVM()

    for func_name, args in ops:
        if func_name == "chu_xiang":
            if args:
                vm.chu_xiang(int(args[0]) if args[0].isdigit() else 0)
        elif func_name == "bian_yao":
            if args:
                vm.bian_yao(int(args[0]) if args[0].isdigit() else 0)
        elif func_name == "xiang_cheng":
            name = vm.xiang_cheng()
            print(f"  > 象成 -> 【{name}】  {vm.gua}")
        elif func_name == "cha":
            state = vm.cha()
            print(f"  象：{state['象']}  {state['数']}  {state['名']}")

    return vm


# ═══════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════

def yanshi():
    print("=" * 60)
    print("  易 象 计 算")
    print("  不是冯·诺依曼。是卦象的变易。")
    print("=" * 60)

    # ===============================================================
    #  演示一：乾卦变坤卦
    # ===============================================================
    print("\n【演示一】乾卦 → 逐一变六爻 → 坤卦")
    print("  这就是「变易」——不是计算，是形态转换。\n")

    source = [
        "初象 63",    # 乾卦 (阳阳阳阳阳阳)
        "变 5",
        "变 4",
        "变 3",
        "变 2",
        "变 1",
        "变 0",
        "象成",      # 坤卦 (阴阴阴阴阴阴)
    ]
    vm = run_yijing(source)

    # ===============================================================
    #  演示二：学 — 认识一个字的过程，不是查表
    # ===============================================================
    print("\n" + "-" * 40)
    print("【演示二】识字 = 象成")
    print("  看到一笔 → 卦象变化 → 逐渐接近 → 象成")
    print("  这是人类识字的方式，不是数据库查找。\n")

    # 模拟：看到「木」字的过程
    # 初象 = 混沌 (0) → 横(变0) → 竖(变1) → 撇(变2) → 捺(变3) → 象成
    source2 = [
        "初象 0",
        "察",
        "变 0",
        "察",
        "变 1",
        "察",
        "变 2",
        "察",
        "变 3",
        "察",
        "象成",
    ]
    vm2 = run_yijing(source2)

    # ===============================================================
    #  演示三：纯汉字编写
    # ===============================================================
    print("\n" + "-" * 40)
    print("【演示三】纯易象字谱")
    print("  这些指令没有英文原名。\n")

    chun_hanzi = [
        "； 一卦始于混沌",
        "初象 42",
        "察",
        "",
        "； 变易",
        "变 2",
        "察",
        "",
        "； 再变",
        "变 5",
        "察",
        "",
        "； 象已成型",
        "象成",
    ]

    print("  源码：")
    for line in chun_hanzi:
        print(f"    {line}")
    print()

    vm3 = run_yijing(chun_hanzi)

    print("\n" + "=" * 60)
    print("  六十四卦，象在其中。")
    print("  非指令，非执行，非流水线。")
    print("  只是变易。")
    print("=" * 60)


if __name__ == "__main__":
    yanshi()

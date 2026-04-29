# -*- coding: utf-8 -*-
"""
算筭字谱 (SuanChou Character Notation)
==========================================
受古琴减字谱启发而设计的汉字原生汇编语言。

古琴减字谱：取汉字部件，组合为「一字一指令」的紧凑记谱法。
  例：「大」+「九」+「七」→ 一个合成字，表示「拇指按九徽七弦」

算筭字谱：同样的思路 —— 用汉字部件组合表达计算机指令。
  例：「载」+「甲」+「卌二」→ 载甲卌二 = LOAD R0, #42

寄存器命名：十天干
  甲(R0) 乙(R1) 丙(R2) 丁(R3) 戊(R4) 己(R5) 庚(R6) 辛(R7)

运行方式：
  py suanchou_zupu.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber, CountingRodComputer
from suanchou_isa import SuanChouOpcode, SuanChouInstruction
from suanchou_vm import SuanChouVM


# ================================================================
# 算筭字谱 —— 汉字指令 ↔ 操作码映射表
# ================================================================

ZUPU_TABLE = {
    # 数据传输指令
    "停":   SuanChouOpcode.HALT,   # 停机
    "载":   SuanChouOpcode.LOAD,   # 载入数值
    "传":   SuanChouOpcode.MOV,    # 传递寄存器间
    "存":   SuanChouOpcode.STORE,  # 存入内存
    "取":   SuanChouOpcode.LMEM,   # 从内存取出

    # 算术
    "加":   SuanChouOpcode.ADD,
    "减":   SuanChouOpcode.SUB,
    "乘":   SuanChouOpcode.MUL,
    "除":   SuanChouOpcode.DIV,

    # 逻辑
    "与":   SuanChouOpcode.AND,    # 按位与（两位皆通则通）
    "或":   SuanChouOpcode.OR,     # 按位或（任一位通则通）
    "异":   SuanChouOpcode.XOR,    # 按位异或（两位不同则通）
    "非":   SuanChouOpcode.NOT,    # 按位取反

    # 位移
    "左":   SuanChouOpcode.SHL,    # 左移
    "右":   SuanChouOpcode.SHR,    # 右移

    # 控制流
    "比":   SuanChouOpcode.CMP,    # 比较
    "跳":   SuanChouOpcode.JMP,    # 无条件跳转
    "等":   SuanChouOpcode.JE,     # 相等则跳
    "别":   SuanChouOpcode.JNE,    # 不等则跳
    "大":   SuanChouOpcode.JG,     # 大于则跳
    "小":   SuanChouOpcode.JL,     # 小于则跳

    # 算筭原生指令
    "识":   SuanChouOpcode.ROD_CHAR,   # 识字：算筭码→汉字
    "查":   SuanChouOpcode.ROD_FIND,   # 查字：查找相关汉字
    "校":   SuanChouOpcode.ROD_CMP,    # 校字：比较两字算筭码
    "合":   SuanChouOpcode.ROD_MERGE,  # 合字：OR合并两字算筭码
    "交":   SuanChouOpcode.ROD_OVERLAP,# 交叠：AND找共同笔画
    "签":   SuanChouOpcode.ROD_TAG,    # 标签：查语义标签
    "印":   SuanChouOpcode.ROD_PRINT,  # 印记：输出算筭码
    "显":   SuanChouOpcode.ROD_SHOW,   # 显示：输出汉字

    # 算筭图形指令
    "绘数": SuanChouOpcode.ROD_DRAW_NUM,   # 绘制大号数字
    "绘字": SuanChouOpcode.ROD_DRAW_CHAR,  # 绘制汉字卡片
    "绘棒": SuanChouOpcode.ROD_DRAW_ROD,   # 绘制算筭棒
    "绘框": SuanChouOpcode.ROD_DRAW_BOX,   # 绘制信息框
    "待算": SuanChouOpcode.ROD_CALC,       # 进入交互式计算器（旧）

    # 算筭交互指令
    "清屏": SuanChouOpcode.ROD_CLEAR,      # 清空画布
    "置键": SuanChouOpcode.ROD_KEY,        # 放置按钮
    "待触": SuanChouOpcode.ROD_WAIT,       # 等待点击
    "触值": SuanChouOpcode.ROD_TOUCH,      # 读取点击值
    "绘文": SuanChouOpcode.ROD_TEXT,       # 显示文本
}

# 天干寄存器表
TIANGAN = {
    "甲": 0, "乙": 1, "丙": 2, "丁": 3,
    "戊": 4, "己": 5, "庚": 6, "辛": 7,
}

# 反向表（显示用）
TIANGAN_REV = {v: k for k, v in TIANGAN.items()}

# 指令分类（用于显示）
ZUPU_CATEGORIES = {
    "数据传输": ["载", "传", "存", "取", "停"],
    "算术运算": ["加", "减", "乘", "除"],
    "逻辑运算": ["与", "或", "异", "非"],
    "位移操作": ["左", "右"],
    "控制流程": ["比", "跳", "等", "别", "大", "小"],
    "算筭原生": ["识", "查", "校", "合", "交", "签", "印", "显"],
    "算筭图形": ["绘数", "绘字", "绘棒", "绘框", "待算"],
    "算筭交互": ["清屏", "置键", "待触", "触值", "绘文"],
}

# 指令含义说明
ZUPU_MEANING = {
    "载": "载入 → 将数值装入算筭寄存器",
    "传": "传递 → 寄存器间传递数据",
    "存": "存入 → 存入算筭内存",
    "取": "取出 → 从算筭内存取出",
    "停": "停机 → 算筭机停止运行",
    "加": "相加 → 两算筭数按位全加",
    "减": "相减 → 补码加法实现",
    "乘": "相乘 → 移位累加实现",
    "除": "相除 → 移位减法实现",
    "与": "通通为通 → 按位与运算",
    "或": "通断为通 → 按位或运算",
    "异": "不同为通 → 按位异或运算",
    "非": "翻转 → 通变断，断变通",
    "左": "左移 → 高位增长",
    "右": "右移 → 低位缩减",
    "比": "比较 → 两数相较，设置标志",
    "跳": "跳转 → 无条件跳至某行",
    "等": "等则跳 → 相等时跳转",
    "别": "别则跳 → 不等时跳转",
    "大": "大则跳 → 大于时跳转",
    "小": "小则跳 → 小于时跳转",
    "识": "识字 → 算筭码反查为何字",
    "查": "查字 → 寻笔画相似之字",
    "校": "校字 → 比两字算筭码异同",
    "合": "合字 → 合并两字笔画",
    "交": "交叠 → 寻两字共同笔画",
    "签": "标签 → 寻共享语义之字",
    "印": "印记 → 以算筭码输出寄存器",
    "显": "显示 → 以汉字形式输出",
    "绘数": "绘数 → 将寄存器值绘制为大号数字",
    "绘字": "绘字 → 绘制汉字卡片",
    "绘棒": "绘棒 → 可视化算筭棒排列",
    "绘框": "绘框 → 绘制信息框（标题, 内容）",
    "待算": "待算 → 进入图形交互式计算器（旧）",
    "清屏": "清屏 → 清除画布上所有内容",
    "置键": "置键 → 放置一个可点击按钮",
    "待触": "待触 → 等待用户点击按钮",
    "触值": "触值 → 将点击值存入寄存器",
    "绘文": "绘文 → 将寄存器值绘制为文本",
}


class SuanChouZupuAssembler:
    """
    算筭字谱汇编器
    
    接受汉字书写的汇编代码，输出与英文汇编器完全相同的算筭机器码。
    
    语法：
      指令 目标寄存器, 源操作数
      ; 注释
    
    寄存器：甲 乙 丙 丁 戊 己 庚 辛
    
    示例：
      载 甲, #42       ; 相当于 LOAD R0, #42
      载 乙, #13       ; 相当于 LOAD R1, #13
      加 甲, 乙        ; 相当于 ADD  R0, R1
      印 甲            ; 相当于 ROD_PRINT R0
      停               ; 相当于 HALT
    """

    @staticmethod
    def assemble(zupu_lines):
        """
        汇编算筭字谱源代码
        参数:
            zupu_lines: 算筭字谱源代码行列表
        返回:
            (SuanChouInstruction列表, 错误列表)
        """
        instructions = []
        errors = []
        labels = {}

        # 第一遍：收集标签
        addr = 0
        for line_num, line in enumerate(zupu_lines, 1):
            line = line.strip()
            if not line or line.startswith("；") or line.startswith(";"):
                continue
            # 先剥离行尾注释再检查标签
            semi = line.find("；")
            if semi == -1:
                semi = line.find(";")
            if semi >= 0:
                line = line[:semi].strip()
            if line.endswith("：") or line.endswith(":"):
                label = line[:-1].strip()
                labels[label] = addr
                continue
            addr += 1

        # 第二遍：汇编
        addr = 0
        for line_num, line in enumerate(zupu_lines, 1):
            line = line.strip()
            if not line or line.startswith("；") or line.startswith(";"):
                continue
            # 先剥离行尾注释再检查标签
            semi = line.find("；")
            if semi == -1:
                semi = line.find(";")
            if semi >= 0:
                line = line[:semi].strip()
            if line.endswith("：") or line.endswith(":"):
                continue

            # 解析指令和操作数
            # 格式: 指令 操作数, 操作数
            # 或:   指令
        
            parts = line.replace("，", ",").split()
            if not parts:
                continue

            mnemonic = parts[0]
            operands = parts[1:] if len(parts) > 1 else []

            # 查找操作码
            if mnemonic not in ZUPU_TABLE:
                errors.append(
                    f"第{line_num}行: 不识指令「{mnemonic}」")
                continue

            opcode = ZUPU_TABLE[mnemonic]
            dest = 0
            src = 0

            # 跳转指令集
            _JUMP = {"跳", "等", "别", "大", "小"}

            # 解析操作数
            if operands:
                # 跳转指令特殊处理：操作数是地址而非寄存器
                if mnemonic in _JUMP:
                    src_op = operands[0].lstrip("#")
                    if src_op in labels:
                        src = labels[src_op]
                    else:
                        src = int(src_op)
                    inst = SuanChouInstruction(opcode, 0, src)
                    instructions.append(inst)
                    addr += 1
                    continue

                # 目标操作数
                dest_op = operands[0].rstrip(",")
                if dest_op in TIANGAN:
                    dest = TIANGAN[dest_op]
                else:
                    errors.append(
                        f"第{line_num}行: 不识寄存器「{dest_op}」"
                        f"，可用：{' '.join(TIANGAN.keys())}")
                    continue

                # 源操作数
                if len(operands) > 1:
                    src_op = operands[1].lstrip(",")
                    if src_op in TIANGAN:
                        src = TIANGAN[src_op]
                    elif src_op.startswith("#"):
                        # #立即数 或 #标签名
                        src_str = src_op[1:]
                        if src_str in labels:
                            src = labels[src_str]
                        else:
                            src = int(src_str)
                    elif src_op in labels:
                        src = labels[src_op]
                    else:
                        try:
                            src = int(src_op)
                        except ValueError:
                            errors.append(
                                f"第{line_num}行: 不识操作数「{src_op}」")
                            continue

            inst = SuanChouInstruction(opcode, dest, src)
            instructions.append(inst)
            addr += 1

        return instructions, errors

    @staticmethod
    def disassemble(instructions):
        """反汇编为算筭字谱格式"""
        print(f"\n  {'地址':6s} {'算筭机器码':24s} {'算筭字谱':20s} {'英文对照'}")
        print("  " + "-" * 80)
        for i, inst in enumerate(instructions):
            rod = inst.to_rod_string()
            zupu_str = SuanChouZupuAssembler._to_zupu(inst)
            eng_str = inst.disassemble()
            print(f"  {i:04d}   {rod}   {zupu_str:18s} {eng_str}")

    @staticmethod
    def _to_zupu(inst):
        """将单条指令转为算筭字谱表示"""
        op = inst.opcode
        rd = inst.dest_reg
        rs = inst.src

        # 找到操作码对应的汉字
        zupu_op = None
        for ch, code in ZUPU_TABLE.items():
            if code == op:
                zupu_op = ch
                break
        if not zupu_op:
            return f"?({op})"

        reg_name = TIANGAN_REV.get(rd, f"R{rd}")

        # 根据指令类型格式化
        if op == SuanChouOpcode.HALT:
            return "停"
        elif op == SuanChouOpcode.ROD_CALC:
            return "待算"
        elif op == SuanChouOpcode.ROD_CLEAR:
            return "清屏"
        elif op == SuanChouOpcode.ROD_WAIT:
            return "待触"
        elif op == SuanChouOpcode.NOT:
            return f"非 {reg_name}"
        elif op in (SuanChouOpcode.LOAD,):
            return f"载 {reg_name}, #{rs}"
        elif op in (SuanChouOpcode.LMEM, SuanChouOpcode.STORE):
            return f"{zupu_op} {reg_name}, #{rs}"
        elif op in (SuanChouOpcode.ROD_PRINT, SuanChouOpcode.ROD_SHOW,
                     SuanChouOpcode.ROD_FIND, SuanChouOpcode.ROD_TAG,
                     SuanChouOpcode.ROD_DRAW_NUM, SuanChouOpcode.ROD_DRAW_CHAR,
                     SuanChouOpcode.ROD_DRAW_ROD,
                     SuanChouOpcode.ROD_TOUCH, SuanChouOpcode.ROD_TEXT):
            return f"{zupu_op} {reg_name}"
        elif op in (SuanChouOpcode.JMP, SuanChouOpcode.JE,
                     SuanChouOpcode.JNE, SuanChouOpcode.JG,
                     SuanChouOpcode.JL):
            return f"{zupu_op} #{rs}"
        elif op == SuanChouOpcode.ROD_DRAW_BOX:
            src_reg = TIANGAN_REV.get(rs, f"R{rs}")
            return f"{zupu_op} {reg_name}, {src_reg}"
        elif op == SuanChouOpcode.ROD_KEY:
            src_reg = TIANGAN_REV.get(rs, f"R{rs}")
            return f"{zupu_op} {reg_name}, {src_reg}"
        else:
            src_reg = TIANGAN_REV.get(rs, None)
            if src_reg:
                return f"{zupu_op} {reg_name}, {src_reg}"
            else:
                return f"{zupu_op} {reg_name}, #{rs}"


def show_zupu_isa():
    """展示算筭字谱指令集"""
    print("=" * 70)
    print("  算筭字谱 (SuanChou Character Notation)")
    print("  以汉字书写计算机指令")
    print("=" * 70)

    print(f"\n  寄存器：{'  '.join(f'{k}=R{v}' for k, v in TIANGAN.items())}")
    print()

    for category, mnemonics in ZUPU_CATEGORIES.items():
        print(f"  【{category}】")
        for m in mnemonics:
            code = ZUPU_TABLE[m]
            rod = SuanChouOpcode.to_rod(code)
            meaning = ZUPU_MEANING.get(m, "")
            print(f"    {m}    {rod}  ({code:06b})  {meaning}")
        print()


def show_guqin_parallel():
    """
    展示古琴减字谱与算筭字谱的平行结构
    
    古琴减字谱是现存最古老的「领域专用语言」(DSL) 之一，
    其核心思想与算筭字谱完全一致：
    用汉字的部件组合来表达复杂指令。
    """
    print("=" * 70)
    print("  古琴减字谱 × 算筭字谱 —— 跨越千年的平行结构")
    print("=" * 70)

    print("""
  古琴减字谱 (唐代, ~7世纪)
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │   减字谱的原理：                                         │
  │   从多个完整的汉字中各取一个「部件」，                    │
  │   组合成一个新的「合成字」，                             │
  │   用一个字表达一条完整的演奏指令。                       │
  │                                                         │
  │   例：                                                   │
  │                                                         │
  │   ┌─────┬─────┬─────┐                                   │
  │   │ 部件 │ 来源 │ 含义 │                                 │
  │   ├─────┼─────┼─────┤                                   │
  │   │  大  │ 大指 │ 拇指按弦 │                             │
  │   │  九  │ 九徽 │ 第九徽位 │                             │
  │   │  七  │ 七弦 │ 第七根弦 │                             │
  │   └─────┴─────┴─────┘                                   │
  │                                                         │
  │   合成： [大九七] = 拇指按九徽挑七弦                     │
  │   一个字，一条指令，无需多余的符号。                     │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
""")

    print("""
  算筭字谱 (现在, 2026)
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │   同样的原理：                                           │
  │   从汉字中取部件，组合为算筭指令。                       │
  │                                                         │
  │   ┌─────┬─────┬──────────────────────────┐             │
  │   │ 部件 │ 来源 │ 含义                    │             │
  │   ├─────┼─────┼──────────────────────────┤             │
  │   │  载  │ 装载 │ LOAD 操作               │             │
  │   │  甲  │ 天干 │ 寄存器 0               │             │
  │   │ 卌二 │ 四十+二│ 数值 42               │             │
  │   └─────┴─────┴──────────────────────────┘             │
  │                                                         │
  │   合成： [载甲卌二] = LOAD R0, #42                      │
  │   如果算筭处理器有对应的字库，                          │
  │   这就是一条完整的机器指令的「字形」。                   │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
""")

    print("""
  三个层次的平行关系
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │                  古琴减字谱          算筭字谱            │
  │  ──────────  ──────────────────  ──────────────────      │
  │  领域          音乐演奏            计算机指令             │
  │  基本单位      汉字部件            汉字部件               │
  │  组合方式      取字之半，合为新字  取字之义，合为指令     │
  │  表示密度      一字一指令          一字一指令             │
  │  目标受众      琴人                程序员/算筭机          │
  │  数字化        需要专用字库        理想：算筭处理器字库   │
  │                                                          │
  │  共同特质：                                              │
  │    · 都不是拼音文字，而是「部件组合文字」                 │
  │    · 一个符号 = 一个完整语义单元                          │
  │    · 信息密度远超线性符号系统                            │
  │    · 对母语者天然可读                                    │
  │                                                          │
  └──────────────────────────────────────────────────────────┘
""")

    print("""
  如果算筭字谱有专用字体…
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │  想象一个「算筭指令字库」：                               │
  │                                                          │
  │   载 + 甲 + 数值部件 → 一个合成字                         │
  │   加 + 甲 + 乙       → 一个合成字                         │
  │   比 + 甲 + 乙       → 一个合成字                         │
  │   跳 + 行号部件      → 一个合成字                         │
  │   识 + 甲            → 一个合成字                         │
  │                                                          │
  │  整个程序就是一行「汉字」，                                │
  │  每个字都是一条完整的机器指令，                            │
  │  人可以直接读，机器可以直接执行。                          │
  │                                                          │
  │  这就是古琴减字谱在计算机领域的回响。                      │
  │                                                          │
  └──────────────────────────────────────────────────────────┘
""")


def demo_zupu_vm():
    """演示用算筭字谱编写并执行程序"""
    print("=" * 70)
    print("  算筭字谱编程演示")
    print("  用汉字写汇编 → 编译为算筭码 → 在虚拟机中执行")
    print("=" * 70)

    assembler = SuanChouZupuAssembler()

    # ===== 程序1：基础算术 =====
    print("\n" + "-" * 70)
    print("  [字谱程序1] 计算 42 + 13 × 7")
    print("-" * 70)

    zupu_prog_1 = [
        "； 算筭字谱程序 —— 计算 42 + 13 × 7",
        "",
        "载 甲, #42       ； 甲 = 42",
        "载 乙, #13       ； 乙 = 13",
        "载 丙, #7        ； 丙 = 7",
        "乘 乙, 丙        ； 乙 = 乙 × 丙 = 91",
        "加 甲, 乙        ； 甲 = 甲 + 乙 = 133",
        "印 甲            ； 以算筭码显示结果",
        "停               ； 程序结束",
    ]

    print("\n  算筭字谱源码：")
    for line in zupu_prog_1:
        print(f"    {line}")

    insts, errs = assembler.assemble(zupu_prog_1)
    if errs:
        for e in errs:
            print(f"  [错误] {e}")
        return

    print("\n  汇编结果（算筭字谱 ↔ 英文对照）：")
    assembler.disassemble(insts)

    vm = SuanChouVM()
    vm.load_program(insts)
    vm.run(trace=False)
    print("\n  执行结果：")
    vm.show_output()

    # ===== 程序2：汉字识别 =====
    print("\n" + "-" * 70)
    print("  [字谱程序2] 算筭码识字")
    print("-" * 70)

    from stroke_dictionary import StrokeDictionary
    dic = StrokeDictionary()
    ri_obj = dic.get_character("日")
    rod_bits = ri_obj._encoded._bits
    ri_val = 0
    for j, bit in enumerate(rod_bits):
        if bit.is_on:
            ri_val |= (1 << j)

    zupu_prog_2 = [
        "； 算筭字谱 —— 识字",
        "",
        "载 甲, #" + str(ri_val) + "   ； 载入算筭码",
        "识 甲                ； 识别为何字",
        "显 甲                ； 显示为汉字",
        "签 甲                ； 查询语义关联字",
        "停",
    ]

    print("  算筭字谱源码：")
    for line in zupu_prog_2:
        print(f"    {line}")

    insts2, errs2 = assembler.assemble(zupu_prog_2)
    if errs2:
        for e in errs2:
            print(f"  [错误] {e}")
        return

    assembler.disassemble(insts2)

    vm2 = SuanChouVM()
    # 预载数据到高地址
    vm2.memory[32] = CountingRodNumber(ri_val, ri_obj.bits)
    vm2.load_program(insts2)
    vm2.run(trace=False)
    print("\n  执行结果：")
    vm2.show_output()

    # ===== 程序3：循环 · 用天干寄存器 =====
    print("\n" + "-" * 70)
    print("  [字谱程序3] 循环累加（天干寄存器）")
    print("-" * 70)

    zupu_prog_3 = [
        "； 算筭字谱 —— 计算 5+4+3+2+1",
        "",
        "载 甲, #0     ； 甲 = 累加器 = 0",
        "载 乙, #5     ； 乙 = 计数器 = 5",
        "载 丙, #1     ； 丙 = 递减量 = 1",
        "",
        "循环：",
        "加 甲, 乙     ； 甲 = 甲 + 乙",
        "减 乙, 丙     ； 乙 = 乙 - 丙",
        "比 乙, 丙     ； 比较 乙 和 丙",
        "大 #循环     ； 若 乙 > 丙 则跳回循环",
        "加 甲, 乙     ； 最后一次累加",
        "印 甲         ； 输出 甲",
        "停",
    ]

    print("  算筭字谱源码：")
    for line in zupu_prog_3:
        print(f"    {line}")

    insts3, errs3 = assembler.assemble(zupu_prog_3)
    if errs3:
        for e in errs3:
            print(f"  [错误] {e}")
        return

    assembler.disassemble(insts3)

    vm3 = SuanChouVM()
    vm3.load_program(insts3)
    vm3.run(trace=False)
    print("\n  执行结果：")
    vm3.show_output()

    print("\n" + "=" * 70)
    print("  算筭字谱演示完毕。")
    print()
    print("  算筭字谱 = 算筭英文汇编 ≡ 算筭机器码")
    print("  三种写法，同一套机器码。")
    print("=" * 70)


def show_side_by_side():
    """三种表示法的并排对比"""
    print("=" * 70)
    print("  三种表示法并排对比")
    print("  算筭字谱  ←→  英文汇编  ←→  算筭机器码")
    print("=" * 70)

    print("""
  算筭字谱                    英文汇编                   算筭机器码
  ────────────────────────  ─────────────────────────  ─────────────────
  载 甲, #42                 LOAD R0, #42               |||||—||||—|—|—|
  载 乙, #13                 LOAD R1, #13               |||||—||—|||——|—
  载 丙, #7                  LOAD R2, #7                |||||—|—||||———
  乘 乙, 丙                  MUL  R1, R2                ||—|—||—|||||—|
  加 甲, 乙                  ADD  R0, R1                ||—||||||||||||—
  印 甲                      ROD_PRINT R0               —————||||||||||||
  停                         HALT                       ||||||||||||||||

  等价性：
    同一段算筭汇编，可以写成英文 (LOAD/ADD/HALT)、
    也可以写成汉字 (载/加/停)。
    编译出的算筭机器码完全一致 —— 只是人类看的文字不同。

  这意味着什么？
    如果你有一个算筭码处理器，它的指令集可以用人类语言定义。
    英语编程 → 算筭码 → 电子运行 [OK]
    中文编程 → 算筭码 → 电子运行 [OK]
    这两种「语言」在机器码层面是无法区分的。
    
    算筭码才是真正的「世界语」—— 它不在乎你用什么文字写程序，
    它只在乎 — 和 |。
""")

    # 验证等价性
    from suanchou_vm import SuanChouAssembler
    eng_asm = SuanChouAssembler()
    zupu_asm = SuanChouZupuAssembler()

    eng_prog = [
        "LOAD R0, #42", "LOAD R1, #13", "LOAD R2, #7",
        "MUL  R1, R2", "ADD  R0, R1", "ROD_PRINT R0", "HALT",
    ]
    zupu_prog = [
        "载 甲, #42", "载 乙, #13", "载 丙, #7",
        "乘 乙, 丙", "加 甲, 乙", "印 甲", "停",
    ]

    eng_insts = eng_asm.assemble(eng_prog)
    zupu_insts, _ = zupu_asm.assemble(zupu_prog)

    identical = True
    for i, (e, z) in enumerate(zip(eng_insts, zupu_insts)):
        if e.encode().to_int() != z.encode().to_int():
            identical = False
            print(f"  差异: 指令[{i}] 英文={e.encode().to_int()} 字谱={z.encode().to_int()}")
    
    if identical:
        print(f"  >>> 验证通过：{len(eng_insts)}条指令，英文汇编与算筭字谱产生完全相同的机器码。")
    else:
        print(f"  >>> 验证失败！")

    print()


def main():
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║                                                      ║")
    print("  ║     算  筭  字  谱                                   ║")
    print("  ║     SuanChou Character Notation                      ║")
    print("  ║                                                      ║")
    print("  ║     受古琴减字谱启发                                 ║")
    print("  ║     以汉字部件组合表达计算机指令                      ║")
    print("  ║                                                      ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()

    # 1. 展示指令集
    show_zupu_isa()
    input("[按 Enter 继续]")

    # 2. 展示古琴对比
    show_guqin_parallel()
    input("[按 Enter 继续]")

    # 3. 演示编程
    demo_zupu_vm()
    print()
    input("[按 Enter 继续]")

    # 4. 并排对比
    show_side_by_side()

    print("\n" + "=" * 70)
    print("  表示完毕。")
    print()
    print("  古琴减字谱用一个合成字表达一条演奏指令。")
    print("  算筭字谱用一个汉字表达一条计算指令。")
    print("  两者的根本思想是相同的：")
    print("  「汉字不是字母的排列，而是意义的组合。」")
    print("=" * 70)


if __name__ == "__main__":
    main()

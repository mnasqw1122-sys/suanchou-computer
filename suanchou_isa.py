# -*- coding: utf-8 -*-
"""
算筭指令集架构 (SuanChou ISA)
==================================
直接以算筭码（— 和 |）作为底层指令集的虚拟机指令体系。

核心思想：
  传统计算机：高级语言 → 编译 → 二进制机器码 → CPU执行
  算筭计算机：自然语言/汉字 → 算筭汇编 → 算筭机器码 → 算筭VM执行
  
  "跳过二进制翻译层，直接执行算筭码" —— 这就是效率提升的根源。

指令格式（16位）：
  [操作码 6位] [目标寄存器 3位] [源寄存器/立即数 7位]
  
  位序显示（MSB→LSB）：
  操作码[5:0] 目标[2:0] 源[6:0]

8个通用寄存器 R0-R7，每个寄存器存储一个算筭数
"""

from counting_rod_computer import (
    CountingRodBit, CountingRodNumber, CountingRodComputer
)

# ================================================================
# 算筭指令集定义（6位操作码）
# ================================================================

class SuanChouOpcode:
    """算筭操作码定义 —— 每种操作都直接用算筭符号表示"""

    # 数据传输
    HALT  = 0b000000  # 停机
    LOAD  = 0b000001  # 加载立即数到寄存器
    MOV   = 0b000010  # 寄存器间移动
    STORE = 0b000011  # 存储寄存器到内存
    LMEM  = 0b000100  # 从内存加载到寄存器

    # 算术运算
    ADD   = 0b001000  # 加法 Rdest = Rdest + Rsrc
    SUB   = 0b001001  # 减法
    MUL   = 0b001010  # 乘法
    DIV   = 0b001011  # 除法（商→Rdest, 余→Rspecial）

    # 逻辑运算
    AND   = 0b010000  # 按位与
    OR    = 0b010001  # 按位或
    XOR   = 0b010010  # 按位异或
    NOT   = 0b010011  # 按位取反（单操作数，忽略源）

    # 位移运算
    SHL   = 0b010100  # 左移
    SHR   = 0b010101  # 右移

    # 控制流
    CMP   = 0b011000  # 比较 Rdest 和 Rsrc，设置标志
    JMP   = 0b011001  # 无条件跳转（立即数地址）
    JE    = 0b011010  # 相等跳转
    JNE   = 0b011011  # 不等跳转
    JG    = 0b011100  # 大于跳转
    JL    = 0b011101  # 小于跳转

    # ========== 算筭特有指令 ==========
    # 这些指令直接操作算筭码，无需二进制转换
    ROD_CHAR  = 0b100000  # 从算筭码加载汉字：将算筭码字符串转为笔画存入寄存器
    ROD_FIND  = 0b100001  # 算筭码查字：以寄存器中的算筭码在字典中查找汉字
    ROD_CMP   = 0b100010  # 算筭码比较两字：RX和RY的算筭码逐位比较
    ROD_MERGE = 0b100011  # 算筭码合并：OR两个字的算筭码（模拟合字）
    ROD_OVERLAP = 0b100100  # 算筭码重叠：AND两个字的算筭码（找共同笔画）
    ROD_TAG   = 0b100101  # 语义标签查询：查寄存器中汉字的语义标签
    # ========== 算筭图形指令 ==========
    # 这些指令在支持图形的算筭系统上产生可视化输出
    ROD_DRAW_NUM  = 0b100110  # 绘制大号数字：根据Rdest的值绘制大号数字
    ROD_DRAW_CHAR = 0b100111  # 绘制汉字卡片：根据Rdest中的算筭码绘制汉字
    ROD_DRAW_ROD  = 0b101000  # 绘制算筭棒：可视化Rdest中的算筭码
    ROD_DRAW_BOX  = 0b101001  # 绘制信息框
    ROD_CALC      = 0b101010  # 进入交互式计算器模式（旧，将废弃）

    # ========== 算筭交互指令 ==========
    # 这些指令让 .suan 程序能自己写图形程序
    ROD_CLEAR    = 0b101011  # 清屏：清除画布
    ROD_KEY      = 0b101100  # 置键：Rdest=位置, Rsrc=标签值
    ROD_WAIT     = 0b101101  # 待触：暂停，等待用户点击
    ROD_TOUCH    = 0b101110  # 触值：将点击值存入Rdest
    ROD_TEXT     = 0b101111  # 绘文：以Rdest的值作为文本绘制在画布中央

    ROD_PRINT = 0b111110  # 输出寄存器（以算筭码显示）
    ROD_SHOW  = 0b111111  # 输出寄存器（以汉字显示）

    # 操作码到名称映射
    _NAMES = {
        0b000000: "HALT",    0b000001: "LOAD",    0b000010: "MOV",
        0b000011: "STORE",   0b000100: "LMEM",
        0b001000: "ADD",     0b001001: "SUB",     0b001010: "MUL",
        0b001011: "DIV",
        0b010000: "AND",     0b010001: "OR",      0b010010: "XOR",
        0b010011: "NOT",     0b010100: "SHL",     0b010101: "SHR",
        0b011000: "CMP",     0b011001: "JMP",     0b011010: "JE",
        0b011011: "JNE",     0b011100: "JG",      0b011101: "JL",
        0b100000: "ROD_CHAR", 0b100001: "ROD_FIND",
        0b100010: "ROD_CMP",  0b100011: "ROD_MERGE",
        0b100100: "ROD_OVERLAP", 0b100101: "ROD_TAG",
        0b100110: "ROD_DRAW_NUM", 0b100111: "ROD_DRAW_CHAR",
        0b101000: "ROD_DRAW_ROD", 0b101001: "ROD_DRAW_BOX",
        0b101010: "ROD_CALC",
        0b101011: "ROD_CLEAR", 0b101100: "ROD_KEY",
        0b101101: "ROD_WAIT", 0b101110: "ROD_TOUCH",
        0b101111: "ROD_TEXT",
        0b111110: "ROD_PRINT", 0b111111: "ROD_SHOW",
    }

    @classmethod
    def name(cls, opcode):
        """获取操作码名称"""
        return cls._NAMES.get(opcode, f"UNKNOWN({opcode:06b})")

    @classmethod
    def to_rod(cls, opcode):
        """将操作码转为算筭字符串"""
        bits = []
        for i in range(6):
            bits.append(CountingRodBit((opcode >> (5 - i)) & 1))
        return "".join(str(b) for b in bits)

    @classmethod
    def from_rod(cls, rod_str):
        """从算筭字符串解析操作码"""
        clean = rod_str.replace(" ", "")
        opcode = 0
        for i, ch in enumerate(clean[:6]):
            if ch == CountingRodBit.ON_SYMBOL:
                opcode |= (1 << (5 - i))
        return opcode


class SuanChouInstruction:
    """单条算筭指令——16位算筭码"""

    def __init__(self, opcode, dest_reg=0, src=0):
        """
        创建一条算筭指令
        参数:
            opcode: 6位操作码
            dest_reg: 3位目标寄存器（0-7）
            src: 7位源（寄存器号 0-7 或立即数 0-127）
        """
        self.opcode = opcode & 0b111111
        self.dest_reg = dest_reg & 0b111
        self.src = src & 0b1111111

    def encode(self):
        """
        编码为 16 位算筭数
        格式：[opcode 6位][dest 3位][src 7位] = 16位
        """
        value = (self.opcode << 10) | (self.dest_reg << 7) | self.src
        return CountingRodNumber(value, 16)

    def to_rod_string(self):
        """以算筭字符串显示"""
        encoded = self.encode()
        return encoded.to_rod_string()

    def disassemble(self):
        """
        反汇编为人类可读形式
        """
        op_name = SuanChouOpcode.name(self.opcode)
        reg_names = [f"R{i}" for i in range(8)]

        # 根据指令类型解释操作数
        op_cat = self.opcode >> 3

        if self.opcode == SuanChouOpcode.HALT:
            return "HALT"
        elif self.opcode == SuanChouOpcode.ROD_CALC:
            return "ROD_CALC"
        elif self.opcode in (SuanChouOpcode.ROD_CLEAR,):
            return "ROD_CLEAR"
        elif self.opcode in (SuanChouOpcode.ROD_WAIT,):
            return "ROD_WAIT"
        elif self.opcode == SuanChouOpcode.NOT:
            return f"NOT  {reg_names[self.dest_reg]}"
        elif self.opcode in (SuanChouOpcode.LOAD,):
            return f"LOAD {reg_names[self.dest_reg]}, #{self.src}"
        elif self.opcode in (SuanChouOpcode.LMEM, SuanChouOpcode.STORE):
            return f"{op_name}  {reg_names[self.dest_reg]}, #{self.src}"
        elif self.opcode in (SuanChouOpcode.JMP, SuanChouOpcode.JE,
                             SuanChouOpcode.JNE, SuanChouOpcode.JG,
                             SuanChouOpcode.JL):
            return f"{op_name}  #{self.src}"
        elif self.opcode in (SuanChouOpcode.ROD_PRINT, SuanChouOpcode.ROD_SHOW,
                             SuanChouOpcode.ROD_FIND, SuanChouOpcode.ROD_TAG,
                             SuanChouOpcode.ROD_DRAW_NUM, SuanChouOpcode.ROD_DRAW_CHAR,
                             SuanChouOpcode.ROD_DRAW_ROD,
                             SuanChouOpcode.ROD_TOUCH, SuanChouOpcode.ROD_TEXT):
            return f"{op_name} {reg_names[self.dest_reg]}"
        elif self.opcode in (SuanChouOpcode.ROD_CHAR,):
            return f"{op_name} {reg_names[self.dest_reg]}, #{self.src}"
        elif self.opcode in (SuanChouOpcode.ROD_CMP, SuanChouOpcode.ROD_MERGE,
                             SuanChouOpcode.ROD_OVERLAP, SuanChouOpcode.ROD_DRAW_BOX,
                             SuanChouOpcode.ROD_KEY):
            return f"{op_name} {reg_names[self.dest_reg]}, R{self.src}"
        else:
            if self.src < 8:
                return f"{op_name}  {reg_names[self.dest_reg]}, {reg_names[self.src]}"
            else:
                return f"{op_name}  {reg_names[self.dest_reg]}, #{self.src}"

    def __str__(self):
        return f"[{self.to_rod_string()}] {self.disassemble()}"


def make_instruction(opcode, dest=0, src=0):
    """快速创建指令的辅助函数"""
    return SuanChouInstruction(opcode, dest, src)


# ================================================================
# 算筭指令集列表展示
# ================================================================

def show_isa():
    """展示算筭指令集"""
    print("=" * 70)
    print("  算筭指令集 (SuanChou ISA)")
    print("  所有指令直接以 — 和 | 编码")
    print("=" * 70)

    print(f"\n【数据传输指令】")
    for op in (SuanChouOpcode.LOAD, SuanChouOpcode.MOV, SuanChouOpcode.STORE, SuanChouOpcode.LMEM):
        inst = SuanChouInstruction(op, 0, 1)
        print(f"  {SuanChouOpcode.to_rod(op)}  {SuanChouOpcode.name(op):8s}  {inst.disassemble()}")

    print(f"\n【算术运算指令】")
    for op in (SuanChouOpcode.ADD, SuanChouOpcode.SUB, SuanChouOpcode.MUL, SuanChouOpcode.DIV):
        inst = SuanChouInstruction(op, 0, 1)
        print(f"  {SuanChouOpcode.to_rod(op)}  {SuanChouOpcode.name(op):8s}  {inst.disassemble()}")

    print(f"\n【逻辑运算指令】")
    for op in (SuanChouOpcode.AND, SuanChouOpcode.OR, SuanChouOpcode.XOR, SuanChouOpcode.NOT):
        inst = SuanChouInstruction(op, 0, 1)
        print(f"  {SuanChouOpcode.to_rod(op)}  {SuanChouOpcode.name(op):8s}  {inst.disassemble()}")

    print(f"\n【位移指令】")
    for op in (SuanChouOpcode.SHL, SuanChouOpcode.SHR):
        inst = SuanChouInstruction(op, 0, 1)
        print(f"  {SuanChouOpcode.to_rod(op)}  {SuanChouOpcode.name(op):8s}  {inst.disassemble()}")

    print(f"\n【控制流指令】")
    for op in (SuanChouOpcode.CMP, SuanChouOpcode.JMP, SuanChouOpcode.JE,
               SuanChouOpcode.JNE, SuanChouOpcode.JG, SuanChouOpcode.JL):
        inst = SuanChouInstruction(op, 0, 1)
        print(f"  {SuanChouOpcode.to_rod(op)}  {SuanChouOpcode.name(op):8s}  {inst.disassemble()}")

    print(f"\n【算筭原生指令】⭐ 独有优势")
    for op in (SuanChouOpcode.ROD_CHAR, SuanChouOpcode.ROD_FIND,
               SuanChouOpcode.ROD_CMP, SuanChouOpcode.ROD_MERGE,
               SuanChouOpcode.ROD_OVERLAP, SuanChouOpcode.ROD_TAG,
               SuanChouOpcode.ROD_PRINT, SuanChouOpcode.ROD_SHOW):
        inst = SuanChouInstruction(op, 0, 1)
        print(f"  {SuanChouOpcode.to_rod(op)}  {SuanChouOpcode.name(op):10s}  {inst.disassemble()}")


if __name__ == "__main__":
    show_isa()

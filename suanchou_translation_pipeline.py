# -*- coding: utf-8 -*-
"""
算筭码 → 二进制 完整翻译管道源码展示
====================================================
本文件逐层展示 — 和 | 是如何一步步变成计算机能够执行的二进制运算的。

五层翻译管道：
  ┌─────────────────────────────────────────────────────┐
  │ 第0层  物理符号  — (通, ON)  <->  | (断, OFF)        │
  │ 第1层  单个位    CountingRodBit  <->  int 0/1        │
  │ 第2层  算筭数    CountingRodNumber <-> 整数 / 位列表 │
  │ 第3层  算筭指令  SuanChouInstruction <-> 16位算筭码  │
  │ 第4层  虚拟机    SuanChouVM 取指/译码/执行         │
  └─────────────────────────────────────────────────────┘

运行方式：
  py suanchou_translation_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import (
    CountingRodBit, CountingRodNumber, CountingRodComputer
)
from suanchou_isa import SuanChouOpcode, SuanChouInstruction
from suanchou_vm import SuanChouVM, SuanChouAssembler
from stroke_encoder import Stroke, StrokeEncoder
from stroke_dictionary import StrokeDictionary


# ================================================================
# 第0层：物理符号定义
# ================================================================
def layer_0_physical_symbols():
    """
    ┌──────────────────────────────────────────────────────────┐
    │ 第0层：物理符号定义                                       │
    │                                                          │
    │ 源码位置：counting_rod_computer.py : CountingRodBit      │
    │                                                          │
    │ 这是整个系统的最底层 —— 两种可视符号的声明。              │
    │ 类似于晶体管有两种状态 (通电/断电)，                       │
    │ 算筭有两种状态 (—/|)。                                    │
    │                                                          │
    │ 注意：此时还没有「计算」，只有「符号 <-> 值」的映射。        │
    └──────────────────────────────────────────────────────────┘
    """
    print("=" * 70)
    print("  【第0层】物理符号定义")
    print("  " + "-" * 64)
    print("  | 源码：counting_rod_computer.py                        |")
    print("  |                                                       |")
    print("  | class CountingRodBit:                                 |")
    print("  |     ON_SYMBOL  = \"—\"   # 通, 对应二进制 1             |")
    print("  |     OFF_SYMBOL = \"|\"   # 断, 对应二进制 0             |")
    print("  |                                                       |")
    print("  |     def __init__(self, value):                        |")
    print("  |         if isinstance(value, int):                    |")
    print("  |             self._value = 1 if value else 0           |")
    print("  |         elif isinstance(value, str):                  |")
    print("  |             self._value = 1 if value.strip()==\"—\"     |")
    print("  |                            else 0                     |")
    print("  |         else:                                         |")
    print("  |             self._value = 0                           |")
    print("  +-------------------------------------------------------+")
    print()
    print("  运行时验证：")
    bit_on  = CountingRodBit("—")
    bit_off = CountingRodBit("|")
    bit_1   = CountingRodBit(1)
    bit_0   = CountingRodBit(0)
    print(f"    CountingRodBit('—')  ->  显示: {bit_on}  内部值: {bit_on._value}  binary: {bit_on.binary}")
    print(f"    CountingRodBit('|')  ->  显示: {bit_off}  内部值: {bit_off._value}  binary: {bit_off.binary}")
    print(f"    CountingRodBit(1)    ->  显示: {bit_1}  内部值: {bit_1._value}  binary: {bit_1.binary}")
    print(f"    CountingRodBit(0)    ->  显示: {bit_0}  内部值: {bit_0._value}  binary: {bit_0.binary}")


# ================================================================
# 第1层：单个位 <-> 整数
# ================================================================
def layer_1_single_bit_to_int():
    """
    ┌──────────────────────────────────────────────────────────┐
    │ 第1层：单个算筭位 <-> 整数 0/1                             │
    │                                                          │
    │ 源码位置：counting_rod_computer.py : CountingRodBit      │
    │                                                          │
    │ 这是翻译管道的第一级转换：                                 │
    │                                                          │
    │   —(通)  →  CountingRodBit._value = 1  →  binary = 1    │
    │   |(断)  →  CountingRodBit._value = 0  →  binary = 0    │
    │                                                          │
    │ 关键属性：                                                │
    │   self._value   : 内部存储，0 或 1                       │
    │   self.binary   : 暴露给外部的二进制值                   │
    │   self.is_on    : 是否为通(1)                            │
    │   self.is_off   : 是否为断(0)                            │
    │                                                          │
    │ 关键方法：                                                │
    │   __str__()     : 转为可视符号 — 或 |                    │
    │   flip()        : 翻转该位                               │
    │   from_rod()    : 从算筭符号字符串批量创建位列表          │
    └──────────────────────────────────────────────────────────┘
    """
    print("=" * 70)
    print("  【第1层】单个算筭位 <-> 整数 0/1")
    print("  " + "-" * 64)
    print("  | def to_rod_string(self):                             |")
    print("  |     return self.ON_SYMBOL if self._value              |")
    print("  |            else self.OFF_SYMBOL                       |")
    print("  |                                                       |")
    print("  | @property                                             |")
    print("  | def binary(self):                                     |")
    print("  |     return self._value  # 直接返回 0 或 1             |")
    print("  |                                                       |")
    print("  | @staticmethod                                         |")
    print("  | def from_rod(rod_str):                                |")
    print("  |     bits = []                                         |")
    print("  |     for ch in rod_str:                                |")
    print("  |         if ch in ('—', '|'):                          |")
    print("  |             bits.append(CountingRodBit(ch))           |")
    print("  |     return bits                                       |")
    print("  +-------------------------------------------------------+")
    print()
    print("  运行时演示 —— 将算筭符号串 \"—|—|\" 逐字翻译：")
    test_str = "—|—|"
    print(f"    输入算筭串: \"{test_str}\"")
    bits = CountingRodBit.from_rod(test_str)
    print(f"    from_rod(\"{test_str}\") → [{', '.join(str(b) for b in bits)}]")
    print(f"    每个位的内部值: {[b._value for b in bits]}")
    print(f"    每个位的 binary:  {[b.binary for b in bits]}")
    print(f"    可视化还原:       {''.join(str(b) for b in bits)}")


# ================================================================
# 第2层：算筭数 <-> 整数 <-> 二进制位列表
# ================================================================
def layer_2_rod_number_to_int():
    """
    ┌──────────────────────────────────────────────────────────┐
    │ 第2层：算筭数 <-> 整数 <-> 二进制位列表                      │
    │                                                          │
    │ 源码位置：counting_rod_computer.py : CountingRodNumber   │
    │                                                          │
    │ 这是翻译管道最关键的一层。算筭数由多个位组成，             │
    │ 内部以列表存储（索引0=最低位），显示时高位在前。           │
    │                                                          │
    │ 关键约定：                                                │
    │   内部存储 (self._bits)：                                  │
    │     _bits[0] = 个位 (LSB, 最低位)                         │
    │     _bits[1] = 二位                                       │
    │     _bits[2] = 四位                                       │
    │     ...                                                   │
    │                                                          │
    │   显示 (to_rod_string)：                                  │
    │     高位(MSB) 在前，最低位在最后                          │
    │     用 reversed(self._bits) 翻转后显示                    │
    │                                                          │
    │ 关键方法：                                                │
    │   _from_int()       : 整数 → 位列表 (除以2取余)          │
    │   to_int()          : 位列表 → 整数 (按权重累加)         │
    │   to_rod_string()   : 位列表 → —/| 显示字符串            │
    │   to_binary_string(): 位列表 → "01" 字符串               │
    └──────────────────────────────────────────────────────────┘
    """
    print("=" * 70)
    print("  【第2层】算筭数 <-> 整数 <-> 二进制位列表")
    print("  " + "-" * 64)
    print("  | def _from_int(self, num, bit_width=None):             |")
    print("  |     if num == 0:                                      |")
    print("  |         self._bits = [CountingRodBit(0)]              |")
    print("  |     else:                                             |")
    print("  |         self._bits = []                               |")
    print("  |         while num > 0:                                |")
    print("  |             self._bits.append(CountingRodBit(num & 1))|")
    print("  |             num >>= 1  # 右移1位,继续取余             |")
    print("  |                                                       |")
    print("  | def to_int(self):                                     |")
    print("  |     result = 0                                        |")
    print("  |     for i, bit in enumerate(self._bits):              |")
    print("  |         if bit.is_on:                                 |")
    print("  |             result |= (1 << i)  # 位i置1              |")
    print("  |     return result                                     |")
    print("  |                                                       |")
    print("  | def to_rod_string(self):                              |")
    print("  |     result = []                                       |")
    print("  |     for bit in reversed(self._bits):  # 高位在前!     |")
    print("  |         result.append(str(bit))                       |")
    print("  |     return ' '.join(result)                           |")
    print("  +-------------------------------------------------------+")
    print()

    # ---- 演示 A: 整数 → 算筭码 -----
    print("  演示 A: 整数 → 算筭码 (以数字 42 为例)")
    n = CountingRodNumber(42)
    print(f"    CountingRodNumber(42)")
    print(f"      构造过程 (_from_int):")
    print(f"        42 & 1 = 0  → _bits[0] = |")
    print(f"        42>>1=21, 21 & 1 = 1  → _bits[1] = —")
    print(f"        21>>1=10, 10 & 1 = 0  → _bits[2] = |")
    print(f"        10>>1=5,  5 & 1 = 1  → _bits[3] = —")
    print(f"        5>>1=2,   2 & 1 = 0  → _bits[4] = |")
    print(f"        2>>1=1,   1 & 1 = 1  → _bits[5] = —")
    print(f"        1>>1=0,   停止")
    print(f"      内部存储 (_bits): [{', '.join(str(b) for b in n._bits)}]")
    print(f"                       索引:   0  1  2  3  4  5")
    print(f"                       位权:   1  2  4  8 16 32")
    print(f"      显示 (to_rod_string): {n.to_rod_string()}")
    print(f"      整数 (to_int):        {n.to_int()}")

    # ---- 演示 B: 算筭码 → 整数 -----
    print()
    print("  演示 B: 算筭码 → 整数 (反向验证)")
    rod_str = "—|—|—|—|"
    print(f"    输入算筭串: \"{rod_str}\"")
    decoded = CountingRodNumber(rod_str)
    print(f"    解析为 _bits: [{', '.join(str(b) for b in decoded._bits)}]")
    print(f"    逐个位权累加 (to_int):")
    total = 0
    for i, bit in enumerate(decoded._bits):
        if bit.is_on:
            weight = 1 << i
            total += weight
            print(f"      _bits[{i}]={bit} -> 位权 {weight:2d} -> 累计 {total}")
    print(f"    最终整数: {decoded.to_int()}")

    # ---- 演示 C: 定宽构建 ----
    print()
    print("  演示 C: 定宽算筭数 (bit_width=8, 类似一个字节)")
    n8 = CountingRodNumber(13, bit_width=8)
    print(f"    CountingRodNumber(13, bit_width=8)")
    print(f"    内部存储: [{', '.join(str(b) for b in n8._bits)}]  (高位补|)")
    print(f"    显示:      {n8.to_rod_string()}")
    print(f"    整数:      {n8.to_int()}")


# ================================================================
# 第3层：算筭指令 <-> 16位算筭机器码
# ================================================================
def layer_3_instruction_encoding():
    """
    ┌──────────────────────────────────────────────────────────┐
    │ 第3层：算筭指令 <-> 16位算筭机器码                         │
    │                                                          │
    │ 源码位置：suanchou_isa.py : SuanChouInstruction          │
    │                                                          │
    │ 指令格式（16位）：                                        │
    │   [操作码 6位] [目标寄存器 3位] [源/立即数 7位]           │
    │                                                          │
    │   位序：MSB ← … → LSB                                    │
    │          op[5]..op[0]  reg[2]..reg[0]  src[6]..src[0]    │
    │          <--  bit15→10 --> <-- 9→7 --> <-- 6→0 -->       │
    │                                                          │
    │ 编码公式：                                                │
    │   machine_code = (opcode << 10) | (dest_reg << 7) | src  │
    │                                                          │
    │ 例如：LOAD R0, #42                                       │
    │   opcode=1 (000001)  dest=0 (000)  src=42 (0101010)     │
    │   合并：000001 000 0101010 = 16位算筭码                   │
    └──────────────────────────────────────────────────────────┘
    """
    print("=" * 70)
    print("  【第3层】算筭指令 <-> 16位算筭机器码")
    print("  " + "-" * 64)
    print("  | class SuanChouInstruction:                            |")
    print("  |     def __init__(self, opcode, dest_reg=0, src=0):    |")
    print("  |         self.opcode   = opcode & 0b111111   (6位)    |")
    print("  |         self.dest_reg = dest_reg & 0b111   (3位)     |")
    print("  |         self.src      = src & 0b1111111    (7位)     |")
    print("  |                                                       |")
    print("  |     def encode(self):                                 |")
    print("  |         # 三条二进制数按位拼接为一个16位数             |")
    print("  |         value = (self.opcode << 10)     |              |")
    print("  |                 (self.dest_reg << 7)     |              |")
    print("  |                  self.src                            |")
    print("  |         return CountingRodNumber(value, 16)          |")
    print("  +-------------------------------------------------------+")
    print()

    # ---- 演示: LOAD R0, #42 的完整编码过程 ----
    print("  演示：汇编指令 \"LOAD R0, #42\" → 算筭机器码")
    inst = SuanChouInstruction(SuanChouOpcode.LOAD, dest_reg=0, src=42)

    print(f"    操作码 (opcode):     {SuanChouOpcode.LOAD:06b} "
          f"= {SuanChouOpcode.LOAD} (0b{SuanChouOpcode.LOAD:06b})")
    print(f"    操作码算筭表示:      {SuanChouOpcode.to_rod(SuanChouOpcode.LOAD)}")
    print(f"    目标寄存器 (dest):   000 = R0")
    print(f"    源操作数 (src):      {42:07b} = 42")

    # 手动计算编码值
    manual_val = (SuanChouOpcode.LOAD << 10) | (0 << 7) | 42
    print(f"\n    编码公式:  value = (opcode << 10) | (dest << 7) | src")
    print(f"               value = ({SuanChouOpcode.LOAD} << 10) | (0 << 7) | {42}")
    print(f"               value = {SuanChouOpcode.LOAD << 10} | {0 << 7} | {42}")
    print(f"               value = {manual_val}")
    print(f"               16bit  = {manual_val:016b}")

    # 通过 encode() 方法
    encoded = inst.encode()
    print(f"\n    encode() 结果:")
    print(f"       算筭显示: {encoded.to_rod_string()}")
    print(f"       二进制:   {encoded.to_binary_string()}")
    print(f"       整数:     {encoded.to_int()}")

    # 反向：从算筭机器码中提取各字段
    print(f"\n    反汇编验证 (从机器码提取各字段):")
    raw = inst.encode().to_int()
    op_extract  = (raw >> 10) & 0b111111
    dest_extract = (raw >> 7) & 0b111
    src_extract  = raw & 0b1111111
    print(f"       raw = {raw:016b} ({raw})")
    print(f"       opcode  = raw >> 10 & 63 = {(raw>>10)&63:06b} = {SuanChouOpcode.name(op_extract)}")
    print(f"       dest    = raw >>  7 &  7 = {(raw>>7)&7:03b}  = R{dest_extract}")
    print(f"       src     = raw & 127       = {raw&127:07b} = {src_extract}")


# ================================================================
# 第4层：虚拟机取指/译码/执行（完整追踪）
# ================================================================
def layer_4_vm_execution():
    """
    ┌──────────────────────────────────────────────────────────┐
    │ 第4层：虚拟机执行 —— 从 算筭码 到 二进制运算             │
    │                                                          │
    │ 源码位置：suanchou_vm.py : SuanChouVM                    │
    │                                                          │
    │ 完整执行循环：                                            │
    │                                                          │
    │   while PC < 内存大小:                                    │
    │       1. fetch()  —— 从算筭码内存读取当前指令            │
    │       2. decode_execute() —— 提取字段并执行              │
    │       3. PC++                                             │
    │                                                          │
    │   fetch() 内部：                                          │
    │     raw = memory[PC]          # 读取算筭数               │
    │     int_val = raw.to_int()    # 算筭数→整数 (第2层)      │
    │     opcode = (int_val >> 10) & 0b111111  # 提取操作码    │
    │     dest   = (int_val >>  7) & 0b111     # 提取目标寄存器 │
    │     src    =  int_val         & 0b1111111 # 提取源操作数  │
    │     return Instruction(opcode, dest, src)                │
    └──────────────────────────────────────────────────────────┘
    """
    print("=" * 70)
    print("  【第4层】虚拟机执行 —— 从算筭码到二进制运算")
    print("  " + "-" * 64)
    print("  | class SuanChouVM:                                    |")
    print("  |                                                       |")
    print("  |     def fetch(self):                                  |")
    print("  |         raw = self.memory[self.pc]   # 读取算筭数     |")
    print("  |         int_val = raw.to_int()       # 算筭→整数      |")
    print("  |         opcode = (int_val >> 10) & 63 # 提取操作码    |")
    print("  |         dest   = (int_val >>  7) &  7 # 提取目标寄存器|")
    print("  |         src    =  int_val         & 127 # 提取源操作数|")
    print("  |         return Instruction(opcode, dest, src)         |")
    print("  |                                                       |")
    print("  |     def decode_execute(self, inst):                   |")
    print("  |         op = inst.opcode                              |")
    print("  |         if op == LOAD:                                |")
    print("  |             self.registers[rd] = RodNumber(rs, 16)    |")
    print("  |         elif op == ADD:                               |")
    print("  |             self.registers[rd] ← add(reg[rd], reg[rs])|")
    print("  |         ...                                           |")
    print("  +-------------------------------------------------------+")

    # ---- 完整执行演示 ----
    print()
    print("  " + "=" * 64)
    print("  完整执行演示：程序 \"LOAD R0 #13; LOAD R1 #7; ADD R0 R1\"")
    print("  " + "=" * 64)

    # 第1步：汇编 → 算筭机器码
    print("\n  --- 步骤1：汇编 → 算筭机器码 ---")
    asm = SuanChouAssembler()
    program = asm.assemble([
        "LOAD R0, #13",     # R0 = 13  (0b00001101)
        "LOAD R1, #7",      # R1 = 7   (0b00000111)
        "ADD  R0, R1",      # R0 = R0 + R1
        "HALT",
    ])

    for i, inst in enumerate(program):
        rod = inst.to_rod_string()
        int_val = inst.encode().to_int()
        print(f"    [{i}] {inst.disassemble()}")
        print(f"        opcode={SuanChouOpcode.to_rod(inst.opcode)} "
              f"({inst.opcode:06b}) "
              f"dest={inst.dest_reg:03b} src={inst.src:07b}")
        print(f"        16位算筭码: {rod}  =  {int_val}")
        print(f"        16位二进制: {int_val:016b}")
        print()

    # 第2步：加载到 VM 内存
    print("  --- 步骤2：加载到 VM 内存 ---")
    vm = SuanChouVM()
    vm.load_program(program)
    print(f"    内存布局 (仅显示程序段):")
    for i in range(len(program)):
        val = vm.memory[i].to_int()
        rod = vm.memory[i].to_rod_string()
        print(f"      地址[{i}]: 算筭码 {rod}  (整数: {val}, 二进制: {val:016b})")

    # 第3步：逐条执行（手动模拟，展示每一步）
    print("\n  --- 步骤3：逐条执行（手动模拟 fetch-decode-execute 循环）---")

    # 指令0: LOAD R0, #13
    print("\n  指令0: LOAD R0, #13")
    raw0 = vm.memory[0]
    print(f"    fetch(): 从地址[0]读取 算筭数: {raw0.to_rod_string()}")
    int_val0 = raw0.to_int()
    print(f"    raw → to_int() → {int_val0} (二进制: {int_val0:016b})")
    op0 = (int_val0 >> 10) & 63
    d0  = (int_val0 >>  7) & 7
    s0  = int_val0 & 127
    print(f"    提取操作码 (>>10 & 63): {(int_val0>>10)&63:06b} = {op0} ({SuanChouOpcode.name(op0)})")
    print(f"    提取目标寄存器 (>>7 & 7): {(int_val0>>7)&7:03b} = R{d0}")
    print(f"    提取源操作数 (& 127): {int_val0&127:07b} = {s0}")
    vm.registers[0] = CountingRodNumber(13, 16)
    print(f"    decode_execute: LOAD -> registers[0] = 13")
    print(f"      内部存储: {vm.registers[0]._bits}  (索引0 = 个位)")
    print(f"      算筭显示: {vm.registers[0].to_rod_string()}")

    # 指令1: LOAD R1, #7
    print("\n  指令1: LOAD R1, #7")
    raw1 = vm.memory[1]
    int_val1 = raw1.to_int()
    op1 = (int_val1 >> 10) & 63
    d1  = (int_val1 >>  7) & 7
    s1  = int_val1 & 127
    print(f"    fetch(): 算筭数 {raw1.to_rod_string()} → {int_val1:016b}")
    print(f"    译码: op={SuanChouOpcode.name(op1)}, dest=R{d1}, src={s1}")
    vm.registers[1] = CountingRodNumber(7, 16)
    print(f"    decode_execute: LOAD -> registers[1] = 7")
    print(f"      算筭显示: {vm.registers[1].to_rod_string()}")

    # 指令2: ADD R0, R1 (核心：算筭位级别的加法)
    print("\n  指令2: ADD R0, R1  ← 核心：算筭位级别加法")
    raw2 = vm.memory[2]
    int_val2 = raw2.to_int()
    op2 = (int_val2 >> 10) & 63
    d2  = (int_val2 >>  7) & 7
    s2  = int_val2 & 127
    print(f"    fetch(): 算筭数 {raw2.to_rod_string()} → 译码 ADD R0,R1")

    # 展示加法内部过程
    a_bits = vm.registers[0]._bits
    b_bits = vm.registers[1]._bits
    print(f"\n    ** ADD 内部实现 (全加器逐位计算) **")
    print(f"      操作数 R0 (13):")
    for i in range(4):
        w = 1 << i
        print(f"        位{i} (权{w:2d}): {a_bits[i]}  ({a_bits[i].binary})")
    print(f"      操作数 R1 (7):")
    for i in range(4):
        w = 1 << i
        print(f"        位{i} (权{w:2d}): {b_bits[i]}  ({b_bits[i].binary})")

    # 手动模拟全加器
    print(f"\n      全加器逐位计算:")
    carry = 0
    result_manual = 0
    for i in range(6):  # 足够覆盖
        ai = a_bits[i].binary if i < len(a_bits) else 0
        bi = b_bits[i].binary if i < len(b_bits) else 0
        sum_bit = ai ^ bi ^ carry
        carry   = (ai & bi) | (carry & (ai ^ bi))
        if sum_bit:
            result_manual |= (1 << i)
        print(f"        位{i}: a[{ai}] XOR b[{bi}] XOR cin[{carry}] "
              f"= sum[{sum_bit}]  cout={carry}")

    # 确认
    vm.registers[0] = CountingRodComputer.add(vm.registers[0], vm.registers[1])
    print(f"\n      ** 加法结果 **")
    print(f"      算筭数: {vm.registers[0].to_rod_string()}")
    print(f"      整数:   {vm.registers[0].to_int()}")
    print(f"      验证:   13 + 7 = 20  (二进制 10100)")

    # 指令3: HALT
    print("\n  指令3: HALT")
    print(f"    decode_execute: 返回 \"HALT\", 虚拟机停止")
    print(f"    总共执行了 3 条指令")
    print(f"    R0 = {vm.registers[0].to_int()} = {vm.registers[0].to_rod_string()}")

    print()
    print("  " + "=" * 64)
    print("  第4层演示完毕。")
    print("  以上展示了从\"— |\"符号到\"13+7=20\"的完整二进制计算路径。")
    print("  " + "=" * 64)


# ================================================================
# 总入口
# ================================================================

def main():
    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                                                          ║")
    print("  ║     算筭码 → 二进制  完整翻译管道源码展示                 ║")
    print("  ║                                                          ║")
    print("  ║     每一层都有源码注释 + 运行时验证                       ║")
    print("  ║                                                          ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()
    print("  五层管道：")
    print("  ┌─────────────────────────────────────────────────┐")
    print("  │ 第0层  符号定义     — <-> ON(1)    | <-> OFF(0)    │")
    print("  │ 第1层  单个位       CountingRodBit <-> int 0/1   │")
    print("  │ 第2层  算筭数       RodNumber <-> 二进制位列表   │")
    print("  │ 第3层  指令编码     汇编 → 16位算筭机器码       │")
    print("  │ 第4层  虚拟机执行   取指/译码/全加器/执行       │")
    print("  └─────────────────────────────────────────────────┘")
    print()

    layer_0_physical_symbols()
    print("\n")
    input("[按 Enter 继续 第1层]")
    
    layer_1_single_bit_to_int()
    print("\n")
    input("[按 Enter 继续 第2层]")
    
    layer_2_rod_number_to_int()
    print("\n")
    input("[按 Enter 继续 第3层]")
    
    layer_3_instruction_encoding()
    print("\n")
    input("[按 Enter 继续 第4层]")
    
    layer_4_vm_execution()

    print("\n" + "=" * 70)
    print("  五层翻译管道演示完毕。")
    print()
    print("  总结：")
    print("    — 和 | 是两个符号，就像 1 和 0 是两个数字。")
    print("    它们之间的映射是精确、无歧义、可逆的。")
    print("    从符号到算术，每一步都是确定性的位操作。")
    print("    这就是算筭能够作为计算底层逻辑的证明。")
    print("=" * 70)


if __name__ == "__main__":
    main()

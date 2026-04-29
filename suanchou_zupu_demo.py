# -*- coding: utf-8 -*-
"""
算筭字谱实战程序 ——「日月校·阶乘」
================================================
用算筭字谱编写的完整程序，在算筭虚拟机上运行。

三件事：
  1. 校字 —— 比较「日」和「月」的算筭码，输出异同位数
  2. 合字/交叠 —— 合并「木」和「本」的笔画，找共同部分
  3. 阶乘 —— 用循环计算 5! = 120

运行方式：
  py suanchou_zupu_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber
from suanchou_zupu import SuanChouZupuAssembler
from suanchou_vm import SuanChouVM
from stroke_dictionary import StrokeDictionary


def rod_bits_to_int(rod_bits):
    val = 0
    for j, bit in enumerate(rod_bits):
        if bit.is_on:
            val |= (1 << j)
    return val


def demo():
    print("=" * 70)
    print("  算筭字谱实战 ——「日月校 · 阶乘」")
    print("=" * 70)

    # ================================================================
    # 准备汉字数据
    # ================================================================
    dic = StrokeDictionary()
    ri   = dic.get_character("日")
    yue  = dic.get_character("月")
    mu   = dic.get_character("木")
    ben  = dic.get_character("本")

    for c in [ri, yue, mu, ben]:
        if c._encoded is None:
            c.encode()

    ri_val  = rod_bits_to_int(ri._encoded._bits)
    yue_val = rod_bits_to_int(yue._encoded._bits)
    mu_val  = rod_bits_to_int(mu._encoded._bits)
    ben_val = rod_bits_to_int(ben._encoded._bits)

    print(f"\n  数据:")
    print(f"    「日」{ri.rod_string}  ({ri.bits}位, 值={ri_val})")
    print(f"    「月」{yue.rod_string}  ({yue.bits}位, 值={yue_val})")
    print(f"    「木」{mu.rod_string}  ({mu.bits}位, 值={mu_val})")
    print(f"    「本」{ben.rod_string}  ({ben.bits}位, 值={ben_val})")

    # ================================================================
    # 创建 VM，预载汉字算筭码到数据段 (地址 32+)
    # ================================================================
    DATA = 32
    vm = SuanChouVM()
    vm.memory[DATA + 0] = CountingRodNumber(ri_val, ri.bits)
    vm.memory[DATA + 1] = CountingRodNumber(yue_val, yue.bits)
    vm.memory[DATA + 2] = CountingRodNumber(mu_val, mu.bits)
    vm.memory[DATA + 3] = CountingRodNumber(ben_val, ben.bits)

    # ================================================================
    # 算筭字谱程序
    # ================================================================
    print("\n" + "=" * 70)
    print("  【算筭字谱源码】")
    print("=" * 70)

    zupu_source = [
        "； 日月校 · 阶乘 —— 算筭字谱程序",
        "",
        "； ── 阶段一：校字，比较日和月 ──",
        f"取 甲, #{DATA + 0}",
        f"取 乙, #{DATA + 1}",
        "校 甲, 乙",
        "印 甲",
        "印 辛",
        "",
        "； ── 阶段二：合字，合并木和本的笔画 ──",
        f"取 甲, #{DATA + 2}",
        f"取 乙, #{DATA + 3}",
        "合 甲, 乙",
        "印 甲",
        "",
        "； ── 阶段三：交叠，找木和本共同笔画 ──",
        f"取 甲, #{DATA + 2}",
        f"取 乙, #{DATA + 3}",
        "交 甲, 乙",
        "印 甲",
        "",
        "； ── 阶段四：阶乘 5! = 120 ──",
        "载 甲, #1",
        "载 乙, #5",
        "载 丙, #1",
        "乘阶：",
        "乘 甲, 乙",
        "减 乙, 丙",
        "比 乙, 丙",
        "大 #乘阶",
        "乘 甲, 乙",
        "印 甲",
        "",
        "停",
    ]

    for line in zupu_source:
        print(f"  {line}")

    # ================================================================
    # 编译
    # ================================================================
    print("\n" + "=" * 70)
    print("  【编译 → 算筭机器码】")
    print("=" * 70)

    asm = SuanChouZupuAssembler()
    instructions, errors = asm.assemble(zupu_source)

    if errors:
        print("\n  [错误]")
        for e in errors:
            print(f"    {e}")
        return

    asm.disassemble(instructions)

    # ================================================================
    # 执行
    # ================================================================
    print("\n" + "=" * 70)
    print("  【执行追踪】")
    print("=" * 70)

    vm.load_program(instructions)
    vm.run(trace=True)

    print("\n" + "=" * 70)
    print("  【结果】")
    print("=" * 70)
    vm.show_output()

    # 解释输出
    outputs = vm.output_rods
    print(f"\n  解读：")
    for line in outputs:
        print(f"    {line}")

    # 验证
    r0 = vm.registers[0].to_int()
    print(f"\n  验证：")
    print(f"    阶乘结果: {r0} (期望 120)")
    if r0 == 120:
        print(f"    [OK] 5! = 120 计算正确")
    else:
        print(f"    [FAIL] 期望 120, 得到 {r0}")

    print(f"\n  总指令数: {vm.instruction_count}")
    print(f"\n  停机。日月校字毕，阶乘亦成。")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()

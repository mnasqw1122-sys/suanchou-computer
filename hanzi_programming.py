# -*- coding: utf-8 -*-
"""
汉字编程实践 (Chinese Character Programming Practice)
==========================================================
一个用汉字写程序、在算筭虚拟机上运行的交互式编程环境。

你写好算筭字谱程序 → 编译 → 算筭码 → 执行 → 看结果。
全程不用一个英文单词。

运行方式：
  py hanzi_programming.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber
from suanchou_zupu import (
    SuanChouZupuAssembler, ZUPU_TABLE, ZUPU_CATEGORIES,
    ZUPU_MEANING, TIANGAN
)
from suanchou_vm import SuanChouVM
from stroke_dictionary import StrokeDictionary


def show_welcome():
    print("""
  ╔══════════════════════════════════════════════════════════╗
  ║                                                          ║
  ║       汉 字 编 程 实 践                                  ║
  ║       Chinese Character Programming Practice             ║
  ║                                                          ║
  ║       不用英文  只用汉字   写出能运行的程序                ║
  ║                                                          ║
  ╚══════════════════════════════════════════════════════════╝
""")


def show_help():
    print("""
  ┌──────────────────────────────────────────────────────────┐
  │  命令说明：                                               │
  │                                                          │
  │   指令    — 显示所有可用指令                              │
  │   寄存器  — 显示天干寄存器表                              │
  │   编写    — 开始写一个新的程序                            │
  │   示例    — 运行一个示例程序                              │
  │   帮助    — 显示这个说明                                  │
  │   退出    — 离开                                          │
  └──────────────────────────────────────────────────────────┘
""")


def show_instructions():
    print("""
  ┌──────────────────────────────────────────────────────────┐
  │  算筭字谱指令集                                          │
  ├──────────────────────────────────────────────────────────┤
""")
    for cat, mnemonics in ZUPU_CATEGORIES.items():
        print(f"  │  【{cat}】")
        for m in mnemonics:
            meaning = ZUPU_MEANING.get(m, "")
            print(f"  │    {m}   —  {meaning}")
        if cat != list(ZUPU_CATEGORIES.keys())[-1]:
            print("  │")
    print("""  │
  │  语法：                                                  │
  │    指令 目标, 源                                         │
  │    例如：载 甲, #42      加 甲, 乙       停              │
  │                                                          │
  │    ; 开头为注释    ：结尾为标签                           │
  │    例如：; 这是注释     循环：                            │
  └──────────────────────────────────────────────────────────┘
""")


def show_registers():
    print("""
  ┌──────────────────────────────────────────────────────────┐
  │  天干寄存器                                              │
  ├──────────────────────────────────────────────────────────┤
  │    甲 = R0       乙 = R1       丙 = R2       丁 = R3     │
  │    戊 = R4       己 = R5       庚 = R6       辛 = R7     │
  └──────────────────────────────────────────────────────────┘
""")


def run_example():
    print("""
  ╔══════════════════════════════════════════════════════════╗
  ║  示例：计算 5 + 4 + 3 + 2 + 1 = 15                      ║
  ╚══════════════════════════════════════════════════════════╝
""")

    source = [
        "； 累加程序",
        "载 甲, #0",
        "载 乙, #5",
        "载 丙, #1",
        "循环：",
        "加 甲, 乙",
        "减 乙, 丙",
        "比 乙, 丙",
        "大 #循环",
        "加 甲, 乙",
        "印 甲",
        "停",
    ]

    print("  【源码】")
    for line in source:
        print(f"    {line}")

    print(f"\n  【编译 → {len(source)} 行 → 算筭码】")
    asm = SuanChouZupuAssembler()
    insts, errs = asm.assemble(source)
    if errs:
        for e in errs:
            print(f"    错误: {e}")
        return

    # 只显示关键几条
    key_indices = [0, 1, 2, 4, 5, 6, 7, 10, 11]
    for i in key_indices:
        if i < len(insts):
            inst = insts[i]
            print(f"    [{i:02d}] {inst.to_rod_string()}  {inst.disassemble()}")

    print(f"\n  【执行】")
    vm = SuanChouVM()
    vm.load_program(insts)
    vm.run()
    result = vm.registers[0].to_int()
    print(f"    甲 (R0) = {result}")
    if result == 15:
        print(f"    >>> 正确！5+4+3+2+1 = 15")
    else:
        print(f"    >>> 错误！期望 15")

    print(f"    总共执行了 {vm.instruction_count} 条指令")
    print()


def write_program():
    print("""
  ╔══════════════════════════════════════════════════════════╗
  ║  编写算筭字谱程序                                        ║
  ║                                                          ║
  ║  输入你的程序，一行一条指令。                             ║
  ║  输入空行结束编写，程序将编译并执行。                    ║
  ║                                                          ║
  ║  可用指令：载 传 存 取 停 加 减 乘 除                    ║
  ║           与 或 异 非 左 右 比 跳 等 别 大 小             ║
  ║           识 查 校 合 交 签 印 显                        ║
  ║                                                          ║
  ║  寄存器：甲 乙 丙 丁 戊 己 庚 辛                         ║
  ║  输入  :帮助  查看语法帮助                               ║
  ║  输入  :取消  放弃编写                                   ║
  ╚══════════════════════════════════════════════════════════╝
""")

    lines = []
    line_no = 1
    while True:
        try:
            line = input(f"  {line_no:02d}> ").rstrip()
        except (EOFError, KeyboardInterrupt):
            print("\n  已取消。")
            return

        if line.strip() == ":帮助":
            print("""
    语法：
      指令 目标寄存器, 源操作数
      例如：
        载 甲, #42      甲 = 42
        加 甲, 乙        甲 = 甲 + 乙
        乘 甲, 乙        甲 = 甲 × 乙
        比 甲, 乙        比较
        印 甲           输出甲的值
        停              停机

      ; 开头为注释
      : 结尾为标签 (如 循环：)

      # 开头为立即数
      跳转指令 (跳/等/别/大/小) 操作数是地址或标签
        例如：大 #循环
""")
            continue

        if line.strip() == ":取消":
            print("  已取消。")
            return

        if line.strip() == "":
            if len(lines) == 0:
                print("  未输入任何指令。")
                return
            break

        lines.append(line)
        line_no += 1

    if not lines:
        return

    print(f"\n  【编译中... {len(lines)} 行】")
    asm = SuanChouZupuAssembler()
    insts, errs = asm.assemble(lines)

    if errs:
        print(f"\n  [编译错误]")
        for e in errs:
            print(f"    {e}")
        return

    print(f"  编译成功！{len(insts)} 条算筭机器码。")
    print(f"\n  【算筭机器码】")
    for i, inst in enumerate(insts):
        print(f"    [{i:02d}] {inst.to_rod_string()}  {inst.disassemble()}")

    print(f"\n  【执行中...】")
    vm = SuanChouVM()
    vm.load_program(insts)
    vm.run()
    print(f"\n  【执行结果】")
    vm.show_output()

    print(f"\n  寄存器状态:")
    for i in range(8):
        r = vm.registers[i]
        if r.to_int() != 0 or i < 4:  # 只显示非零寄存器
            print(f"    {TIANGAN.get(i, f'R{i}')} (R{i}) = "
                  f"{r.to_rod_string()} ({r.to_int()})")

    print(f"  共执行 {vm.instruction_count} 条指令。")
    print()


def preload_demo_data(vm, data_addr=32):
    """预载演示用汉字数据到 VM 内存"""
    dic = StrokeDictionary()
    chars_data = {
        "日": data_addr + 0,
        "月": data_addr + 1,
        "木": data_addr + 2,
        "水": data_addr + 3,
        "火": data_addr + 4,
    }

    char_objs = {}
    for cn, addr in chars_data.items():
        obj = dic.get_character(cn)
        if obj:
            if obj._encoded is None:
                obj.encode()
            val = 0
            for j, bit in enumerate(obj._encoded._bits):
                if bit.is_on:
                    val |= (1 << j)
            vm.memory[addr] = CountingRodNumber(val, obj.bits)
            char_objs[cn] = obj

    return char_objs


def run_riyue_demo():
    print("""
  ╔══════════════════════════════════════════════════════════╗
  ║  日月校 —— 比较「日」和「月」的字形                      ║
  ╚══════════════════════════════════════════════════════════╝
""")

    DATA = 32
    vm = SuanChouVM()
    chars = preload_demo_data(vm, DATA)

    ri = chars.get("日")
    yue = chars.get("月")
    if not ri or not yue:
        print("  字典数据缺失。")
        return

    source = [
        "； 日月校",
        f"取 甲, #{DATA + 0}",
        "识 甲",
        "显 甲",
        f"取 甲, #{DATA + 0}",
        f"取 乙, #{DATA + 1}",
        "校 甲, 乙",
        "印 甲",
        "印 辛",
        "停",
    ]

    print("  【源码】")
    for line in source:
        print(f"    {line}")

    asm = SuanChouZupuAssembler()
    insts, errs = asm.assemble(source)
    if not errs:
        vm.load_program(insts)
        vm.run()
        print(f"\n  【结果】")
        vm.show_output()
        if vm.output_rods:
            print(f"\n  解读：")
            print(f"    差异位 = {vm.output_rods[0]}")
            print(f"    共同位 = {vm.output_rods[1]}")
    else:
        for e in errs:
            print(f"  错误: {e}")
    print()


def run_countdown():
    print("""
  ╔══════════════════════════════════════════════════════════╗
  ║  倒计时 —— 从 9 数到 1                                  ║
  ╚══════════════════════════════════════════════════════════╝
""")

    source = [
        "； 倒计数",
        "载 甲, #9",
        "载 乙, #1",
        "循环：",
        "印 甲",
        "减 甲, 乙",
        "比 甲, 乙",
        "大 #循环",
        "印 甲",
        "停",
    ]

    print("  【源码】")
    for line in source:
        print(f"    {line}")

    asm = SuanChouZupuAssembler()
    insts, errs = asm.assemble(source)
    if errs:
        for e in errs:
            print(f"  错误: {e}")
        return

    print(f"\n  编译成功: {len(insts)} 条指令")
    vm = SuanChouVM()
    vm.load_program(insts)
    vm.run()
    print(f"\n  执行结果:")
    for out in vm.output_rods:
        print(f"    {out}")
    print(f"  共输出 {len(vm.output_rods)} 个数 (期望 9 个, 9到1)")
    print()


def run_sequence():
    print("""
  ╔══════════════════════════════════════════════════════════╗
  ║  阶乘 —— 5! = 120                                      ║
  ╚══════════════════════════════════════════════════════════╝
""")

    source = [
        "； 阶乘：5!",
        "载 甲, #1            ； 甲 = 累乘器",
        "载 乙, #5            ； 乙 = 乘数",
        "载 丙, #1            ； 丙 = 常量1",
        "",
        "循环：",
        "乘 甲, 乙            ； 甲 = 甲 × 乙",
        "减 乙, 丙            ； 乙--",
        "比 乙, 丙            ； 比较",
        "大 #循环            ； 乙 > 1 则继续",
        "",
        "印 甲                 ； 输出 120",
        "停",
    ]

    print("  【源码】")
    for line in source:
        print(f"    {line}")

    asm = SuanChouZupuAssembler()
    insts, errs = asm.assemble(source)
    if errs:
        for e in errs:
            print(f"  编译错误: {e}")
        return

    print(f"\n  编译成功: {len(insts)} 条指令")
    vm = SuanChouVM()
    vm.load_program(insts)
    vm.run()
    print(f"\n  执行结果 (期望: 5! = 120):")
    for out in vm.output_rods:
        print(f"    {out}")
    print(f"  结果: {vm.registers[0].to_int()} (期望 120)")
    print()


def main():
    show_welcome()
    show_help()

    while True:
        try:
            cmd = input("  汉字编程> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break

        if not cmd:
            continue

        cmd_lower = cmd.lower()

        if cmd_lower in ("退出", "quit", "q", "exit"):
            print("  再见！")
            break

        elif cmd in ("帮助", "help", "?"):
            show_help()

        elif cmd in ("指令", "指令集"):
            show_instructions()

        elif cmd in ("寄存器", "天干"):
            show_registers()

        elif cmd in ("编写", "写程序"):
            write_program()

        elif cmd in ("示例", "例子"):
            run_example()

        elif cmd in ("日月", "日月校"):
            run_riyue_demo()

        elif cmd in ("倒计时", "倒数"):
            run_countdown()

        elif cmd in ("阶乘", "数列"):
            run_sequence()

        else:
            print(f"  不识命令「{cmd}」。输入「帮助」查看可用命令。")


if __name__ == "__main__":
    main()

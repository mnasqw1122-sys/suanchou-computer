# -*- coding: utf-8 -*-
"""
算筭字谱运行器 (SuanChou Runner)
====================================
加载 .suan 文件 → 算筭字谱编译 → 算筭虚拟机执行

用法：
  py suan_run.py 石破天惊.suan
  py suan_run.py 阶乘.suan
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodNumber
from suanchou_zupu import SuanChouZupuAssembler
from suanchou_vm import SuanChouVM
from stroke_dictionary import StrokeDictionary
from extended_strokes import EXTENDED_STROKE_DATA


def preload_characters(vm, data_addr=32):
    """预加载扩展字典中的全部汉字到 VM 内存"""
    dic = StrokeDictionary()
    char_addrs = {}
    addr = data_addr

    for char_name, data in EXTENDED_STROKE_DATA.items():
        if char_name in dic._characters:
            obj = dic._characters[char_name]
        else:
            from stroke_dictionary import Character
            obj = Character(
                char=char_name, stroke_sequence=data["strokes"],
                meaning=data["meaning"], radical=data["radical"],
                category=data["category"], semantic_tags=data["tags"],
                pinyin=data["pinyin"],
            )
        if obj._encoded is None:
            obj.encode()
        val = 0
        for j, bit in enumerate(obj._encoded._bits):
            if bit.is_on:
                val |= (1 << j)
        vm.memory[addr] = CountingRodNumber(val, obj.bits)
        char_addrs[char_name] = addr
        addr += 1

    return char_addrs


def run_suan_file(filepath):
    """编译并运行一个 .suan 文件"""
    # 读取源文件
    with open(filepath, "r", encoding="utf-8") as f:
        source_lines = [line.rstrip() for line in f.readlines()]

    print(f"  加载：{os.path.basename(filepath)} ({len(source_lines)} 行)")
    print()

    # 编译
    asm = SuanChouZupuAssembler()
    insts, errs = asm.assemble(source_lines)

    if errs:
        print("  [编译错误]")
        for e in errs:
            print(f"    {e}")
        return

    print(f"  编译成功：{len(insts)} 条算筭机器码")
    print()

    # 准备 VM
    vm = SuanChouVM()
    preload_characters(vm, 32)

    # 加载程序
    vm.load_program(insts)

    # 执行
    print("  [执行中...]")
    vm.run(trace=False)
    print()

    # 输出
    print("  [程序输出]")
    if vm.output_rods:
        print("    算筭结果：")
        for out in vm.output_rods:
            print(f"      {out}")
    if vm.output:
        print("    汉字结果：")
        for out in vm.output:
            print(f"      {out}")

    print(f"\n  指令计数：{vm.instruction_count}")
    print(f"  最终 R0 值：{vm.registers[0].to_int()}")


def main():
    if len(sys.argv) < 2:
        print("算筭字谱运行器")
        print()
        print("用法：")
        print("  py suan_run.py <文件.suan>")
        print()
        print("示例：")
        print("  py suan_run.py 石破天惊.suan")
        print("  py suan_run.py 阶乘.suan")
        print()
        print("可用 .suan 文件：")
        for f in sorted(os.listdir(".")):
            if f.endswith(".suan"):
                print(f"  {f}")
        print()
        print("也可以把 .suan 文件拖到这个脚本上运行。")
        return

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"  文件不存在：{filepath}")
        return

    if not filepath.endswith(".suan"):
        print(f"  不是 .suan 文件：{filepath}")
        return

    print("=" * 70)
    print("  算筭字谱运行器")
    print("  SuanChou Zupu Runner")
    print("=" * 70)
    print()

    run_suan_file(filepath)

    print()
    print("=" * 70)
    print("  运行完毕。")
    print("=" * 70)


if __name__ == "__main__":
    main()

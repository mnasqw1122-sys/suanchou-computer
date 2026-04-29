# -*- coding: utf-8 -*-
"""算筭运行器入口 —— 供 PyInstaller 打包为 suan.exe"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodNumber
from suanchou_zupu import SuanChouZupuAssembler
from suanchou_vm import SuanChouVM
from stroke_dictionary import StrokeDictionary, Character
from extended_strokes import EXTENDED_STROKE_DATA


def main():
    if len(sys.argv) < 2:
        print("算筭字谱运行器 (suan.exe)")
        print("用法：suan.exe <文件.suan>")
        print()
        print("也可以把 .suan 文件拖到 suan.exe 图标上。")
        input("\n按 Enter 退出...")
        return

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"文件不存在：{filepath}")
        input("\n按 Enter 退出...")
        return

    # 读取 .suan 源文件
    with open(filepath, "r", encoding="utf-8") as f:
        source = [line.rstrip() for line in f.readlines()]

    print(f"\n算筭字谱运行器")
    print(f"文件：{os.path.basename(filepath)} ({len(source)} 行)")
    print()

    # 编译
    asm = SuanChouZupuAssembler()
    insts, errs = asm.assemble(source)

    if errs:
        print("[编译错误]")
        for e in errs:
            print(f"  {e}")
        input("\n按 Enter 退出...")
        return

    print(f"编译成功：{len(insts)} 条算筭机器码")
    print()

    # 准备 VM
    vm = SuanChouVM()

    # 预加载汉字数据
    dic = StrokeDictionary()
    DATA = 32
    addr = DATA
    for char_name, data in EXTENDED_STROKE_DATA.items():
        if char_name in dic._characters:
            obj = dic._characters[char_name]
        else:
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
        addr += 1

    # 加载程序
    vm.load_program(insts)

    # 执行
    print("[执行]")
    vm.run(trace=False)
    print()

    # 显示结果
    print("[结果]")
    if vm.output:
        print("  汉字输出：")
        for line in vm.output:
            print(f"    {line}")
    if vm.output_rods:
        print("  算筭输出：")
        for line in vm.output_rods:
            print(f"    {line}")

    print(f"\n执行 {vm.instruction_count} 条指令。")
    input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()

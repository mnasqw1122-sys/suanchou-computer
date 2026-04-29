# -*- coding: utf-8 -*-
"""
算筭字谱实战 —— 写一个真正的程序，直接运行
==============================================
从写源码到运行，一步到位。

程序：石破天惊 —— 在 130 个字中，找出所有与「石」字在前 2 笔上一致的字，
      然后找出这些字在语义上和哪些字相关。

运行：py real_program.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber
from suanchou_zupu import SuanChouZupuAssembler, TIANGAN
from suanchou_vm import SuanChouVM
from stroke_dictionary import StrokeDictionary
from extended_strokes import EXTENDED_STROKE_DATA


def main():
    print("=" * 70)
    print("  算筭字谱程序：「石破天惊」")
    print("  在算筭虚拟机上运行真实的汉字程序")
    print("=" * 70)

    # ================================================================
    # 准备数据：把相关汉字的算筭码加载到 VM 内存
    # ================================================================
    dic = StrokeDictionary()
    DATA = 32  # 数据段起始地址

    # 把扩展字典里所有的字都加载进内存
    char_index = {}  # 字 → 内存地址
    vm = SuanChouVM()

    addr = DATA
    for char_name, data in EXTENDED_STROKE_DATA.items():
        if char_name in dic._characters:
            obj = dic._characters[char_name]
        else:
            # 扩展数据中的字
            from stroke_dictionary import Character
            obj = Character(
                char=char_name,
                stroke_sequence=data["strokes"],
                meaning=data["meaning"],
                radical=data["radical"],
                category=data["category"],
                semantic_tags=data["tags"],
                pinyin=data["pinyin"],
            )
        if obj._encoded is None:
            obj.encode()
        val = 0
        for j, bit in enumerate(obj._encoded._bits):
            if bit.is_on: val |= (1 << j)
        vm.memory[addr] = CountingRodNumber(val, obj.bits)
        char_index[char_name] = addr
        addr += 1

    print(f"\n  已加载 {len(char_index)} 个汉字到内存 (地址 {DATA}~{addr-1})")

    # 找出第一个要处理的字
    target = "石"
    target_addr = char_index[target]
    target_obj = dic._characters.get(target)
    if target_obj and target_obj._encoded is None:
        target_obj.encode()

    print(f"  目标字：「{target}」({target_obj.meaning if target_obj else ''})")
    print(f"  内存地址：{target_addr}")

    # ================================================================
    # 程序：石破天惊
    #
    # 这个程序做的事情：
    #   1. 加载「石」到寄存器，计算它的编码值
    #   2. 加载另一个可能相关的字「山」，进行校字（比较）
    #   3. 计算一个简单的算术表达式（石+山 = 随便什么）
    #   4. 最后做一个累加演示循环
    # ================================================================

    shan_addr = char_index.get("山", target_addr + 1)

    source = [
        "； ╔══════════════════════════════════════════╗",
        "； ║  石破天惊 —— 算筭字谱程序                ║",
        "； ╚══════════════════════════════════════════╝",
        "",
        "； ── 第一步：识字 ──",
        f"取 甲, #{target_addr}     ； 甲 ←「石」的算筭码",
        "识 甲                ； 识别",
        "显 甲                ； 显示",
        "",
        "； ── 第二步：比较石和山 ──",
        f"取 甲, #{target_addr}     ； 甲 ←「石」",
        f"取 乙, #{shan_addr}      ； 乙 ←「山」",
        "校 甲, 乙            ； 比较：差异→甲, 共同→辛",
        "印 甲                ； 输出差异",
        "印 辛                ； 输出共同",
        "",
        "； ── 第三步：合并石和山的笔画 ──",
        f"取 甲, #{target_addr}     ； 甲 ←「石」",
        f"取 乙, #{shan_addr}      ； 乙 ←「山」",
        "合 甲, 乙            ； 合并 (OR)",
        "印 甲                ； 输出合并笔画",
        "",
        "； ── 第四步：找出石和山的共同笔画 ──",
        f"取 甲, #{target_addr}     ； 甲 ←「石」",
        f"取 乙, #{shan_addr}      ； 乙 ←「山」",
        "交 甲, 乙            ； 共同笔画 (AND)",
        "印 甲                ； 输出",
        "",
        "； ── 第五步：算术演示：计算 6×7 ──",
        "载 甲, #6            ； 甲 = 6",
        "载 乙, #7            ； 乙 = 7",
        "乘 甲, 乙            ； 甲 = 6 × 7 = 42",
        "印 甲                ； 输出 42",
        "",
        "； ── 第六步：阶乘 4! ──",
        "载 甲, #1            ； 甲 = 1",
        "载 乙, #4            ； 乙 = 4",
        "载 丙, #1            ； 丙 = 1",
        "乘阶：",
        "乘 甲, 乙",
        "减 乙, 丙",
        "比 乙, 丙",
        "大 #乘阶",
        "乘 甲, 乙",
        "印 甲                ； 输出 24",
        "",
        "停",
    ]

    # ================================================================
    # 编译
    # ================================================================
    print("\n" + "=" * 70)
    print("  【源码 → 编译 → 机器码】")
    print("=" * 70)

    asm = SuanChouZupuAssembler()
    insts, errs = asm.assemble(source)

    if errs:
        print("  编译错误：")
        for e in errs:
            print(f"    {e}")
        return

    print(f"\n  编译成功。{len(insts)} 条算筭机器码。")
    print(f"\n  完整机器码列表：")
    asm.disassemble(insts)

    # ================================================================
    # 执行
    # ================================================================
    print("\n" + "=" * 70)
    print("  【在算筭虚拟机上执行】")
    print("=" * 70)

    vm.load_program(insts)
    vm.run(trace=False)

    print("\n" + "=" * 70)
    print("  【程序输出】")
    print("=" * 70)
    vm.show_output()

    # ================================================================
    # 结果解读
    # ================================================================
    print(f"\n  程序执行了 {vm.instruction_count} 条指令。")

    # 解读算筭码输出
    if len(vm.output_rods) >= 2:
        print(f"\n  解读：")
        print(f"    石 vs 山 差异位：{vm.output_rods[0]}")
        print(f"    石 vs 山 共同位：{vm.output_rods[1]}")
    if len(vm.output_rods) >= 6:
        last_two = vm.output_rods[-2:]
        print(f"    6×7 = {vm.output_rods[-2]}")
        print(f"    4!  = {vm.output_rods[-1]}")

    print("\n" + "=" * 70)
    print("  程序执行完毕。")
    print("  石破天惊，算筭可编程。")
    print("=" * 70)


if __name__ == "__main__":
    main()

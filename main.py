# -*- coding: utf-8 -*-
"""
算筭计算机 —— 完整演示入口
================================
展示从算筭到汉字理解的完整计算管道。

思想脉络：
  古代算筭(— / |) → 二进制计算(0/1) → 笔画编码 → 字形理解

运行方式：
  python main.py
  python main.py --interactive   (交互模式)
  python main.py --demo-all       (完整演示)
"""

import sys
from counting_rod_computer import (
    CountingRodComputer, CountingRodNumber, CountingRodBit,
    demo_computer
)
from stroke_encoder import Stroke, StrokeEncoder, demo_stroke_encoding
from stroke_dictionary import StrokeDictionary, demo_dictionary
from semantic_layer import SemanticLayer, demo_semantic_layer


def print_banner():
    """打印系统横幅"""
    banner = r"""
 ╔══════════════════════════════════════════════════════╗
 ║                                                      ║
 ║          算  筭  计  算  机                           ║
 ║       SuanChou Computer                              ║
 ║                                                      ║
 ║   以古代算筭为计算基础，打通汉字与计算的桥梁            ║
 ║                                                      ║
 ║   —  = 通 (on, 1)     |  = 断 (off, 0)              ║
 ║                                                      ║
 ╚══════════════════════════════════════════════════════╝
"""
    print(banner)


def show_full_pipeline():
    """
    完整演示：算筭 → 二进制 → 笔画 → 理解 → 关联
    展示整个系统的核心流程
    """
    print("\n" + "█" * 70)
    print("█  完整管道演示：从算筭信号到汉字理解")
    print("█" * 70)

    comp = CountingRodComputer
    encoder = StrokeEncoder()
    dic = StrokeDictionary()
    sem = SemanticLayer(dic)

    # ============================================================
    #  阶段一：算筭计算基础
    # ============================================================
    print("\n" + "─" * 70)
    print("  【阶段一】算筭计算：仅用 — 和 | 完成运算")
    print("─" * 70)

    a = comp.make_number(7)   # 7 = 00000111 → | | | | | — — —
    b = comp.make_number(5)   # 5 = 00000101 → | | | | | — | —
    print(f"  算筭数 A = {a.to_rod_string()} (十进制: {a.to_int()})")
    print(f"  算筭数 B = {b.to_rod_string()} (十进制: {b.to_int()})")
    print(f"  A + B = {comp.add(a, b).to_rod_string()} = {comp.add(a, b).to_int()}")
    print(f"  A - B = {comp.subtract(a, b).to_rod_string()} = {comp.subtract(a, b).to_int()}")
    print(f"  A × B = {comp.multiply(a, b).to_rod_string()} = {comp.multiply(a, b).to_int()}")
    print(f"  A & B = {comp.and_op(a, b).to_rod_string()} = {comp.and_op(a, b).to_int()}")

    # ============================================================
    #  阶段二：汉字笔画编码
    # ============================================================
    print("\n" + "─" * 70)
    print("  【阶段二】笔画编码：汉字 → 笔画 → 算筭")
    print("─" * 70)

    example_chars = ["人", "木", "日", "水", "天"]
    for cn in example_chars:
        char_obj = dic.get_character(cn)
        if char_obj:
            strokes_str = " ".join(f"{Stroke(s).symbol}" for s in char_obj.stroke_sequence)
            print(f"\n  「{cn}」({char_obj.meaning})")
            print(f"    笔画：{strokes_str}")
            print(f"    算筭：{char_obj.rod_string}")
            print(f"    位宽：{char_obj.bits} 位 (= {char_obj.stroke_count} 笔画 × 3)")

    # ============================================================
    #  阶段三：笔画模式匹配
    # ============================================================
    print("\n" + "─" * 70)
    print("  【阶段三】模式匹配：用算筭计算发现字形关系")
    print("─" * 70)

    # 「木」和「本」的比较
    mu = dic.get_character("木")
    ben = dic.get_character("本")
    similarity = sem.compute_similarity(mu, ben)
    overlap_strokes, overlap_rod = sem.compute_stroke_overlap(mu, ben)
    diff_count, diff_rod = sem.compute_difference(mu, ben)

    print(f"\n  「木」({mu.rod_string}) vs「本」({ben.rod_string})")
    print(f"  相似度：{similarity:.1f}%")
    print(f"  重叠笔画（AND）：{' → '.join(overlap_strokes)}")
    print(f"  差异位（XOR）：{diff_count} 位")
    print(f"  「本」比「木」多一横，这在算筭层面上清晰可见！")

    # ============================================================
    #  阶段四：语义理解
    # ============================================================
    print("\n" + "─" * 70)
    print("  【阶段四】语义理解：从笔画信号到含义")
    print("─" * 70)

    # 给定笔画序列，系统"理解"这是什么字
    test_strokes = ["竖", "折", "横", "横"]  # 这可能是「日」的笔画
    print(f"\n  收到笔画信号：{' → '.join(test_strokes)}")
    encoded = encoder.encode_character(test_strokes)
    print(f"  转换为算筭：{encoded.to_rod_string()}")
    result = sem.understand_from_strokes(test_strokes)
    print(result.summary())

    # ============================================================
    #  阶段五：关联图谱
    # ============================================================
    print("\n" + "─" * 70)
    print("  【阶段五】关联图谱：算筭揭示汉字之间的深层联系")
    print("─" * 70)

    # 以「日」为中心
    ri = dic.get_character("日")
    print(f"\n  中心字：「日」({ri.meaning})")
    print(f"  算筭编码：{ri.rod_string}")

    # 找出所有包含「日」相关笔画模式的其他字
    ri_prefix = ri.stroke_sequence[:2]  # ["竖", "折"]
    related = dic.find_by_stroke_pattern(ri_prefix)
    print(f"\n  共享笔画前缀「{' → '.join(ri_prefix)}」的汉字：")
    for r in related:
        sim = sem.compute_similarity(ri, r)
        common_tags = set(ri.semantic_tags) & set(r.semantic_tags)
        print(f"    {r} (相似度 {sim:.0f}%)", end="")
        if common_tags:
            print(f" [共同语义：{'、'.join(common_tags)}]")
        else:
            print()

    # 语义层面关联
    print(f"\n  与「日」共享语义标签的汉字：")
    tag_related = dic.find_related_by_tags(ri)
    for r in tag_related:
        common = set(ri.semantic_tags) & set(r.semantic_tags)
        print(f"    {r} ← {'、'.join(common)}")

    # ============================================================
    #  总结
    # ============================================================
    print("\n" + "█" * 70)
    print("█  管道演示完毕")
    print("█" * 70)


def interactive_mode():
    """
    交互模式 —— 让用户输入汉字来探索算筭系统
    """
    print_banner()
    dic = StrokeDictionary()
    sem = SemanticLayer(dic)

    print("\n[字典] 当前字典收录的汉字：")
    all_chars = dic.list_all()
    char_names = [c.char for c in all_chars]
    print("  " + " ".join(char_names))

    while True:
        print("\n" + "=" * 60)
        print("  选项：")
        print("    1. 查看某个汉字的算筭编码")
        print("    2. 比较两个汉字")
        print("    3. 查看汉字的关联图谱")
        print("    4. 通过笔画序列来理解")
        print("    5. 通过算筭符号来理解")
        print("    q. 退出")
        print("=" * 60)

        choice = input("\n请选择 (1/2/3/4/5/q): ").strip()

        if choice == "q":
            print("再见！")
            break
        elif choice == "1":
            char = input("请输入汉字：").strip()
            obj = dic.get_character(char)
            if obj:
                print(f"\n{obj.summary()}")
            else:
                print(f"字典中未收录「{char}」")
        elif choice == "2":
            a = input("第一个汉字：").strip()
            b = input("第二个汉字：").strip()
            sem.compare_characters(a, b)
        elif choice == "3":
            char = input("中心汉字：").strip()
            sem.compute_relatedness_graph(char)
        elif choice == "4":
            print("可用的笔画：横、竖、撇、捺、点、折、钩、提")
            seq_str = input("请输入笔画序列（用空格分隔）：").strip()
            strokes = seq_str.split()
            result = sem.understand_from_strokes(strokes)
            print(result.summary())
        elif choice == "5":
            rod_str = input("请输入算筭符号（— 和 |）：").strip()
            result = sem.understand_from_rod(rod_str)
            print(result.summary())
        else:
            print("无效选项")


def show_philosophy():
    """
    展示哲学思考 —— 这个系统的深层意义
    """
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    哲 学 思 考                                   ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1. 算筭与二进制的同构性                                        ║
║     — 和 | 本质上就是两种状态，这和计算机的 0 和 1 完全一致。   ║
║     古代中国人用算筭完成复杂计算，证明「两种状态即可表达一切」。  ║
║                                                                  ║
║  2. 汉字笔画与信号的映射                                        ║
║     每个汉字由基本笔画组成（横竖撇捺点折钩提），                  ║
║     每种笔画可用 3 个 bit 唯一编码，                             ║
║     于是每个汉字的「形」可以完全转化为一串 — 和 | 信号。         ║
║                                                                  ║
║  3. 「理解」就是「计算」                                        ║
║     当大脑看到一个汉字时，它所做的无非是：                        ║
║     ① 接收视觉笔画信号                                          ║
║     ② 与存储的模式进行对比（模式匹配 = 算筭位运算）              ║
║     ③ 激活相关的语义网络（联想 = 字典索引查找）                  ║
║     ④ 产生理解                                                  ║
║     这整个流程都可以用算筭计算来模拟。                            ║
║                                                                  ║
║  4. 打通计算机与自然语言的隔阂                                  ║
║     如果我们承认：                                               ║
║     · 汉字 = 笔画序列 = 算筭信号 = 二进制数据                    ║
║     · 「理解」= 模式匹配 + 语义联想 = 计算                       ║
║     那么计算机和自然语言之间就没有本质的隔阂。                    ║
║     它们只是同一个计算过程在不同层次上的表现。                    ║
║                                                                  ║
║  5. 局限与展望                                                  ║
║     当前系统只能处理预定义的笔画字典，真正的语义理解              ║
║     需要大规模语料和深度学习。但它的价值在于证明：                ║
║     「算筭计算模型」可以为汉字理解提供一个自洽的基础。            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def main():
    """主入口"""
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if "--interactive" in args or "-i" in args:
        interactive_mode()
        return

    if "--philosophy" in args or "-p" in args:
        print_banner()
        show_philosophy()
        return

    # 默认：完整演示
    print_banner()
    show_philosophy()

    print("\n" + "=" * 70)
    print("  按 Enter 键开始完整演示...")
    print("=" * 70)
    input()

    show_full_pipeline()

    print("\n" + "=" * 70)
    print("  演示完毕！")
    print("  运行 'python main.py --interactive' 进入交互模式")
    print("  运行 'python main.py --philosophy' 查看哲学思考")
    print("=" * 70)


if __name__ == "__main__":
    main()

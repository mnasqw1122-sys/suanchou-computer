# -*- coding: utf-8 -*-
"""
看：从什么都不是的 0101，到能看到的 —|，到能理解的「木」
============================================================
这是算筭码最直观的价值证明。

运行：py see.py
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stroke_encoder import Stroke, StrokeEncoder
from stroke_dictionary import StrokeDictionary
from counting_rod_computer import CountingRodBit, CountingRodNumber


def demo():
    print("=" * 70)
    print("  看：从 0101 到直观感受")
    print("=" * 70)

    print("""
  核心问题：
    一串 0101——这些没有脸的比特，
    能不能变成我们直接感受到的东西？

  答案是：能。只需要把 0 和 1 换成 — 和 |。
""")

    # 获取「木」的算筭码
    dic = StrokeDictionary()
    mu = dic.get_character("木")
    encoded_mu = mu.encode()
    rod_str = encoded_mu.to_rod_string()

    # 转为裸 01
    binary_str = "".join("1" if ch == "—" else "0" for ch in rod_str if ch in "—|")

    # ====== 阶段 1：裸二进制 ======
    print("  ┌──────────────────────────────────────────────────────┐")
    print("  │  阶段 1：裸二进制                                     │")
    print("  │                                                      │")
    print(f"  │    {binary_str}                                        │")
    print("  │                                                      │")
    print("  │   这是什么？不知道。                                  │")
    print("  │   一段比特。可能是数字、地址、乱码。                   │")
    print("  │   你无法直视它，因为它什么都不是。                     │")
    print("  └──────────────────────────────────────────────────────┘")
    print()

    # ====== 阶段 2：算筭表示 ======
    print("  ┌──────────────────────────────────────────────────────┐")
    print("  │  阶段 2：算筭表示                                     │")
    print("  │                                                      │")
    print(f"  │    {rod_str}                                    │")
    print("  │                                                      │")
    print("  │   有形状了。— 和 | —— 横竖交错。                      │")
    print("  │   你能「看见」它了。一个排列，像几根算筭摆在那里。     │")
    print("  │   这不再是抽象的数字。这是具体的符号。                 │")
    print("  └──────────────────────────────────────────────────────┘")
    print()

    # ====== 阶段 3：笔画分解 ======
    print("  ┌──────────────────────────────────────────────────────┐")
    print("  │  阶段 3：笔画分解（每 3 位 = 一笔）                    │")
    print("  │                                                      │")
    encoder = StrokeEncoder()
    strokes = encoder.rod_string_to_strokes(rod_str)
    for i, s_name in enumerate(strokes):
        s = Stroke(s_name)
        print(f"  │     第 {i+1} 笔：{s.symbol} ({s_name})  编码 {s.code:03b}")
    print("  │                                                      │")
    print("  │   每一位都有它的笔画名。                               │")
    print("  │   这不是随机的。每一个 —|— 都是人用毛笔写的。         │")
    print("  └──────────────────────────────────────────────────────┘")
    print()

    # ====== 阶段 4：理解 ======
    print("  ┌──────────────────────────────────────────────────────┐")
    print("  │  阶段 4：理解                                         │")
    print("  │                                                      │")
    chars_in_dic = dic.find_by_strokes(strokes)
    if chars_in_dic:
        c = chars_in_dic[0]
        print(f"  │    横 竖 撇 捺                                        │")
        print(f"  │    ↑                                                │")
        print(f"  │    【{c.char}】                                              │")
        print(f"  │    {c.meaning}                                   │")
        print(f"  │    部首「{c.radical}」  造字法「{c.category}」                      │")
    print("  │                                                      │")
    print("  │   四笔拼在一起，你知道这是什么字。                     │")
    print("  │   这个过程就是「理解」。                               │")
    print("  │   从一串没意义的 0/1，到能叫出它的名字。               │")
    print("  └──────────────────────────────────────────────────────┘")

    # ====== 对比实验：随机 vs 有意义的 ======
    print()
    print("-" * 70)
    print("  对比实验：随机比特 vs 算筭码")
    print()

    random_bits = "".join(random.choice("01") for _ in range(12))
    random_rods = " ".join("—" if c == "1" else "|" for c in random_bits)
    print(f"  随机生成 12 位：{random_bits}")
    print(f"  改写成 — | ：  {random_rods}")

    # 尝试解析
    try:
        r_strokes = []
        for i in range(0, 12, 3):
            chunk = random_bits[i:i+3]
            # 转成 rod 方式
            rod_chunk = "".join("—" if c == "1" else "|" for c in chunk)
            bits = CountingRodBit.from_rod(rod_chunk)
            bits.reverse()
            s = Stroke.from_bits(bits)
            r_strokes.append(s.name)
        stroke_str = "  ".join(r_strokes)
        print(f"  尝试解析为笔画：{stroke_str}")
        found = dic.find_by_strokes(r_strokes)
        if found:
            print(f"  偶然命中：「{found[0].char}」({found[0].meaning})")
        else:
            print(f"  字典中没有这个字。")
            print(f"  随机的 —| 组合 ≠ 真实的字。")
    except:
        print(f"  无法解析。")
    print()

    print("=" * 70)
    print("  结论")
    print("=" * 70)
    print("""
    0101 → 没有意义，无法直视
    ——| → 有形状，能看见算筭排列
    横竖撇捺 → 这是「木」，一棵树的形状

    每一步都在增加「意义」。
    算筭码的价值就是把这种增加标准化，
    让计算机也能走完从「0101」到「木」的全程。
""")


if __name__ == "__main__":
    demo()

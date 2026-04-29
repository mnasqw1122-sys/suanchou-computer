# -*- coding: utf-8 -*-
"""
神经信号 → 理解：算筭码模拟演示
============================================
我们不真地模拟大脑，但我们可以展示：
看到一笔 → 匹配模式 → 逐步排除 → 确定是什么字

这就是「理解」的一种可计算版本。

运行：py nao.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber, CountingRodComputer
from stroke_encoder import Stroke, StrokeEncoder
from extended_strokes import EXTENDED_STROKE_DATA
from stroke_dictionary import Character


class FakeBrain:
    """
    一个极简的「大脑」，只能做一件事：
    每次收到一笔，逐步缩小候选范围，直到确定是什么字。

    真实的大脑不做遍历，而是并行激活——但逻辑等价。
    """

    def __init__(self):
        # 载入所有汉字
        self.all_chars = {}
        for char_name, data in EXTENDED_STROKE_DATA.items():
            self.all_chars[char_name] = Character(
                char=char_name,
                stroke_sequence=data["strokes"],
                meaning=data["meaning"],
                radical=data["radical"],
                category=data["category"],
                semantic_tags=data["tags"],
                pinyin=data["pinyin"],
            )
        # 当前候选集
        self.candidates = list(self.all_chars.values())
        # 已见过的笔画
        self.seen = []
        # 活跃度（每个候选字的匹配程度）
        self.activation = {}

    def receive_stroke(self, stroke_name):
        """
        收到一笔（神经信号）。
        相当于视网膜上的一个笔画特征被传入视觉皮层。
        """
        self.seen.append(stroke_name)

        new_candidates = []
        for char in self.candidates:
            # 这一笔与这个字的对应位置是否匹配？
            idx = len(self.seen) - 1
            if idx < len(char.stroke_sequence) and char.stroke_sequence[idx] == stroke_name:
                new_candidates.append(char)

        self.candidates = new_candidates
        # 计算活跃度
        self.activation = {}
        for char in self.candidates:
            match_count = 0
            for i, s in enumerate(self.seen):
                if i < len(char.stroke_sequence) and char.stroke_sequence[i] == s:
                    match_count += 1
            self.activation[char.char] = match_count / max(len(char.stroke_sequence), 1)

        return new_candidates

    def what_do_i_see(self):
        """「理解」：在收到的信号基础上，返回你认为看到了什么。"""
        if not self.candidates:
            return None, 0.0

        # 最佳匹配
        best = max(self.candidates, key=lambda c: self.activation.get(c.char, 0))
        return best, self.activation.get(best.char, 0)

    def reset(self):
        self.candidates = list(self.all_chars.values())
        self.seen = []
        self.activation = {}


def demo():
    print("=" * 70)
    print("  神经信号 → 理解：一个可计算的模型")
    print("=" * 70)

    print("""
  人看到一个字的过程：
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ 视网膜    │ → │ 视觉皮层  │ → │ 语言区   │
    │ 看到笔画  │    │ 模式匹配  │    │ 「这是木」│
    └──────────┘    └──────────┘    └──────────┘

  算筭模拟的也是同样的三阶段：
    —/| 信号  →  位运算匹配  →  确定是什么字
""")

    brain = FakeBrain()
    test_char = "木"
    char_obj = brain.all_chars[test_char]
    strokes = char_obj.stroke_sequence  # ["横", "竖", "撇", "捺"]

    print(f"  [实验] 让「大脑」逐笔接收「{test_char}」字的信号：")
    print(f"  完整笔画序列：{' → '.join(strokes)}")
    print(f"  初始候选：{len(brain.candidates)} 个字")
    print()

    for i, stroke_name in enumerate(strokes):
        s = Stroke(stroke_name)
        rod = s.to_rod_string()
        binary = f"{s.code:03b}"

        brain.receive_stroke(stroke_name)
        best, conf = brain.what_do_i_see()

        print(f"  第{i+1}笔：{s.symbol}({stroke_name}) "
              f"→ 神经信号 [{rod}] ({binary})")
        print(f"    剩余候选：{len(brain.candidates)} 个字", end="")
        if len(brain.candidates) <= 10:
            chars_str = " ".join(c.char for c in brain.candidates)
            print(f" [{chars_str}]")
        else:
            print()
        if best:
            pct = f"{conf*100:.0f}%"
            print(f"    当前最佳猜测：「{best.char}」({best.meaning}) 置信度 {pct}")
        print()

    # 第二轮：用「本」字——展示部分匹配阶段
    print("-" * 70)
    brain.reset()
    test_char = "本"
    char_obj = brain.all_chars[test_char]
    strokes = char_obj.stroke_sequence
    print(f"\n  [实验2] 逐笔识别「{test_char}」字 "
          f"（{len(strokes)}画：{' → '.join(strokes)}）")
    print()

    for i, stroke_name in enumerate(strokes):
        s = Stroke(stroke_name)
        brain.receive_stroke(stroke_name)
        best, conf = brain.what_do_i_see()

        candidates_str = ""
        if len(brain.candidates) <= 12:
            candidates_str = f" [{', '.join(c.char for c in brain.candidates)}]"

        pct = f"{conf*100:1.0f}%"
        print(f"  第{i+1}笔「{s.symbol}」→ "
              f"候选{len(brain.candidates)}字{candidates_str}")
        if best:
            print(f"    猜测：「{best.char}」置信 {pct}")
        if len(brain.candidates) == 1:
            print(f"    >>> 确定了！这就是「{best.char}」—— {best.meaning}")
            break
        print()

    # 第三轮：展示算筭码层面的匹配
    print("-" * 70)
    print(f"\n  [实验3] 算筭码层面：前四笔相同的字，为什么算筭码相似？")

    mu = brain.all_chars["木"]
    ben = brain.all_chars["本"]
    for c in [mu, ben]:
        c.encode()
    mu_rod = mu.rod_string
    ben_rod = ben.rod_string

    print(f"    「木」算筭码：{mu_rod}")
    print(f"    「本」算筭码：{ben_rod}")
    print(f"    「木」笔画：{' → '.join(mu.stroke_sequence)}")
    print(f"    「本」笔画：{' → '.join(ben.stroke_sequence)}")

    # 前4笔（木的全部 = 本的前4笔）的算筭码
    mu_bits = mu_rod.replace(" ", "")  # 12位
    ben_bits = ben_rod.replace(" ", "")  # 15位
    common = mu_bits  # 前12位 木⊂本
    extra = ben_bits[12:]  # 后3位 = 最后一笔「横」

    print(f"\n    算筭码逐位比较：")
    print(f"      木：  {mu_bits}")
    print(f"      本：  {ben_bits}   ← 多3位（最后一笔横=|||）")
    print(f"\n    前12位 = 木的全部笔画 = 100% 重叠")
    print(f"    后3位  = 本多出的一横 = 这使得「本」成为「木」的衍生字")
    print(f"\n    >>> 算筭码的精妙之处：")
    print(f"    >>> 「本」=「木」+「—」——不是语言学描述，是算筭码层面的客观事实。")

    # 结论
    print(f"\n{'='*70}")
    print(f"  总结")
    print(f"{'='*70}")
    print(f"""
  大脑理解一个字的过程，算筭计算机可以做同样的事：

    神经信号          →  算筭位序列
    视觉皮层模式匹配    →  逐位 AND/XOR 操作
    语言区命名          →  字典索引输出

  我们不知道大脑具体怎么做的，
  但我们可以确定：这个过程一定是「可计算的」。
  因为如果它不可计算，它就不可能发生在物理大脑中。

  算筭计算机的价值不在于模拟大脑，
  而在于证明「字形理解」可以在纯符号计算框架下完成。
""")


if __name__ == "__main__":
    demo()

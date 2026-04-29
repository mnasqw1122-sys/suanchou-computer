# -*- coding: utf-8 -*-
"""
语义理解模拟层 (Semantic Layer)
--------------------------------
用算筭计算来模拟「理解」汉字的过程。

核心思想：
「理解」本质上是一种计算。当我们看到一个汉字时：
1. 视觉系统将其笔画转化为神经信号
2. 大脑对这些信号进行模式匹配、联想、推断
3. 产生对该字的「理解」

如果算筭能够进行完整的逻辑计算，那么它就能够模拟这个过程：
- 将笔画转化为 —/| 信号流
- 用算筭运算（与、或、异或、加减等）处理这些信号
- 在字典中查找匹配的模式
- 产生语义输出

这个模拟层不是真正的 AI 理解，而是展示了：
「符号计算本身就可以产生类似理解的行为」。
"""

from counting_rod_computer import (
    CountingRodNumber, CountingRodComputer, CountingRodBit
)
from stroke_encoder import Stroke, StrokeEncoder
from stroke_dictionary import StrokeDictionary, Character


class UnderstandingResult:
    """
    理解结果 —— 算筭计算机对汉字进行「计算」后产生的结果
    """

    def __init__(self, target_char, match_score, related_chars,
                 stroke_matches, semantic_matches, computation_detail=""):
        """
        参数:
            target_char: 最匹配的汉字
            match_score: 匹配分数 (0-100)
            related_chars: 相关汉字列表
            stroke_matches: 笔画层面匹配的字
            semantic_matches: 语义层面匹配的字
            computation_detail: 计算过程描述
        """
        self.target_char = target_char
        self.match_score = match_score
        self.related_chars = related_chars
        self.stroke_matches = stroke_matches
        self.semantic_matches = semantic_matches
        self.computation_detail = computation_detail

    def summary(self):
        """生成理解结果摘要"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  理解结果")
        lines.append(f"{'='*60}")
        if self.target_char:
            lines.append(f"\n  [命中] 最佳匹配：{self.target_char}")
            lines.append(f"  匹配度：{self.match_score:.1f}%")
        if self.computation_detail:
            lines.append(f"\n  [算筭] 计算过程：{self.computation_detail}")
        if self.stroke_matches:
            lines.append(f"\n  [笔]  笔画层面相关字：")
            for c in self.stroke_matches[:5]:
                lines.append(f"     {c}")
        if self.semantic_matches:
            lines.append(f"\n  [脑] 语义层面相关字：")
            for c in self.semantic_matches[:5]:
                lines.append(f"     {c}")
        lines.append(f"{'='*60}")
        return "\n".join(lines)


class SemanticLayer:
    """
    语义理解层 —— 用算筭计算来理解汉字

    这个层次模拟了一个完整的「理解」管道：
    输入（笔画/算筭信号）→ 计算处理 → 字典匹配 → 语义输出
    """

    def __init__(self, dictionary=None):
        """
        初始化语义层
        参数:
            dictionary: StrokeDictionary 实例
        """
        self.dictionary = dictionary or StrokeDictionary()
        self.encoder = StrokeEncoder()
        self.computer = CountingRodComputer()

    def compute_similarity(self, char_a, char_b):
        """
        计算两个汉字在笔画层面的相似度
        在笔画级别进行比较（而非位级别），避免因码值对齐产生的误判。
        使用 Dice 系数：2 * |A ∩ B| / (|A| + |B|) * 100
        """
        strokes_a = char_a.stroke_sequence
        strokes_b = char_b.stroke_sequence

        # 计算匹配的笔画数（按位置逐一比较，到较短的序列为止）
        min_len = min(len(strokes_a), len(strokes_b))
        match_count = 0
        for i in range(min_len):
            if strokes_a[i] == strokes_b[i]:
                match_count += 1

        total = len(strokes_a) + len(strokes_b)
        if total == 0:
            return 0.0
        return (2 * match_count / total) * 100

    def compute_stroke_overlap(self, char_a, char_b):
        """
        计算两个汉字的笔画重叠部分（算筭 AND 运算）
        返回重叠部分对应的笔画描述
        """
        encoded_a = char_a.encode()
        encoded_b = char_b.encode()

        # 对齐
        max_len = max(len(encoded_a._bits), len(encoded_b._bits))
        a_bits = encoded_a._bits[:]
        b_bits = encoded_b._bits[:]
        while len(a_bits) < max_len:
            a_bits.append(CountingRodBit(0))
        while len(b_bits) < max_len:
            b_bits.append(CountingRodBit(0))

        # AND 运算
        overlap_bits = []
        for i in range(max_len):
            overlap_bits.append(
                CountingRodBit(a_bits[i].binary & b_bits[i].binary)
            )

        # 解码回笔画
        overlap = CountingRodNumber(0)
        overlap._bits = overlap_bits

        # 按3位一组解析重叠笔画
        strokes = []
        for i in range(0, len(overlap_bits), 3):
            if i + 3 <= len(overlap_bits):
                chunk = overlap_bits[i:i+3]
                if all(b.binary == 0 for b in chunk):
                    continue  # 空笔画跳过
                stroke = Stroke.from_bits(chunk)
                strokes.append(stroke.name)

        return strokes, overlap.to_rod_string()

    def compute_difference(self, char_a, char_b):
        """
        计算两个汉字的差异部分（算筭 XOR 运算）
        差异部分显示两个字的笔画区别在哪里
        """
        encoded_a = char_a.encode()
        encoded_b = char_b.encode()

        max_len = max(len(encoded_a._bits), len(encoded_b._bits))
        a_bits = encoded_a._bits[:]
        b_bits = encoded_b._bits[:]
        while len(a_bits) < max_len:
            a_bits.append(CountingRodBit(0))
        while len(b_bits) < max_len:
            b_bits.append(CountingRodBit(0))

        # XOR 运算
        diff_bits = []
        for i in range(max_len):
            diff_bits.append(
                CountingRodBit(a_bits[i].binary ^ b_bits[i].binary)
            )

        diff = CountingRodNumber(0)
        diff._bits = diff_bits

        diff_count = sum(b.binary for b in diff_bits)
        return diff_count, diff.to_rod_string()

    def compute_combined_pattern(self, char_a, char_b):
        """
        计算两个汉字的合并笔画模式（算筭 OR 运算）
        模拟「如果两个字合成一个新字会是什么笔画」
        """
        encoded_a = char_a.encode()
        encoded_b = char_b.encode()

        max_len = max(len(encoded_a._bits), len(encoded_b._bits))
        a_bits = encoded_a._bits[:]
        b_bits = encoded_b._bits[:]
        while len(a_bits) < max_len:
            a_bits.append(CountingRodBit(0))
        while len(b_bits) < max_len:
            b_bits.append(CountingRodBit(0))

        # OR 运算
        combined_bits = []
        for i in range(max_len):
            combined_bits.append(
                CountingRodBit(a_bits[i].binary | b_bits[i].binary)
            )

        # 解码合并笔画
        strokes = []
        for i in range(0, len(combined_bits), 3):
            if i + 3 <= len(combined_bits):
                chunk = combined_bits[i:i+3]
                if all(b.binary == 0 for b in chunk):
                    continue
                stroke = Stroke.from_bits(chunk)
                strokes.append(stroke.name)

        combined = CountingRodNumber(0)
        combined._bits = combined_bits
        return strokes, combined.to_rod_string()

    def understand_from_strokes(self, stroke_sequence):
        """
        给定笔画序列，用算筭计算来「理解」它是什么汉字。
        这模拟了人看到一个字的笔画后，大脑进行模式匹配的过程。

        参数:
            stroke_sequence: 笔画名称列表
        返回:
            UnderstandingResult: 理解结果
        """
        # 步骤1：将笔画编码为算筭信号
        encoded = self.encoder.encode_character(stroke_sequence)
        rod_str = encoded.to_rod_string()

        detail = f"收到笔画信号 → 编码为算筭 [{rod_str}] → 在字典中计算匹配"

        # 步骤2：在字典中进行精确匹配
        exact_matches = self.dictionary.find_by_strokes(stroke_sequence)

        # 步骤3：精确匹配
        if exact_matches:
            target = exact_matches[0]
            stroke_related = self.dictionary.find_related_by_strokes(target, match_length=2)
            semantic_related = self.dictionary.find_related_by_tags(target)
            return UnderstandingResult(
                target_char=target,
                match_score=100.0,
                related_chars=stroke_related + semantic_related,
                stroke_matches=stroke_related,
                semantic_matches=semantic_related,
                computation_detail=detail + f" → 精确命中 {target}"
            )

        # 步骤4：部分笔画模式匹配
        best_match = None
        best_score = 0.0
        all_partial = []

        # 尝试不同长度的笔画前缀匹配
        for prefix_len in range(len(stroke_sequence), 0, -1):
            prefix = stroke_sequence[:prefix_len]
            partial_matches = self.dictionary.find_by_stroke_pattern(prefix)
            if partial_matches:
                for pm in partial_matches:
                    score = (prefix_len / max(len(stroke_sequence), pm.stroke_count)) * 100
                    if score > best_score:
                        best_score = score
                        best_match = pm
                    all_partial.append(pm)
                break

        # 步骤5：如果以上都找不到，用算筭编码前缀在字典中模糊搜索
        if not best_match:
            for prefix_len in range(len(rod_str), 0, -3):
                prefix_rod = rod_str[:prefix_len]
                rod_matches = self.dictionary.find_by_rod_prefix(prefix_rod)
                if rod_matches:
                    best_match = rod_matches[0]
                    best_score = 50.0
                    all_partial = rod_matches
                    break

        if best_match:
            semantic_related = self.dictionary.find_related_by_tags(best_match)
            return UnderstandingResult(
                target_char=best_match,
                match_score=best_score,
                related_chars=all_partial,
                stroke_matches=all_partial,
                semantic_matches=semantic_related,
                computation_detail=detail + f" → 模糊匹配到 {best_match}（匹配度{best_score:.1f}%）"
            )

        # 步骤6：完全无法理解
        return UnderstandingResult(
            target_char=None,
            match_score=0.0,
            related_chars=[],
            stroke_matches=[],
            semantic_matches=[],
            computation_detail=detail + " → 未识别"
        )

    def understand_from_rod(self, rod_string):
        """
        直接从算筭符号（— 和 |）来理解它代表什么汉字。
        这模拟了：当你看到一串算筭信号，你能解读出它是什么字吗？

        参数:
            rod_string: 算筭符号字符串
        """
        clean = rod_string.replace(" ", "")

        # 步骤1：尝试精确 rod 匹配（最快路径）
        exact_matches = self.dictionary.find_by_rod_exact(clean)
        if exact_matches:
            exact_match = exact_matches[0]  # 取第一个
            # 如果有同笔顺多字，在计算过程中注明
            if len(exact_matches) > 1:
                homographs = "、".join(c.char for c in exact_matches)
                detail = f"收到算筭信号 [{clean}] → 精确命中（同笔顺字：{homographs}）"
            else:
                detail = f"收到算筭信号 [{clean}] → 精确命中"
            stroke_related = self.dictionary.find_related_by_strokes(exact_match, match_length=2)
            semantic_related = self.dictionary.find_related_by_tags(exact_match)
            return UnderstandingResult(
                target_char=exact_match,
                match_score=100.0,
                related_chars=stroke_related + semantic_related,
                stroke_matches=stroke_related,
                semantic_matches=semantic_related,
                computation_detail=detail
            )

        # 步骤2：从算筭信号解码笔画
        strokes = self.encoder.rod_string_to_strokes(rod_string)

        # 步骤3：用笔画序列进行理解
        if strokes:
            return self.understand_from_strokes(strokes)
        else:
            return UnderstandingResult(
                target_char=None,
                match_score=0.0,
                related_chars=[],
                stroke_matches=[],
                semantic_matches=[],
                computation_detail="无法从算筭信号中解析出有效笔画"
            )

    def compare_characters(self, char_a_name, char_b_name):
        """
        用算筭计算来比较两个汉字，展示它们的关系
        """
        char_a = self.dictionary.get_character(char_a_name)
        char_b = self.dictionary.get_character(char_b_name)

        if not char_a or not char_b:
            print(f"字典中找不到汉字: {char_a_name if not char_a else char_b_name}")
            return

        print(f"\n{'='*60}")
        print(f"  算筭比较：{char_a} vs {char_b}")
        print(f"{'='*60}")

        # 显示笔画编码
        print(f"\n  {char_a.char} 笔画：{' → '.join(char_a.stroke_sequence)}")
        print(f"       算筭：{char_a.rod_string}")
        print(f"\n  {char_b.char} 笔画：{' → '.join(char_b.stroke_sequence)}")
        print(f"       算筭：{char_b.rod_string}")

        # 相似度计算
        similarity = self.compute_similarity(char_a, char_b)
        print(f"\n  [数据] 笔画相似度：{similarity:.1f}%")

        # 重叠笔画
        overlap_strokes, overlap_rod = self.compute_stroke_overlap(char_a, char_b)
        print(f"  [关联] 重叠笔画：{' → '.join(overlap_strokes) if overlap_strokes else '(无)'}")
        print(f"       算筭：{overlap_rod}")

        # 差异笔画
        diff_count, diff_rod = self.compute_difference(char_a, char_b)
        print(f"  [差异] 差异位数：{diff_count}")
        print(f"       算筭：{diff_rod}")

        # 合并笔画
        combined_strokes, combined_rod = self.compute_combined_pattern(char_a, char_b)
        print(f"  [合并] 合并笔画：{' → '.join(combined_strokes) if combined_strokes else '(无)'}")
        print(f"       算筭：{combined_rod}")

        # 语义关系
        common_tags = set(char_a.semantic_tags) & set(char_b.semantic_tags)
        if common_tags:
            print(f"  [标签]  共同语义标签：{'、'.join(common_tags)}")

        print(f"{'='*60}")

    def compute_relatedness_graph(self, center_char_name, depth=1):
        """
        生成以某字为中心的关联图
        展示算筭计算如何揭示汉字之间的多重关系
        """
        center = self.dictionary.get_character(center_char_name)
        if not center:
            print(f"找不到汉字: {center_char_name}")
            return

        print(f"\n{'='*60}")
        print(f"  关联图谱 —— 中心字：{center}")
        print(f"{'='*60}")

        # 第1层：笔画层面相关
        print(f"\n  [算筭] 第一层：笔画层面关联（算筭模式匹配）")
        print(f"  " + "-" * 50)
        all_chars = self.dictionary.list_all()
        similarities = []
        for other in all_chars:
            if other.char != center.char:
                sim = self.compute_similarity(center, other)
                if sim > 0:
                    similarities.append((other, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)

        for char_obj, sim in similarities[:8]:
            overlap_strokes, _ = self.compute_stroke_overlap(center, char_obj)
            bar = "█" * int(sim / 10) + " " * (10 - int(sim / 10))
            print(f"  {bar} {char_obj} (相似度 {sim:.0f}%)")
            if overlap_strokes:
                print(f"        共享笔画：{' → '.join(overlap_strokes[:4])}")

        # 第2层：语义层面相关
        print(f"\n  [脑] 第二层：语义层面关联（标签共享）")
        print(f"  " + "-" * 50)
        semantic_related = self.dictionary.find_related_by_tags(center)
        for char_obj in semantic_related[:5]:
            common = set(center.semantic_tags) & set(char_obj.semantic_tags)
            print(f"  {char_obj} ← 共同标签：{'、'.join(common)}")

        # 第3层：造字法层面相关
        print(f"\n  [书] 第三层：造字法层面关联")
        print(f"  " + "-" * 50)
        same_category = [c for c in all_chars
                         if c.category == center.category and c.char != center.char]
        for char_obj in same_category[:5]:
            print(f"  {char_obj} ← 同为「{center.category}」字")


def demo_semantic_layer():
    """
    演示语义理解模拟层
    """
    print("=" * 60)
    print("  语义理解模拟层 (Semantic Layer) 演示")
    print("  用算筭计算来理解汉字")
    print("=" * 60)

    sem = SemanticLayer()

    # 演示1：给定笔画序列，理解是什么字
    print("\n" + "—" * 60)
    print("  演示1：通过笔画序列理解汉字")
    print("—" * 60)

    # 给「木」的笔画
    result = sem.understand_from_strokes(["横", "竖", "撇", "捺"])
    print(result.summary())

    # 给部分笔画（模拟只看到了一半）
    result = sem.understand_from_strokes(["竖", "折", "横"])
    print(result.summary())

    # 演示2：比较两个汉字的算筭关系
    print("\n" + "—" * 60)
    print("  演示2：用算筭比较两个汉字")
    print("—" * 60)

    sem.compare_characters("木", "本")  # 「本」是「木」加一横
    sem.compare_characters("日", "月")  # 都是天体
    sem.compare_characters("人", "大")  # 「大」是「人」加一横

    # 演示3：从算筭信号直接理解
    print("\n" + "—" * 60)
    print("  演示3：从算筭信号理解")
    print("—" * 60)

    mu = sem.dictionary.get_character("木")
    print(f"\n  收到算筭信号: {mu.rod_string}")
    print(f"  解读：这串 — 和 | 代表什么字？")
    result = sem.understand_from_rod(mu.rod_string)
    print(result.summary())

    # 演示4：关联图谱
    print("\n" + "—" * 60)
    print("  演示4：以「木」为中心的关联图谱")
    print("—" * 60)
    sem.compute_relatedness_graph("木")

    return sem


if __name__ == "__main__":
    demo_semantic_layer()

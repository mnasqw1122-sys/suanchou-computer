# -*- coding: utf-8 -*-
"""
算筭码搜索引擎 + 可视化演示
==========================================
在算筭思想继续前进的两个方向：

1. 算筭码搜索：用笔画和算筭码作为查询语言搜索汉字
   不依赖拼音、不依赖 Unicode 编号、纯粹以「形」搜字

2. 可视化演示：从算筭码到汉字理解的完整流水线
   每一步都展示算筭码的变换过程

这是算筭思想在软件层面能走到的实际应用边界。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber, CountingRodComputer
from stroke_encoder import Stroke, StrokeEncoder
from stroke_dictionary import StrokeDictionary, Character
from semantic_layer import SemanticLayer
from extended_strokes import EXTENDED_STROKE_DATA


# ================================================================
# 第一部分：扩展字典（合并原始40字 + 扩展数据）
# ================================================================

class ExtendedStrokeDict(StrokeDictionary):
    """
    扩展版笔画字典 —— 合并原始40字和扩展数据库
    """

    def __init__(self):
        super().__init__()
        # 将扩展数据添加到字典
        for char_name, data in EXTENDED_STROKE_DATA.items():
            if char_name in self._characters:
                continue  # 不覆盖已有数据
            char_obj = Character(
                char=char_name,
                stroke_sequence=data["strokes"],
                meaning=data["meaning"],
                radical=data["radical"],
                category=data["category"],
                semantic_tags=data["tags"],
                pinyin=data["pinyin"],
            )
            self._characters[char_name] = char_obj

        # 重建所有索引
        self._stroke_index = {}
        self._tag_index = {}
        self._rod_index = {}
        self._rod_exact_index = {}
        self._stroke_homographs = {}
        self._build_indexes()


# ================================================================
# 第二部分：算筭码搜索引擎
# ================================================================

class SuanChouSearchEngine:
    """
    算筭码搜索引擎
    
    以笔画、算筭码、语义标签为查询语言搜索汉字。
    不依赖拼音、Unicode。纯粹以「形」和「义」查找。
    """

    def __init__(self):
        self.dict = ExtendedStrokeDict()
        self.sem = SemanticLayer(self.dict)
        self.encoder = StrokeEncoder()
        self.computer = CountingRodComputer()

    def search_by_strokes(self, stroke_names, mode="exact"):
        """
        按笔画名称搜索
        参数:
            stroke_names: 笔画名称列表
            mode: "exact" 精确 / "prefix" 前缀 / "contains" 包含
        """
        if mode == "exact":
            return self.dict.find_by_strokes(stroke_names)
        elif mode == "prefix":
            return self.dict.find_by_stroke_pattern(stroke_names)
        elif mode == "contains":
            results = []
            pattern = tuple(stroke_names)
            p_len = len(pattern)
            for char_obj in self.dict.list_all():
                seq = char_obj.stroke_sequence
                for i in range(len(seq) - p_len + 1):
                    if tuple(seq[i:i + p_len]) == pattern:
                        results.append((char_obj, i))
                        break
            return results
        return []

    def search_by_rod(self, rod_string, mode="exact"):
        """
        按算筭码搜索
        参数:
            rod_string: 算筭符号字符串
            mode: "exact" 精确 / "prefix" 前缀
        """
        clean = rod_string.replace(" ", "")
        if mode == "exact":
            return self.dict.find_by_rod_exact(clean)
        elif mode == "prefix":
            return self.dict.find_by_rod_prefix(clean)
        return []

    def search_by_tags(self, tags, mode="any"):
        """
        按语义标签搜索
        参数:
            tags: 标签名称列表
            mode: "any" 任意匹配 / "all" 全部匹配
        """
        if mode == "any":
            results = set()
            for tag in tags:
                for char_obj in self.dict.find_by_tag(tag):
                    results.add(char_obj)
            return list(results)
        elif mode == "all":
            results = []
            for char_obj in self.dict.list_all():
                if all(tag in char_obj.semantic_tags for tag in tags):
                    results.append(char_obj)
            return results
        return []

    def search_similar(self, char_name, top_n=10):
        """
        搜索与给定汉字字形相似的汉字
        用算筭码相似度计算
        """
        target = self.dict.get_character(char_name)
        if not target:
            return []

        scored = []
        for other in self.dict.list_all():
            if other.char == target.char:
                continue
            sim = self.sem.compute_similarity(target, other)
            if sim > 0:
                scored.append((other, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def search_by_stroke_count(self, count_min, count_max=None):
        """按笔画数范围搜索"""
        if count_max is None:
            count_max = count_min
        results = []
        for char_obj in self.dict.list_all():
            if count_min <= char_obj.stroke_count <= count_max:
                results.append(char_obj)
        return sorted(results, key=lambda c: c.stroke_count)

    def search_by_radical(self, radical):
        """按部首搜索"""
        results = []
        for char_obj in self.dict.list_all():
            if char_obj.radical == radical:
                results.append(char_obj)
        return results

    def search_by_category(self, category):
        """按造字法搜索"""
        results = []
        for char_obj in self.dict.list_all():
            if char_obj.category == category:
                results.append(char_obj)
        return results

    def suggest_strokes(self, partial_text):
        """根据文字提示笔画名称"""
        all_strokes = ["横", "竖", "撇", "捺", "点", "折", "钩", "提"]
        if not partial_text:
            return all_strokes
        return [s for s in all_strokes if partial_text in s]


# ================================================================
# 第三部分：可视化演示
# ================================================================

def show_search_demo():
    """演示算筭码搜索引擎"""
    print("=" * 70)
    print("  算筭码搜索引擎 (SuanChou Search Engine)")
    print("  用笔画和算筭码作为查询语言")
    print("=" * 70)

    engine = SuanChouSearchEngine()

    # 统计
    chars = engine.dict.list_all()
    print(f"\n  字典规模：{len(chars)} 个汉字")
    print(f"  造字法分布：象形 {len(engine.search_by_category('象形'))} 字, "
          f"会意 {len(engine.search_by_category('会意'))} 字, "
          f"形声 {len(engine.search_by_category('形声'))} 字, "
          f"指事 {len(engine.search_by_category('指事'))} 字")

    # 演示1：按笔画前缀搜索
    print("\n" + "-" * 70)
    print("  [搜索1] 笔画前缀搜索：笔画以 [横, 竖] 开头的字")
    print("-" * 70)
    results = engine.search_by_strokes(["横", "竖"], "prefix")
    for r in results[:12]:
        strokes_str = " ".join(s.symbol for s in [Stroke(n) for n in r.stroke_sequence])
        print(f"  「{r.char}」 {strokes_str}  ({r.meaning})")

    # 演示2：按语义标签搜索
    print("\n" + "-" * 70)
    print("  [搜索2] 语义标签搜索：标签包含「植物」的字")
    print("-" * 70)
    results = engine.search_by_tags(["植物"], "any")
    for r in results:
        strokes_str = " ".join(s.symbol for s in [Stroke(n) for n in r.stroke_sequence])
        print(f"  「{r.char}」 {strokes_str}  ({r.meaning})")

    # 演示3：字形相似搜索
    print("\n" + "-" * 70)
    print("  [搜索3] 字形相似搜索：与「木」最相似的字")
    print("-" * 70)
    results = engine.search_similar("木", top_n=10)
    for char_obj, sim in results:
        bar = "█" * int(sim / 10) + " " * (10 - int(sim / 10))
        print(f"  {bar} 「{char_obj.char}」({char_obj.meaning}) 相似度 {sim:.0f}%")

    # 演示4：部首搜索
    print("\n" + "-" * 70)
    print("  [搜索4] 部首搜索：氵(水部)的字")
    print("-" * 70)
    results = engine.search_by_radical("氵")
    for r in results:
        strokes_str = " ".join(s.symbol for s in [Stroke(n) for n in r.stroke_sequence])
        print(f"  「{r.char}」 {strokes_str}  ({r.meaning})")

    # 演示5：笔画数搜索
    print("\n" + "-" * 70)
    print("  [搜索5] 笔画数搜索：4画的字")
    print("-" * 70)
    results = engine.search_by_stroke_count(4)
    for r in results:
        strokes_str = " ".join(s.symbol for s in [Stroke(n) for n in r.stroke_sequence])
        print(f"  「{r.char}」 {strokes_str}  ({r.meaning})")

    # 演示6：算筭码直接搜索
    print("\n" + "-" * 70)
    print("  [搜索6] 算筭码搜索：用它自身的算筭码查询「明」")
    print("-" * 70)
    ming = engine.dict.get_character("明")
    rod_str = ming.rod_string
    print(f"  算筭码：{rod_str}")
    results = engine.search_by_rod(rod_str, "exact")
    for r in results:
        print(f"  -> 「{r.char}」({r.meaning})")

    print("\n" + "=" * 70)
    print("  搜索演示完毕")
    print("=" * 70)


def show_visual_pipeline():
    """
    完整可视化流水线演示
    从算筭码到汉字理解的每一步
    """
    print("=" * 70)
    print("  算筭码可视化流水线")
    print("  从原始信号到理解的完整过程")
    print("=" * 70)

    engine = SuanChouSearchEngine()
    dic = engine.dict

    # 选择一组示范字
    demo_chars = ["木", "林", "森", "休", "本"]

    for cn in demo_chars:
        char_obj = dic.get_character(cn)
        if not char_obj:
            continue

        print(f"\n{'='*70}")
        print(f"  流水线演示：{char_obj}")
        print(f"{'='*70}")

        # 步骤1：笔画分解
        print(f"\n  [步骤1] 笔画分解")
        strokes_visual = " ".join(
            f"{Stroke(n).symbol}({n})" for n in char_obj.stroke_sequence
        )
        print(f"    「{cn}」的笔画序列：{strokes_visual}")
        print(f"    笔画数：{char_obj.stroke_count}")

        # 步骤2：二进制编码
        print(f"\n  [步骤2] 3-bit 笔画编码")
        for i, stroke_name in enumerate(char_obj.stroke_sequence, 1):
            stroke = Stroke(stroke_name)
            rod = stroke.to_rod_string()
            print(f"    笔画{i}: {stroke.symbol}({stroke_name}) "
                  f"-> code={stroke.code:03b} -> 算筭 [{rod}]")

        # 步骤3：算筭码表示
        print(f"\n  [步骤3] 完整算筭码")
        full_rod = char_obj.rod_string
        bit_width = char_obj.bits
        print(f"    算筭码：「{cn}」= {full_rod}")
        print(f"    位宽：{bit_width} 位")

        # 步骤4：算筭码反查验证
        print(f"\n  [步骤4] 算筭码反查（精确匹配）")
        found = engine.search_by_rod(char_obj.rod_string, "exact")
        if found:
            for f in found:
                marker = " <<< 精确命中!" if f.char == cn else ""
                print(f"    匹配到：「{f.char}」({f.meaning}){marker}")
        else:
            print(f"    未找到精确匹配")

        # 步骤5：字形关联
        print(f"\n  [步骤5] 字形层面关联（算筭相似度）")
        similar = engine.search_similar(cn, top_n=5)
        for other, sim in similar:
            print(f"    「{other.char}」相似度 {sim:.0f}%  ({other.meaning})")

        # 步骤6：语义层面关联
        print(f"\n  [步骤6] 语义层面关联（标签匹配）")
        # 找共同标签的
        tag_related = set()
        for tag in char_obj.semantic_tags:
            for other in engine.search_by_tags([tag], "any"):
                if other.char != cn:
                    common = set(char_obj.semantic_tags) & set(other.semantic_tags)
                    tag_related.add((other, ",".join(common)))
        for other, tags in list(tag_related)[:5]:
            print(f"    「{other.char}」共享标签：{tags}  ({other.meaning})")

    # 展示特殊流水线：木 -> 林 -> 森
    print(f"\n{'='*70}")
    print(f"  合体字流水线：木 -> 林 -> 森")
    print(f"{'='*70}")

    mu = dic.get_character("木")
    lin = dic.get_character("林")
    sen = dic.get_character("森")

    if mu and lin and sen:
        print(f"\n  木 {mu.rod_string}  ({mu.stroke_count}画)")
        print(f"  → 双木成林 {lin.rod_string}  ({lin.stroke_count}画) "
              f"{'='.join([mu.rod_string.replace(' ','')]*2)[:24]}...")
        print(f"  → 三木成森 {sen.rod_string}  ({sen.stroke_count}画) "
              f"{'='.join([mu.rod_string.replace(' ','')]*3)[:36]}...")
        print(f"\n  算筭码视角：")
        print(f"    木 × 2 = 林（字形叠加，语义：聚集）")
        print(f"    木 × 3 = 森（字形密度增加，语义：繁茂）")
        print(f"    这是算筭码能够直观表达的结构信息！")

    print(f"\n{'='*70}")
    print(f"  流水线演示完毕")
    print(f"{'='*70}")


def show_full_report():
    """生成完整搜索报告"""
    print("=" * 70)
    print("  算筭搜索引擎 — 系统概览")
    print("=" * 70)

    engine = SuanChouSearchEngine()
    chars = engine.dict.list_all()
    total = len(chars)

    print(f"\n  收录汉字总数：{total}")

    # 笔画数分布
    by_count = {}
    for c in chars:
        by_count[c.stroke_count] = by_count.get(c.stroke_count, 0) + 1
    print(f"\n  笔画数分布：")
    for count in sorted(by_count.keys()):
        chars_list = [c.char for c in chars if c.stroke_count == count]
        print(f"    {count:2d}画 ({by_count[count]:2d}字): {' '.join(chars_list[:20])}")

    # 造字法分布
    by_cat = {}
    for c in chars:
        cat = c.category or "未知"
        by_cat[cat] = by_cat.get(cat, 0) + 1
    print(f"\n  造字法分布：")
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}字")

    # 语义标签频次 Top 20
    tag_freq = {}
    for c in chars:
        for tag in c.semantic_tags:
            tag_freq[tag] = tag_freq.get(tag, 0) + 1
    print(f"\n  语义标签频次 Top 15：")
    for tag, count in sorted(tag_freq.items(), key=lambda x: -x[1])[:15]:
        bar = "█" * count
        print(f"    {tag:6s} {bar} ({count}字)")

    # 部首分布
    radical_freq = {}
    for c in chars:
        r = c.radical
        radical_freq[r] = radical_freq.get(r, 0) + 1
    print(f"\n  部首分布（出现2次以上）：")
    for rad, count in sorted(radical_freq.items(), key=lambda x: -x[1]):
        if count >= 2:
            chars_list = [c.char for c in chars if c.radical == rad]
            print(f"    {rad}: {' '.join(chars_list)}")

    # 算筭码位宽分布
    bit_freq = {}
    for c in chars:
        bits = c.bits
        bit_freq[bits] = bit_freq.get(bits, 0) + 1
    print(f"\n  算筭码位宽分布：")
    for bits in sorted(bit_freq.keys()):
        chars_list = [c.char for c in chars if c.bits == bits]
        print(f"    {bits:2d}位 ({bit_freq[bits]:2d}字): {' '.join(chars_list[:15])}")


def interactive_search():
    """交互式搜索引擎"""
    print("=" * 70)
    print("  算筭码交互搜索引擎")
    print("  输入 'help' 查看命令, 'quit' 退出")
    print("=" * 70)

    engine = SuanChouSearchEngine()

    print(f"\n  当前字典：{len(engine.dict.list_all())} 字")
    print(f"  可用的笔画名称：横 竖 撇 捺 点 折 钩 提")
    print(f"  语义标签示例：数字 自然 植物 天体 动物 矿物")
    print(f"               人类 方位 时间 品质 器官 动作")
    print()

    while True:
        try:
            cmd = input("  搜索> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break

        if not cmd:
            continue

        if cmd.lower() in ("quit", "q", "exit"):
            print("  再见！")
            break

        if cmd.lower() == "help":
            print("""
  命令语法：
    strokes <笔画1> <笔画2> ...    按笔画搜索
    rod <算筭码>                   按算筭码搜索
    similar <汉字>                 相似字形搜索
    tags <标签1> <标签2> ...      按语义标签搜索
    count <数字>                   按笔画数搜索
    radical <部首>                 按部首搜索
    category <造字法>              按造字法搜索
    info <汉字>                    查看汉字完整信息
    stats                          显示字典统计
    quit                           退出
""")
            continue

        parts = cmd.split()
        action = parts[0].lower()
        args = parts[1:]

        if action == "strokes" and args:
            results = engine.search_by_strokes(args, "prefix")
            if results:
                print(f"  找到 {len(results)} 个匹配：")
                for r in results[:15]:
                    print(f"    「{r.char}」{'  '.join(r.stroke_sequence)}  ({r.meaning})")
            else:
                print(f"  未找到匹配")

        elif action == "rod" and args:
            results = engine.search_by_rod(args[0].replace(",", ""), "prefix")
            if results:
                print(f"  找到 {len(results)} 个匹配：")
                for r in results[:10]:
                    print(f"    「{r.char}」{r.rod_string}  ({r.meaning})")
            else:
                print(f"  未找到匹配")

        elif action == "similar" and args:
            results = engine.search_similar(args[0], top_n=10)
            if results:
                print(f"  与「{args[0]}」最相似的 {len(results)} 个字：")
                for char_obj, sim in results:
                    bar = "█" * int(sim / 10) + " " * (10 - int(sim / 10))
                    print(f"    {bar} 「{char_obj.char}」({char_obj.meaning}) {sim:.0f}%")
            else:
                print(f"  未找到相似字")

        elif action == "tags" and args:
            results = engine.search_by_tags(args, "any")
            if results:
                print(f"  标签匹配 {len(results)} 个字：")
                for r in results[:15]:
                    match_tags = [t for t in args if t in r.semantic_tags]
                    print(f"    「{r.char}」({r.meaning}) [{'、'.join(match_tags)}]")
            else:
                print(f"  未找到匹配")

        elif action == "count" and args:
            try:
                n = int(args[0])
                results = engine.search_by_stroke_count(n)
                if results:
                    print(f"  {n}画的字 ({len(results)}个)：")
                    for r in results:
                        print(f"    「{r.char}」{'  '.join(r.stroke_sequence)}  ({r.meaning})")
                else:
                    print(f"  未找到{n}画的字")
            except ValueError:
                print(f"  请输入有效数字")

        elif action == "radical" and args:
            results = engine.search_by_radical(args[0])
            if results:
                print(f"  部首「{args[0]}」的字 ({len(results)}个)：")
                for r in results:
                    print(f"    「{r.char}」({r.meaning})")
            else:
                print(f"  未找到")

        elif action == "category" and args:
            results = engine.search_by_category(args[0])
            if results:
                print(f"  造字法「{args[0]}」的字 ({len(results)}个)：")
                for r in results:
                    print(f"    「{r.char}」({r.meaning})")
            else:
                print(f"  未找到。可用：象形 指事 会意 形声")

        elif action == "info" and args:
            obj = engine.dict.get_character(args[0])
            if obj:
                print(f"\n{obj.summary()}")
            else:
                print(f"  未收录「{args[0]}」")

        elif action == "stats":
            chars = engine.dict.list_all()
            by_count = {}
            for c in chars:
                by_count[c.stroke_count] = by_count.get(c.stroke_count, 0) + 1
            by_cat = {}
            for c in chars:
                cat = c.category or "未知"
                by_cat[cat] = by_cat.get(cat, 0) + 1
            print(f"\n  总字数：{len(chars)}")
            print(f"  笔画范围：{min(by_count.keys())} - {max(by_count.keys())} 画")
            print(f"  造字法：{'  '.join(f'{k}:{v}' for k,v in sorted(by_cat.items(), key=lambda x:-x[1]))}")

        else:
            print(f"  未知命令：「{action}」，输入 'help' 查看帮助")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="算筭码搜索引擎")
    parser.add_argument("--search", "-s", action="store_true", help="运行搜索演示")
    parser.add_argument("--pipeline", "-p", action="store_true", help="运行流水线演示")
    parser.add_argument("--report", "-r", action="store_true", help="生成系统报告")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式搜索")
    parser.add_argument("--all", "-a", action="store_true", help="运行全部演示")

    args = parser.parse_args()

    if args.interactive:
        interactive_search()
    elif args.all:
        show_full_report()
        print("\n"); show_search_demo()
        print("\n"); show_visual_pipeline()
    elif args.search:
        show_search_demo()
    elif args.pipeline:
        show_visual_pipeline()
    elif args.report:
        show_full_report()
    else:
        # 默认运行全部
        show_full_report()
        print("\n")
        show_search_demo()
        print("\n")
        show_visual_pipeline()
        print(f"\n  使用 'py suanchou_search.py -i' 进入交互搜索模式")

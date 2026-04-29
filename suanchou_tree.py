# -*- coding: utf-8 -*-
"""
算筭字族演化树 (SuanChou Character Family Tree)
==================================================
用算筭码的前缀关系自动发现汉字之间的衍生关系，
用 Unicode 字符在终端画出字族树。

核心算法：
  如果字 A 的笔画序列是字 B 的严格前缀，则 B 是 A 的「子字」。
  在算筭码层面，这意味着 B 的算筭码以 A 的算筭码开头。
  
  「本」=「木」+「一横」——不是语言学描述，是算筭码层面的客观事实。

运行方式：
  py suanchou_tree.py
  py suanchou_tree.py --interactive   (交互模式)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber
from stroke_encoder import Stroke, StrokeEncoder
from extended_strokes import EXTENDED_STROKE_DATA
from stroke_dictionary import Character
from suanchou_search import ExtendedStrokeDict


class CharacterNode:
    """字族树节点"""

    def __init__(self, char_obj, parent=None, shared_strokes=None, added_strokes=None):
        """
        创建一个字族树节点
        参数:
            char_obj: Character 对象
            parent: 父节点
            shared_strokes: 与父节点共享的笔画
            added_strokes: 相比父节点新增的笔画
        """
        self.char_obj = char_obj
        self.parent = parent
        self.children = []
        self.shared_strokes = shared_strokes or []
        self.added_strokes = added_strokes or []
        self.depth = 0 if parent is None else parent.depth + 1

    @property
    def char(self):
        return self.char_obj.char

    @property
    def rod_string(self):
        return self.char_obj.rod_string

    @property
    def meaning(self):
        return self.char_obj.meaning

    @property
    def stroke_sequence(self):
        return self.char_obj.stroke_sequence

    def add_child(self, child_node):
        self.children.append(child_node)
        child_node.parent = self

    def __str__(self):
        return f"「{self.char}」({self.meaning})"

    def __repr__(self):
        return self.__str__()


class CharacterFamilyTree:
    """
    字族演化树 —— 自动发现并可视化汉字间的衍生关系
    """

    def __init__(self):
        self.dict = ExtendedStrokeDict()
        self.encoder = StrokeEncoder()
        self.all_chars = self.dict.list_all()
        self.roots = []
        self._build_tree()

    def _build_tree(self):
        """
        构建字族森林。
        算法：
          1. 按笔画数升序排列所有字
          2. 对每个字，找是否有笔画数更少的字是其前缀
          3. 取最长前缀匹配的字作为父节点
        """
        node_map = {}  # char_name -> CharacterNode
        sorted_chars = sorted(self.all_chars, key=lambda c: c.stroke_count)

        for char_obj in sorted_chars:
            seg = char_obj.stroke_sequence
            # 找最长前缀匹配
            best_parent = None
            best_match_len = 0

            for other_obj in sorted_chars:
                if other_obj.stroke_count >= char_obj.stroke_count:
                    break  # 后面的笔画数 >= 此字，不可能严格前缀
                oseg = other_obj.stroke_sequence
                if len(oseg) < best_match_len:
                    continue
                if seg[:len(oseg)] == oseg:
                    if len(oseg) > best_match_len:
                        best_parent = node_map.get(other_obj.char)
                        best_match_len = len(oseg)

            # 创建节点
            shared = char_obj.stroke_sequence[:best_match_len] if best_match_len > 0 else []
            added = char_obj.stroke_sequence[best_match_len:] if best_match_len > 0 else []
            node = CharacterNode(char_obj, best_parent, shared, added)
            node_map[char_obj.char] = node

            if best_parent:
                best_parent.add_child(node)
            else:
                self.roots.append(node)

    def find_root_for_char(self, char_name):
        """找到某字所在的根节点"""
        found = None
        for root in self.roots:
            found = self._find_in_subtree(root, char_name)
            if found:
                return root
        return None

    def _find_in_subtree(self, node, char_name):
        if node.char == char_name:
            return node
        for child in node.children:
            result = self._find_in_subtree(child, char_name)
            if result:
                return result
        return None

    def get_subtree(self, root_char_name):
        """获取以某字为根的字族子树（重新构建局部树）"""
        root_obj = self.dict.get_character(root_char_name)
        if not root_obj:
            return None

        # 找出所有以此字为前缀的其他字
        descendants = []
        for other in self.all_chars:
            if other.char == root_char_name:
                continue
            if (other.stroke_count > root_obj.stroke_count and
                    other.stroke_sequence[:len(root_obj.stroke_sequence)] == root_obj.stroke_sequence):
                descendants.append(other)

        # 构建局部树
        root_node = CharacterNode(root_obj)

        # 按笔画数排序，逐步添加
        descendants.sort(key=lambda c: c.stroke_count)
        node_map = {root_char_name: root_node}

        for char_obj in descendants:
            seg = char_obj.stroke_sequence
            # 在已添加的节点中找最长前缀
            best_parent = None
            best_len = 0
            for name, node in node_map.items():
                oseg = node.char_obj.stroke_sequence
                if len(oseg) < len(seg) and seg[:len(oseg)] == oseg:
                    if len(oseg) > best_len:
                        best_parent = node
                        best_len = len(oseg)

            if best_parent:
                shared = seg[:best_len]
                added = seg[best_len:]
                child_node = CharacterNode(char_obj, best_parent, shared, added)
                best_parent.add_child(child_node)
                node_map[char_obj.char] = child_node

        return root_node


class TreeRenderer:
    """
    用 Unicode 字符在终端渲染字族树
    """

    # 画树所用的字符
    VLINE = "│"
    HLINK = "── "
    BRANCH = "├─ "
    LAST = "└─ "
    SPACE = "   "
    GAP = "    "

    @staticmethod
    def render_node(node, prefix="", is_last=True, is_root=True,
                    show_detail=True, max_stroke_show=5):
        """
        递归渲染节点
        参数:
            node: 当前节点
            prefix: 前缀字符串
            is_last: 是否是父节点的最后一个子节点
            is_root: 是否是根节点
            show_detail: 是否显示详细信息
            max_stroke_show: 显示多少笔画后省略
        """
        lines = []

        # 渲染当前节点的行
        if is_root:
            branch = ""
            connector = ""
        elif is_last:
            branch = prefix + TreeRenderer.LAST
            connector = prefix + TreeRenderer.SPACE
        else:
            branch = prefix + TreeRenderer.BRANCH
            connector = prefix + TreeRenderer.VLINE + TreeRenderer.GAP

        # 节点主行
        if show_detail:
            # 笔画摘要
            strokes_summary = " → ".join(
                f"{Stroke(s).symbol}" for s in node.stroke_sequence[:max_stroke_show]
            )
            if len(node.stroke_sequence) > max_stroke_show:
                strokes_summary += f" ...(+{len(node.stroke_sequence) - max_stroke_show})"

            line = f"{branch}[{node.char}] {strokes_summary}"
            lines.append(line)

            # 含义行
            meaning_line = f"{connector}【{node.meaning}】"
            lines.append(meaning_line)

            # 算筭码行（截断显示）
            rod = node.rod_string
            if len(rod) > 48:
                rod = rod[:44] + " ···"
            rod_line = f"{connector}算筭: {rod}"
            lines.append(rod_line)

            # 如果非根，显示新增笔画
            if node.added_strokes:
                added = " + ".join(f"{Stroke(s).symbol}" for s in node.added_strokes)
                pad = " " * len(node.parent.char) if node.parent else ""
                add_line = f"{connector}{pad} +[{added}]"
                lines.append(add_line)
        else:
            line = f"{branch}「{node.char}」({node.meaning})"
            lines.append(line)

        # 递归渲染子节点
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            child_prefix = connector if not is_root else ""
            child_lines = TreeRenderer.render_node(
                child, prefix=child_prefix, is_last=is_last_child,
                is_root=False, show_detail=show_detail,
                max_stroke_show=max_stroke_show
            )
            lines.extend(child_lines)

        return lines

    @classmethod
    def render_forest(cls, roots, show_detail=True, max_stroke_show=5):
        """渲染整片森林"""
        all_lines = []
        for i, root in enumerate(roots):
            if len(root.children) == 0:
                continue  # 跳过没有子节点的孤字
            root_lines = cls.render_node(
                root, is_last=(i == len(roots) - 1), is_root=True,
                show_detail=show_detail, max_stroke_show=max_stroke_show
            )
            all_lines.extend(root_lines)
            if i < len(roots) - 1:
                all_lines.append("")  # 空行分隔
        return all_lines

    @classmethod
    def render_compact(cls, roots, max_depth=4):
        """
        紧凑渲染 —— 只显示树结构骨架，不显示每个字的详情
        适合快速浏览全局结构
        """
        all_lines = []

        def _render(node, prefix="", is_last=True, is_root=True, depth=0):
            if depth > max_depth:
                return

            if is_root:
                branch = ""
                stem = ""
                deep_prefix = ""
            elif is_last:
                branch = prefix + cls.LAST
                stem = prefix + cls.SPACE
                deep_prefix = prefix + cls.SPACE
            else:
                branch = prefix + cls.BRANCH
                stem = prefix + cls.VLINE + cls.GAP
                deep_prefix = prefix + cls.VLINE + cls.GAP

            strokes_short = "".join(f"{Stroke(s).symbol}" for s in node.stroke_sequence[:4])
            if len(node.stroke_sequence) > 4:
                strokes_short += "…"

            count = f"{node.char_obj.stroke_count}画" if node.char_obj.stroke_count else ""
            tag = node.char_obj.category or ""
            line = f"{branch}「{node.char}」{strokes_short}  {count}  {tag}  {node.meaning}"
            all_lines.append(line)

            for i, child in enumerate(node.children):
                is_last_child = (i == len(node.children) - 1)
                child_prefix = deep_prefix
                _render(child, prefix=child_prefix, is_last=is_last_child,
                        is_root=False, depth=depth + 1)

        for i, root in enumerate(roots):
            if len(root.children) == 0:
                continue
            _render(root, is_last=(i == len(roots) - 1), is_root=True, depth=0)
            if i < len(roots) - 1:
                all_lines.append("")

        return all_lines


def show_full_forest():
    """展示完整字族森林"""
    print("=" * 70)
    print("  算筭字族演化树 —— 完整森林")
    print("  用算筭码前缀关系自动发现汉字衍生脉络")
    print("=" * 70)

    tree = CharacterFamilyTree()

    print(f"\n  字典规模：{len(tree.all_chars)} 个汉字")
    print(f"  发现字族：{len(tree.roots)} 个根节点（其中 {sum(1 for r in tree.roots if len(r.children) > 0)} 个有后代）")
    print()

    # 紧凑展示
    compact_lines = TreeRenderer.render_compact(tree.roots)
    for line in compact_lines:
        print(f"  {line}")

    print()

    # 统计
    print("-" * 70)
    print("  字族规模统计")
    print("-" * 70)
    family_sizes = []
    for root in tree.roots:
        size = _count_nodes(root)
        if size > 1:
            family_sizes.append((root, size))
    family_sizes.sort(key=lambda x: -x[1])
    for root, size in family_sizes:
        children_names = "  ".join(f"「{c.char}」" for c in root.children[:6])
        if len(root.children) > 6:
            children_names += f" ... (+{len(root.children) - 6})"
        print(f"  「{root.char}」({root.meaning}) → 字族{size}字: {children_names}")


def _count_nodes(node):
    """递归计算子树节点数"""
    count = 1
    for child in node.children:
        count += _count_nodes(child)
    return count


def show_single_family(char_name, detail=True):
    """展示单个字族的详细演化树"""
    tree = CharacterFamilyTree()
    root = tree.get_subtree(char_name)
    if not root:
        print(f"字典中未收录「{char_name}」")
        return

    char_obj = tree.dict.get_character(char_name)
    print("=" * 70)
    print(f"  字族演化树 —— 「{char_name}」为核心")
    print(f"  笔画数：{char_obj.stroke_count}  算筭位宽：{char_obj.bits}")
    print(f"  算筭码：{char_obj.rod_string}")
    print("=" * 70)

    subtree_size = _count_nodes(root)
    print(f"\n  字族规模：{subtree_size} 字（含根）")
    print()

    if detail:
        lines = TreeRenderer.render_node(
            root, is_last=True, is_root=True,
            show_detail=True, max_stroke_show=6
        )
        for line in lines:
            print(f"  {line}")
    else:
        compact = TreeRenderer.render_compact([root], max_depth=5)
        for line in compact:
            print(f"  {line}")

    # 算筭码层面的总结
    print(f"\n  {'─' * 66}")
    print(f"  【算筭码视角】")
    print(f"  {'─' * 66}")

    root_rod = root.rod_string.replace(" ", "")
    print(f"  根「{root.char}」的算筭码 ({len(root_rod)}位):")
    print(f"    {root.rod_string}")
    print()

    for child in root.children:
        child_rod = child.rod_string.replace(" ", "")
        overlap_len = len(root_rod)  # 前缀
        extra_rod = child.rod_string.replace(" ", "")[overlap_len:]
        added_display = " + ".join(f"{Stroke(s).symbol}({s})" for s in child.added_strokes)
        print(f"  子「{child.char}」= 父前缀 + [{added_display}]")
        print(f"    父前缀: {root.rod_string[:overlap_len + overlap_len // 3]}...")
        print(f"    新增位: {' '.join([c for c in extra_rod])}  "
              f"({len(extra_rod)}位 = {len(child.added_strokes)}笔 × 3)")
        print()


def show_evolution_path(start_char, end_char):
    """展示从一个字到另一个字的逐笔演化路径"""
    tree = CharacterFamilyTree()
    dict_obj = tree.dict
    a = dict_obj.get_character(start_char)
    b = dict_obj.get_character(end_char)
    if not a or not b:
        print("字典中未收录此字")
        return

    seg_a = a.stroke_sequence
    seg_b = b.stroke_sequence

    # 找公共前缀
    common_len = 0
    for i in range(min(len(seg_a), len(seg_b))):
        if seg_a[i] == seg_b[i]:
            common_len += 1
        else:
            break

    print("=" * 70)
    print(f"  演化路径：「{start_char}」→「{end_char}」")
    print("=" * 70)

    print(f"\n  公共笔画前缀 ({common_len}笔)：")
    common_strokes = seg_a[:common_len]
    common_display = " → ".join(f"{Stroke(s).symbol}" for s in common_strokes)
    print(f"    {common_display}")

    if common_len < len(seg_a):
        removed = seg_a[common_len:]
        print(f"\n  「{start_char}」的特有笔画：")
        for s in removed:
            stroke = Stroke(s)
            print(f"    移出: {stroke.symbol}({s}) 算筭 [{stroke.to_rod_string()}]")

    if common_len < len(seg_b):
        added = seg_b[common_len:]
        print(f"\n  「{end_char}」的新增笔画：")
        for s in added:
            stroke = Stroke(s)
            print(f"    加入: {stroke.symbol}({s}) 算筭 [{stroke.to_rod_string()}]")

    # 算筭码层面的比对
    print(f"\n  算筭码对比：")
    a_rod = a.rod_string
    b_rod = b.rod_string
    # 找到 rod 字符串中的差异位置
    a_clean = a.rod_string.replace(" ", "")
    b_clean = b.rod_string.replace(" ", "")
    rod_common = common_len * 3
    print(f"    公共部分: {' '.join([c for c in a_clean[:rod_common]])} "
          f"(前{rod_common}位，{common_len}笔)")
    if rod_common < len(a_clean):
        print(f"    「{start_char}」独有: {' '.join([c for c in a_clean[rod_common:]])}")
    if rod_common < len(b_clean):
        print(f"    「{end_char}」独有: {' '.join([c for c in b_clean[rod_common:]])}")


def show_tree_statistics():
    """字族树统计分析"""
    tree = CharacterFamilyTree()

    print("=" * 70)
    print("  字族树统计报告")
    print("=" * 70)

    print(f"\n  总字数：{len(tree.all_chars)}")
    print(f"  根节点数（无前缀祖先）：{len(tree.roots)}")
    print(f"  有后代的根节点：{sum(1 for r in tree.roots if len(r.children) > 0)}")

    # 深度分布
    max_depth = 0
    depth_count = {}
    for root in tree.roots:
        d = _max_depth(root)
        max_depth = max(max_depth, d)
        depth_count[d] = depth_count.get(d, 0) + 1

    print(f"\n  最大演化深度：{max_depth}")
    print(f"  深度分布：")
    for d in sorted(depth_count.keys()):
        print(f"    深度{d}: {depth_count[d]}条演化链")

    # 最"高产"的字族
    families = []
    for root in tree.roots:
        size = _count_nodes(root)
        if size > 1:
            families.append((root, size))
    families.sort(key=lambda x: -x[1])

    print(f"\n  Top 10 最庞大的字族：")
    for i, (root, size) in enumerate(families[:10]):
        desc = "  ".join(f"「{c.char}」" for c in root.children[:8])
        if len(root.children) > 8:
            desc += f" ... (+{len(root.children) - 8})"
        print(f"    {i+1}. 「{root.char}」({root.meaning}) — {size}字: {desc}")

    # 衍生距离分布（子节点比父节点多几笔）
    added_count = {}
    for root in tree.roots:
        _collect_added_counts(root, added_count)
    print(f"\n  子字新增笔画数分布：")
    for added, count in sorted(added_count.items(), key=lambda x: -x[1]):
        print(f"    +{added}笔: {count}对父子关系")


def _max_depth(node):
    """计算子树最大深度"""
    if not node.children:
        return node.depth
    return max(_max_depth(child) for child in node.children)


def _collect_added_counts(node, counter):
    for child in node.children:
        added = len(child.added_strokes)
        counter[added] = counter.get(added, 0) + 1
        _collect_added_counts(child, counter)


def interactive_mode():
    """交互式字族树探索"""
    tree = CharacterFamilyTree()

    print("=" * 70)
    print("  字族演化树 —— 交互探索")
    print("=" * 70)

    print(f"\n  字典共 {len(tree.all_chars)} 字")
    print(f"  有后代的根字：")
    for root in tree.roots:
        if len(root.children) > 0:
            children_list = " ".join(f"「{c.char}」" for c in root.children[:8])
            if len(root.children) > 8:
                children_list += f" ... (+{len(root.children)-8})"
            print(f"    「{root.char}」→ {children_list}")

    while True:
        print("\n" + "=" * 60)
        print("  命令：")
        print("    <汉字>     查看该字的字族树")
        print("    path <A> <B>  展示从A到B的演化路径")
        print("    forest     显示完整森林")
        print("    stats      显示统计报告")
        print("    list       列出所有可查看的字族")
        print("    q          退出")
        print("=" * 60)

        try:
            cmd = input("\n字族树> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not cmd:
            continue

        if cmd.lower() in ("q", "quit", "exit", "退出"):
            print("再见！")
            break

        if cmd.lower() == "forest":
            show_full_forest()
            continue

        if cmd.lower() == "stats":
            show_tree_statistics()
            continue

        if cmd.lower() == "list":
            print("\n可查看的字族（有后代的根字）：")
            for root in tree.roots:
                if len(root.children) > 0:
                    size = _count_nodes(root)
                    children_list = " ".join(f"{c.char}" for c in root.children[:6])
                    if len(root.children) > 6:
                        children_list += " ..."
                    print(f"  「{root.char}」({size}字): {children_list}")
            continue

        parts = cmd.split()
        if len(parts) >= 3 and parts[0].lower() == "path":
            show_evolution_path(parts[1], parts[2])
            continue

        # 假设是单个汉字
        char = parts[0]
        root = tree.get_subtree(char)
        if root is None:
            # 尝试在完整森林中查找
            forest_root = tree.find_root_for_char(char)
            if forest_root:
                print(f"\n「{char}」不是根字，它属于「{forest_root.char}」的字族。")
                print("重新显示以「" + forest_root.char + "」为根：")
                show_single_family(forest_root.char, detail=False)
            else:
                print(f"字典中未收录「{char}」")
        else:
            detail = len(cmd.split()) < 2 or cmd.split()[1].lower() != "compact"
            show_single_family(char, detail=detail)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="算筭字族演化树")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--forest", "-f", action="store_true", help="显示完整森林")
    parser.add_argument("--stats", "-s", action="store_true", help="统计报告")
    parser.add_argument("--char", "-c", type=str, help="查看指定字的字族树")
    parser.add_argument("--path", "-p", nargs=2, metavar=("A", "B"), help="展示A到B的演化路径")

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.forest:
        show_full_forest()
    elif args.stats:
        show_tree_statistics()
    elif args.path:
        show_evolution_path(args.path[0], args.path[1])
    elif args.char:
        show_single_family(args.char, detail=True)
    else:
        # 默认：展示森林 + 几个重点字族
        show_full_forest()

        print("\n" + "=" * 70)
        print("  重点字族详解")
        print("=" * 70)

        for key_char in ["木", "人", "日", "水", "火", "口"]:
            show_single_family(key_char, detail=True)
            print()

        print("=" * 70)
        print("  运行 'py suanchou_tree.py -i' 进入交互模式")
        print("=" * 70)


if __name__ == "__main__":
    main()

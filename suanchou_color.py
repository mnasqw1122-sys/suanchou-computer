# -*- coding: utf-8 -*-
"""
算筭码染色可视化 (SuanChou Color Visualization)
==================================================
用 ANSI 终端颜色给算筭码 — 和 | 加上视觉语义。

每种笔画对应一种颜色，让你一眼看出：
  · 长串算筭码中，哪些位属于哪一笔
  · 两个字比较时，差异位在哪里、共同位在哪里
  · 笔画叠加如何体现在算筭码层面

颜色映射：
  横(一)=蓝  竖(丨)=红  撇(丿)=绿  捺(乀)=黄
  点(丶)=紫  折(乙)=青  钩(亅)=亮白  提(/)=深红
  
支持 Windows 10+ 原生 ANSI 颜色。

运行方式：
  py suanchou_color.py
  py suanchou_color.py --char 木        (查看单字染色)
  py suanchou_color.py --compare 木 本  (两字对比)
  py suanchou_color.py --legend         (颜色图例)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber, CountingRodComputer
from stroke_encoder import Stroke, StrokeEncoder
from extended_strokes import EXTENDED_STROKE_DATA
from stroke_dictionary import Character
from suanchou_search import ExtendedStrokeDict


# ================================================================
# ANSI 颜色定义
# ================================================================

class Color:
    """ANSI 终端颜色代码"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # 亮色
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # 背景色
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_GRAY = "\033[47m"
    
    # 用于算筭码正常位的默认色
    ROD_DEFAULT = "\033[37m"       # 白色
    ROD_DIM = "\033[90m"           # 灰色（用于非活动位）


# 笔画 → 颜色映射
STROKE_COLORS = {
    "横": Color.BLUE,
    "竖": Color.RED,
    "撇": Color.GREEN,
    "捺": Color.YELLOW,
    "点": Color.MAGENTA,
    "折": Color.CYAN,
    "钩": Color.BRIGHT_WHITE,
    "提": Color.BRIGHT_RED,
}

# 笔画 → 背景色映射（用于高亮差异）
STROKE_BG_COLORS = {
    "横": Color.BG_BLUE,
    "竖": Color.BG_RED,
    "撇": Color.BG_GREEN,
    "捺": Color.BG_YELLOW,
    "点": Color.BG_MAGENTA,
    "折": Color.BG_CYAN,
    "钩": "",  # 无背景，用亮前景
    "提": "",  # 无背景，用亮前景
}


def colorize_rod_string(char_obj, use_background=False):
    """
    给算筭码字符串按笔画上色。
    参数:
        char_obj: Character 对象
        use_background: 是否使用背景色（用于高亮模式）
    返回:
        带 ANSI 颜色码的字符串
    """
    rod_clean = char_obj.rod_string.replace(" ", "")
    strokes = char_obj.stroke_sequence
    
    parts = []
    for i, stroke_name in enumerate(strokes):
        start = i * 3
        end = start + 3
        chunk = rod_clean[start:end] if end <= len(rod_clean) else rod_clean[start:]
        
        fg_color = STROKE_COLORS.get(stroke_name, Color.WHITE)
        bg_color = STROKE_BG_COLORS.get(stroke_name, "") if use_background else ""
        
        parts.append(f"{fg_color}{bg_color}{chunk}{Color.RESET}")
    
    return " ".join(parts)


def colorize_rod_raw(rod_clean, stroke_sequence, highlight_indices=None, dim_indices=None):
    """
    给原始算筭码字符串按笔画上色，同时支持高亮和暗淡。
    参数:
        rod_clean: 无空格的算筭码字符串
        stroke_sequence: 笔画名称列表（长度 = len(rod_clean) / 3）
        highlight_indices: 需要高亮的位索引集合
        dim_indices: 需要暗淡的位索引集合
    返回:
        带 ANSI 颜色码的字符串
    """
    highlight_indices = highlight_indices or set()
    dim_indices = dim_indices or set()
    
    parts = []
    for i, stroke_name in enumerate(stroke_sequence):
        start = i * 3
        end = start + 3
        chunk = rod_clean[start:end] if end <= len(rod_clean) else rod_clean[start:]
        
        fg_color = STROKE_COLORS.get(stroke_name, Color.WHITE)
        
        # 逐位检查是否需要特殊处理
        colored_chars = []
        for j, ch in enumerate(chunk):
            bit_idx = start + j
            if bit_idx in highlight_indices:
                colored_chars.append(f"{Color.BOLD}{Color.BRIGHT_WHITE}{ch}{Color.RESET}")
            elif bit_idx in dim_indices:
                colored_chars.append(f"{Color.DIM}{ch}{Color.RESET}")
            else:
                colored_chars.append(f"{fg_color}{ch}{Color.RESET}")
        
        parts.append("".join(colored_chars))
    
    return " ".join(parts)


def compare_two_chars(char_a_name, char_b_name):
    """
    用算筭码染色比较两个汉字。
    展示：
      1. 各自的算筭码（带颜色）
      2. 差异位高亮（用 XOR）
      3. 共同位暗淡（用 AND）
      4. 统计差异
    """
    dic = ExtendedStrokeDict()
    a = dic.get_character(char_a_name)
    b = dic.get_character(char_b_name)
    
    if not a or not b:
        print(f"字典中未收录: {char_a_name if not a else char_b_name}")
        return
    
    # 编码
    a_rod_clean = a.rod_string.replace(" ", "")
    b_rod_clean = b.rod_string.replace(" ", "")
    
    # 对齐
    max_len = max(len(a_rod_clean), len(b_rod_clean))
    while len(a_rod_clean) < max_len:
        a_rod_clean += "|"
    while len(b_rod_clean) < max_len:
        b_rod_clean += "|"
    
    # 扩展笔画序列
    a_strokes = list(a.stroke_sequence)
    b_strokes = list(b.stroke_sequence)
    while len(a_strokes) * 3 < max_len:
        a_strokes.append("?")
    while len(b_strokes) * 3 < max_len:
        b_strokes.append("?")
    
    # 计算异同
    a_bits = []
    b_bits = []
    for ch in a_rod_clean:
        a_bits.append(1 if ch == "—" else 0)
    for ch in b_rod_clean:
        b_bits.append(1 if ch == "—" else 0)
    
    diff_indices = set()
    common_count = 0
    diff_count = 0
    for i in range(max_len):
        if a_bits[i] != b_bits[i]:
            diff_indices.add(i)
            diff_count += 1
        else:
            common_count += 1
    
    width = 72
    
    print()
    print("=" * width)
    print(f"  算筭码染色对比: 「{a.char}」vs「{b.char}」")
    print("=" * width)
    
    # 基本信息
    print(f"\n  「{a.char}」{a.meaning}   {a.stroke_count}画  {a.bits}位  部首: {a.radical}")
    print(f"  「{b.char}」{b.meaning}   {b.stroke_count}画  {b.bits}位  部首: {b.radical}")
    
    # 笔画序列对比
    print(f"\n  [----- 笔画序列对比 -----]")
    a_stroke_display = " → ".join(f"{STROKE_COLORS.get(s, Color.WHITE)}{Stroke(s).symbol}{Color.RESET}" 
                                   for s in a.stroke_sequence)
    b_stroke_display = " → ".join(f"{STROKE_COLORS.get(s, Color.WHITE)}{Stroke(s).symbol}{Color.RESET}" 
                                   for s in b.stroke_sequence)
    print(f"  「{a.char}」: {a_stroke_display}")
    print(f"  「{b.char}」: {b_stroke_display}")
    
    # 算筭码对比 - 原始颜色版
    print(f"\n  [----- 算筭码（按笔画分别染色）-----]")
    a_colored = colorize_rod_string(a, use_background=False)
    b_colored = colorize_rod_string(b, use_background=False)
    print(f"  「{a.char}」: {a_colored}")
    print(f"  「{b.char}」: {b_colored}")
    
    # 算筭码对比 - 差异高亮版
    print(f"\n  [----- 算筭码对比（差异位高亮）-----]")
    
    # 用 colorize_rod_raw
    a_diff_colored = colorize_rod_raw(a_rod_clean, a_strokes, 
                                       highlight_indices=diff_indices)
    b_diff_colored = colorize_rod_raw(b_rod_clean, b_strokes, 
                                       highlight_indices=diff_indices)
    
    print(f"  「{a.char}」: {a_diff_colored}")
    print(f"  「{b.char}」: {b_diff_colored}")
    
    # 差异统计
    print(f"\n  [----- 差异分析 -----]")
    total = max_len
    pct = diff_count / total * 100 if total > 0 else 0
    common_pct = common_count / total * 100 if total > 0 else 0
    
    # 可视化条
    bar_len = 50
    diff_filled = int(pct / 100 * bar_len)
    common_filled = bar_len - diff_filled
    
    bar_diff = f"{Color.BRIGHT_WHITE}{Color.BOLD}#{Color.RESET}" * diff_filled
    bar_common = f"{Color.DIM}.{Color.RESET}" * common_filled
    bar = bar_diff + bar_common
    
    print(f"  差异位: {diff_count}/{total} ({pct:.1f}%)")
    print(f"  共同位: {common_count}/{total} ({common_pct:.1f}%)")
    print(f"  可视化: [{bar}]")
    print(f"          {'^差异位' if diff_count > 0 else ''}  {'共同位' if common_count > 0 else ''}")
    
    # 按笔画分组统计差异
    print(f"\n  [----- 按笔画分组差异 -----]")
    # 对于每个笔画位置，检查是否完全一致
    num_strokes = max(len(a.stroke_sequence), len(b.stroke_sequence))
    identical_strokes = 0
    different_strokes = 0
    only_a = 0
    only_b = 0
    
    for i in range(num_strokes):
        a_s = a.stroke_sequence[i] if i < len(a.stroke_sequence) else None
        b_s = b.stroke_sequence[i] if i < len(b.stroke_sequence) else None
        
        a_chunk = a_rod_clean[i*3:(i+1)*3] if i*3 < len(a_rod_clean) else ""
        b_chunk = b_rod_clean[i*3:(i+1)*3] if i*3 < len(b_rod_clean) else ""
        
        if a_s and b_s:
            if a_chunk == b_chunk:
                identical_strokes += 1
                marker = f"{Color.DIM}  [=]{Color.RESET}"
            else:
                different_strokes += 1
                marker = f"{Color.BRIGHT_WHITE}{Color.BOLD}  [X]{Color.RESET}"
            a_display = f"{STROKE_COLORS.get(a_s, '')}{Stroke(a_s).symbol}({a_s}){Color.RESET}"
            b_display = f"{STROKE_COLORS.get(b_s, '')}{Stroke(b_s).symbol}({b_s}){Color.RESET}"
            print(f"  笔{i+1}: {a_display} {a_chunk}  vs  {b_display} {b_chunk} {marker}")
        elif a_s:
            only_a += 1
            a_display = f"{STROKE_COLORS.get(a_s, '')}{Stroke(a_s).symbol}({a_s}){Color.RESET}"
            print(f"  笔{i+1}: {a_display} {a_chunk}  (仅「{a.char}」有)")
        elif b_s:
            only_b += 1
            b_display = f"{STROKE_COLORS.get(b_s, '')}{Stroke(b_s).symbol}({b_s}){Color.RESET}"
            print(f"  笔{i+1}: {b_display} {b_chunk}  (仅「{b.char}」有)")
    
    print(f"\n  摘要: {identical_strokes}笔相同, {different_strokes}笔不同, "
          f"{only_a}笔仅「{a.char}」有, {only_b}笔仅「{b.char}」有")
    
    # 语义标签对比
    a_tags = set(a.semantic_tags)
    b_tags = set(b.semantic_tags)
    common_tags = a_tags & b_tags
    only_a_tags = a_tags - b_tags
    only_b_tags = b_tags - a_tags
    
    if a_tags or b_tags:
        print(f"\n  [----- 语义标签对比 -----]")
        if common_tags:
            print(f"  共同: {Color.BRIGHT_GREEN}{'、'.join(common_tags)}{Color.RESET}")
        if only_a_tags:
            print(f"  「{a.char}」独有: {Color.BLUE}{'、'.join(only_a_tags)}{Color.RESET}")
        if only_b_tags:
            print(f"  「{b.char}」独有: {Color.RED}{'、'.join(only_b_tags)}{Color.RESET}")
    
    print()
    print("=" * width)


def show_single_char(char_name):
    """
    展示单个汉字的算筭码染色。
    分解每个笔画 — 对用的颜色 — 对应的 3 位算筭码。
    """
    dic = ExtendedStrokeDict()
    char_obj = dic.get_character(char_name)
    
    if not char_obj:
        print(f"字典中未收录「{char_name}」")
        return
    
    width = 72
    
    print()
    print("=" * width)
    print(f"  算筭码染色: 「{char_obj.char}」")
    print("=" * width)
    
    print(f"\n  汉字: 「{char_obj.char}」  {char_obj.meaning}")
    print(f"  笔画数: {char_obj.stroke_count}  算筭位宽: {char_obj.bits}")
    print(f"  部首: {char_obj.radical}  造字法: {char_obj.category}")
    if char_obj.semantic_tags:
        print(f"  语义标签: {'、'.join(char_obj.semantic_tags)}")
    
    # 逐笔画分解（带颜色）
    print(f"\n  [----- 逐笔画分解 -----]")
    print(f"  {'笔画':8s}  {'编码':8s}  {'算筭码':12s}  {'裸二进制':10s}")
    print(f"  {'-' * 48}")
    
    rod_clean = char_obj.rod_string.replace(" ", "")
    for i, stroke_name in enumerate(char_obj.stroke_sequence):
        stroke = Stroke(stroke_name)
        color = STROKE_COLORS.get(stroke_name, "")
        symbol = stroke.symbol
        rod = stroke.to_rod_string()
        binary = f"{stroke.code:03b}"
        
        chunk_start = i * 3
        chunk_end = chunk_start + 3
        rod_chunk = rod_clean[chunk_start:chunk_end] if chunk_end <= len(rod_clean) else ""
        
        print(f"  {color}{symbol:4s}({stroke_name}){Color.RESET}  "
              f"{color}{binary}{Color.RESET}     "
              f"{color}{rod_chunk}{Color.RESET}         "
              f"{binary}")
    
    # 完整算筭码（带颜色）
    print(f"\n  [----- 完整算筭码（带颜色）-----]")
    colored = colorize_rod_string(char_obj, use_background=False)
    print(f"  {colored}")
    
    # 位统计
    ones = sum(1 for ch in rod_clean if ch == "—")
    zeros = sum(1 for ch in rod_clean if ch == "|")
    print(f"\n  位统计: 「—」({ones}个)  「|」({zeros}个)  总计 {len(rod_clean)} 位")
    
    # 每笔画位统计
    print(f"\n  [----- 每笔画位分布 -----]")
    for i, stroke_name in enumerate(char_obj.stroke_sequence):
        color = STROKE_COLORS.get(stroke_name, "")
        symbol = Stroke(stroke_name).symbol
        chunk = rod_clean[i*3:(i+1)*3]
        chunk_ones = sum(1 for ch in chunk if ch == "—")
        chunk_zeros = sum(1 for ch in chunk if ch == "|")
        bar_len = chunk_ones
        bar = "—" * bar_len + "|" * chunk_zeros
        print(f"  {color}笔{i+1}: {symbol}({stroke_name})  [{bar}]  —:{chunk_ones} |:{chunk_zeros}{Color.RESET}")
    
    print()
    print("=" * width)


def show_color_legend():
    """显示颜色图例"""
    width = 60
    
    print()
    print("=" * width)
    print("  算筭码染色图例")
    print("=" * width)
    
    print(f"\n  每种笔画有自己独特的颜色：")
    print()
    
    for stroke_name, color in STROKE_COLORS.items():
        stroke = Stroke(stroke_name)
        symbol = stroke.symbol
        rod = stroke.to_rod_string()
        binary = f"{stroke.code:03b}"
        
        print(f"  {color}{symbol:4s} {stroke_name:4s}  "
              f"[{rod}]  编码 {binary}{Color.RESET}")
    
    print(f"\n  [----- 实际演示：用所有笔画拼一个虚拟字 -----]")
    # 展示所有八种笔画各一个
    all_8_strokes = ["横", "竖", "撇", "捺", "点", "折", "钩", "提"]
    print()
    print("  笔画序列: ", end="")
    for s_name in all_8_strokes:
        color = STROKE_COLORS.get(s_name, "")
        sym = Stroke(s_name).symbol
        print(f"{color}{sym}{Color.RESET} ", end="")
    print()
    
    print("  算筭码:   ", end="")
    for s_name in all_8_strokes:
        color = STROKE_COLORS.get(s_name, "")
        rod = Stroke(s_name).to_rod_string()
        print(f"{color}{rod}{Color.RESET} ", end="")
    print()
    
    print(f"\n  [----- 差异对比样式 -----]")
    print(f"  {Color.DIM}暗淡位 = 两字相同的位{Color.RESET}")
    print(f"  {Color.BRIGHT_WHITE}{Color.BOLD}高亮位 = 两字不同的位{Color.RESET}")
    
    print()
    print("=" * width)


def show_multi_char_grid(chars=None):
    """
    展示多个汉字的算筭码网格 —— 让你直观感受不同字的算筭码结构。
    类似基因序列比对的可视化风格。
    """
    dic = ExtendedStrokeDict()
    
    if chars is None:
        chars = ["一", "二", "三", "木", "本", "林", "人", "大", "天", "日", "月", "明"]
    
    width = 90
    
    print()
    print("=" * width)
    print("  算筭码网格 —— 多字并列对比")
    print("  类似基因序列比对的视觉风格")
    print("=" * width)
    
    # 先收集所有字的算筭码
    char_data = []
    max_rod_len = 0
    for cn in chars:
        obj = dic.get_character(cn)
        if obj:
            rod = obj.rod_string.replace(" ", "")
            max_rod_len = max(max_rod_len, len(rod))
            char_data.append((cn, obj, rod))
    
    if not char_data:
        print("  无可显示的字")
        return
    
    print(f"\n  {'字':4s} {'画数':4s} {'算筭码（按笔画染色）'}")
    print(f"  {'-' * (width - 4)}")
    
    for cn, obj, rod in char_data:
        # 补位对齐
        padded_rod = rod + "|" * (max_rod_len - len(rod))
        # 构建扩展的笔画序列
        padded_strokes = list(obj.stroke_sequence)
        while len(padded_strokes) * 3 < len(padded_rod):
            padded_strokes.append("?")
        
        colored = colorize_rod_raw(padded_rod, padded_strokes)
        
        meaning_short = obj.meaning[:6] if obj.meaning else ""
        print(f"  「{cn}」{obj.stroke_count:2d}画 {colored}  {meaning_short}")
    
    print()
    print("  " + "-" * (width - 4))
    print(f"  {Color.DIM}对齐后填充位用灰色显示{Color.RESET}")
    print()
    print("=" * width)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="算筭码染色可视化")
    parser.add_argument("--char", "-c", type=str, help="查看单个汉字的算筭码染色")
    parser.add_argument("--compare", "-d", nargs=2, metavar=("A", "B"), help="染色对比两个汉字")
    parser.add_argument("--legend", "-l", action="store_true", help="显示颜色图例")
    parser.add_argument("--grid", "-g", action="store_true", help="显示多字网格")
    
    args = parser.parse_args()
    
    # 启用 Windows 终端 ANSI 支持
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass
    
    if args.legend:
        show_color_legend()
        return
    
    if args.grid:
        show_multi_char_grid()
        return
    
    if args.char:
        show_single_char(args.char)
        return
    
    if args.compare:
        compare_two_chars(args.compare[0], args.compare[1])
        return
    
    # 默认：展示图例 + 几个关键字的对比 + 网格
    show_color_legend()
    
    print("\n")
    show_single_char("木")
    show_single_char("明")
    
    print("\n")
    compare_two_chars("木", "本")
    
    print("\n")
    compare_two_chars("日", "月")
    
    print("\n")
    show_multi_char_grid(["一", "二", "三", "木", "本", "林", "森", "休"])
    
    print("\n" + "=" * 70)
    print("  演示完毕。")
    print(f"  运行 'py suanchou_color.py --char <字>' 查看单字染色")
    print(f"  运行 'py suanchou_color.py --compare <A> <B>' 对比两字")
    print(f"  运行 'py suanchou_color.py --grid' 查看网格")
    print("=" * 70)


if __name__ == "__main__":
    main()

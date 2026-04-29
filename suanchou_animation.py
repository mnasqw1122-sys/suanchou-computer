# -*- coding: utf-8 -*-
"""
算筭码逐帧识别动画 (SuanChou Frame-by-Frame Recognition Animation)
====================================================================
从 0 和 1 的裸比特，到一笔一笔积累的算筭码，到最终识别出汉字 —— 
把「理解 = 计算」的过程变成一段可以观看的动画。

理念：
  当人眼看到一个汉字时，不是一瞬间看完全部笔画的，
  而是逐笔扫描、逐笔匹配、逐步缩小候选范围。
  这个过程完全可以用算筭码来模拟和可视化。

运行方式：
  py suanchou_animation.py
  py suanchou_animation.py --speed fast  (快速模式)
  py suanchou_animation.py --speed slow  (慢速模式)
  py suanchou_animation.py --demo-all    (演示所有实验字)
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from counting_rod_computer import CountingRodBit, CountingRodNumber
from stroke_encoder import Stroke, StrokeEncoder
from extended_strokes import EXTENDED_STROKE_DATA
from stroke_dictionary import Character
from suanchou_search import ExtendedStrokeDict


class StrokeByStrokeRecognizer:
    """
    逐笔识别引擎 —— 模拟视觉系统逐步接收笔画信号的过程。
    
    每个汉字被逐笔「播放」给识别器，识别器在每一步：
      1. 收到一笔（含视觉符号、名称、算筭码）
      2. 缩小候选集（排除不匹配的字）
      3. 更新当前最佳猜测
      4. 记录这个「认知状态快照」
    """

    def __init__(self):
        self.dict = ExtendedStrokeDict()
        self.encoder = StrokeEncoder()
        self.all_chars = self.dict.list_all()

    def recognize(self, char_name, play_speed="normal"):
        """
        逐笔识别一个汉字，返回每一步的快照列表。
        参数:
            char_name: 要识别的汉字
            play_speed: "slow"/"normal"/"fast"
        返回:
            (snapshots, final_result) 
        """
        char_obj = self.dict.get_character(char_name)
        if not char_obj:
            return [], None

        strokes = char_obj.stroke_sequence
        candidates = list(self.all_chars)
        snapshots = []

        for step, stroke_name in enumerate(strokes):
            stroke = Stroke(stroke_name)
            rod = stroke.to_rod_string()
            binary = f"{stroke.code:03b}"

            # 用裸 01 表示这一笔
            raw_bits = "".join("1" if b.is_on else "0" for b in stroke.to_bits())

            # 缩小候选集
            new_candidates = []
            for c in candidates:
                if step < len(c.stroke_sequence) and c.stroke_sequence[step] == stroke_name:
                    new_candidates.append(c)

            candidates = new_candidates

            # 计算活跃度
            activation = {}
            for c in candidates:
                match_count = 0
                for i, sn in enumerate(strokes[:step + 1]):
                    if i < len(c.stroke_sequence) and c.stroke_sequence[i] == sn:
                        match_count += 1
                activation[c.char] = match_count / max(len(c.stroke_sequence), 1)

            # 最佳猜测
            best = None
            best_conf = 0.0
            if candidates:
                best = max(candidates, key=lambda c: activation.get(c.char, 0))
                best_conf = activation.get(best.char, 0)

            # 累积算筭码
            accumulated_rod = ""
            for i in range(step + 1):
                s = Stroke(strokes[i])
                accumulated_rod += s.to_rod_string()
            # 每3位加空格
            acc_with_spaces = " ".join(
                accumulated_rod[i:i + 3] for i in range(0, len(accumulated_rod), 3)
            )

            snapshot = {
                "step": step + 1,
                "total_strokes": len(strokes),
                "stroke_symbol": stroke.symbol,
                "stroke_name": stroke_name,
                "stroke_rod": rod,
                "stroke_binary": binary,
                "stroke_raw_bits": raw_bits,
                "accumulated_rod": acc_with_spaces,
                "accumulated_bits": accumulated_rod,
                "candidates": list(candidates),
                "candidate_count": len(candidates),
                "best_guess": best,
                "best_confidence": best_conf,
                "is_final": (step == len(strokes) - 1),
                "is_identified": (len(candidates) == 1 and best and best.char == char_name),
            }
            snapshots.append(snapshot)

        return snapshots, char_obj


class AnimationRenderer:
    """
    动画渲染器 —— 把逐笔识别快照渲染为终端动画
    """

    @staticmethod
    def render_frame(snapshot, char_obj, frame_index, total_frames, width=70):
        """
        渲染单帧动画
        参数:
            snapshot: 步骤快照
            char_obj: 目标汉字对象
            frame_index: 当前帧序号
            total_frames: 总帧数
            width: 显示宽度
        """
        lines = []

        # 标题栏
        header = f"  逐笔识别  [{frame_index}/{total_frames}]  目标: 「{char_obj.char}」"
        lines.append("┌" + "─" * (width - 2) + "┐")
        lines.append(f"│{header:<{width - 2}}│")
        lines.append("├" + "─" * (width - 2) + "┤")

        # 区域1：视觉输入区（模拟"视网膜看到的东西"）
        s = snapshot
        lines.append("│  [眼] 视觉输入（视网膜信号）" + " " * (width - 24) + "│")
        
        # 裸 0101 信号
        raw_line = f"│     裸二进制: {s['stroke_raw_bits']}"
        raw_line += " " * (width - len(raw_line) - 1) + "│"
        lines.append(raw_line)

        # 算筭符号
        rod_line = f"│     算筭表示: {s['stroke_rod']}    ← 「{s['stroke_symbol']}」({s['stroke_name']})"
        rod_line += " " * (width - len(rod_line) - 1) + "│"
        lines.append(rod_line)

        lines.append("│" + " " * (width - 2) + "│")

        # 区域2：累积算筭码区
        lines.append("│  [计] 累积算筭码" + " " * (width - 16) + "│")
        acc = s["accumulated_rod"]
        if len(acc) > 50:
            acc = acc[:47] + "..."
        acc_line = f"│     {acc}"
        acc_line += " " * (width - len(acc_line) - 1) + "│"
        lines.append(acc_line)

        # 已接收笔画摘要
        strokes_done = " → ".join(
            f"{Stroke(cn).symbol}" for cn in char_obj.stroke_sequence[:s["step"]]
        )
        strokes_remaining = ""
        if s["step"] < len(char_obj.stroke_sequence):
            remaining = char_obj.stroke_sequence[s["step"]:]
            strokes_remaining = "  「" + "".join(Stroke(cn).symbol for cn in remaining) + "」待接收"
        done_line = f"│     已接收: {strokes_done}{strokes_remaining}"
        done_line = done_line[:width - 2]
        done_line += " " * (width - len(done_line) - 1) + "│"
        lines.append(done_line)

        lines.append("│" + " " * (width - 2) + "│")

        # 区域3：候选集缩小可视化
        lines.append("│  [搜] 候选字集（不断缩小）" + " " * (width - 22) + "│")
        
        if s["candidate_count"] <= 20:
            candidates_str = " ".join(f"「{c.char}」" for c in s["candidates"][:15])
            if len(s["candidates"]) > 15:
                candidates_str += f" ... (+{len(s['candidates']) - 15})"
        else:
            candidates_str = f"（共 {s['candidate_count']} 个候选，太多无法显示）"

        cand_line = f"│     [{s['candidate_count']}字] {candidates_str}"
        cand_line = cand_line[:width - 2]
        cand_line += " " * (width - len(cand_line) - 1) + "│"
        lines.append(cand_line)

        # 进度条（候选缩小的视觉化）
        total_chars = 130
        remaining = s["candidate_count"]
        eliminated = total_chars - remaining
        bar_len = 40
        filled = int(eliminated / total_chars * bar_len)
        bar = "#" * filled + "." * (bar_len - filled)
        bar_line = f"│     排除进度: [{bar}] {eliminated}/{total_chars}"
        bar_line += " " * (width - len(bar_line) - 1) + "│"
        lines.append(bar_line)

        lines.append("│" + " " * (width - 2) + "│")

        # 区域4：最佳猜测
        lines.append("│  [靶] 当前最佳猜测" + " " * (width - 18) + "│")
        if s["best_guess"]:
            conf_bar_len = 30
            conf_filled = int(s["best_confidence"] * conf_bar_len)
            conf_bar = "=" * conf_filled + "-" * (conf_bar_len - conf_filled)
            
            guess_line = f"│     「{s['best_guess'].char}」({s['best_guess'].meaning})"
            guess_line += " " * (width - len(guess_line) - 1) + "│"
            lines.append(guess_line)
            
            conf_line = f"│     置信度: [{conf_bar}] {s['best_confidence'] * 100:.0f}%"
            conf_line += " " * (width - len(conf_line) - 1) + "│"
            lines.append(conf_line)
        else:
            lines.append("│     (无匹配)" + " " * (width - 14) + "│")

        lines.append("├" + "─" * (width - 2) + "┤")

        # 底部状态
        if s["is_identified"]:
            # 识别成功！
            status = "*** 确定！就是这个字！"
            lines.append(f"│  {status:<{width - 2}}│")
            id_line = f"│  识别结果: 「{char_obj.char}」— {char_obj.meaning}"
            id_line += " " * (width - len(id_line) - 1) + "│"
            lines.append(id_line)
            lines.append(f"│  算筭编码: {char_obj.rod_string}")
            lines.append("│" + " " * (width - 2) + "│")
            lines.append("│  从 0101 到理解 —— 每一步都是计算" + " " * (width - 35) + "│")
        elif s["is_final"]:
            status = f"[完] 全部笔画已接收 ({s['total_strokes']}笔)"
            lines.append(f"│  {status:<{width - 2}}│")
        else:
            status = f"[>>] 等待下一笔... (已收{s['step']}/{s['total_strokes']}笔)"
            lines.append(f"│  {status:<{width - 2}}│")

        lines.append("└" + "─" * (width - 2) + "┘")

        return lines


def get_speed_delay(speed_name):
    """获取延迟时间（秒）"""
    speeds = {
        "slow": 1.5,
        "normal": 0.8,
        "fast": 0.3,
        "veryfast": 0.1,
    }
    return speeds.get(speed_name, 0.8)


def play_animation(char_name, speed="normal"):
    """
    播放一个汉字的逐笔识别动画
    """
    recognizer = StrokeByStrokeRecognizer()
    char_obj = recognizer.dict.get_character(char_name)

    if not char_obj:
        print(f"  [错误] 字典中未收录「{char_name}」")
        return

    snapshots, _ = recognizer.recognize(char_name, speed)
    if not snapshots:
        return

    width = 70
    delay = get_speed_delay(speed)

    print("\n" + "═" * width)
    print(f"  算筭码逐笔识别动画 —— 目标汉字「{char_name}」")
    print(f"  笔画序列：{' → '.join(char_obj.stroke_sequence)}")
    print(f"  笔画数：{char_obj.stroke_count}  算筭码位宽：{char_obj.bits}")
    print("═" * width)

    total_frames = len(snapshots)

    for i, snap in enumerate(snapshots):
        frame_lines = AnimationRenderer.render_frame(
            snap, char_obj, i + 1, total_frames, width
        )

        # 清屏（先上移足够行数）
        if i > 0:
            # 回到之前的帧开始位置（帧高度约 22 行）
            for _ in range(len(frame_lines) + 2):
                print("\033[F\033[K", end="")

        # 打印当前帧
        for line in frame_lines:
            print(line)

        time.sleep(delay)

        if snap["is_identified"] and i < total_frames - 1:
            # 识别出之后稍停
            time.sleep(delay * 2)

    # 最终报告
    print()
    print("─" * width)
    print(f"  【识别完成】「{char_obj.char}」— {char_obj.meaning}")
    print(f"  算筭码: {char_obj.rod_string}")
    print(f"  部首: {char_obj.radical}  造字法: {char_obj.category}")
    if char_obj.semantic_tags:
        print(f"  语义标签: {'、'.join(char_obj.semantic_tags)}")
    print("─" * width)


def show_step_by_step(char_name):
    """
    手动逐步模式 —— 按 Enter 逐笔推进
    """
    recognizer = StrokeByStrokeRecognizer()
    char_obj = recognizer.dict.get_character(char_name)

    if not char_obj:
        print(f"  [错误] 字典中未收录「{char_name}」")
        return

    snapshots, _ = recognizer.recognize(char_name)
    if not snapshots:
        return

    width = 70
    print("\n" + "═" * width)
    print(f"  逐笔识别（手动模式）—— 目标汉字「{char_name}」")
    print(f"  笔画序列：{' → '.join(char_obj.stroke_sequence)}")
    print(f"  按 Enter 逐笔推进, 输入 'q' 退出")
    print("═" * width)

    total = len(snapshots)
    for i, snap in enumerate(snapshots):
        input(f"\n  [按 Enter 接收第{i+1}/{total}笔] ")

        print(f"\n  {'─' * (width - 2)}")
        print(f"  第 {i+1} 笔: 「{snap['stroke_symbol']}」({snap['stroke_name']})")
        print(f"  算筭编码: {snap['stroke_rod']}  二进制: {snap['stroke_binary']}")
        print(f"  累积算筭: {snap['accumulated_rod']}")
        print(f"  候选字数: {snap['candidate_count']}", end="")

        if snap["candidate_count"] <= 15:
            print(f"  →  {' '.join(c.char for c in snap['candidates'])}")
        else:
            print()

        if snap["best_guess"]:
            conf = snap["best_confidence"]
            bar_len = 20
            filled = int(conf * bar_len)
            bar = "=" * filled + "-" * (bar_len - filled)
            print(f"  最佳猜测:  「{snap['best_guess'].char}」({snap['best_guess'].meaning})")
            print(f"  置信度:    [{bar}] {conf * 100:.0f}%")

            if snap["is_identified"]:
                print(f"\n  >>> 确定！这就是「{char_obj.char}」— {char_obj.meaning}")
                print(f"  >>> 算筭码完整编码：{char_obj.rod_string}")
                break

    print(f"\n  {'─' * (width - 2)}")
    print("  识别流程结束。")
    print(f"  从 130 个候选开始，经 {char_obj.stroke_count} 笔后确定了「{char_obj.char}」。")
    print(f"  这个过程就是「理解」。")


def demo_all(speed="normal"):
    """
    演示所有有趣的实验字
    选取的是一些能清楚展示「候选不断缩小」过程的字
    """
    demo_chars = [
        "木",  # 4笔, 简单象形
        "本",  # 5笔, 木加一横, 展示前缀匹配威力
        "日",  # 4笔, 常见象形
        "明",  # 8笔, 会意字, 前4笔=日
        "春",  # 9笔, 笔画多, 逐步缩小的过程很长
    ]

    width = 70
    print("=" * width)
    print("  算筭码逐笔识别 —— 全部演示")
    print(f"  速度: {speed}    共 {len(demo_chars)} 个实验字")
    print("=" * width)

    for char_name in demo_chars:
        print(f"\n\n{'>>>' * 12}")
        print(f"  实验字: 「{char_name}」")
        print(f"{'>>>' * 12}")
        input("  [按 Enter 开始]")
        play_animation(char_name, speed)


def show_comparison_panel():
    """
    并排对比面板 —— 展示多个字在逐笔识别过程中的候选变化
    不带动画，静态展示关键数据
    """
    recognizer = StrokeByStrokeRecognizer()

    width = 78
    print("=" * width)
    print("  逐笔识别对比面板")
    print("  展示不同汉字在识别过程中的候选集缩小曲线")
    print("=" * width)

    panel_chars = ["木", "本", "林", "明", "春"]
    all_snapshots = {}

    for cn in panel_chars:
        snaps, char_obj = recognizer.recognize(cn)
        if snaps:
            all_snapshots[cn] = {
                "snaps": snaps,
                "obj": char_obj,
                "strokes": char_obj.stroke_sequence,
            }

    # 表头
    print(f"\n  {'字':4s} {'笔数':4s} {'笔画序列':24s} {'每笔后候选数'}")
    print("  " + "─" * (width - 4))

    for cn in panel_chars:
        data = all_snapshots.get(cn)
        if not data:
            continue
        obj = data["obj"]
        snaps = data["snaps"]
        strokes_short = " → ".join(
            f"{Stroke(s).symbol}" for s in obj.stroke_sequence[:6]
        )
        if len(obj.stroke_sequence) > 6:
            strokes_short += "…"

        count_trace = []
        for s in snaps:
            count_trace.append(f"{s['candidate_count']:3d}")

        count_str = " → ".join(count_trace)

        print(f"  「{cn}」{obj.stroke_count:3d}画 {strokes_short:<24s} 候选: {count_str}")

    print()

    # 详细展示「本」的每笔细节（因为它是"木+一横"，最有代表性）
    print("─" * width)
    print(f"  详解「本」的识别过程（最有代表性的前缀匹配案例）")
    print("─" * width)

    data = all_snapshots.get("本")
    if data:
        obj = data["obj"]
        for snap in data["snaps"]:
            s = snap
            cand_display = ""
            if s["candidate_count"] <= 12:
                cand_display = f" [{', '.join(c.char for c in s['candidates'])}]"
            guess_info = ""
            if s["best_guess"]:
                guess_info = f"  ← 猜测「{s['best_guess'].char}」({s['best_confidence']*100:.0f}%)"
            print(f"    笔{s['step']}: {s['stroke_symbol']}({s['stroke_name']}) "
                  f"[{s['stroke_rod']}] → 候选{s['candidate_count']}{cand_display}{guess_info}")

    print()
    print("─" * width)
    print("  关键发现：")
    print("    前4笔「本」=「木」(完全重叠)→ 此时候选包含「木」「本」「林」等木部字")
    print("    第5笔「横」出现 → 排除「木」(木只有4笔)，确定为「本」")
    print("    这就是算筭码层面的「前缀匹配」：在算筭码中，前12位完全一致。")
    print("─" * width)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="算筭码逐笔识别动画")
    parser.add_argument("--char", "-c", type=str, help="指定要识别的汉字")
    parser.add_argument("--step", "-s", action="store_true", help="手动逐步模式")
    parser.add_argument("--speed", type=str, default="normal",
                        choices=["slow", "normal", "fast", "veryfast"],
                        help="动画速度")
    parser.add_argument("--demo-all", "-a", action="store_true", help="演示所有实验字")
    parser.add_argument("--panel", "-p", action="store_true", help="显示对比面板")

    args = parser.parse_args()

    if args.panel:
        show_comparison_panel()
        return

    if args.demo_all:
        demo_all(args.speed)
        return

    if args.char:
        if args.step:
            show_step_by_step(args.char)
        else:
            play_animation(args.char, args.speed)
        return

    # 默认：展示对比面板 + 演示一个字
    show_comparison_panel()

    print("\n" + "=" * 70)
    print("  交互选择")
    print("=" * 70)

    demo_opts = {
        "1": ("木", "4笔象形，最短路径"),
        "2": ("本", "5笔，木+一横，展示前缀匹配"),
        "3": ("明", "8笔会意，日+月合成"),
        "4": ("春", "9笔，长路径逐步缩小"),
        "a": ("all", "演示全部"),
        "q": ("quit", "退出"),
    }

    for key, (char, desc) in demo_opts.items():
        if key in ("a", "q"):
            label = {"a": "全部演示", "q": "退出"}[key]
            print(f"  [{key}] {label}")
        else:
            print(f"  [{key}] 「{char}」— {desc}")

    try:
        choice = input("\n请选择 (1/2/3/4/a/q): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n再见！")
        return

    if choice == "q":
        print("再见！")
        return
    elif choice == "a":
        demo_all("fast")
        return
    elif choice in demo_opts:
        char_name = demo_opts[choice][0]
        play_animation(char_name, "normal")

        # 也展示手动模式？
        print(f"\n  试试手动逐笔模式：py suanchou_animation.py -c {char_name} -s")
    else:
        print("无效选择，默认演示「本」")
        play_animation("本", "normal")

    print("\n" + "=" * 70)
    print("  运行 'py suanchou_animation.py --panel' 查看对比面板")
    print("  运行 'py suanchou_animation.py -c <字> -s' 手动逐笔探索")
    print("=" * 70)


if __name__ == "__main__":
    main()

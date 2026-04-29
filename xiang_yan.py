# -*- coding: utf-8 -*-
"""
象 演  (Xiang Yan)  ——  非过程式计算模型
============================================================
不执行指令。只演化配置。

核心：
  初象 = 初始形态
  约束 = 必须满足的条件
  势   = 当前未满足的冲突量
  变   = 形态为减少势而发生的改变
  象成 = 势为零的稳定形态（答案）

类比：
  冯·诺依曼：你开车 → 左转 → 右转 → 到了
  象演：      你描述目的地 → 地形自动把你滑过去

运行：py xiang_yan.py
"""

import itertools, random, time


class XiangYan:
    """
    象演引擎。
    不是VM。没有PC。没有指令。
    只有配置 + 约束 + 演化。
    """

    def __init__(self):
        self.config = []         # 当前配置（数组/网格/字阵）
        self.constraints = []    # (检查函数, 修复函数, 名称)
        self.history = []        # 每步的势值
        self.steps = 0

    def set_initial(self, config):
        """初象 — 设定初始形态"""
        self.config = list(config)
        self.history = [self._total_tension()]
        self.steps = 0

    def add_constraint(self, check, repair, name=""):
        """加约束 — 配置必须满足这个条件。若不满，修复函数减少冲突"""
        self.constraints.append((check, repair, name))

    def _total_tension(self):
        """势 — 当前未满足程度的总和"""
        total = 0
        for check, _, _ in self.constraints:
            broken = check(self.config)
            total += sum(broken.values()) if isinstance(broken, dict) else len(broken)
        return total

    def settle(self, max_steps=10000):
        """象成 — 让配置自行演化到势=0"""
        for _ in range(max_steps):
            tension = self._total_tension()
            self.history.append(tension)
            if tension == 0:
                return True  # 象成
            self._step()
            self.steps += 1
        return False  # 未收敛

    def _step(self):
        """变 — 一次演化步：找一个约束违反，修复它"""
        # 随机选一个违反的约束来修
        indices = list(range(len(self.constraints)))
        random.shuffle(indices)
        for i in indices:
            check, repair, _ = self.constraints[i]
            broken = check(self.config)
            if broken:
                repair(self.config, broken)
                return

    def show(self):
        print(f"  势: {'▓' * min(20, self._total_tension())}{'░' * max(0, 20 - self._total_tension())} {self._total_tension()}")
        if self._total_tension() == 0:
            print(f"  象成 — 配置已稳定")
        else:
            print(f"  演化中 — 势={self._total_tension()}")
        print(f"  形态: {self.config}")


# ═══════════════════════════════════════════════════════════
#  演示 1：排序 — 不写算法，只写约束
# ═══════════════════════════════════════════════════════════

def demo_sort():
    print("=" * 60)
    print("  象演 · 排序")
    print("  不写排序算法。只约束「左 ≤ 右」。")
    print("=" * 60)

    xy = XiangYan()

    # 初象：乱序
    xy.set_initial([9, 3, 7, 1, 5, 2, 8, 4, 6])

    # 约束：每个位置 ≤ 下一个位置
    def check_sorted(cfg):
        violations = []
        for i in range(len(cfg) - 1):
            if cfg[i] > cfg[i + 1]:
                violations.append(i)
        return violations

    def repair_sorted(cfg, violations):
        i = random.choice(violations)
        cfg[i], cfg[i + 1] = cfg[i + 1], cfg[i]

    xy.add_constraint(check_sorted, repair_sorted, "序")

    print(f"  初象: {xy.config}")
    print(f"  初始势: {xy._total_tension()}")
    xy.settle()
    print(f"  步数: {xy.steps}")
    print(f"  象成: {xy.config}")
    print(f"  演化曲线: {xy.history[:10]}...{xy.history[-5:]}")


# ═══════════════════════════════════════════════════════════
#  演示 2：补全 — 猜缺失的字
# ═══════════════════════════════════════════════════════════

def demo_completion():
    print("\n" + "=" * 60)
    print("  象演 · 补全")
    print("  木 _ 林 森 → 缺的应该是「本」")
    print("  约束：「相近位置的笔画前缀应一致」")
    print("=" * 60)

    # 每个字用4笔编码（横竖撇捺点折...）
    strokes_of = {
        "木": ["横", "竖", "撇", "捺"],
        "本": ["横", "竖", "撇", "捺", "横"],
        "林": ["横", "竖", "撇", "捺", "横", "竖", "撇", "捺"],
        "森": ["横", "竖", "撇", "捺", "横", "竖", "撇", "捺", "横", "竖", "撇", "捺"],
    }

    # 初象：木 ? 林 森
    xy = XiangYan()
    candidates = ["木", "本", "林", "森"]
    xy.set_initial(["木", "?", "林", "森"])

    def check_completion(cfg):
        # 如果 ? 还在，报违反
        if "?" in cfg:
            return {cfg.index("?"): 1}
        return {}

    def repair_completion(cfg, violations):
        idx = list(violations.keys())[0]
        prev = strokes_of.get(cfg[idx - 1], []) if idx > 0 else []
        nxt = strokes_of.get(cfg[idx + 1], []) if idx < len(cfg) - 1 else []
        best = "?"
        best_score = -1
        for c in candidates:
            s = strokes_of.get(c, [])
            score = 0
            for j, st in enumerate(s):
                if j < len(prev) and st == prev[j]:
                    score += 3
            for j, st in enumerate(s):
                if j < len(nxt) and st == nxt[j]:
                    score += 1
            if prev and nxt and len(prev) < len(s) < len(nxt):
                score += 5
            if (idx > 0 and c == cfg[idx - 1]) or (idx < len(cfg) - 1 and c == cfg[idx + 1]):
                score -= 20
            if score > best_score:
                best_score = score
                best = c
        cfg[idx] = best

    xy.add_constraint(check_completion, repair_completion, "补全")
    xy.settle()
    print(f"  初象: ['木', '?', '林', '森']")
    print(f"  象成: {xy.config}")
    print(f"  '本' = '木'+'—'，前四笔和木完全相同")


# ═══════════════════════════════════════════════════════════
#  演示 3：八卦生成 — 阴阳自组织
# ═══════════════════════════════════════════════════════════

def demo_bagua():
    print("\n" + "=" * 60)
    print("  象演 · 八卦生成")
    print("  约束：「上下相邻的爻应尽量不同」")
    print("  初象随机 → 自行排成规律形态")
    print("=" * 60)

    xy = XiangYan()
    # 初象：8×3 随机阴阳
    initial = [random.choice([1, 0]) for _ in range(24)]
    xy.set_initial(initial)

    def check_bagua(cfg):
        violations = []
        for i in range(len(cfg) - 1):
            # 相邻相同则违规
            if cfg[i] == cfg[i + 1]:
                violations.append(i)
        return violations

    def repair_bagua(cfg, violations):
        i = random.choice(violations)
        cfg[i] = 1 - cfg[i]

    xy.add_constraint(check_bagua, repair_bagua, "八卦交错")

    print(f"  初象: {''.join('—' if b else '--' for b in xy.config)}")
    print(f"  初始势: {xy._total_tension()}")
    xy.settle()
    print(f"  演化步数: {xy.steps}")
    print(f"  象成: {''.join('—' if b else '--' for b in xy.config)}")
    print(f"  这形成了交错的稳定形态")


# ═══════════════════════════════════════════════════════════
#  演示 4：字形趋近 — 看到一个字的过程
# ═══════════════════════════════════════════════════════════

def demo_target():
    print("\n" + "=" * 60)
    print("  象演 · 字形趋近")
    print("  初象随机 → 目标「木」(横竖撇捺)")
    print("  不是指令达成，是约束拉近")
    print("=" * 60)

    from extended_strokes import EXTENDED_STROKE_DATA
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # 取「木」的笔画编码
    mu_strokes = EXTENDED_STROKE_DATA["木"]["strokes"]
    # 用 3-bit 编码：横=000, 竖=001, 撇=010, 捺=011
    stroke_to_bits = {"横": [0, 0, 0], "竖": [0, 0, 1], "撇": [0, 1, 0],
                      "捺": [0, 1, 1], "点": [1, 0, 0], "折": [1, 0, 1],
                      "提": [1, 1, 0]}
    target_bits = []
    for s in mu_strokes:
        target_bits.extend(stroke_to_bits.get(s, [0, 0, 0]))

    xy = XiangYan()
    # 初象：随机12位
    initial = [random.choice([1, 0]) for _ in range(12)]
    xy.set_initial(initial)

    def check_target(cfg):
        # 返回到目标的距离
        violations = {}
        for i, (c, t) in enumerate(zip(cfg, target_bits)):
            if c != t:
                violations[i] = t
        return violations

    def repair_target(cfg, violations):
        # 随机修复一个不对的位
        i = random.choice(list(violations.keys()))
        cfg[i] = violations[i]

    xy.add_constraint(check_target, repair_target, "趋木")

    print(f"  目标: {''.join('—' if b else '--' for b in target_bits)}  (木)")
    print(f"  初象: {''.join('—' if b else '--' for b in xy.config)}")
    print(f"  初始势: {xy._total_tension()}")
    xy.settle()
    print(f"  步数: {xy.steps}")
    print(f"  象成: {''.join('—' if b else '--' for b in xy.config)}")
    print(f"  {'[OK] 完全匹配' if xy.config == target_bits else '[X] '}")


# ═══════════════════════════════════════════════════════════
#  核心对比：冯·诺依曼 vs 象演
# ═══════════════════════════════════════════════════════════

def comparison():
    print("\n" + "=" * 60)
    print("  冯·诺依曼  vs  象演")
    print("=" * 60)
    print("""
  排序 [9,3,7,1,5,2,8,4,6]：

  冯·诺依曼（快排）：
    pivot = 5
    分区 → [3,1,2,4] [5] [9,7,8,6]
    递归左 → [1,2,3,4]
    递归右 → [6,7,8,9]
    → 程序员必须精确控制每一步

  象演：
    约束：「左 ≤ 右」
    初象：[9,3,7,1,5,2,8,4,6]
    演化：每步随机交换一个违反的对
    → 约束自行驱动排序，程序员只描述目标

  区别不在结果（结果一样）。
  区别在思维方式：
    冯：「怎么做」
    象：「是什么」
""")

    print("  象演不做的事：")
    print("    没有跳转 (JMP/JE/JG)")
    print("    没有寄存器 (R0-R7)")
    print("    没有程序计数器 (PC)")
    print("    没有指令流水线")
    print("    没有算法设计")
    print()
    print("  象演做的事：")
    print("    你描述约束")
    print("    约束自己去找满足它的配置")
    print("    势趋零 = 答案")
    print()


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    random.seed(42)
    demo_sort()
    demo_completion()
    demo_bagua()
    demo_target()
    comparison()

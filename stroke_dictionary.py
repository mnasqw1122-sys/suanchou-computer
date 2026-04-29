# -*- coding: utf-8 -*-
"""
笔画-汉字字典 (Stroke Dictionary)
----------------------------------
建立笔画模式到汉字的映射关系。

每个汉字被表示为：
1. 其标准笔画序列（笔顺）
2. 语义信息（含义、部首、造字法、语义标签）
3. 算筭编码（笔画序列对应的 —/| 编码）

这个字典是连接「算筭计算」和「汉字理解」的关键桥梁。
"""

from stroke_encoder import Stroke, StrokeEncoder


class Character:
    """一个汉字的完整表示"""

    def __init__(self, char, stroke_sequence, meaning, radical="",
                 category="", semantic_tags=None, pinyin=""):
        """
        创建一个汉字条目
        参数:
            char: 汉字本身
            stroke_sequence: 标准笔画名称列表
            meaning: 基本含义
            radical: 部首
            category: 造字法（象形/指事/会意/形声）
            semantic_tags: 语义标签列表
            pinyin: 拼音
        """
        self.char = char
        self.stroke_sequence = stroke_sequence
        self.meaning = meaning
        self.radical = radical
        self.category = category
        self.semantic_tags = semantic_tags or []
        self.pinyin = pinyin
        self.stroke_count = len(stroke_sequence)

        # 编码缓存
        self._encoded = None
        self._rod_string = None

    def encode(self):
        """将笔画序列编码为算筭数"""
        if self._encoded is None:
            encoder = StrokeEncoder()
            self._encoded = encoder.encode_character(self.stroke_sequence)
            self._rod_string = self._encoded.to_rod_string()
        return self._encoded

    @property
    def rod_string(self):
        """获取算筭表示字符串"""
        if self._rod_string is None:
            self.encode()
        return self._rod_string

    @property
    def bits(self):
        """获取算筭位宽（笔画的3倍）"""
        return self.stroke_count * 3

    def __str__(self):
        return f"「{self.char}」({self.meaning})"

    def __repr__(self):
        return self.__str__()

    def summary(self):
        """返回汉字完整信息"""
        return (f"汉字：{self.char}\n"
                f"拼音：{self.pinyin}\n"
                f"含义：{self.meaning}\n"
                f"部首：{self.radical}\n"
                f"造字法：{self.category}\n"
                f"笔画数：{self.stroke_count}\n"
                f"笔画序列：{' → '.join(self.stroke_sequence)}\n"
                f"算筭编码：{self.rod_string}\n"
                f"语义标签：{'、'.join(self.semantic_tags)}")


# ============================================================
# 汉字笔画字典 —— 精心选取的常用汉字及其标准笔顺
# ============================================================

STROKE_DICT = {
    # ---------- 数字类 ----------
    "一": Character("一", ["横"], "数字一", "一", "指事", ["数字", "序数"], "yī"),
    "二": Character("二", ["横", "横"], "数字二", "二", "指事", ["数字", "序数"], "èr"),
    "三": Character("三", ["横", "横", "横"], "数字三", "一", "指事", ["数字", "序数"], "sān"),
    "十": Character("十", ["横", "竖"], "数字十", "十", "指事", ["数字", "序数", "完备"], "shí"),

    # ---------- 自然类（象形字） ----------
    "日": Character("日", ["竖", "折", "横", "横"], "太阳；白天", "日", "象形", ["天体", "光明", "时间"], "rì"),
    "月": Character("月", ["撇", "折", "横", "横"], "月亮；月份", "月", "象形", ["天体", "时间", "阴柔"], "yuè"),
    "山": Character("山", ["竖", "折", "竖"], "山岳", "山", "象形", ["自然", "高耸", "稳固"], "shān"),
    "水": Character("水", ["竖", "钩", "横", "撇", "捺"], "水流；液体", "水", "象形", ["自然", "流动", "柔韧"], "shuǐ"),
    "火": Character("火", ["点", "撇", "撇", "捺"], "火焰", "火", "象形", ["自然", "热能", "光明"], "huǒ"),
    "木": Character("木", ["横", "竖", "撇", "捺"], "树木；木材", "木", "象形", ["植物", "材料", "生长"], "mù"),
    "石": Character("石", ["横", "撇", "竖", "折", "横"], "石头", "石", "象形", ["矿物", "坚硬", "稳固"], "shí"),
    "田": Character("田", ["竖", "折", "横", "竖", "横"], "田地", "田", "象形", ["土地", "农业", "种植"], "tián"),
    "雨": Character("雨", ["横", "竖", "折", "竖", "点", "点", "点", "点"], "雨水", "雨", "象形", ["自然", "降水", "滋润"], "yǔ"),
    "土": Character("土", ["横", "竖", "横"], "泥土；大地", "土", "象形", ["土地", "自然", "基础"], "tǔ"),

    # ---------- 人类相关（象形/会意） ----------
    "人": Character("人", ["撇", "捺"], "人类；他人", "人", "象形", ["生命", "社会", "主体"], "rén"),
    "大": Character("大", ["横", "撇", "捺"], "大小之大；伟大", "大", "象形", ["尺度", "宏大", "程度"], "dà"),
    "天": Character("天", ["横", "横", "撇", "捺"], "天空；上天；自然", "大", "指事", ["自然", "至高", "宇宙"], "tiān"),
    "子": Character("子", ["折", "竖", "横"], "孩子；子嗣", "子", "象形", ["人类", "后代", "新生"], "zǐ"),
    "女": Character("女", ["折", "撇", "横"], "女性；女儿", "女", "象形", ["人类", "阴性", "柔美"], "nǚ"),
    "心": Character("心", ["点", "钩", "点", "点"], "心脏；心灵；情感", "心", "象形", ["器官", "情感", "思想"], "xīn"),
    "目": Character("目", ["竖", "折", "横", "横", "横"], "眼睛；观看", "目", "象形", ["器官", "视觉", "观察"], "mù"),
    "手": Character("手", ["撇", "横", "横", "竖"], "手掌；动手", "手", "象形", ["器官", "动作", "技能"], "shǒu"),
    "口": Character("口", ["竖", "折", "横"], "嘴巴；开口", "口", "象形", ["器官", "语言", "通道"], "kǒu"),

    # ---------- 方位与状态（指事/会意） ----------
    "上": Character("上", ["竖", "横", "横"], "上方；向上", "一", "指事", ["方位", "上升", "高位"], "shàng"),
    "下": Character("下", ["横", "竖", "点"], "下方；向下", "一", "指事", ["方位", "下降", "低位"], "xià"),
    "中": Character("中", ["竖", "折", "横", "竖"], "中间；内部", "丨", "指事", ["方位", "平衡", "核心"], "zhōng"),
    "小": Character("小", ["竖", "点", "点"], "微小；幼小", "小", "象形", ["尺度", "谦逊", "精细"], "xiǎo"),
    "不": Character("不", ["横", "撇", "竖", "点"], "否定；不是", "一", "指事", ["逻辑", "否定", "排除"], "bù"),

    # ---------- 动作与能力（会意/形声） ----------
    "力": Character("力", ["折", "撇"], "力量；能力", "力", "象形", ["力量", "动作", "能力"], "lì"),
    "工": Character("工", ["横", "竖", "横"], "工作；工匠", "工", "象形", ["劳动", "技能", "制造"], "gōng"),
    "文": Character("文", ["点", "横", "撇", "捺"], "文字；文化", "文", "象形", ["文化", "书写", "知识"], "wén"),
    "言": Character("言", ["点", "横", "横", "横", "竖", "折", "横"],
                    "言语；说话", "言", "会意", ["语言", "沟通", "表达"], "yán"),

    # ---------- 物质与价值 ----------
    "金": Character("金", ["撇", "捺", "横", "横", "竖", "点", "撇", "横"],
                    "金属；黄金", "金", "形声", ["矿物", "价值", "坚固"], "jīn"),
    "玉": Character("玉", ["横", "横", "竖", "横", "点"], "玉石；珍宝", "玉", "象形", ["矿物", "珍贵", "纯洁"], "yù"),
    "白": Character("白", ["撇", "竖", "折", "横", "横"], "白色；明亮；清楚", "白", "象形", ["颜色", "光明", "纯洁"], "bái"),
    "米": Character("米", ["点", "撇", "横", "竖", "撇", "捺"], "大米；谷物", "米", "象形", ["食物", "农业", "基础"], "mǐ"),
    "竹": Character("竹", ["撇", "横", "竖", "撇", "横", "竖"],
                    "竹子", "竹", "象形", ["植物", "坚韧", "节操"], "zhú"),

    # ---------- 复合语义（会意字） ----------
    "本": Character("本", ["横", "竖", "撇", "捺", "横"],
                    "根本；本源", "木", "指事", ["基础", "本质", "起源"], "běn"),
    "林": Character("林", ["横", "竖", "撇", "捺", "横", "竖", "撇", "捺"],
                    "树林", "木", "会意", ["植物", "众多", "聚集"], "lín"),
    "明": Character("明", ["竖", "折", "横", "横", "撇", "折", "横", "横"],
                    "光明；明白；明日", "日", "会意", ["光明", "智慧", "时间"], "míng"),
}


class StrokeDictionary:
    """
    笔画字典 —— 提供笔画模式到汉字的查找功能
    """

    def __init__(self):
        self._characters = dict(STROKE_DICT)
        # 构建索引：笔画模式 → 汉字列表
        self._stroke_index = {}
        # 构建索引：语义标签 → 汉字列表
        self._tag_index = {}
        # 构建索引：算筭编码子串 → 汉字列表
        self._rod_index = {}
        # 构建索引：精确算筭编码 → 汉字（用于精确匹配）
        self._rod_exact_index = {}
        # 同笔顺汉字记录
        self._stroke_homographs = {}

        self._build_indexes()

    def _build_indexes(self):
        """构建各种查找索引"""
        for char_name, char_obj in self._characters.items():
            # 笔画序列索引
            stroke_key = tuple(char_obj.stroke_sequence)
            if stroke_key not in self._stroke_index:
                self._stroke_index[stroke_key] = []
            self._stroke_index[stroke_key].append(char_obj)

            # 语义标签索引
            for tag in char_obj.semantic_tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                self._tag_index[tag].append(char_obj)

            # 算筭编码索引（按笔画子串）
            rod = char_obj.rod_string.replace(" ", "")
            for length in range(3, len(rod) + 1, 3):
                prefix = rod[:length]
                if prefix not in self._rod_index:
                    self._rod_index[prefix] = []
                if char_obj not in self._rod_index[prefix]:
                    self._rod_index[prefix].append(char_obj)
            # 精确算筭编码索引（支持同笔顺的多字）
            if rod not in self._rod_exact_index:
                self._rod_exact_index[rod] = []
            self._rod_exact_index[rod].append(char_obj)
            if len(self._rod_exact_index[rod]) > 1:
                names = [c.char for c in self._rod_exact_index[rod]]
                self._stroke_homographs[rod] = names

    def get_character(self, char_name):
        """
        按汉字名称获取字符对象
        """
        return self._characters.get(char_name)

    def find_by_strokes(self, stroke_sequence):
        """
        通过笔画序列查找汉字
        参数:
            stroke_sequence: 笔画名称列表
        返回:
            匹配的汉字列表
        """
        return self._stroke_index.get(tuple(stroke_sequence), [])

    def find_by_stroke_count(self, count):
        """
        按笔画数量查找汉字
        """
        result = []
        for char_obj in self._characters.values():
            if char_obj.stroke_count == count:
                result.append(char_obj)
        return result

    def find_by_tag(self, tag):
        """
        按语义标签查找汉字
        """
        return self._tag_index.get(tag, [])

    def find_by_rod_prefix(self, rod_string):
        """
        按算筭编码前缀（部分笔画模式）查找汉字
        参数:
            rod_string: 算筭符号字符串（如 "||—"）
        返回:
            匹配的汉字列表（按其编码以此前缀开头的）
        """
        clean = rod_string.replace(" ", "")
        return self._rod_index.get(clean, [])

    def find_by_rod_exact(self, rod_string):
        """
        按精确算筭编码查找汉字
        参数:
            rod_string: 算筭符号字符串
        返回:
            精确匹配的 Character 对象列表（可能有同笔顺多字）
        """
        clean = rod_string.replace(" ", "")
        return self._rod_exact_index.get(clean, [])

    def find_by_stroke_pattern(self, stroke_pattern):
        """
        按笔画模式（部分笔画序列）查找汉字
        参数:
            stroke_pattern: 笔画名称列表（可以是部分序列）
        返回:
            笔画序列以此模式开头的汉字列表
        """
        result = []
        pattern_len = len(stroke_pattern)
        for char_obj in self._characters.values():
            if char_obj.stroke_sequence[:pattern_len] == stroke_pattern:
                result.append(char_obj)
        return result

    def find_related_by_strokes(self, char_obj, match_length=2):
        """
        查找与给定汉字共享笔画前缀的其他汉字
        这模拟了「看到部分笔画，联想相关汉字」的过程
        参数:
            char_obj: 汉字对象
            match_length: 匹配的前缀笔画数
        返回:
            相关汉字列表
        """
        prefix = char_obj.stroke_sequence[:match_length]
        return self.find_by_stroke_pattern(prefix)

    def find_related_by_tags(self, char_obj):
        """
        查找与给定汉字共享语义标签的其他汉字
        这模拟了语义联想
        """
        related = set()
        for tag in char_obj.semantic_tags:
            for other in self.find_by_tag(tag):
                if other.char != char_obj.char:
                    related.add(other)
        return list(related)

    def list_all(self):
        """列出所有汉字"""
        return list(self._characters.values())

    def show_dictionary_stats(self):
        """显示字典统计信息"""
        chars = self.list_all()
        print(f"\n[字典] 字典统计：")
        print(f"   收录汉字：{len(chars)} 个")
        print(f"   笔画索引条目：{len(self._stroke_index)}")
        print(f"   语义标签数：{len(self._tag_index)}")

        print(f"\n   按造字法分类：")
        categories = {}
        for c in chars:
            cat = c.category if c.category else "未知"
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items()):
            print(f"     {cat}：{count} 字")

        print(f"\n   按笔画数分布：")
        by_count = {}
        for c in chars:
            by_count[c.stroke_count] = by_count.get(c.stroke_count, 0) + 1
        for count in sorted(by_count.keys()):
            print(f"     {count}画：{by_count[count]} 字")


def demo_dictionary():
    """
    演示笔画字典功能
    """
    print("=" * 60)
    print("  笔画-汉字字典 (Stroke Dictionary) 演示")
    print("=" * 60)

    dic = StrokeDictionary()
    dic.show_dictionary_stats()

    # 查找演示
    print("\n" + "=" * 60)
    print("  查找功能演示")
    print("=" * 60)

    # 通过笔画模式查找
    print("\n[查找] 查找笔画模式 [横, 竖] 开头的字：")
    results = dic.find_by_stroke_pattern(["横", "竖"])
    for r in results:
        print(f"   {r} [笔画：{' → '.join(r.stroke_sequence)}] [标签：{'、'.join(r.semantic_tags)}]")

    # 语义关联
    print("\n[关联] 查找与「日」共享语义标签的字：")
    ri = dic.get_character("日")
    related = dic.find_related_by_tags(ri)
    for r in related:
        print(f"   {r} ← 共有标签")

    # 字形关联
    print("\n[关联] 查找与「木」共享笔画前缀的字：")
    mu = dic.get_character("木")
    related_stroke = dic.find_related_by_strokes(mu, match_length=2)
    for r in related_stroke:
        if r.char != "木":
            print(f"   {r} [共同前缀：{' → '.join(mu.stroke_sequence[:2])}]")

    print("\n" + "=" * 60)
    return dic


if __name__ == "__main__":
    demo_dictionary()

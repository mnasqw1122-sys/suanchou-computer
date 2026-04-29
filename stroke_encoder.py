# -*- coding: utf-8 -*-
"""
笔画编码系统 (Stroke Encoder)
-------------------------------
将汉字拆解为基本笔画，并用 3-bit 二进制编码。
每种笔画对应一个唯一的 3 位编码，从而将整个汉字转化为一串二进制位。

这样，汉字就变成了一串可以在算筭计算机上处理的 — 和 | 序列，
实现了「字形 → 笔画 → 二进制 → 算筭」的完整映射链。

基本的八种笔画（永字八法 + 折笔）：
  横(一) 竖(丨) 撇(丿) 捺(乀) 点(丶) 折(乙) 钩(亅) 提(/)

编码规则（3-bit 二进制）：
  横 = 000   竖 = 001   撇 = 010   捺 = 011
  点 = 100   折 = 101   钩 = 110   提 = 111
"""

from counting_rod_computer import CountingRodBit, CountingRodNumber, CountingRodComputer


class Stroke:
    """单个笔画"""

    # 八种基本笔画定义
    # 注意：符号使用 GBK 编码兼容字符，避免 Unicode 扩展区字符
    STROKE_TYPES = {
        "横": {"code": 0, "symbol": "一", "description": "水平横线"},
        "竖": {"code": 1, "symbol": "丨", "description": "垂直竖线"},
        "撇": {"code": 2, "symbol": "丿", "description": "向左下斜"},
        "捺": {"code": 3, "symbol": "乀", "description": "向右下斜"},
        "点": {"code": 4, "symbol": "丶", "description": "短小点画"},
        "折": {"code": 5, "symbol": "乙", "description": "转折笔画"},
        "钩": {"code": 6, "symbol": "亅", "description": "弯钩笔画"},
        "提": {"code": 7, "symbol": "/", "description": "向右上提"},
    }

    # 编码到笔画名的反向映射
    CODE_TO_NAME = {v["code"]: k for k, v in STROKE_TYPES.items()}

    def __init__(self, stroke_name_or_code):
        """
        创建笔画
        参数:
            stroke_name_or_code: 笔画名称（如"横"）或编码（0-7）
        """
        if isinstance(stroke_name_or_code, str):
            if stroke_name_or_code in self.STROKE_TYPES:
                self.name = stroke_name_or_code
                self.code = self.STROKE_TYPES[stroke_name_or_code]["code"]
            else:
                raise ValueError(f"未知笔画: {stroke_name_or_code}")
        elif isinstance(stroke_name_or_code, int):
            if 0 <= stroke_name_or_code <= 7:
                self.code = stroke_name_or_code
                self.name = self.CODE_TO_NAME[stroke_name_or_code]
            else:
                raise ValueError(f"笔画编码超出范围: {stroke_name_or_code}")

    @property
    def symbol(self):
        """笔画的可视化符号"""
        return self.STROKE_TYPES[self.name]["symbol"]

    def to_bits(self):
        """
        将笔画转换为 3 位算筭位列表
        例如：横(code=0) → [|, |, |]  即三位断
             提(code=7) → [—, —, —]  即三位通
        """
        bits = []
        for i in range(3):
            bit_value = (self.code >> i) & 1
            bits.append(CountingRodBit(bit_value))
        return bits

    def to_rod_string(self):
        """以算筭符号显示笔画编码"""
        bits = self.to_bits()
        return "".join(str(b) for b in bits)

    @staticmethod
    def from_bits(bit_list):
        """从 3 个算筭位恢复笔画"""
        code = 0
        for i, bit in enumerate(bit_list[:3]):
            if bit.is_on:
                code |= (1 << i)
        return Stroke(code)

    def __str__(self):
        return f"{self.symbol}({self.name})"

    def __repr__(self):
        return self.__str__()


class StrokeEncoder:
    """
    笔画编码器 —— 将汉字与二进制/算筭之间进行互转
    """

    def __init__(self):
        pass

    def encode_character(self, stroke_sequence):
        """
        将笔画序列编码为算筭数
        参数:
            stroke_sequence: 笔画名称列表，如 ["横", "竖", "横", "折", ...]
        返回:
            CountingRodNumber: 整个汉字笔画序列对应的算筭数
        """
        all_bits = []
        for stroke_name in stroke_sequence:
            stroke = Stroke(stroke_name)
            all_bits.extend(stroke.to_bits())
        result = CountingRodNumber(0)
        result._bits = all_bits
        return result

    def encode_text(self, stroke_sequences):
        """
        将一段文字（多个汉字的笔画序列列表）编码为算筭数
        参数:
            stroke_sequences: 多个汉字的笔画序列的列表
        返回:
            CountingRodNumber: 整段文字对应的算筭数
        """
        all_bits = []
        for seq in stroke_sequences:
            for stroke_name in seq:
                stroke = Stroke(stroke_name)
                all_bits.extend(stroke.to_bits())
        result = CountingRodNumber(0)
        result._bits = all_bits
        return result

    def decode_to_strokes(self, counting_rod_number):
        """
        从算筭数解码回笔画序列
        每 3 位为一组，对应一个笔画
        参数:
            counting_rod_number: 算筭数
        返回:
            笔画名称列表
        """
        bits = counting_rod_number._bits
        strokes = []
        for i in range(0, len(bits), 3):
            if i + 3 <= len(bits):
                chunk = bits[i:i+3]
                stroke = Stroke.from_bits(chunk)
                strokes.append(stroke.name)
        return strokes

    def rod_string_to_strokes(self, rod_string):
        """
        将算筭符号字符串解析为笔画序列
        注意：显示的算筭串是 MSB-first（高位在前），
        且 to_rod_string() 用 reversed() 反转了整个位序列。
        因此解码时需：
        1. 每3位组内翻转（显示MSB→存储LSB）
        2. 笔画组之间翻转（reversed 导致整串倒序）
        参数:
            rod_string: 由 — 和 | 组成的字符串
        返回:
            笔画名称列表
        """
        clean = rod_string.replace(" ", "")
        strokes = []
        for i in range(0, len(clean), 3):
            chunk = clean[i:i+3]
            if len(chunk) == 3:
                bits = CountingRodBit.from_rod(chunk)
                bits.reverse()
                stroke = Stroke.from_bits(bits)
                strokes.append(stroke.name)
        # 整串被 reversed() 反转过，笔画的组间顺序也需要翻转回来
        strokes.reverse()
        return strokes

    def show_character_encoding(self, char_name, stroke_sequence):
        """
        展示一个汉字的完整编码过程
        参数:
            char_name: 汉字
            stroke_sequence: 笔画序列
        """
        print(f"\n[笔画] 汉字「{char_name}」的笔画编码：")
        print(f"   笔画序列：{' → '.join(stroke_sequence)}")

        encoded = self.encode_character(stroke_sequence)
        print(f"   算筭编码：{encoded.to_rod_string()}")

        # 展示每个笔画的编码
        print(f"   逐笔画分解：")
        all_bits = encoded._bits
        for i in range(0, len(all_bits), 3):
            chunk_bits = all_bits[i:i+3]
            stroke = Stroke.from_bits(chunk_bits)
            rod_str = "".join(str(b) for b in chunk_bits)
            print(f"     {stroke.symbol}({stroke.name}) → 算筭 [{rod_str}]")

        print(f"   总位宽：{len(encoded._bits)} 位")
        return encoded


def demo_stroke_encoding():
    """
    演示笔画编码系统
    """
    print("=" * 60)
    print("  笔画编码系统 (Stroke Encoder) 演示")
    print("  汉字笔画 → 3-bit 二进制 → 算筭符号")
    print("=" * 60)

    encoder = StrokeEncoder()

    # 展示所有基本笔画及其编码
    print("\n[列表] 八种基本笔画的算筭编码：")
    print("  笔画   符号    编码(bin)    算筭表示")
    print("  " + "-" * 45)
    for name, info in Stroke.STROKE_TYPES.items():
        stroke = Stroke(name)
        rod = stroke.to_rod_string()
        bin_str = f"{info['code']:03b}"
        print(f"  {name}     {info['symbol']}      {bin_str}         {rod}")

    # 编码示例汉字
    print("\n" + "=" * 60)

    # 示例：「人」= 撇 + 捺
    encoder.show_character_encoding("人", ["撇", "捺"])

    # 示例：「天」= 横 + 横 + 撇 + 捺
    encoder.show_character_encoding("天", ["横", "横", "撇", "捺"])

    # 示例：「木」= 横 + 竖 + 撇 + 捺
    encoder.show_character_encoding("木", ["横", "竖", "撇", "捺"])

    # 示例：「水」= 竖 + 钩 + 横 + 撇 + 捺
    encoder.show_character_encoding("水", ["竖", "钩", "横", "撇", "捺"])

    # 测试编解码往返
    print("\n[往返] 编解码往返测试：")
    test_seq = ["横", "竖", "撇", "捺", "点", "折", "钩", "提"]
    encoded = encoder.encode_character(test_seq)
    decoded = encoder.decode_to_strokes(encoded)
    print(f"   原始笔画：{test_seq}")
    print(f"   算筭编码：{encoded.to_rod_string()}")
    print(f"   解码结果：{decoded}")
    print(f"   一致性：{'[OK] 通过' if test_seq == decoded else '[FAIL] 失败'}")

    print("\n" + "=" * 60)
    print("  结论：每个汉字笔画对应 3 位算筭信号，")
    print("  整个汉字的字形可以用一串 — 和 | 精确表示。")
    print("=" * 60)

    return encoder


if __name__ == "__main__":
    demo_stroke_encoding()

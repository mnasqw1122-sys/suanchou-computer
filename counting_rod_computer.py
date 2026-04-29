# -*- coding: utf-8 -*-
"""
算筭计算核心 (Counting Rod Computer)
------------------------------------
基于古代中国算筭原理的计算引擎。
—  表示「通」(on, 1)，对应二进制 1
|  表示「断」(off, 0)，对应二进制 0

算筭的横竖交替表示不同位值，这里我们将它映射到二进制计算模型。
每一位用 — 或 | 表示，从而可以用算筭完成所有现代计算机的基本运算。
"""


class CountingRodBit:
    """算筭中的单独一位"""

    ON_SYMBOL = "—"
    OFF_SYMBOL = "|"

    def __init__(self, value):
        """
        初始化一个算筭位
        参数:
            value: 可以是整数 0/1，或符号 "—"/"|"
        """
        if isinstance(value, int):
            self._value = 1 if value else 0
        elif isinstance(value, str):
            self._value = 1 if value.strip() == self.ON_SYMBOL else 0
        else:
            self._value = 0

    @property
    def is_on(self):
        """该位是否为通（1）"""
        return self._value == 1

    @property
    def is_off(self):
        """该位是否为断（0）"""
        return self._value == 0

    @property
    def binary(self):
        """返回二进制数值 0 或 1"""
        return self._value

    def __str__(self):
        """可视化表示为 — 或 |"""
        return self.ON_SYMBOL if self._value else self.OFF_SYMBOL

    def __repr__(self):
        return f"位({str(self)})"

    def __eq__(self, other):
        if isinstance(other, CountingRodBit):
            return self._value == other._value
        return NotImplemented

    def flip(self):
        """翻转该位：通变断，断变通"""
        self._value = 1 - self._value
        return self

    @staticmethod
    def from_rod(rod_str):
        """从算筭符号字符串创建位列表"""
        bits = []
        for ch in rod_str:
            if ch in (CountingRodBit.ON_SYMBOL, CountingRodBit.OFF_SYMBOL):
                bits.append(CountingRodBit(ch))
        return bits


class CountingRodNumber:
    """
    算筭数 —— 用算筭位序列表示的数字。
    采用二进制表示，左边为高位（中国古代算筭中左边为高位）。
    """

    def __init__(self, value, bit_width=None):
        """
        初始化算筭数
        参数:
            value: 整数、二进制字符串、算筭符号字符串、或 CountingRodBit 列表
            bit_width: 固定位宽（不够则高位补 |）
        """
        if isinstance(value, int):
            self._from_int(value, bit_width)
        elif isinstance(value, str):
            # 判断是否为算筭符号字符串
            if all(c in (CountingRodBit.ON_SYMBOL, CountingRodBit.OFF_SYMBOL) for c in value):
                self._bits = CountingRodBit.from_rod(value)
                self._bits.reverse()  # 字符串左高右低 → 列表索引0为低位
            else:
                # 尝试作为二进制字符串解析
                clean = value.replace(" ", "")
                rods = []
                for ch in clean:
                    if ch == "1":
                        rods.append(CountingRodBit.ON_SYMBOL)
                    elif ch == "0":
                        rods.append(CountingRodBit.OFF_SYMBOL)
                self._bits = CountingRodBit.from_rod("".join(rods))
                self._bits.reverse()
        elif isinstance(value, list):
            self._bits = list(value)
        else:
            self._bits = []

    def _from_int(self, num, bit_width=None):
        """从整数构建算筭数"""
        if num == 0:
            self._bits = [CountingRodBit(0)]
        else:
            self._bits = []
            while num > 0:
                self._bits.append(CountingRodBit(num & 1))
                num >>= 1
        if bit_width is not None:
            while len(self._bits) < bit_width:
                self._bits.append(CountingRodBit(0))
            self._bits = self._bits[:bit_width]

    @property
    def bit_width(self):
        """返回位宽"""
        return len(self._bits)

    def to_int(self):
        """转换为整数"""
        result = 0
        for i, bit in enumerate(self._bits):
            if bit.is_on:
                result |= (1 << i)
        return result

    def to_binary_string(self):
        """转换为二进制字符串（高位在前）"""
        return "".join(str(bit.binary) for bit in reversed(self._bits))

    def to_rod_string(self):
        """
        以古代算筭方式可视化：
        从高位到低位依次显示，用 — 和 | 表示。
        模仿古代算筭的横竖交替排布风格。
        """
        result = []
        for i, bit in enumerate(reversed(self._bits)):
            result.append(str(bit))
        return " ".join(result)

    def to_ancient_style(self):
        """
        以古代算筭的经典排布方式显示：
        个位用纵式（|），十位用横式（—），百位用纵式，千位用横式...
        即：个位（低位）用 |, 十位用 —, 以此交替
        注意：算筭记数法中 0 用空位 ○ 表示
        """
        result = []
        # self._bits[0] 是最低位（个位）
        for i in range(len(self._bits) - 1, -1, -1):
            bit = self._bits[i]
            position = i  # 位序号：个位=0, 十位=1, 百位=2...
            if bit.is_on:
                if position % 2 == 0:
                    result.append("|")  # 个位、百位...用纵式
                else:
                    result.append("—")  # 十位、千位...用横式
            else:
                result.append("○")  # 零用空位表示
        return " ".join(result)

    def __str__(self):
        return f"算筭[{self.to_rod_string()}] = {self.to_int()}"

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self._bits)


class CountingRodComputer:
    """
    算筭计算机 —— 只用 — 和 | 完成所有运算。
    这是整个系统的计算核心，所有运算都通过算筭位的翻转和组合来实现。
    """

    @staticmethod
    def make_number(value, bit_width=8):
        """
        创建一个算筭数
        参数:
            value: 整数
            bit_width: 位宽（默认8位，如同一个字节）
        """
        return CountingRodNumber(value, bit_width)

    @staticmethod
    def add(a, b):
        """
        算筭加法
        使用算筭位级别的全加器逻辑：
        - 半加器：本位 = A异或B, 进位 = A与B
        - 全加器：考虑低位进位
        全部用 — 和 | 来完成
        """
        a_bits = a._bits[:]
        b_bits = b._bits[:]
        max_len = max(len(a_bits), len(b_bits))
        while len(a_bits) < max_len:
            a_bits.append(CountingRodBit(0))
        while len(b_bits) < max_len:
            b_bits.append(CountingRodBit(0))

        result_bits = []
        carry = CountingRodBit(0)

        for i in range(max_len):
            # 全加器：sum = a XOR b XOR carry
            xor_ab = CountingRodBit(a_bits[i].binary ^ b_bits[i].binary)
            sum_bit = CountingRodBit(xor_ab.binary ^ carry.binary)

            # 进位 = (a AND b) OR (carry AND (a XOR b))
            ab = CountingRodBit(a_bits[i].binary & b_bits[i].binary)
            cxor = CountingRodBit(carry.binary & xor_ab.binary)
            new_carry = CountingRodBit(ab.binary | cxor.binary)

            result_bits.append(sum_bit)
            carry = new_carry

        if carry.is_on:
            result_bits.append(carry)

        result = CountingRodNumber(0)
        result._bits = result_bits
        return result

    @staticmethod
    def subtract(a, b):
        """
        算筭减法
        通过补码加法实现：A - B = A + (~B + 1)
        """
        # 对 B 取反
        not_b_bits = [CountingRodBit(1 - bit.binary) for bit in b._bits]
        # 扩展到与 A 相同位宽
        while len(not_b_bits) < len(a._bits):
            not_b_bits.append(CountingRodBit(1))
        not_b = CountingRodNumber(0)
        not_b._bits = not_b_bits

        # ~B + 1
        one = CountingRodNumber(1)
        neg_b = CountingRodComputer.add(not_b, one)

        # A + (-B)
        result = CountingRodComputer.add(a, neg_b)
        # 截断到相同位宽
        if len(result._bits) > len(a._bits):
            result._bits = result._bits[:len(a._bits)]
        return result

    @staticmethod
    def multiply(a, b):
        """
        算筭乘法
        使用移位相加法：逐位检查乘数，遇通(—)则累加
        """
        result = CountingRodNumber(0)
        for i, bit in enumerate(b._bits):
            if bit.is_on:
                shifted_bits = [CountingRodBit(0)] * i + a._bits[:]
                shifted = CountingRodNumber(0)
                shifted._bits = shifted_bits
                result = CountingRodComputer.add(result, shifted)
        return result

    @staticmethod
    def divide(a, b):
        """
        算筭除法（整数除法）
        使用移位减法：从高位开始，够减则商位置通(—)
        """
        if b.to_int() == 0:
            raise ValueError("算筭除法：除数不能为零")
        if a.to_int() < b.to_int():
            return CountingRodNumber(0), a

        quotient = CountingRodNumber(0)
        remainder = CountingRodNumber(a.to_int(), max(a.bit_width, b.bit_width))

        # 将除数对齐到被除数的最高有效位
        # 使用实际有效位长而非填充位宽
        shift = a.to_int().bit_length() - b.to_int().bit_length()
        if shift < 0:
            shift = 0

        for i in range(shift, -1, -1):
            shifted_bits = [CountingRodBit(0)] * i + b._bits[:]
            shifted = CountingRodNumber(0)
            shifted._bits = shifted_bits

            if remainder.to_int() >= shifted.to_int():
                remainder = CountingRodComputer.subtract(remainder, shifted)
                quotient_bits = quotient._bits[:]
                while len(quotient_bits) <= i:
                    quotient_bits.append(CountingRodBit(0))
                quotient_bits[i] = CountingRodBit(1)
                quotient._bits = quotient_bits

        return quotient, remainder

    @staticmethod
    def and_op(a, b):
        """算筭按位与运算：两位皆通则通，否则断"""
        result_bits = []
        max_len = max(len(a._bits), len(b._bits))
        for i in range(max_len):
            va = a._bits[i].binary if i < len(a._bits) else 0
            vb = b._bits[i].binary if i < len(b._bits) else 0
            result_bits.append(CountingRodBit(va & vb))
        result = CountingRodNumber(0)
        result._bits = result_bits
        return result

    @staticmethod
    def or_op(a, b):
        """算筭按位或运算：任一位通则通"""
        result_bits = []
        max_len = max(len(a._bits), len(b._bits))
        for i in range(max_len):
            va = a._bits[i].binary if i < len(a._bits) else 0
            vb = b._bits[i].binary if i < len(b._bits) else 0
            result_bits.append(CountingRodBit(va | vb))
        result = CountingRodNumber(0)
        result._bits = result_bits
        return result

    @staticmethod
    def xor_op(a, b):
        """算筭按位异或运算：两位不同则通，相同则断"""
        result_bits = []
        max_len = max(len(a._bits), len(b._bits))
        for i in range(max_len):
            va = a._bits[i].binary if i < len(a._bits) else 0
            vb = b._bits[i].binary if i < len(b._bits) else 0
            result_bits.append(CountingRodBit(va ^ vb))
        result = CountingRodNumber(0)
        result._bits = result_bits
        return result

    @staticmethod
    def not_op(a):
        """算筭按位取反：通变断，断变通"""
        result_bits = [CountingRodBit(1 - bit.binary) for bit in a._bits]
        result = CountingRodNumber(0)
        result._bits = result_bits
        return result

    @staticmethod
    def compare(a, b):
        """
        比较两个算筭数的大小
        返回: -1 (a < b), 0 (a = b), 1 (a > b)
        """
        int_a = a.to_int()
        int_b = b.to_int()
        if int_a < int_b:
            return -1
        elif int_a > int_b:
            return 1
        return 0

    @staticmethod
    def shift_left(a, n):
        """算筭左移：高位增加 n 位断(|)，相当于乘以 2^n"""
        result_bits = [CountingRodBit(0)] * n + a._bits[:]
        result = CountingRodNumber(0)
        result._bits = result_bits
        return result

    @staticmethod
    def shift_right(a, n):
        """算筭右移：低位去除 n 位，相当于除以 2^n"""
        if n >= len(a._bits):
            return CountingRodNumber(0)
        result = CountingRodNumber(0)
        result._bits = a._bits[n:]
        return result

    @staticmethod
    def bits_to_rod_string(bits):
        """将位列表转为算筭可视化字符串"""
        return "".join(str(CountingRodBit(b)) for b in bits)


def demo_computer():
    """
    演示算筭计算机的基本运算能力
    """
    print("=" * 60)
    print("  算筭计算机 (Counting Rod Computer) 演示")
    print("  — = 通(1)    | = 断(0)")
    print("=" * 60)

    comp = CountingRodComputer

    # 创建算筭数
    a = comp.make_number(42)  # 42 = 00101010
    b = comp.make_number(13)  # 13 = 00001101

    print(f"\n[算筭] 算筭数 A: {a.to_rod_string()} (十进制: {a.to_int()})")
    print(f"[算筭] 算筭数 B: {b.to_rod_string()} (十进制: {b.to_int()})")

    # 加法
    c = comp.add(a, b)
    print(f"\n[+] 加法 A + B = {c.to_rod_string()} = {c.to_int()} (验证: {42}+{13}={42+13})")

    # 减法
    d = comp.subtract(a, b)
    print(f"[-] 减法 A - B = {d.to_rod_string()} = {d.to_int()} (验证: {42}-{13}={42-13})")

    # 乘法
    e = comp.multiply(a, b)
    print(f"[*]  乘法 A × B = {e.to_rod_string()} = {e.to_int()} (验证: {42}×{13}={42*13})")

    # 除法
    q, r = comp.divide(a, b)
    print(f"[/] 除法 A ÷ B = {q.to_rod_string()} = {q.to_int()} 余 {r.to_int()} (验证: {42}÷{13}={42//13}余{42%13})")

    # 逻辑运算
    and_r = comp.and_op(a, b)
    or_r = comp.or_op(a, b)
    xor_r = comp.xor_op(a, b)
    print(f"\n[关联] 按位与 = {and_r.to_rod_string()} = {and_r.to_int()}")
    print(f"[关联] 按位或 = {or_r.to_rod_string()} = {or_r.to_int()}")
    print(f"[关联] 按位异或 = {xor_r.to_rod_string()} = {xor_r.to_int()}")

    # 位移
    sl = comp.shift_left(a, 2)
    sr = comp.shift_right(a, 2)
    print(f"\n[<<] 左移2位 = {sl.to_rod_string()} = {sl.to_int()}")
    print(f"[>>] 右移2位 = {sr.to_rod_string()} = {sr.to_int()}")

    print("\n" + "=" * 60)
    print("  结论：仅用 — 和 | 即可完成全部计算机基本运算")
    print("=" * 60)


if __name__ == "__main__":
    demo_computer()

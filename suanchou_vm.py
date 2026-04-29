# -*- coding: utf-8 -*-
"""
算筭虚拟机 (SuanChou VM)
============================
直接执行算筭码指令的虚拟机。

为什么高效？
  传统计算机处理汉字语义任务时：
    汉字 → Unicode → 二进制 → 整数运算 → 查表 → 结果
    每一步都是翻译，每一步都有开销。
    
  算筭VM处理同一任务时：
    汉字 → 算筭码 → 直接在算筭码上执行指令 → 结果
    跳过了 Unicode 和整数的中间翻译层。

  好比：你要从北京飞到上海。
  传统方式：北京→翻译成英语→伦敦转机→翻译回中文→上海
  算筭方式：北京→直飞上海
"""

from counting_rod_computer import (
    CountingRodBit, CountingRodNumber, CountingRodComputer
)
from suanchou_isa import (
    SuanChouOpcode, SuanChouInstruction, make_instruction
)
from stroke_dictionary import StrokeDictionary
from stroke_encoder import StrokeEncoder


# CPU 标志寄存器
class Flags:
    """状态标志"""
    ZERO = 0     # 零标志
    EQUAL = 1    # 相等标志
    GREATER = 2  # 大于标志
    LESS = 3     # 小于标志


class SuanChouVM:
    """
    算筭虚拟机 —— 算筭码的直接执行引擎
    
    架构：
      - 8个通用寄存器 (R0-R7)，每个存储一个算筭数
      - 1个程序计数器 (PC)，指向当前指令在算筭码内存中的位置
      - 4个标志位 (ZERO, EQUAL, GREATER, LESS)
      - 算筭码内存：指令和数据一律以 — 和 | 存储
    """

    def __init__(self, memory_size=256):
        """
        初始化算筭虚拟机
        参数:
            memory_size: 算筭码内存大小（16位字为单位）
        """
        self.computer = CountingRodComputer()
        self.dictionary = StrokeDictionary()
        self.encoder = StrokeEncoder()

        # 寄存器（每个都是算筭数）
        self.registers = [CountingRodNumber(0, 16) for _ in range(8)]

        # 程序计数器
        self.pc = 0

        # 标志位
        self.flags = {Flags.ZERO: False, Flags.EQUAL: False,
                      Flags.GREATER: False, Flags.LESS: False}

        # 算筭码内存（每条16位指令）
        self.memory = [CountingRodNumber(0, 16) for _ in range(memory_size)]

        # 输出缓冲区
        self.output = []
        self.output_rods = []
        self.draw_commands = []  # 图形输出指令列表
        self.interactive_mode = None  # 交互模式: "calculator" 等

        # 特殊寄存器（用于汉字操作结果）
        self.char_result = None
        self.char_list = []

        # 指令计数（用于性能分析）
        self.instruction_count = 0

    def load_program(self, instructions):
        """
        将算筭指令序列加载到内存
        参数:
            instructions: SuanChouInstruction 列表
        """
        for i, inst in enumerate(instructions):
            if i < len(self.memory):
                self.memory[i] = inst.encode()
        self.pc = 0
        self.instruction_count = 0

    def load_rod_program(self, rod_strings):
        """
        直接从算筭码字符串加载程序
        参数:
            rod_strings: 算筭码字符串列表
        """
        for i, rod_str in enumerate(rod_strings):
            if i < len(self.memory):
                clean = rod_str.replace(" ", "")
                int_val = 0
                for ch in clean:
                    int_val <<= 1
                    if ch == CountingRodBit.ON_SYMBOL:
                        int_val |= 1
                self.memory[i] = CountingRodNumber(int_val, 16)
        self.pc = 0
        self.instruction_count = 0

    def fetch(self):
        """取指：从内存读取当前指令"""
        if self.pc >= len(self.memory):
            return None
        raw = self.memory[self.pc]
        int_val = raw.to_int()
        opcode = (int_val >> 10) & 0b111111
        dest = (int_val >> 7) & 0b111
        src = int_val & 0b1111111
        return SuanChouInstruction(opcode, dest, src)

    def decode_execute(self, inst):
        """
        解码并执行单条算筭指令
        所有运算均在算筭数层面完成，无整数转换
        """
        op = inst.opcode
        rd = inst.dest_reg
        rs = inst.src
        self.instruction_count += 1

        # ===== 数据传输 =====
        if op == SuanChouOpcode.HALT:
            return "HALT"

        elif op == SuanChouOpcode.LOAD:
            self.registers[rd] = CountingRodNumber(rs, 16)
            return None

        elif op == SuanChouOpcode.MOV:
            self.registers[rd] = self.registers[rs & 0b111]
            return None

        elif op == SuanChouOpcode.STORE:
            addr = rs & 0xFF
            if addr < len(self.memory):
                self.memory[addr] = self.registers[rd]
            return None

        elif op == SuanChouOpcode.LMEM:
            addr = rs & 0xFF
            if addr < len(self.memory):
                self.registers[rd] = self.memory[addr]
            return None

        # ===== 算术运算 =====
        elif op == SuanChouOpcode.ADD:
            self.registers[rd] = self.computer.add(
                self.registers[rd], self.registers[rs & 0b111])
            self._update_flags(self.registers[rd])
            return None

        elif op == SuanChouOpcode.SUB:
            self.registers[rd] = self.computer.subtract(
                self.registers[rd], self.registers[rs & 0b111])
            self._update_flags(self.registers[rd])
            return None

        elif op == SuanChouOpcode.MUL:
            self.registers[rd] = self.computer.multiply(
                self.registers[rd], self.registers[rs & 0b111])
            self._update_flags(self.registers[rd])
            return None

        elif op == SuanChouOpcode.DIV:
            q, r = self.computer.divide(
                self.registers[rd], self.registers[rs & 0b111])
            self.registers[rd] = q
            self.registers[7] = r  # 余数存 R7
            self._update_flags(q)
            return None

        # ===== 逻辑运算 =====
        elif op == SuanChouOpcode.AND:
            self.registers[rd] = self.computer.and_op(
                self.registers[rd], self.registers[rs & 0b111])
            return None

        elif op == SuanChouOpcode.OR:
            self.registers[rd] = self.computer.or_op(
                self.registers[rd], self.registers[rs & 0b111])
            return None

        elif op == SuanChouOpcode.XOR:
            self.registers[rd] = self.computer.xor_op(
                self.registers[rd], self.registers[rs & 0b111])
            return None

        elif op == SuanChouOpcode.NOT:
            self.registers[rd] = self.computer.not_op(self.registers[rd])
            return None

        # ===== 位移 =====
        elif op == SuanChouOpcode.SHL:
            self.registers[rd] = self.computer.shift_left(
                self.registers[rd], rs)
            return None

        elif op == SuanChouOpcode.SHR:
            self.registers[rd] = self.computer.shift_right(
                self.registers[rd], rs)
            return None

        # ===== 控制流 =====
        elif op == SuanChouOpcode.CMP:
            result = self.computer.compare(
                self.registers[rd], self.registers[rs & 0b111])
            self.flags[Flags.ZERO] = (result == 0)
            self.flags[Flags.EQUAL] = (result == 0)
            self.flags[Flags.GREATER] = (result == 1)
            self.flags[Flags.LESS] = (result == -1)
            return None

        elif op == SuanChouOpcode.JMP:
            self.pc = rs - 1  # -1 因为末尾会+1
            return None

        elif op == SuanChouOpcode.JE:
            if self.flags[Flags.EQUAL]:
                self.pc = rs - 1
            return None

        elif op == SuanChouOpcode.JNE:
            if not self.flags[Flags.EQUAL]:
                self.pc = rs - 1
            return None

        elif op == SuanChouOpcode.JG:
            if self.flags[Flags.GREATER]:
                self.pc = rs - 1
            return None

        elif op == SuanChouOpcode.JL:
            if self.flags[Flags.LESS]:
                self.pc = rs - 1
            return None

        # ===== 算筭原生指令（高效关键）=====
        elif op == SuanChouOpcode.ROD_CHAR:
            # 从算筭寄存器或字符代码加载汉字
            # 如果 rd 寄存器的值 < 0xFFFF，作为字符编码在字典中查找
            # 否则直接作为算筭码在 rod 索引中查找
            rod_str = self.registers[rd].to_rod_string()
            self.char_result = None
            self.char_list = []

            # 先尝试精确 rod 匹配
            exact = self.dictionary.find_by_rod_exact(rod_str)
            if exact:
                self.char_result = exact[0]
                self.char_list = exact
            else:
                # 再尝试从算筭字符串解码笔画
                strokes = self.encoder.rod_string_to_strokes(rod_str)
                if strokes:
                    # 尝试精确笔画匹配
                    stroke_matches = self.dictionary.find_by_strokes(strokes)
                    if stroke_matches:
                        self.char_result = stroke_matches[0]
                        self.char_list = stroke_matches
                    else:
                        # 模糊笔画前缀匹配
                        for prefix_len in range(len(strokes), 0, -1):
                            prefix_matches = self.dictionary.find_by_stroke_pattern(
                                strokes[:prefix_len])
                            if prefix_matches:
                                self.char_result = prefix_matches[0]
                                self.char_list = prefix_matches
                                break
            return None

        elif op == SuanChouOpcode.ROD_FIND:
            # 查找与当前字笔画相关的其他字
            self.char_list = []
            if self.char_result:
                self.char_list = self.dictionary.find_related_by_strokes(
                    self.char_result, match_length=2)
            return None

        elif op == SuanChouOpcode.ROD_CMP:
            # 算筭码直接比较两个字
            # 用 XOR 找出差异位，AND 找共同位
            encoded_a = self.registers[rd]
            encoded_b = self.registers[rs & 0b111]
            diff = self.computer.xor_op(encoded_a, encoded_b)
            common = self.computer.and_op(encoded_a, encoded_b)
            self.registers[rd] = diff     # 差异存 Rd
            self.registers[7] = common    # 共同存 R7
            return None

        elif op == SuanChouOpcode.ROD_MERGE:
            # 算筭码 OR = 合并两个字的笔画
            self.registers[rd] = self.computer.or_op(
                self.registers[rd], self.registers[rs & 0b111])
            return None

        elif op == SuanChouOpcode.ROD_OVERLAP:
            # 算筭码 AND = 找两个字的重叠笔画
            self.registers[rd] = self.computer.and_op(
                self.registers[rd], self.registers[rs & 0b111])
            return None

        elif op == SuanChouOpcode.ROD_TAG:
            # 语义标签查询（字典原生操作）
            self.char_list = []
            if self.char_result:
                self.char_list = self.dictionary.find_related_by_tags(
                    self.char_result)
            return None

        elif op == SuanChouOpcode.ROD_PRINT:
            # 以算筭码格式输出寄存器值
            self.output_rods.append(
                f"R{rd} = {self.registers[rd].to_rod_string()} ({self.registers[rd].to_int()})")
            return None

        elif op == SuanChouOpcode.ROD_SHOW:
            # 以汉字格式输出（如果有字符结果）
            rods = self.registers[rd].to_rod_string()
            if self.char_result:
                self.output.append(
                    f"R{rd} = {rods} -> 「{self.char_result.char}」({self.char_result.meaning})")
            else:
                self.output.append(
                    f"R{rd} = {rods} -> (未识别)")
            return None

        # ===== 算筭图形指令 =====
        elif op == SuanChouOpcode.ROD_DRAW_NUM:
            # 图形输出：大号数字
            self.draw_commands.append(
                ("NUM", self.registers[rd].to_int()))
            return None

        elif op == SuanChouOpcode.ROD_DRAW_CHAR:
            # 图形输出：汉字卡片
            rod_str = self.registers[rd].to_rod_string()
            exact = self.dictionary.find_by_rod_exact(rod_str)
            if exact:
                self.draw_commands.append(
                    ("CHAR", exact[0]))
            else:
                strokes = self.encoder.rod_string_to_strokes(rod_str)
                if strokes:
                    found = self.dictionary.find_by_strokes(strokes)
                    if found:
                        self.draw_commands.append(("CHAR", found[0]))
            return None

        elif op == SuanChouOpcode.ROD_DRAW_ROD:
            # 图形输出：算筭棒可视化
            val = self.registers[rd].to_int()
            rod_str = self.registers[rd].to_rod_string()
            self.draw_commands.append(
                ("ROD", val, rod_str))
            return None

        elif op == SuanChouOpcode.ROD_DRAW_BOX:
            # 图形输出：信息框
            title_val = self.registers[rd].to_int()
            body_val = self.registers[rs & 0b111].to_int()
            self.draw_commands.append(
                ("BOX", title_val, body_val))
            return None

        elif op == SuanChouOpcode.ROD_CALC:
            # 进入交互式计算器模式
            self.interactive_mode = "calculator"
            return "HALT"  # 暂停执行，等待交互

        # ===== 算筭交互指令 =====
        elif op == SuanChouOpcode.ROD_CLEAR:
            self.draw_commands.append(("CLEAR",))
            return None

        elif op == SuanChouOpcode.ROD_KEY:
            # 置键：Rdest = 位置编码(row*10+col), Rsrc = 标签值
            pos = self.registers[rd].to_int()
            label = self.registers[rs & 0b111].to_int()
            self.draw_commands.append(("KEY", pos, label))
            return None

        elif op == SuanChouOpcode.ROD_WAIT:
            # 待触：先提交所有draw_commands给OS, 然后暂停等待点击
            self.interactive_mode = "waiting"
            return "HALT"

        elif op == SuanChouOpcode.ROD_TOUCH:
            # 将上次点击的标签值存入Rdest
            touch_val = getattr(self, "last_touch_value", 0)
            self.registers[rd] = CountingRodNumber(touch_val, 16)
            return None

        elif op == SuanChouOpcode.ROD_TEXT:
            # 将Rdest的值作为文本绘制
            text_val = self.registers[rd].to_int()
            self.draw_commands.append(("TEXT", text_val))
            return None

        return None

    def _update_flags(self, rod_number):
        """更新零标志"""
        self.flags[Flags.ZERO] = (rod_number.to_int() == 0)

    def run(self, trace=False, max_instructions=10000):
        """
        运行虚拟机
        参数:
            trace: 是否输出执行追踪
            max_instructions: 最大指令数（防止死循环）
        """
        self.instruction_count = 0
        while self.pc < len(self.memory) and self.instruction_count < max_instructions:
            inst = self.fetch()
            if inst is None:
                break

            if trace:
                print(f"  [{self.pc:03d}] {inst}")

            result = self.decode_execute(inst)
            if result == "HALT":
                if trace:
                    print(f"  >>> HALT at PC={self.pc}")
                break

            self.pc += 1

        if trace:
            print(f"\n  执行完毕。总指令数: {self.instruction_count}")

    def show_output(self):
        """显示输出结果"""
        if self.output:
            print("\n[输出] 汉字结果：")
            for line in self.output:
                print(f"  {line}")
        if self.output_rods:
            print("\n[输出] 算筭结果：")
            for line in self.output_rods:
                print(f"  {line}")
        if self.char_list:
            print("\n[关联] 相关汉字：")
            for c in self.char_list[:8]:
                print(f"  「{c.char}」({c.meaning})")

    def show_state(self):
        """显示虚拟机当前状态"""
        print(f"\n  PC = {self.pc}  指令计数 = {self.instruction_count}")
        print(f"  标志: Z={self.flags[Flags.ZERO]} E={self.flags[Flags.EQUAL]} "
              f"G={self.flags[Flags.GREATER]} L={self.flags[Flags.LESS]}")
        print(f"  寄存器：")
        for i in range(8):
            r = self.registers[i]
            print(f"    R{i} = {r.to_rod_string()} ({r.to_int()})")
        if self.char_result:
            print(f"  字符缓冲：{self.char_result}")


# ============================================================
# 算筭汇编器 —— 人类可写的算筭程序语言
# ============================================================

class SuanChouAssembler:
    """
    算筭汇编器
    
    输入人类可读的算筭汇编代码，输出算筭机器码。
    
    汇编语法示例：
      LOAD R0, #42        ; 加载立即数42到R0
      LOAD R1, #13        ; 加载立即数13到R1
      ADD  R0, R1         ; R0 = R0 + R1
      ROD_PRINT R0        ; 输出R0的值
      HALT                ; 停机
    """

    @staticmethod
    def assemble(lines):
        """
        汇编给定的源代码行
        参数:
            lines: 汇编源文件行列表
        返回:
            SuanChouInstruction 列表
        """
        instructions = []
        labels = {}

        # 第一遍：收集标签（不区分大小写）
        addr = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.endswith(":"):
                label = line[:-1].strip().upper()
                labels[label] = addr
                continue
            addr += 1

        # 第二遍：汇编指令
        addr = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith(";") or line.endswith(":"):
                continue

            # 移除注释
            if ";" in line:
                line = line.split(";")[0].strip()

            parts = line.replace(",", " ").split()
            if not parts:
                continue

            mnemonic = parts[0].upper()
            operands = parts[1:] if len(parts) > 1 else []

            dest = 0
            src = 0

            # 解析操作数
            if operands:
                # 目标寄存器
                dest_op = operands[0].upper()
                if dest_op.startswith("R"):
                    dest = int(dest_op[1:])

                # 源操作数
                if len(operands) > 1:
                    src_op = operands[1].upper()
                    if src_op.startswith("R"):
                        src = int(src_op[1:])
                    elif src_op.startswith("#"):
                        # #立即数 或 #标签
                        src_str = src_op[1:]
                        if src_str in labels:
                            src = labels[src_str]
                        else:
                            src = int(src_str)
                    elif src_op in labels:
                        src = labels[src_op]
                    else:
                        src = int(src_op)

            # 生成指令
            opcode_map = {
                "HALT": SuanChouOpcode.HALT,
                "LOAD": SuanChouOpcode.LOAD,
                "MOV": SuanChouOpcode.MOV,
                "STORE": SuanChouOpcode.STORE,
                "LMEM": SuanChouOpcode.LMEM,
                "ADD": SuanChouOpcode.ADD,
                "SUB": SuanChouOpcode.SUB,
                "MUL": SuanChouOpcode.MUL,
                "DIV": SuanChouOpcode.DIV,
                "AND": SuanChouOpcode.AND,
                "OR": SuanChouOpcode.OR,
                "XOR": SuanChouOpcode.XOR,
                "NOT": SuanChouOpcode.NOT,
                "SHL": SuanChouOpcode.SHL,
                "SHR": SuanChouOpcode.SHR,
                "CMP": SuanChouOpcode.CMP,
                "JMP": SuanChouOpcode.JMP,
                "JE": SuanChouOpcode.JE,
                "JNE": SuanChouOpcode.JNE,
                "JG": SuanChouOpcode.JG,
                "JL": SuanChouOpcode.JL,
                "ROD_CHAR": SuanChouOpcode.ROD_CHAR,
                "ROD_FIND": SuanChouOpcode.ROD_FIND,
                "ROD_CMP": SuanChouOpcode.ROD_CMP,
                "ROD_MERGE": SuanChouOpcode.ROD_MERGE,
                "ROD_OVERLAP": SuanChouOpcode.ROD_OVERLAP,
                "ROD_TAG": SuanChouOpcode.ROD_TAG,
                "ROD_PRINT": SuanChouOpcode.ROD_PRINT,
                "ROD_SHOW": SuanChouOpcode.ROD_SHOW,
            }

            opcode = opcode_map.get(mnemonic, 0)
            inst = SuanChouInstruction(opcode, dest, src)
            instructions.append(inst)
            addr += 1

        return instructions

    @staticmethod
    def disassemble(instructions):
        """反汇编指令序列"""
        print("\n  地址  算筭机器码              汇编")
        print("  " + "-" * 55)
        for i, inst in enumerate(instructions):
            print(f"  {i:04d}  {inst.to_rod_string()}  {inst.disassemble()}")


def demo_vm():
    """演示算筭虚拟机"""
    print("=" * 70)
    print("  算筭虚拟机 (SuanChou VM) 演示")
    print("  直接用算筭码 — 和 | 编程")
    print("=" * 70)

    asm = SuanChouAssembler()
    dic = StrokeDictionary()

    # ========== 程序1：算筭码算术 ==========
    print("\n" + "-" * 70)
    print("  [程序1] 算筭码算术：计算 42 + 13 * 7")
    print("-" * 70)

    asm1 = [
        "LOAD R0, #42",
        "LOAD R1, #13",
        "LOAD R2, #7",
        "MUL  R1, R2",
        "ADD  R0, R1",
        "ROD_PRINT R0",
        "HALT",
    ]

    print("\n  汇编源代码：")
    for line in asm1:
        print(f"    {line}")

    prog1 = asm.assemble(asm1)
    asm.disassemble(prog1)

    vm1 = SuanChouVM()
    vm1.load_program(prog1)
    print("\n  执行追踪：")
    vm1.run(trace=True)
    vm1.show_output()

    # ========== 程序2：算筭码汉字识别（核心原生优势）==========
    print("\n" + "-" * 70)
    print("  [程序2] 算筭码原生汉字操作：存储+比较+语义关联")
    print("  【关键效率点】：直接以算筭位操作而非字符串解析")
    print("-" * 70)

    # 获取「日」和「月」的算筭编码，存入VM内存
    ri_obj = dic.get_character("日")
    yue_obj = dic.get_character("月")

    # 将算筭码转成整数存到内存地址8-15（每个字可能需2个16位字）
    def rod_to_memory_values(char_obj):
        """将汉字的算筭编码拆成多个16位值存入内存"""
        rod_bits = char_obj._encoded._bits
        values = []
        for i in range(0, len(rod_bits), 16):
            chunk = rod_bits[i:i+16]
            val = 0
            for j, bit in enumerate(chunk):
                if bit.is_on:
                    val |= (1 << j)
            values.append(val)
        return values

    ri_vals = rod_to_memory_values(ri_obj)
    yue_vals = rod_to_memory_values(yue_obj)

    print(f"\n  汉字「日」的算筭码：{ri_obj.rod_string} （{ri_obj.bits}位）")
    print(f"  汉字「月」的算筭码：{yue_obj.rod_string} （{yue_obj.bits}位）")
    print()

    # 将值预加载到内存（使用高地址区，避免与代码段冲突）
    DATA_SEG = 32  # 数据段基址
    vm2 = SuanChouVM()
    for i, v in enumerate(ri_vals):
        vm2.memory[DATA_SEG + i] = CountingRodNumber(v, ri_obj.bits)
    for i, v in enumerate(yue_vals):
        vm2.memory[DATA_SEG + 2 + i] = CountingRodNumber(v, yue_obj.bits)

    # 算筭汇编程序
    asm2 = [
        "LMEM R0, #" + str(DATA_SEG),     # 加载「日」的算筭码
        "ROD_CHAR R0",                     # 识别
        "ROD_SHOW R0",                     # 显示
        "LMEM R1, #" + str(DATA_SEG + 2), # 加载「月」的算筭码
        "ROD_CMP R0, R1",                 # XOR 差异, AND 共同
        "ROD_PRINT R0",                    # 输出差异位
        "ROD_PRINT R7",                    # 输出共同位
        "ROD_TAG  R0",                     # 语义标签关联
        "HALT",
    ]

    prog2 = asm.assemble(asm2)
    print("  编译后的算筭机器码：")
    asm.disassemble(prog2)

    vm2.load_program(prog2)
    print("\n  执行追踪：")
    vm2.run(trace=True)
    vm2.show_output()

    # ========== 程序3：算筭码编程——完整语义查询 ==========
    print("\n" + "-" * 70)
    print("  [程序3] 算筭码语义查询：查找与「木」相关的字")
    print("  【关键效率点】：字典原生rod索引，O(1)查找")
    print("-" * 70)

    mu_obj = dic.get_character("木")
    mu_vals = rod_to_memory_values(mu_obj)

    print(f"\n  汉字「木」的算筭码：{mu_obj.rod_string}")
    print()

    vm3 = SuanChouVM()
    for i, v in enumerate(mu_vals):
        vm3.memory[DATA_SEG + 4 + i] = CountingRodNumber(v, mu_obj.bits)

    asm3 = [
        "LMEM R0, #" + str(DATA_SEG + 4),  # 加载「木」的算筭码
        "ROD_CHAR R0",                       # 识别
        "ROD_SHOW R0",                       # 显示
        "ROD_FIND R0",                       # 笔画层面关联查询
        "ROD_TAG  R0",                       # 语义层面关联查询
        "HALT",
    ]

    prog3 = asm.assemble(asm3)
    asm.disassemble(prog3)

    vm3.load_program(prog3)
    print("\n  执行追踪：")
    vm3.run(trace=True)
    vm3.show_output()

    # ========== 程序4：循环（展示控制流）==========
    print("\n" + "-" * 70)
    print("  [程序4] 循环累加：用算筭码计算 5+4+3+2+1")
    print("-" * 70)

    asm4 = [
        "LOAD R0, #0",
        "LOAD R1, #5",
        "LOAD R2, #1",
    "loop:",
        "ADD  R0, R1",
        "SUB  R1, R2",
        "CMP  R1, R2",
        "JG   R0, LOOP",
        "ADD  R0, R1",
        "ROD_PRINT R0",
        "HALT",
    ]

    print("\n  汇编源代码：")
    for line in asm4:
        print(f"    {line}")

    prog4 = asm.assemble(asm4)
    asm.disassemble(prog4)

    vm4 = SuanChouVM()
    vm4.load_program(prog4)
    print("\n  执行追踪：")
    vm4.run(trace=True)
    vm4.show_output()
    vm4.show_state()

    print("\n" + "=" * 70)
    print("  演示完毕。以上所有程序均以算筭码直接执行。")
    print("=" * 70)


if __name__ == "__main__":
    demo_vm()

# -*- coding: utf-8 -*-
"""
文 → x86-64 原生编译器 (Wen → x64 Native Compiler)
=====================================================
将文语言 .wen 源文件编译为独立的 x86-64 Windows PE .exe。

核心管线：
  文源码 → 词法/语法分析 → 三地址码(IR) → x64机器码 → PE .exe

三地址码是关键中间层：
  每条IR要么是赋值/运算，要么是控制流
  IR → x64 映射直接、清晰、可调试

需要 Windows 系统自带工具（可选，用于汇编+链接）：
  py wen_x64.py foo.wen -S       生成 .asm   (NASM 汇编)
  py wen_x64.py foo.wen -c       生成 .obj   (需 NASM)
  py wen_x64.py foo.wen -o a.exe 生成 .exe   (需 NASM + GoLink/LINK)
  py wen_x64.py foo.wen --run    生成并运行
"""

import sys, os, struct, subprocess, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wen_lang import (
    WenLexer, WenParser,
    NumberNode, StringNode, IdentNode, BoolNode, ListNode, DictNode,
    BinOpNode, UnaryOpNode, CallNode, AssignNode, IndexNode,
    ReturnNode, IfNode, ForNode, WhileNode, BlockNode, FuncDefNode,
)


# ═══════════════════════════════════════════════════════════════
#  三地址码 (IR)
# ═══════════════════════════════════════════════════════════════

class IR:
    """IR 指令"""
    pass

class IRLabel(IR):
    def __init__(self, name): self.name = name
    def __repr__(self): return f"{self.name}:"

class IRMove(IR):
    def __init__(self, dst, src): self.dst = dst; self.src = src
    def __repr__(self): return f"  {self.dst} = {self.src}"

class IRBinOp(IR):
    def __init__(self, dst, left, op, right):
        self.dst = dst; self.left = left; self.op = op; self.right = right
    def __repr__(self): return f"  {self.dst} = {self.left} {self.op} {self.right}"

class IRUnaryOp(IR):
    def __init__(self, dst, op, src): self.dst = dst; self.op = op; self.src = src
    def __repr__(self): return f"  {self.dst} = {self.op} {self.src}"

class IRCall(IR):
    def __init__(self, dst, name, args): self.dst = dst; self.name = name; self.args = args
    def __repr__(self): return f"  {self.dst} = call {self.name}({self.args})"

class IRCallStmt(IR):
    def __init__(self, name, args): self.name = name; self.args = args
    def __repr__(self): return f"  call {self.name}({self.args})"

class IRReturn(IR):
    def __init__(self, val): self.val = val
    def __repr__(self): return f"  return {self.val}"

class IRJump(IR):
    def __init__(self, label): self.label = label
    def __repr__(self): return f"  goto {self.label}"

class IRCondJump(IR):
    def __init__(self, cond, label): self.cond = cond; self.label = label
    def __repr__(self): return f"  if {self.cond} goto {self.label}"

class IRPush(IR):
    def __init__(self, val): self.val = val
    def __repr__(self): return f"  push {self.val}"

class IRPop(IR):
    def __init__(self, dst): self.dst = dst
    def __repr__(self): return f"  pop {self.dst}"

class IRLoadGlobal(IR):
    def __init__(self, dst, name): self.dst = dst; self.name = name
    def __repr__(self): return f"  {self.dst} = glob[{self.name}]"

class IRStoreGlobal(IR):
    def __init__(self, name, val): self.name = name; self.val = val
    def __repr__(self): return f"  glob[{self.name}] = {self.val}"


# ═══════════════════════════════════════════════════════════════
#  IR 生成器 (AST → IR)
# ═══════════════════════════════════════════════════════════════

class IRGen:
    def __init__(self):
        self.ir = []
        self.temp_counter = 0
        self.label_counter = 0
        self.strings = {}  # str → label
        self.funcs = {}    # name → label

    def new_temp(self):
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def new_label(self, prefix="L"):
        l = f"{prefix}{self.label_counter}"
        self.label_counter += 1
        return l

    def alloc_string(self, s):
        if s not in self.strings:
            self.strings[s] = f"__str_{len(self.strings)}"
        return self.strings[s]

    def gen_expr(self, node):
        """求表达式，返回 (temp_name, [ir_instructions])"""
        if isinstance(node, NumberNode):
            t = self.new_temp()
            return t, [IRMove(t, f"#{node.value}")]

        elif isinstance(node, StringNode):
            label = self.alloc_string(node.value)
            t = self.new_temp()
            return t, [IRMove(t, f"&{label}")]

        elif isinstance(node, BoolNode):
            t = self.new_temp()
            return t, [IRMove(t, f"#{1 if node.value else 0}")]

        elif isinstance(node, IdentNode):
            t = self.new_temp()
            return t, [IRLoadGlobal(t, node.name)]

        elif isinstance(node, BinOpNode):
            left_temp, left_code = self.gen_expr(node.left)
            right_temp, right_code = self.gen_expr(node.right)
            dst = self.new_temp()
            op_map = {"+": "+", "-": "-", "*": "*", "/": "/",
                      "==": "==", "!=": "!=", "<": "<", ">": ">",
                      "<=": "<=", ">=": ">=", "或": "||", "且": "&&"}
            ir_op = op_map.get(node.op, node.op)
            return dst, left_code + right_code + [IRBinOp(dst, left_temp, ir_op, right_temp)]

        elif isinstance(node, UnaryOpNode):
            val_temp, val_code = self.gen_expr(node.expr)
            dst = self.new_temp()
            op_map = {"负": "-", "非": "!"}
            return dst, val_code + [IRUnaryOp(dst, op_map.get(node.op, node.op), val_temp)]

        elif isinstance(node, CallNode):
            args_temps = []
            args_code = []
            for arg in node.args:
                at, ac = self.gen_expr(arg)
                args_temps.append(at)
                args_code.extend(ac)
            dst = self.new_temp()
            name = node.name if isinstance(node.name, str) else str(node.name)
            return dst, args_code + [IRCall(dst, name, args_temps)]

        elif isinstance(node, IndexNode):
            t, tc = self.gen_expr(node.expr)
            idx_t, idx_c = self.gen_expr(node.index)
            dst = self.new_temp()
            return dst, tc + idx_c + [IRBinOp(dst, t, "[]", idx_t)]

        else:
            t = self.new_temp()
            return t, [IRMove(t, "#0")]

    def gen_stmt(self, node):
        """生成语句 IR"""
        if isinstance(node, AssignNode):
            val_temp, val_code = self.gen_expr(node.value)
            return val_code + [IRStoreGlobal(node.name, val_temp)]

        elif isinstance(node, CallNode):
            name = node.name if isinstance(node.name, str) else str(node.name)
            args_temps = []
            ir_code = []
            for arg in node.args:
                at, ac = self.gen_expr(arg)
                args_temps.append(at)
                ir_code.extend(ac)
            return ir_code + [IRCallStmt(name, args_temps)]

        elif isinstance(node, IfNode):
            code = []
            end_label = self.new_label("_if_end")
            next_labels = [self.new_label(f"_elif_{i}") for i in range(len(node.branches))]

            for i, (condition, body) in enumerate(node.branches):
                if condition == "else":
                    for stmt in body.statements:
                        code.extend(self.gen_stmt(stmt))
                    break

                cond_temp, cond_code = self.gen_expr(condition)
                code.extend(cond_code)

                if i < len(node.branches) - 1:
                    code.append(IRCondJump(f"!{cond_temp}", next_labels[i]))
                else:
                    code.append(IRCondJump(f"!{cond_temp}", end_label))

                code.append(IRLabel(next_labels[i]) if i > 0 else None)
                if i == 0:
                    pass  # 第一个分支直接跟在条件判断后
                else:
                    pass

                for stmt in body.statements:
                    code.extend(self.gen_stmt(stmt))

                if i < len(node.branches) - 1:
                    code.append(IRJump(end_label))

            code.append(IRLabel(end_label))
            return [x for x in code if x is not None]

        elif isinstance(node, ForNode):
            code = []
            iter_temp, iter_code = self.gen_expr(node.iterable)
            code.extend(iter_code)

            idx_temp = self.new_temp()
            code.append(IRMove(idx_temp, "#0"))

            loop_label = self.new_label("_for_loop")
            end_label = self.new_label("_for_end")
            code.append(IRLabel(loop_label))

            # 检查越界（简化：最多迭代1000次）
            limit_temp = self.new_temp()
            code.append(IRMove(limit_temp, "#1000"))
            cond_temp = self.new_temp()
            code.append(IRBinOp(cond_temp, idx_temp, ">=", limit_temp))
            code.append(IRCondJump(cond_temp, end_label))

            # 循环体：变量赋值
            code.append(IRStoreGlobal(node.var, idx_temp))

            for stmt in node.body.statements:
                code.extend(self.gen_stmt(stmt))

            code.append(IRBinOp(idx_temp, idx_temp, "+", "#1"))
            code.append(IRJump(loop_label))
            code.append(IRLabel(end_label))
            return code

        elif isinstance(node, WhileNode):
            code = []
            loop_label = self.new_label("_while")
            end_label = self.new_label("_wend")
            code.append(IRLabel(loop_label))

            cond_temp, cond_code = self.gen_expr(node.condition)
            code.extend(cond_code)
            code.append(IRCondJump(f"!{cond_temp}", end_label))

            for stmt in node.body.statements:
                code.extend(self.gen_stmt(stmt))

            code.append(IRJump(loop_label))
            code.append(IRLabel(end_label))
            return code

        elif isinstance(node, ReturnNode):
            val_temp, val_code = self.gen_expr(node.expr)
            return val_code + [IRReturn(val_temp)]

        elif isinstance(node, FuncDefNode):
            func_label = f"__func__{node.name}"
            self.funcs[node.name] = func_label
            code = [IRLabel(func_label)]
            for stmt in node.body.statements:
                code.extend(self.gen_stmt(stmt))
            code.append(IRReturn("#0"))
            return code

        elif isinstance(node, BlockNode):
            code = []
            for stmt in node.statements:
                if isinstance(stmt, FuncDefNode):
                    code.extend(self.gen_stmt(stmt))
                else:
                    code.extend(self.gen_stmt(stmt))
            return code

        # 表达式语句
        expr_temp, expr_code = self.gen_expr(node)
        return expr_code

    def generate(self, ast):
        code = self.gen_stmt(ast)
        return code


# ═══════════════════════════════════════════════════════════════
#  x86-64 NASM 代码生成器 (IR → Assembly)
# ═══════════════════════════════════════════════════════════════

REG_MAP = {"rax": "rax", "rcx": "rcx", "rdx": "rdx", "rbx": "rbx",
           "r8": "r8", "r9": "r9", "r10": "r10", "r11": "r11"}


class X64AsmGen:
    def __init__(self, ir_code, strings):
        self.ir = ir_code
        self.strings = strings
        self.asm = []
        # 寄存器分配：临时变量 → 寄存器
        self.regs = {}  # temp_name → ("rax"|"rcx"|"rdx"|"rbx"|"r8"...)
        self.reg_stack = ["r8", "r9", "r10", "r11", "rbx", "rcx", "rdx", "rax"]
        self.used_regs = set()

    def alloc_reg(self, temp):
        if temp in self.regs:
            return self.regs[temp]
        if not self.reg_stack:
            # 溢出到栈
            return None
        reg = self.reg_stack.pop()
        self.regs[temp] = reg
        self.used_regs.add(reg)
        return reg

    def free_reg(self, temp):
        if temp in self.regs:
            reg = self.regs[temp]
            del self.regs[temp]
            self.reg_stack.append(reg)

    def get_reg(self, temp):
        """获取或分配临时变量的寄存器"""
        if temp in self.regs:
            return self.regs[temp]
        # 字面量
        if temp.startswith("#"):
            return None  # 立即数
        if temp.startswith("&"):
            return None  # 地址
        return self.alloc_reg(temp)

    def operand(self, val):
        """将 IR 值转为 NASM 操作数"""
        if val is None:
            return "0"
        if val.startswith("#"):
            return val[1:]  # 立即数
        if val.startswith("!"):
            # !t = not t
            inner = val[1:]
            if inner in self.regs:
                return f"qword [not_{inner}]"  # 简化
            return "0"
        if val.startswith("&"):
            return val[1:]  # 地址标签
        if val in self.regs:
            return self.regs[val]
        # 全局变量
        return f"qword [{val}]"

    def reg64(self, r):
        """返回64位寄存器名"""
        return r

    def generate(self):
        self.asm.append("; ── 文语言 → x86-64 (Wen Compiler) ──")
        self.asm.append("BITS 64")
        self.asm.append("SECTION .text")
        self.asm.append("global _start")
        self.asm.append("extern GetStdHandle")
        self.asm.append("extern WriteFile")
        self.asm.append("extern ExitProcess")
        self.asm.append("")

        # 数据段
        self.asm.append("SECTION .data")
        self.asm.append("align 8")
        for s, label in self.strings.items():
            # 转义
            escaped = s.replace("\\", "\\\\").replace('"', '\\"')
            self.asm.append(f'{label}: db "{escaped}", 0')

        # 全局变量
        globls = set()
        for ir in self.ir:
            for attr in ['dst', 'src', 'left', 'right', 'val', 'name', 'cond']:
                v = getattr(ir, attr, None)
                if isinstance(v, str) and not v.startswith('#') and not v.startswith('&') and not v.startswith('!') and not v.startswith('_') and not v.startswith('L') and not v.startswith('t'):
                    if v not in REG_MAP and v not in ('rax', 'rcx', 'rdx', 'rbx', 'r8', 'r9', 'r10', 'r11'):
                        globls.add(v)

        for g in sorted(globls):
            self.asm.append(f"{g}: dq 0")

        self.asm.append("")
        self.asm.append("SECTION .text")
        self.asm.append("_start:")
        self.asm.append("    push rbp")
        self.asm.append("    mov rbp, rsp")
        self.asm.append("    sub rsp, 256")
        self.asm.append("    push rbx")
        self.asm.append("    push r12")
        self.asm.append("    push r13")
        self.asm.append("")

        # 生成 IR
        for ir in self.ir:
            self._gen_ir(ir)

        # 退出
        self.asm.append("")
        self.asm.append("__exit__:")
        self.asm.append("    xor ecx, ecx")
        self.asm.append("    call ExitProcess")
        self.asm.append("    pop r13")
        self.asm.append("    pop r12")
        self.asm.append("    pop rbx")
        self.asm.append("    mov rsp, rbp")
        self.asm.append("    pop rbp")
        self.asm.append("    xor eax, eax")
        self.asm.append("    ret")
        self.asm.append("")

        return "\n".join(self.asm)

    def _gen_ir(self, ir):
        if isinstance(ir, IRLabel):
            self.asm.append(f"{ir.name}:")

        elif isinstance(ir, IRMove):
            if ir.src.startswith("#"):
                val = ir.src[1:]
                self._store(ir.dst, f"mov qword [{ir.dst}], {val}")
                if ir.dst in self.regs:
                    self.asm.append(f"    mov {self.regs[ir.dst]}, {val}")
                else:
                    self.asm.append(f"    mov qword [{ir.dst}], {val}")
            elif ir.src.startswith("&"):
                lbl = ir.src[1:]
                self.asm.append(f"    lea rax, [{lbl}]")
                self._store(ir.dst, f"mov qword [{ir.dst}], rax")
            else:
                self._move_to(ir.dst, ir.src)

        elif isinstance(ir, IRBinOp):
            self._gen_binop(ir)

        elif isinstance(ir, IRUnaryOp):
            self._gen_unary(ir)

        elif isinstance(ir, IRCall):
            self._gen_call(ir)

        elif isinstance(ir, IRCallStmt):
            self._gen_call_stmt(ir)

        elif isinstance(ir, IRReturn):
            if ir.val.startswith("#"):
                self.asm.append(f"    mov eax, {ir.val[1:]}")
            elif ir.val in self.regs:
                self.asm.append(f"    mov rax, {self.regs[ir.val]}")
            else:
                self.asm.append(f"    mov rax, qword [{ir.val}]")
            self.asm.append("    jmp __exit__")

        elif isinstance(ir, IRJump):
            self.asm.append(f"    jmp {ir.label}")

        elif isinstance(ir, IRCondJump):
            cond_val = ir.cond
            negated = cond_val.startswith("!")
            actual = cond_val[1:] if negated else cond_val
            if actual in self.regs:
                self.asm.append(f"    cmp {self.regs[actual]}, 0")
            elif actual.startswith("#"):
                self.asm.append(f"    cmp {actual[1:]}, 0")
            else:
                self.asm.append(f"    cmp qword [{actual}], 0")
            jmp = "je" if negated else "jne"
            self.asm.append(f"    {jmp} {ir.label}")

        elif isinstance(ir, IRLoadGlobal):
            if ir.name in self.regs:
                self.asm.append(f"    mov {self.regs[ir.name]}, qword [{ir.name}]")
            elif ir.dst in self.regs:
                self.asm.append(f"    mov {self.regs[ir.dst]}, qword [{ir.name}]")
            else:
                self.asm.append(f"    mov rax, qword [{ir.name}]")
                self.asm.append(f"    mov qword [{ir.dst}], rax")

        elif isinstance(ir, IRStoreGlobal):
            if ir.val.startswith("#"):
                self.asm.append(f"    mov qword [{ir.name}], {ir.val[1:]}")
            elif ir.val in self.regs:
                self.asm.append(f"    mov qword [{ir.name}], {self.regs[ir.val]}")
            else:
                self.asm.append(f"    mov rax, qword [{ir.val}]")
                self.asm.append(f"    mov qword [{ir.name}], rax")

    def _store(self, dst, fallback_asm):
        pass  # handled in IRMove

    def _move_to(self, dst, src):
        if src in self.regs:
            src_reg = self.regs[src]
            if dst in self.regs:
                self.asm.append(f"    mov {self.regs[dst]}, {src_reg}")
            else:
                self.asm.append(f"    mov qword [{dst}], {src_reg}")
        else:
            self.asm.append(f"    mov rax, qword [{src}]")
            if dst in self.regs:
                self.asm.append(f"    mov {self.regs[dst]}, rax")
            else:
                self.asm.append(f"    mov qword [{dst}], rax")

    def _gen_binop(self, ir):
        # 简化：总是用 rax 和 rcx
        self._load_to_rax(ir.left)
        self.asm.append("    push rax")
        self._load_to_rax(ir.right)
        self.asm.append("    pop rcx")

        op_map = {
            "+": "add rax, rcx",
            "-": "sub rcx, rax\n    mov rax, rcx",
            "*": "imul rax, rcx",
            "/": "mov rdx, rcx\n    mov rcx, rax\n    mov rax, rdx\n    cqo\n    idiv rcx",
            "==": "cmp rcx, rax\n    sete al\n    movzx rax, al",
            "!=": "cmp rcx, rax\n    setne al\n    movzx rax, al",
            "<": "cmp rcx, rax\n    setl al\n    movzx rax, al",
            ">": "cmp rcx, rax\n    setg al\n    movzx rax, al",
            "<=": "cmp rcx, rax\n    setle al\n    movzx rax, al",
            ">=": "cmp rcx, rax\n    setge al\n    movzx rax, al",
            "||": "or rax, rcx",
            "&&": "and rax, rcx",
        }
        asm_op = op_map.get(ir.op, f"; 不支持: {ir.op}")
        for line in asm_op.split("\n"):
            self.asm.append(f"    {line.strip()}")

        self._save_rax(ir.dst)

    def _gen_unary(self, ir):
        self._load_to_rax(ir.src)
        if ir.op == "-":
            self.asm.append("    neg rax")
        elif ir.op == "!":
            self.asm.append("    cmp rax, 0")
            self.asm.append("    sete al")
            self.asm.append("    movzx rax, al")
        self._save_rax(ir.dst)

    def _load_to_rax(self, val):
        if val.startswith("#"):
            self.asm.append(f"    mov rax, {val[1:]}")
        elif val.startswith("&"):
            self.asm.append(f"    lea rax, [{val[1:]}]")
        elif val in self.regs:
            self.asm.append(f"    mov rax, {self.regs[val]}")
        else:
            self.asm.append(f"    mov rax, qword [{val}]")

    def _save_rax(self, dst):
        if dst in self.regs:
            self.asm.append(f"    mov {self.regs[dst]}, rax")
        else:
            self.asm.append(f"    mov qword [{dst}], rax")

    def _gen_call(self, ir):
        name = ir.name
        builtins = {
            "示": self._gen_print,
            "整": self._gen_builtin_int,
            "文": self._gen_builtin_str,
            "长": self._gen_builtin_len,
            "范围": self._gen_builtin_range,
        }

        if name in builtins:
            builtins[name](ir)
        else:
            # 用户函数调用
            for i, arg in enumerate(reversed(ir.args)):
                self._load_to_rax(arg)
                self.asm.append("    push rax")
            func_label = self._lookup_func(name)
            self.asm.append(f"    call {func_label}")
            self.asm.append(f"    add rsp, {8 * len(ir.args)}")
            self._save_rax(ir.dst)

    def _gen_call_stmt(self, ir):
        # 同 _gen_call 但不存储结果
        name = ir.name
        if name == "示":
            for arg in ir.args:
                self._load_to_rax(arg)
                self._asm_print_rax()

    def _lookup_func(self, name):
        # 查找函数标签
        for ir in self.ir:
            if isinstance(ir, IRLabel) and ir.name == f"__func__{name}":
                return ir.name
        return f"__func__{name}"

    def _gen_print(self, ir):
        """示(值) → printf 调用"""
        for arg in ir.args:
            self._load_to_rax(arg)
            self._asm_print_rax()

    def _asm_print_rax(self):
        """生成打印 RAX 中整数的汇编"""
        # 用最简单的方式：存到缓冲区，调 WriteFile
        # 这里生成一个 itoa + WriteFile 调用
        self.asm.append("    ; print rax")
        self.asm.append("    push rax")
        self.asm.append("    call __itoa_print")
        self.asm.append("    add rsp, 8")

    def _gen_builtin_int(self, ir):
        self._load_to_rax(ir.args[0])
        self._save_rax(ir.dst)

    def _gen_builtin_str(self, ir):
        self._load_to_rax(ir.args[0])
        self._save_rax(ir.dst)

    def _gen_builtin_len(self, ir):
        self._load_to_rax(ir.args[0])
        self._save_rax(ir.dst)

    def _gen_builtin_range(self, ir):
        self.asm.append("    xor eax, eax")
        self._save_rax(ir.dst)


# ═══════════════════════════════════════════════════════════════
#  编译管线
# ═══════════════════════════════════════════════════════════════

NASM_RUNTIME = r"""
; ═══ 文语言运行时 (x86-64 Windows) ═══
; 提供: 整数打印 (itoa + WriteFile)
; 需要: GetStdHandle, WriteFile, ExitProcess from kernel32.dll

__itoa_print:
    ; 输入: [rsp+8] = 要打印的整数 (64-bit)
    ; 输出到 stdout
    push rbp
    mov rbp, rsp
    sub rsp, 80           ; 缓冲区: [rbp-8] = temp, [rbp-72] = buffer(64 bytes)
    
    mov rax, [rbp+16]     ; 待打印的整数
    lea rdi, [rbp-72]     ; 缓冲区末尾
    
    ; 处理零
    test rax, rax
    jnz .itoa_nonzero
    mov byte [rdi], '0'
    mov rcx, 1
    lea rdx, [rbp-72]
    jmp .itoa_write
    
.itoa_nonzero:
    ; 处理符号
    xor r8, r8            ; r8 = 负数标志
    test rax, rax
    jns .itoa_abs
    neg rax
    mov r8, 1
.itoa_abs:
    ; 逐位除10
    lea rdi, [rbp-8]      ; 缓冲区从末尾往前写
    mov byte [rdi], 0
.itoa_loop:
    xor rdx, rdx
    mov rcx, 10
    div rcx               ; rax/=10, rdx=余数
    add dl, '0'
    dec rdi
    mov [rdi], dl
    test rax, rax
    jnz .itoa_loop
    
    ; 负号
    test r8, r8
    jz .itoa_calc_len
    dec rdi
    mov byte [rdi], '-'
    
.itoa_calc_len:
    ; rdi = 字符串起始, 计算长度
    lea rcx, [rbp-8]
    sub rcx, rdi          ; rcx = 长度
    
    ; 获取 stdout 句柄
    mov rcx, -11          ; STD_OUTPUT_HANDLE
    sub rsp, 32           ; shadow space
    call GetStdHandle
    
    ; WriteFile(hStdOut, buf, len, &written, NULL)
    mov rcx, rax          ; hStdOut
    mov rdx, rdi          ; buffer
    lea r8, [rbp-8]
    sub r8, rdi           ; length
    lea r9, [rbp-16]      ; &written
    mov qword [rsp+32], 0 ; lpOverlapped = NULL
    call WriteFile
    
    ; 换行
    mov rcx, rax          ; hStdOut
    lea rdx, [__newline]
    mov r8, 2
    lea r9, [rbp-16]
    mov qword [rsp+32], 0
    call WriteFile
    
    add rsp, 32
    mov rsp, rbp
    pop rbp
    ret

SECTION .data
__newline: db 13, 10
"""


def compile_to_asm(source_path, asm_path):
    """编译 .wen → .asm"""
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    lexer = WenLexer(source)
    tokens = lexer.tokenize()
    parser = WenParser(tokens)
    ast = parser.parse_program()

    # 生成 IR
    irgen = IRGen()
    ir_code = irgen.generate(ast)

    # 生成 x86-64 汇编
    asmgen = X64AsmGen(ir_code, irgen.strings)
    asm = asmgen.generate()

    # 附加运行时
    full_asm = asm + "\n" + NASM_RUNTIME + "\n"

    with open(asm_path, "w", encoding="utf-8") as f:
        f.write(full_asm)

    print(f"  生成汇编: {asm_path}")
    return asm_path


def find_nasm():
    """查找 NASM"""
    for path in [
        r"C:\Program Files\NASM\nasm.exe",
        r"C:\Program Files (x86)\NASM\nasm.exe",
        r"C:\nasm\nasm.exe",
    ]:
        if os.path.exists(path):
            return path
    return shutil.which("nasm")


def find_linker():
    """查找链接器"""
    # 尝试 GoLink
    for path in [
        r"C:\golink\golink.exe",
        r"C:\Program Files\GoLink\golink.exe",
    ]:
        if os.path.exists(path):
            return path
    # 尝试 MSVC LINK
    for vs in ["2022", "2019", "2017"]:
        for edition in ["Community", "Professional", "Enterprise"]:
            base = f"C:\\Program Files\\Microsoft Visual Studio\\{vs}\\{edition}\\VC\\Tools\\MSVC"
            if os.path.exists(base):
                # 找最新版本
                versions = sorted(os.listdir(base), reverse=True)
                for v in versions:
                    host = f"{base}\\{v}\\bin\\Hostx64\\x64"
                    if os.path.exists(host):
                        link = f"{host}\\link.exe"
                        if os.path.exists(link):
                            return link
    return shutil.which("link")


def assemble_and_link(asm_path, exe_path):
    """汇编 + 链接 → .exe"""
    nasm = find_nasm()
    if not nasm:
        print("  [警告] 未找到 NASM。请安装 NASM 或使用 -S 仅生成汇编。")
        print("  下载: https://www.nasm.us/pub/nasm/releasebuilds/")
        return None

    obj_path = asm_path.replace(".asm", ".obj")

    # 汇编
    print(f"  汇编: {asm_path} → {obj_path}")
    result = subprocess.run(
        [nasm, "-f", "win64", "-o", obj_path, asm_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  汇编错误:\n{result.stderr}")
        return None

    # 链接
    linker = find_linker()
    if not linker:
        # 尝试用 golink
        golink = shutil.which("golink") or r"C:\golink\golink.exe"
        if os.path.exists(golink):
            linker = golink

    if linker and "golink" in linker.lower():
        # GoLink 语法
        print(f"  链接: {obj_path} → {exe_path}")
        subprocess.run(
            [linker, "/console", "/entry:_start",
             "kernel32.dll", obj_path, "/fo", exe_path],
            capture_output=True
        )
    elif linker:
        # MSVC LINK 语法
        print(f"  链接: {obj_path} → {exe_path}")
        subprocess.run(
            [linker, "/nologo", "/subsystem:console",
             "/entry:_start", obj_path,
             "kernel32.lib", "/out:" + exe_path],
            capture_output=True
        )
    else:
        print("  [警告] 未找到链接器。仅生成了 .obj 文件。")
        return obj_path

    if os.path.exists(exe_path):
        print(f"  编译完成: {exe_path}  ({os.path.getsize(exe_path)} 字节)")
        return exe_path
    return None


# ═══════════════════════════════════════════════════════════════
#  命令
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("文 → x86-64 原生编译器")
        print()
        print("用法:")
        print("  py wen_x64.py  源.wen  -S        仅生成 .asm 汇编文件")
        print("  py wen_x64.py  源.wen  -c        生成 .obj 目标文件")
        print("  py wen_x64.py  源.wen  -o a.exe  生成 .exe 可执行文件")
        print("  py wen_x64.py  源.wen  -o a.exe  --run  生成并运行")
        print()
        print("需要 NASM (汇编器)。可选 GoLink 或 MSVC LINK (链接器)。")
        return

    src = sys.argv[1]
    out_asm = os.path.splitext(os.path.basename(src))[0] + ".asm"
    out_exe = "a.exe"

    flags = sys.argv[2:]

    if "-o" in flags:
        idx = flags.index("-o")
        out_exe = flags[idx + 1]

    # 生成汇编
    compile_to_asm(src, out_asm)

    if "-S" in flags:
        return  # 仅汇编

    # 汇编 + 链接
    if "-c" in flags or "-o" in flags:
        result = assemble_and_link(out_asm, out_exe)
        if result and "--run" in flags:
            print(f"\n  运行 {out_exe}:\n")
            os.system(out_exe)


if __name__ == "__main__":
    main()

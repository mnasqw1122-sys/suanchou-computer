# -*- coding: utf-8 -*-
"""
文 → C → x86-64 原生编译器
=============================
文语言 → C 代码 → GCC/Clang/TCC → 独立 .exe

这是一条实际的、能工作的路径。
C 的类型系统、运行时、IO 全部直接复用。
产出的 .exe 不依赖 Python、不需要解释器、不需要任何文语言运行时。

用法:
  py wen_c.py 源.wen              生成 源.c
  py wen_c.py 源.wen -o out.exe   生成 C 代码 + 编译 + 链接
  py wen_c.py 源.wen --run        编译 + 运行
"""

import sys, os, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wen_lang import (
    WenLexer, WenParser,
    NumberNode, StringNode, IdentNode, BoolNode, ListNode, DictNode,
    BinOpNode, UnaryOpNode, CallNode, AssignNode, IndexNode,
    ReturnNode, IfNode, ForNode, WhileNode, BlockNode, FuncDefNode,
)


class CCodeGen:
    """文语言 AST → C 代码"""

    def __init__(self):
        self.output = []
        self.indent = 0
        self.temp_counter = 0
        self.label_counter = 0
        self.funcs = {}

    def emit(self, line):
        self.output.append("    " * self.indent + line)

    def new_temp(self):
        t = f"_t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def new_label(self, prefix="L"):
        l = f"{prefix}{self.label_counter}"
        self.label_counter += 1
        return l

    def gen_expr(self, node):
        """生成表达式 C 代码，返回 (c_expr_str, [c_decl_stmts])"""
        if isinstance(node, NumberNode):
            if isinstance(node.value, int):
                return (str(node.value), [])
            return (str(node.value), [])

        elif isinstance(node, StringNode):
            # 转义
            s = node.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            return (f'"{s}"', [])

        elif isinstance(node, BoolNode):
            return ("1" if node.value else "0", [])

        elif isinstance(node, IdentNode):
            return (node.name, [])

        elif isinstance(node, BinOpNode):
            left_str, left_decls = self.gen_expr(node.left)
            right_str, right_decls = self.gen_expr(node.right)

            # C 操作符几乎和文语言一样
            op_map = {"+": "+", "-": "-", "*": "*", "/": "/",
                      "==": "==", "!=": "!=", "<": "<", ">": ">",
                      "<=": "<=", ">=": ">=", "或": "||", "且": "&&",
                      "%": "%"}
            c_op = op_map.get(node.op, node.op)
            result = f"({left_str} {c_op} {right_str})"
            return (result, left_decls + right_decls)

        elif isinstance(node, UnaryOpNode):
            val_str, val_decls = self.gen_expr(node.expr)
            if node.op == "负":
                return (f"(-{val_str})", val_decls)
            elif node.op == "非":
                return (f"(!{val_str})", val_decls)
            return (val_str, val_decls)

        elif isinstance(node, CallNode):
            name = node.name if isinstance(node.name, str) else str(node.name)
            args_strs = []
            args_decls = []
            for arg in node.args:
                a_str, a_decl = self.gen_expr(arg)
                args_strs.append(a_str)
                args_decls.extend(a_decl)

            # 内置映射
            builtin_map = {
                "示": "wen_print",
                "长": "wen_len",
                "整": "wen_int",
                "文": "wen_str",
                "浮": "wen_float",
                "类型": "wen_type",
                "随机数": "wen_random",
                "范围": "wen_range",
            }
            c_name = builtin_map.get(name, name)
            return (f"{c_name}({', '.join(args_strs)})", args_decls)

        elif isinstance(node, IndexNode):
            expr_str, expr_decls = self.gen_expr(node.expr)
            idx_str, idx_decls = self.gen_expr(node.index)
            return (f"wen_index({expr_str}, {idx_str})", expr_decls + idx_decls)

        elif isinstance(node, ListNode):
            items = []
            decls = []
            for item in node.items:
                i_str, i_decl = self.gen_expr(item)
                items.append(i_str)
                decls.extend(i_decl)
            t = self.new_temp()
            items_str = ", ".join(items)
            return (t, decls + [f"wen_list_t {t} = wen_list_make({len(items)}, (wen_value_t[]){{{items_str}}});"])

        elif isinstance(node, DictNode):
            t = self.new_temp()
            decls = []
            dict_items = []
            for k, v in node.pairs:
                ks, kd = self.gen_expr(k)
                vs, vd = self.gen_expr(v)
                decls.extend(kd + vd)
                dict_items.append((ks, vs))
            d_str = ", ".join(f"{{{k}, {v}}}" for k, v in dict_items)
            return (t, decls + [f"wen_dict_t {t} = wen_dict_make({len(dict_items)}, (wen_pair_t[]){{{d_str}}});"])

        return ("0", [])

    def gen_stmt(self, node):
        """生成语句 C 代码，返回 [c_lines]"""
        lines = []

        if isinstance(node, AssignNode):
            val_str, val_decls = self.gen_expr(node.value)
            lines.extend(val_decls)
            if isinstance(node.name, str):
                lines.append(f"long long {node.name} = {val_str};")

        elif isinstance(node, CallNode):
            name = node.name if isinstance(node.name, str) else str(node.name)
            if name == "示":
                args_strs = []
                args_decls = []
                for arg in node.args:
                    a_str, a_decl = self.gen_expr(arg)
                    args_strs.append(a_str)
                    args_decls.extend(a_decl)
                lines.extend(args_decls)
                for a in args_strs:
                    # 检测是否为字符串字面量
                    if a.startswith('"'):
                        lines.append(f'printf("%s\\n", {a});')
                    else:
                        lines.append(f'printf("%lld\\n", (long long)({a}));')
            else:
                expr_str, expr_decls = self.gen_expr(node)
                lines.extend(expr_decls)
                lines.append(f"{expr_str};")

        elif isinstance(node, IfNode):
            for i, (condition, body) in enumerate(node.branches):
                if condition == "else":
                    lines.append("else {")
                    self.indent += 1
                    for s in body.statements:
                        for l in self.gen_stmt(s):
                            lines.append(l)
                    self.indent -= 1
                    lines.append("}")
                else:
                    cond_str, cond_decls = self.gen_expr(condition)
                    lines.extend(cond_decls)
                    kw = "if" if i == 0 else "else if"
                    lines.append(f"{kw} ({cond_str}) {{")
                    self.indent += 1
                    for s in body.statements:
                        for l in self.gen_stmt(s):
                            lines.append(l)
                    self.indent -= 1
                    lines.append("}")

        elif isinstance(node, ForNode):
            iter_str, iter_decls = self.gen_expr(node.iterable)
            lines.extend(iter_decls)
            var = node.var
            lines.append("{")
            self.indent += 1
            lines.append(f"long long _end = wen_len({iter_str});")
            lines.append(f"for (long long _i = 0; _i < _end; _i++) {{")
            self.indent += 1
            lines.append(f"long long {var} = wen_index({iter_str}, _i);")
            for s in node.body.statements:
                for l in self.gen_stmt(s):
                    lines.append(l)
            self.indent -= 1
            lines.append("}")
            self.indent -= 1
            lines.append("}")

        elif isinstance(node, WhileNode):
            cond_str, cond_decls = self.gen_expr(node.condition)
            lines.extend(cond_decls)
            lines.append(f"while ({cond_str}) {{")
            self.indent += 1
            for s in node.body.statements:
                for l in self.gen_stmt(s):
                    lines.append(l)
            self.indent -= 1
            lines.append("}")

        elif isinstance(node, ReturnNode):
            val_str, val_decls = self.gen_expr(node.expr)
            lines.extend(val_decls)
            lines.append(f"return {val_str};")

        elif isinstance(node, FuncDefNode):
            params = ", ".join(f"long long {p}" for p in node.params)
            lines.append(f"long long {node.name}({params}) {{")
            self.indent += 1
            for s in node.body.statements:
                for l in self.gen_stmt(s):
                    lines.append(l)
            self.indent -= 1
            lines.append("}")
            # Also add to funcs dict
            self.funcs[node.name] = len(node.params)

        elif isinstance(node, BlockNode):
            for s in node.statements:
                for l in self.gen_stmt(s):
                    lines.append(l)

        else:
            expr_str, expr_decls = self.gen_expr(node)
            lines.extend(expr_decls)
            lines.append(f"{expr_str};")

        return lines

    def generate(self, ast):
        """生成完整 C 程序"""
        lines = []

        # 头文件
        lines.append("/* 文语言 → C (Wen → C Native Compiler) */")
        lines.append("#include <stdio.h>")
        lines.append("#include <stdlib.h>")
        lines.append("#include <string.h>")
        lines.append("#include <time.h>")
        lines.append("")

        lines.append("/* 运行时 */")
        lines.append("typedef long long wen_value_t;")
        lines.append("long long wen_len(void* p) { return *(long long*)p; }")
        lines.append("")

        # 收集函数定义和非函数语句
        func_defs = []
        body_stmts = []

        if isinstance(ast, BlockNode):
            for stmt in ast.statements:
                if isinstance(stmt, FuncDefNode):
                    func_defs.append(stmt)
                else:
                    body_stmts.append(stmt)

        # 前置声明
        for fd in func_defs:
            params = ", ".join(f"long long {p}" for p in fd.params)
            lines.append(f"long long {fd.name}({params});")
        lines.append("")

        # 函数定义
        for fd in func_defs:
            params = ", ".join(f"long long {p}" for p in fd.params)
            lines.append(f"long long {fd.name}({params}) {{")
            self.indent += 1
            for s in fd.body.statements:
                for l in self.gen_stmt(s):
                    lines.append("    " + l)
            self.indent -= 1
            lines.append("}")
            lines.append("")

        # main
        lines.append("int main() {")
        lines.append(f"    srand((unsigned)time(NULL));")
        for stmt in body_stmts:
            for l in self.gen_stmt(stmt):
                lines.append("    " + l)
        lines.append("    return 0;")
        lines.append("}")

        return "\n".join(lines)


def compile_wen_to_c(source_path, c_path=None):
    """编译 .wen → .c"""
    if c_path is None:
        c_path = os.path.splitext(source_path)[0] + ".c"

    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    lexer = WenLexer(source)
    tokens = lexer.tokenize()
    parser = WenParser(tokens)
    ast = parser.parse_program()

    gen = CCodeGen()
    c_code = gen.generate(ast)

    with open(c_path, "w", encoding="utf-8-sig") as f:
        f.write(c_code)

    print(f"  生成 C 代码: {c_path}")
    return c_path


def find_c_compiler():
    """查找可用的 C 编译器"""
    for cmd in ["gcc", "clang", "tcc", "cc"]:
        path = shutil.which(cmd)
        if path: return path

    # MSVC cl.exe — 需要找到 vcvars64.bat 来设置环境
    for vs_base in [r"C:\Program Files\Microsoft Visual Studio\2022",
                     r"C:\Program Files (x86)\Microsoft Visual Studio\2022",
                     r"C:\Program Files\Microsoft Visual Studio\2019"]:
        if os.path.exists(vs_base):
            for edition in ["Community", "Professional", "Enterprise", "BuildTools"]:
                vs_dir = os.path.join(vs_base, edition)
                if not os.path.exists(vs_dir): continue
                # 找 vcvars
                vcvars = os.path.join(vs_dir, "VC", "Auxiliary", "Build", "vcvars64.bat")
                if os.path.exists(vcvars):
                    return ("msvc", vcvars)
    return None


def compile_with_msvc(c_path, exe_path, vcvars_path):
    """使用 MSVC 编译"""
    import tempfile
    # 写一个临时批处理文件
    batch_content = f'@echo off\r\ncall "{vcvars_path}"\r\ncl.exe /nologo /O2 "{c_path}" /Fe:"{exe_path}"\r\n'
    tmp_bat = os.path.join(tempfile.gettempdir(), "_wen_build.bat")
    with open(tmp_bat, "w") as f:
        f.write(batch_content)
    result = subprocess.run(["cmd", "/c", tmp_bat], capture_output=True, text=True,
                          encoding="gbk", errors="replace")
    try: os.remove(tmp_bat)
    except: pass
    return result.returncode == 0, result.stdout + result.stderr


def compile_to_exe(source_path, exe_path, keep_c=False):
    """编译 .wen → .exe (via C)"""
    c_path = os.path.splitext(source_path)[0] + ".c"
    compile_wen_to_c(source_path, c_path)

    cc = find_c_compiler()
    if not cc:
        print(f"  [提示] 未找到 C 编译器。C 代码已生成：{c_path}")
        print(f"  安装 MinGW-w64 (gcc) 后运行:")
        print(f"    gcc -O2 {c_path} -o {exe_path}")
        return None

    print(f"  编译: {c_path} → {exe_path}")

    if isinstance(cc, tuple) and cc[0] == "msvc":
        ok, output = compile_with_msvc(c_path, exe_path, cc[1])
        if not ok:
            print(f"  编译错误:\n{output}")
            return None
    else:
        result = subprocess.run([cc, "-O2", c_path, "-o", exe_path],
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  编译错误:\n{result.stderr}")
            return None

    if not keep_c:
        os.remove(c_path)

    print(f"  编译完成: {exe_path}  ({os.path.getsize(exe_path)} 字节)")
    return exe_path


def main():
    if len(sys.argv) < 2:
        print("文 → C → x86-64 原生编译器")
        print()
        print("用法:")
        print("  py wen_c.py  源.wen              生成 .c 文件")
        print("  py wen_c.py  源.wen  -o out.exe   生成 .exe")
        print("  py wen_c.py  源.wen  --run        编译并运行")
        print()
        print("需要 C 编译器: gcc / clang / tcc")
        print("  MinGW-w64: https://www.mingw-w64.org/")
        print("  TCC:       https://bellard.org/tcc/")
        return

    src = sys.argv[1]
    out = os.path.splitext(os.path.basename(src))[0] + ".exe"

    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        out = sys.argv[idx + 1]

    exe = compile_to_exe(src, out)

    if exe and "--run" in sys.argv:
        print(f"\n  运行 {exe}:\n")
        os.system(exe)


if __name__ == "__main__":
    main()

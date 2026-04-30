# -*- coding: utf-8 -*-
r"""
文 语 言  (Wen Language)
============================================================
一种可直接用于开发的中文编程语言。

不是翻译。不是套壳。语法来自中文的自然表达习惯。

变量：    令 名 = 值
函数：    定 函数名 ( 参数 ) ：
            语句...
         结束
条件：    若 条件 ：
            语句...
         或若 条件 ：
            语句...
         否则 ：
            语句...
         结束
循环：    历 项 在 列表 ：
            语句...
         结束
         | 当 条件 ：
            语句...
         结束
输出：    示 值
输入：    听 → 变量
列表：    [ 项1, 项2, 项3 ]
字典：    { 键: 值, 键: 值 }
字符串：   "内容"
注释：    ； 单行注释

运行：  py wen_lang.py run 文件.wen
       py wen_lang.py           ; 进入对话模式
"""

import sys, os, re, math, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from suanchou_vm import SuanChouVM
from suanchou_zupu import SuanChouZupuAssembler
from suanchou_isa import SuanChouOpcode
from counting_rod_computer import CountingRodNumber, CountingRodBit
from stroke_dictionary import StrokeDictionary, Character
from extended_strokes import EXTENDED_STROKE_DATA


# ═══════════════════════════════════════════════════════════════
#  词法分析器
# ═══════════════════════════════════════════════════════════════

class Token:
    def __init__(self, kind, value, line=0, col=0):
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"<{self.kind}:{self.value}>"


# 关键词（均为中文单字或双字，不是英文翻译）
KEYWORDS = {
    # 声明
    "令": "LET",      # let — 声明变量
    "定": "DEF",      # define — 定义函数
    "结束": "END",    # end — 块结束
    "返回": "RETURN", # return — 返回
    # 控制流
    "若": "IF",
    "或若": "ELIF",
    "否则": "ELSE",
    "历": "FOR",      # for-each
    "在": "IN",
    "当": "WHILE",    # while
    # 逻辑
    "且": "AND",
    "或": "OR",
    "非": "NOT",
    # 字面量
    "是": "TRUE",
    "否": "FALSE",
    "空": "NULL",
    # 导入
    "引": "IMPORT",
}

# 单字符标记
SINGLE_CHARS = {
    "+": "PLUS", "-": "MINUS", "*": "MULT", "/": "DIV",
    "=": "EQ", "(": "LPAREN", ")": "RPAREN",
    "[": "LBRACKET", "]": "RBRACKET",
    "{": "LBRACE", "}": "RBRACE",
    ",": "COMMA", ":": "COLON", "：": "COLON",
    ">": "GT", "<": "LT",
    "→": "ARROW",
}

# 双字符标记
DOUBLE_CHARS = {
    "==": "EQEQ", "!=": "NEQ",
    ">=": "GTE", "<=": "LTE",
}


class WenLexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def tokenize(self):
        tokens = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]

            # 跳过空白
            if ch in " \t\r":
                self.pos += 1
                self.col += 1
                continue

            # 换行
            if ch == "\n":
                self.pos += 1
                self.line += 1
                self.col = 1
                tokens.append(Token("NEWLINE", "\n", self.line - 1, 0))
                continue

            # 注释（中英文分号，到行末）
            if ch in "；;":
                while self.pos < len(self.source) and self.source[self.pos] != "\n":
                    self.pos += 1
                continue

            # 字符串
            if ch == '"':
                self.pos += 1
                start = self.pos
                while self.pos < len(self.source) and self.source[self.pos] != '"':
                    if self.source[self.pos] == '\\':
                        self.pos += 1
                    self.pos += 1
                s = self.source[start:self.pos]
                self.pos += 1  # skip closing "
                tokens.append(Token("STRING", s, self.line, self.col))
                self.col += len(s) + 2
                continue

            # 数字
            if ch.isdigit() or (ch == "." and self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit()):
                start = self.pos
                while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == "."):
                    self.pos += 1
                num_str = self.source[start:self.pos]
                tokens.append(Token("NUMBER", float(num_str) if "." in num_str else int(num_str),
                                    self.line, self.col))
                self.col += self.pos - start
                continue

            # 中文字标识符
            if "\u4e00" <= ch <= "\u9fff" or ch == "_" or ch.isalpha():
                start = self.pos
                while self.pos < len(self.source):
                    c = self.source[self.pos]
                    if "\u4e00" <= c <= "\u9fff" or c.isalpha() or c.isdigit() or c == "_":
                        self.pos += 1
                    else:
                        break
                word = self.source[start:self.pos]
                kind = KEYWORDS.get(word, "IDENT")
                tokens.append(Token(kind, word, self.line, self.col))
                self.col += self.pos - start
                continue

            # 双字符标记
            if self.pos + 1 < len(self.source):
                two = self.source[self.pos:self.pos + 2]
                if two in DOUBLE_CHARS:
                    tokens.append(Token(DOUBLE_CHARS[two], two, self.line, self.col))
                    self.pos += 2
                    self.col += 2
                    continue

            # 单字符标记
            if ch in SINGLE_CHARS:
                tokens.append(Token(SINGLE_CHARS[ch], ch, self.line, self.col))
                self.pos += 1
                self.col += 1
                continue

            self.pos += 1
            self.col += 1

        tokens.append(Token("EOF", "", self.line, self.col))
        return tokens


# ═══════════════════════════════════════════════════════════════
#  AST 节点
# ═══════════════════════════════════════════════════════════════

class ASTNode:
    pass


class NumberNode(ASTNode):
    def __init__(self, value): self.value = value
    def __repr__(self): return f"数({self.value})"


class StringNode(ASTNode):
    def __init__(self, value): self.value = value
    def __repr__(self): return f"文({self.value})"


class IdentNode(ASTNode):
    def __init__(self, name): self.name = name
    def __repr__(self): return f"名({self.name})"


class BoolNode(ASTNode):
    def __init__(self, value): self.value = value
    def __repr__(self): return f"是" if self.value else f"否"


class ListNode(ASTNode):
    def __init__(self, items): self.items = items
    def __repr__(self): return f"列({self.items})"


class DictNode(ASTNode):
    def __init__(self, pairs): self.pairs = pairs  # [(key, value), ...]
    def __repr__(self): return f"册({self.pairs})"


class BinOpNode(ASTNode):
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right
    def __repr__(self): return f"({self.left} {self.op} {self.right})"


class UnaryOpNode(ASTNode):
    def __init__(self, op, expr): self.op = op; self.expr = expr
    def __repr__(self): return f"({self.op} {self.expr})"


class CallNode(ASTNode):
    def __init__(self, name, args): self.name = name; self.args = args
    def __repr__(self): return f"调({self.name}, {self.args})"


class AssignNode(ASTNode):
    def __init__(self, name, value): self.name = name; self.value = value
    def __repr__(self): return f"令{self.name}={self.value}"


class IndexNode(ASTNode):
    def __init__(self, expr, index): self.expr = expr; self.index = index
    def __repr__(self): return f"{self.expr}[{self.index}]"


class ReturnNode(ASTNode):
    def __init__(self, expr): self.expr = expr
    def __repr__(self): return f"返回({self.expr})"


class IfNode(ASTNode):
    def __init__(self, branches):
        # [(condition, body), ...] 最后一个可能是 ("else", body)
        self.branches = branches
    def __repr__(self): return f"若({self.branches})"


class ForNode(ASTNode):
    def __init__(self, var, iterable, body): self.var = var; self.iterable = iterable; self.body = body
    def __repr__(self): return f"历{self.var}在{self.iterable}"


class WhileNode(ASTNode):
    def __init__(self, condition, body): self.condition = condition; self.body = body
    def __repr__(self): return f"当{self.condition}"


class BlockNode(ASTNode):
    def __init__(self, statements): self.statements = statements
    def __repr__(self): return f"块({len(self.statements)})"


class FuncDefNode(ASTNode):
    def __init__(self, name, params, body): self.name = name; self.params = params; self.body = body
    def __repr__(self): return f"定{self.name}({self.params})"


class ImportNode(ASTNode):
    def __init__(self, module): self.module = module
    def __repr__(self): return f"引({self.module})"


# ═══════════════════════════════════════════════════════════════
#  语法分析器（递归下降）
# ═══════════════════════════════════════════════════════════════

class WenParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        pos = self.pos + offset
        return self.tokens[pos] if pos < len(self.tokens) else Token("EOF", "")

    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def skip_newlines(self):
        while self.peek().kind == "NEWLINE":
            self.advance()

    def expect(self, kind):
        tok = self.peek()
        if tok.kind != kind:
            raise SyntaxError(f"行{tok.line}: 期望 {kind}，得到 {tok.kind}:{tok.value}")
        return self.advance()

    def parse_program(self):
        stmts = []
        while self.peek().kind != "EOF":
            self.skip_newlines()
            if self.peek().kind == "EOF":
                break
            stmts.append(self.parse_statement())
        return BlockNode(stmts)

    def parse_statement(self):
        tok = self.peek()

        if tok.kind == "LET":  # 令
            return self.parse_assign()

        if tok.kind == "DEF":  # 定
            return self.parse_func_def()

        if tok.kind == "IF":  # 若
            return self.parse_if()

        if tok.kind == "FOR":  # 历
            return self.parse_for()

        if tok.kind == "WHILE":  # 当
            return self.parse_while()

        if tok.kind == "RETURN":  # 返回
            self.advance()
            if self.peek().kind == "NEWLINE" or self.peek().kind == "EOF":
                return ReturnNode(StringNode(""))
            expr = self.parse_expression()
            return ReturnNode(expr)

        if tok.kind == "IMPORT":  # 引
            self.advance()
            mod = self.expect("STRING")
            return ImportNode(mod.value)

        if tok.kind == "IDENT":
            # 可能是赋值或表达式语句
            name = tok.value
            self.advance()
            # 检查是否是索引赋值: 标识符 [ ... ] =
            if self.peek().kind == "LBRACKET":
                # This is an index expression, let parse_expression handle it
                self.pos -= 1  # backtrack
                expr = self.parse_expression()
                if self.peek().kind == "EQ" and self.peek(1).kind != "EQ":
                    self.advance()
                    value = self.parse_expression()
                    if isinstance(expr, IndexNode):
                        return AssignNode(("__index__", expr.expr, expr.index), value)
                return expr
            if self.peek().kind == "EQ" and self.peek(1).kind != "EQ":
                self.advance()  # consume =
                value = self.parse_expression()
                return AssignNode(name, value)
            else:
                # 函数调用作为语句
                self.pos -= 1  # 回退
                return self.parse_expression()

        # 表达式语句
        expr = self.parse_expression()
        return expr

    def parse_assign(self):
        self.expect("LET")
        name = self.expect("IDENT").value
        self.expect("EQ")
        value = self.parse_expression()
        return AssignNode(name, value)

    def parse_func_def(self):
        self.expect("DEF")
        name = self.expect("IDENT").value
        self.expect("LPAREN")
        params = []
        while self.peek().kind != "RPAREN":
            if self.peek().kind == "COMMA":
                self.advance()
            else:
                params.append(self.expect("IDENT").value)
        self.expect("RPAREN")
        self.expect("COLON")
        body = self.parse_block()
        self.expect("END")
        return FuncDefNode(name, params, body)

    def parse_block(self):
        stmts = []
        while True:
            self.skip_newlines()
            tok = self.peek()
            if tok.kind == "END" or tok.kind == "ELIF" or tok.kind == "ELSE" or tok.kind == "EOF":
                break
            stmts.append(self.parse_statement())
        return BlockNode(stmts)

    def parse_if(self):
        self.expect("IF")
        condition = self.parse_expression()
        self.expect("COLON")
        body = self.parse_block()
        branches = [(condition, body)]

        while self.peek().kind == "ELIF":
            self.advance()
            condition = self.parse_expression()
            self.expect("COLON")
            body = self.parse_block()
            branches.append((condition, body))

        if self.peek().kind == "ELSE":
            self.advance()
            self.expect("COLON")
            body = self.parse_block()
            branches.append(("else", body))

        self.expect("END")
        return IfNode(branches)

    def parse_for(self):
        self.expect("FOR")
        var = self.expect("IDENT").value
        self.expect("IN")
        iterable = self.parse_expression()
        self.expect("COLON")
        body = self.parse_block()
        self.expect("END")
        return ForNode(var, iterable, body)

    def parse_while(self):
        self.expect("WHILE")
        condition = self.parse_expression()
        self.expect("COLON")
        body = self.parse_block()
        self.expect("END")
        return WhileNode(condition, body)

    # ── 表达式解析 ──

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.peek().kind == "OR":
            self.advance()
            right = self.parse_and()
            left = BinOpNode(left, "或", right)
        return left

    def parse_and(self):
        left = self.parse_comparison()
        while self.peek().kind == "AND":
            self.advance()
            right = self.parse_comparison()
            left = BinOpNode(left, "且", right)
        return left

    def parse_comparison(self):
        left = self.parse_addition()
        tok = self.peek()
        if tok.kind in ("EQEQ", "NEQ", "LT", "GT", "LTE", "GTE"):
            self.advance()
            right = self.parse_addition()
            return BinOpNode(left, tok.value, right)
        return left

    def parse_addition(self):
        left = self.parse_multiplication()
        while self.peek().kind in ("PLUS", "MINUS"):
            op = self.advance().kind
            right = self.parse_multiplication()
            left = BinOpNode(left, "+" if op == "PLUS" else "-", right)
        return left

    def parse_multiplication(self):
        left = self.parse_unary()
        while self.peek().kind in ("MULT", "DIV"):
            op = self.advance().kind
            right = self.parse_unary()
            left = BinOpNode(left, "*" if op == "MULT" else "/", right)
        return left

    def parse_unary(self):
        tok = self.peek()
        if tok.kind == "MINUS":
            self.advance()
            return UnaryOpNode("负", self.parse_unary())
        if tok.kind == "NOT":
            self.advance()
            return UnaryOpNode("非", self.parse_unary())
        return self.parse_atom()

    def parse_atom(self):
        tok = self.peek()

        if tok.kind == "NUMBER":
            self.advance()
            return NumberNode(tok.value)

        if tok.kind == "STRING":
            self.advance()
            return StringNode(tok.value)

        if tok.kind == "TRUE":
            self.advance()
            return BoolNode(True)

        if tok.kind == "FALSE":
            self.advance()
            return BoolNode(False)

        if tok.kind == "NULL":
            self.advance()
            return StringNode("空")

        if tok.kind == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.expect("RPAREN")
            return expr

        if tok.kind == "LBRACKET":
            # 列表
            self.advance()
            items = []
            while self.peek().kind != "RBRACKET":
                items.append(self.parse_expression())
                if self.peek().kind == "COMMA":
                    self.advance()
            self.expect("RBRACKET")
            return ListNode(items)

        if tok.kind == "LBRACE":
            # 字典
            self.advance()
            pairs = []
            while self.peek().kind != "RBRACE":
                key = self.parse_expression()
                self.expect("COLON")
                value = self.parse_expression()
                pairs.append((key, value))
                if self.peek().kind == "COMMA":
                    self.advance()
            self.expect("RBRACE")
            return DictNode(pairs)

        if tok.kind == "IDENT":
            name = self.advance().value
            # 函数调用？
            if self.peek().kind == "LPAREN":
                self.advance()
                args = []
                while self.peek().kind != "RPAREN":
                    args.append(self.parse_expression())
                    if self.peek().kind == "COMMA":
                        self.advance()
                self.expect("RPAREN")
                return CallNode(name, args)
            # 索引？
            if self.peek().kind == "LBRACKET":
                self.advance()
                index = self.parse_expression()
                self.expect("RBRACKET")
                return IndexNode(IdentNode(name), index)
            return IdentNode(name)

        raise SyntaxError(f"行{tok.line}: 无法解析 '{tok.value}' ({tok.kind})")


# ═══════════════════════════════════════════════════════════════
#  运行时
# ═══════════════════════════════════════════════════════════════

class ReturnSignal(Exception):
    """函数返回信号"""
    def __init__(self, value):
        self.value = value


class WenRuntime:
    def __init__(self):
        self.globals = {}
        self.functions = {}
        self._init_builtins()

    def _init_builtins(self):
        # 内置函数
        self.functions["示"] = self._builtin_show
        self.functions["听"] = self._builtin_listen
        self.functions["长"] = self._builtin_len
        self.functions["整"] = self._builtin_int
        self.functions["文"] = self._builtin_str
        self.functions["浮"] = self._builtin_float
        self.functions["范围"] = self._builtin_range
        self.functions["加项"] = self._builtin_append
        self.functions["排序"] = self._builtin_sort
        self.functions["随机数"] = self._builtin_random
        self.functions["时间"] = self._builtin_time
        self.functions["类型"] = self._builtin_type
        self.functions["印"] = self._builtin_show  # 别名

        # 算筭指令暴露为函数
        self.functions["识"] = self._builtin_rod_char
        self.functions["校"] = self._builtin_rod_cmp
        self.functions["合"] = self._builtin_rod_merge
        self.functions["交"] = self._builtin_rod_overlap

        # 字符数据
        self._load_char_data()

    def _load_char_data(self):
        self.char_data = {}
        self.char_by_name = {}
        dic = StrokeDictionary()
        for cn, data in EXTENDED_STROKE_DATA.items():
            if cn in dic._characters:
                obj = dic._characters[cn]
            else:
                obj = Character(char=cn, stroke_sequence=data["strokes"],
                                meaning=data["meaning"], radical=data["radical"],
                                category=data["category"],
                                semantic_tags=data["tags"], pinyin=data["pinyin"])
            if obj._encoded is None:
                obj.encode()
            self.char_data[cn] = obj
            self.char_by_name[cn] = {
                "字": obj.char, "义": obj.meaning, "音": obj.pinyin,
                "画": obj.stroke_count, "部": obj.radical, "类": obj.category,
                "签": obj.semantic_tags,
            }

    # ── 内置函数 ──
    def _builtin_show(self, *args):
        for a in args:
            print(a, end=" ")
        print()

    def _builtin_listen(self, prompt=""):
        return input(prompt)

    def _builtin_len(self, x):
        return len(x) if hasattr(x, "__len__") else 0

    def _builtin_int(self, x):
        return int(float(x)) if isinstance(x, (int, float, str)) else 0

    def _builtin_str(self, x):
        return str(x)

    def _builtin_float(self, x):
        return float(x)

    def _builtin_range(self, *args):
        if len(args) == 1:
            return list(range(int(args[0])))
        elif len(args) == 2:
            return list(range(int(args[0]), int(args[1])))
        return list(range(int(args[0]), int(args[1]), int(args[2])))

    def _builtin_append(self, lst, item):
        if isinstance(lst, list):
            lst.append(item)
        return lst

    def _builtin_sort(self, lst):
        if isinstance(lst, list):
            return sorted(lst)
        return lst

    def _builtin_random(self, a, b=None):
        if b is None:
            return random.randint(0, int(a))
        return random.randint(int(a), int(b))

    def _builtin_time(self):
        return time.time()

    def _builtin_type(self, x):
        t = type(x).__name__
        mp = {"int": "数", "float": "浮", "str": "文", "list": "列",
              "dict": "册", "bool": "是非", "NoneType": "空"}
        return mp.get(t, t)

    def _builtin_rod_char(self, code):
        """识字：从算筭码查汉字"""
        from counting_rod_computer import CountingRodNumber
        rn = CountingRodNumber(int(code))
        rod_str = rn.to_rod_string()
        for cn, obj in self.char_data.items():
            if obj._encoded and obj._encoded.to_rod_string() == rod_str:
                return self.char_by_name.get(cn, {"字": cn})
        return {"字": "?"}

    def _builtin_rod_cmp(self, cn1, cn2):
        """校字：比较两个字的差异和共同"""
        o1 = self.char_data.get(cn1)
        o2 = self.char_data.get(cn2)
        if o1 and o2:
            v1 = sum(1 << j for j, b in enumerate(o1._encoded._bits) if b.is_on)
            v2 = sum(1 << j for j, b in enumerate(o2._encoded._bits) if b.is_on)
            return {"差异": v1 ^ v2, "共同": v1 & v2}
        return {"差异": 0, "共同": 0}

    def _builtin_rod_merge(self, cn1, cn2):
        """合字：合并两个字"""
        o1 = self.char_data.get(cn1)
        o2 = self.char_data.get(cn2)
        if o1 and o2:
            v1 = sum(1 << j for j, b in enumerate(o1._encoded._bits) if b.is_on)
            v2 = sum(1 << j for j, b in enumerate(o2._encoded._bits) if b.is_on)
            return v1 | v2
        return 0

    def _builtin_rod_overlap(self, cn1, cn2):
        """交字：找共同笔画"""
        o1 = self.char_data.get(cn1)
        o2 = self.char_data.get(cn2)
        if o1 and o2:
            v1 = sum(1 << j for j, b in enumerate(o1._encoded._bits) if b.is_on)
            v2 = sum(1 << j for j, b in enumerate(o2._encoded._bits) if b.is_on)
            return v1 & v2
        return 0

    # ── 求值 ──
    def evaluate(self, node, scope=None):
        if scope is None:
            scope = self.globals
        return self._eval(node, scope)

    def _eval(self, node, scope):
        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, StringNode):
            return node.value

        if isinstance(node, BoolNode):
            return node.value

        if isinstance(node, IdentNode):
            if node.name in scope:
                return scope[node.name]
            if node.name in self.functions:
                return self.functions[node.name]
            if node.name in self.globals:
                return self.globals[node.name]
            raise NameError(f"未定义: {node.name}")

        if isinstance(node, ListNode):
            return [self._eval(item, scope) for item in node.items]

        if isinstance(node, DictNode):
            return {self._eval(k, scope): self._eval(v, scope) for k, v in node.pairs}

        if isinstance(node, BinOpNode):
            left = self._eval(node.left, scope)
            right = self._eval(node.right, scope)

            if node.op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            elif node.op == "-":
                return left - right
            elif node.op == "*":
                return left * right
            elif node.op == "/":
                return left // right if isinstance(left, int) and isinstance(right, int) else left / right
            elif node.op == "或":
                return left or right
            elif node.op == "且":
                return left and right
            elif node.op == "==":
                return left == right
            elif node.op == "!=":
                return left != right
            elif node.op == "<":
                return left < right
            elif node.op == ">":
                return left > right
            elif node.op == "<=":
                return left <= right
            elif node.op == ">=":
                return left >= right

        if isinstance(node, UnaryOpNode):
            v = self._eval(node.expr, scope)
            if node.op == "负":
                return -v
            if node.op == "非":
                return not v

        if isinstance(node, CallNode):
            func = self._eval(node.name, scope) if isinstance(node.name, IdentNode) else (
                self.functions.get(node.name, None))
            if func is None:
                # 用户自定义函数
                func = self.functions.get(node.name)
            if func is None:
                raise NameError(f"未定义函数: {node.name}")

            args = [self._eval(a, scope) for a in node.args]

            if callable(func):
                return func(*args)

            # 用户定义函数 (ast FuncDefNode)
            local_scope = dict(scope)
            for param, arg in zip(func.params, args):
                local_scope[param] = arg

            try:
                for stmt in func.body.statements:
                    self._eval(stmt, local_scope)
                return "空"
            except ReturnSignal as rs:
                return rs.value

        if isinstance(node, AssignNode):
            value = self._eval(node.value, scope)
            if isinstance(node.name, tuple) and node.name[0] == "__index__":
                # Indexed assignment: 列[位] = 值
                obj = self._eval(node.name[1], scope)
                idx = self._eval(node.name[2], scope)
                if isinstance(obj, list):
                    obj[idx] = value
                elif isinstance(obj, dict):
                    obj[idx] = value
                return value
            scope[node.name] = value
            return value

        if isinstance(node, IndexNode):
            obj = self._eval(node.expr, scope)
            idx = self._eval(node.index, scope)
            if isinstance(obj, list):
                if isinstance(idx, int) and 0 <= idx < len(obj):
                    return obj[idx]
            if isinstance(obj, dict):
                return obj.get(idx, None)
            if isinstance(obj, str) and isinstance(idx, int):
                return obj[idx]
            return None

        if isinstance(node, ReturnNode):
            raise ReturnSignal(self._eval(node.expr, scope))

        if isinstance(node, IfNode):
            for condition, body in node.branches:
                if condition == "else" or self._eval(condition, scope):
                    try:
                        for stmt in body.statements:
                            self._eval(stmt, scope)
                    except ReturnSignal:
                        raise
                    return None
            return None

        if isinstance(node, ForNode):
            iterable = self._eval(node.iterable, scope)
            if not hasattr(iterable, "__iter__"):
                iterable = [iterable]
            for item in iterable:
                scope[node.var] = item
                try:
                    for stmt in node.body.statements:
                        self._eval(stmt, scope)
                except ReturnSignal:
                    raise
            return None

        if isinstance(node, WhileNode):
            while self._eval(node.condition, scope):
                try:
                    for stmt in node.body.statements:
                        self._eval(stmt, scope)
                except ReturnSignal:
                    raise
            return None

        if isinstance(node, BlockNode):
            try:
                for stmt in node.statements:
                    self._eval(stmt, scope)
            except ReturnSignal:
                raise
            return None

        if isinstance(node, FuncDefNode):
            self.functions[node.name] = node
            return f"已定义函数: {node.name}"

        if isinstance(node, ImportNode):
            return self._handle_import(node.module)

        return None

    def _handle_import(self, module):
        if module == "算筭":
            # 加载算筭模块
            self.globals["算筭字库"] = self.char_by_name
            self.functions["查字"] = lambda name: self.char_by_name.get(name, None)
            return "已加载算筭模块"
        return f"模块不存在: {module}"


# ═══════════════════════════════════════════════════════════════
#  顶层 API
# ═══════════════════════════════════════════════════════════════

def run_wen_code(source, runtime=None):
    """执行文语言源码"""
    if runtime is None:
        runtime = WenRuntime()

    lexer = WenLexer(source)
    tokens = lexer.tokenize()

    parser = WenParser(tokens)
    ast = parser.parse_program()

    try:
        result = runtime.evaluate(ast)
    except ReturnSignal as rs:
        result = rs.value
    return result


def run_wen_file(filepath):
    """执行 .wen 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    rt = WenRuntime()
    rt.globals["__文件__"] = filepath
    run_wen_code(source, rt)


def repl():
    """文语言对话模式"""
    rt = WenRuntime()
    print("文语言 v1.0  (输入 '退出' 结束)")
    print("帮助: 示('你好')  令x=5  x+3  定函数...")
    print()

    while True:
        try:
            line = input("文> ")
            if line.strip() in ("退出", "exit", "quit"):
                break
            if not line.strip():
                continue

            result = run_wen_code(line, rt)
            if result is not None and result != "空":
                print(f"  → {result}")

        except SyntaxError as e:
            print(f"  语法错误: {e}")
        except NameError as e:
            print(f"  名字错误: {e}")
        except Exception as e:
            print(f"  错误: {e}")

    print("再见。")


# ═══════════════════════════════════════════════════════════════
#  标准库示例程序
# ═══════════════════════════════════════════════════════════════

DEMO_PROGRAMS = {
    "你好世界.wen": r"""
； 第一个文语言程序
示("你好，世界！")
示("算筭计算，文以载道。")
""",

    "计算器.wen": r"""
； ── 文语言计算器 ──

定 加法 (甲, 乙) ：
  返回 甲 + 乙
结束

定 乘法 (甲, 乙) ：
  返回 甲 * 乙
结束

定 阶乘 (数) ：
  若 数 <= 1 ：
    返回 1
  否则 ：
    返回 数 * 阶乘(数 - 1)
  结束
结束

示("加法 38 + 17 =", 加法(38, 17))
示("乘法 12 * 8 =", 乘法(12, 8))
示("阶乘 5! =", 阶乘(5))
示("阶乘 10! =", 阶乘(10))
""",

    "猜数字.wen": r"""
； ── 猜数字游戏 ──
令 目标 = 随机数(1, 100)
令 机会 = 7
令 猜中 = 否

示("我想了一个 1 到 100 之间的数，你猜猜看。")

当 机会 > 0 且 非 猜中 ：
  示("还剩", 机会, "次机会。")
  令 猜 = 整(听("你的猜测: "))
  若 猜 == 目标 ：
    示("恭喜你猜对了！")
    猜中 = 是
  或若 猜 > 目标 ：
    示("太大了！")
  否则 ：
    示("太小了！")
  结束
  机会 = 机会 - 1
结束

若 非 猜中 ：
  示("很遗憾，答案是", 目标)
结束
""",

    "遍历.wen": r"""
； ── 遍历数组与字典 ──

令 数字序列 = [10, 20, 30, 40, 50]
令 总和 = 0

历 数 在 数字序列 ：
  总和 = 总和 + 数
结束

示("数字:", 数字序列)
示("总和:", 总和)

； 字典
令 学生 = { "姓名": "张三", "年龄": 20, "分数": 95 }

示("学生信息:")
历 键 在 ["姓名", "年龄", "分数"] ：
  示("  ", 键, ":", 学生[键])
结束
""",

    "算筭字库.wen": r"""
； ── 算筭字库查询 ──

引 "算筭"

； 查字
示("查「木」字:")
令 木 = 查字("木")
示("  字:", 木["字"])
示("  义:", 木["义"])
示("  音:", 木["音"])
示("  画:", 木["画"])

示("")

示("查「日」字:")
令 日 = 查字("日")
示("  字:", 日["字"])
示("  义:", 日["义"])
示("  音:", 日["音"])
示("  画:", 日["画"])

示("")
示("校字 木 vs 日:")
令 结果 = 校("木", "日")
示("  差异位:", 结果["差异"])
示("  共同位:", 结果["共同"])
示("  笔画合并:", 合("木", "日"))
""",

    "排序算法.wen": r"""
； ── 冒泡排序（文语言实现） ──

定 冒泡排序 (列) ：
  令 列长 = 长(列)
  历 轮 在 范围(列长) ：
    历 位 在 范围(列长 - 轮 - 1) ：
      若 列[位] > 列[位 + 1] ：
        令 暂存 = 列[位]
        列[位] = 列[位 + 1]
        列[位 + 1] = 暂存
      结束
    结束
  结束
  返回 列
结束

令 数据 = [64, 34, 25, 12, 22, 11, 90]
示("排序前:", 数据)
令 排好 = 冒泡排序(数据)
示("排序后:", 排好)
""",

    "九九乘法表.wen": r"""
； ── 九九乘法表 ──

历 行 在 范围(1, 10) ：
  令 行文 = ""
  历 列 在 范围(1, 行 + 1) ：
    令 行文 = 行文 + 文(列) + "x" + 文(行) + "=" + 文(列 * 行) + "  "
  结束
  示(行文)
结束
""",
}


# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("文语言 v1.0")
        print()
        print("用法:")
        print("  py wen_lang.py                进入对话模式")
        print("  py wen_lang.py run 文件.wen   运行 .wen 文件")
        print("  py wen_lang.py demo           运行所有演示程序")
        print("  py wen_lang.py demo 程序名     运行指定演示")
        print()
        repl()
    elif sys.argv[1] == "run":
        if len(sys.argv) < 3:
            print("请指定 .wen 文件")
        else:
            run_wen_file(sys.argv[2])
    elif sys.argv[1] == "demo":
        if len(sys.argv) > 2:
            name = sys.argv[2]
            if name in DEMO_PROGRAMS:
                print(f"=== {name} ===\n")
                run_wen_code(DEMO_PROGRAMS[name])
            else:
                print(f"演示程序: {list(DEMO_PROGRAMS.keys())}")
        else:
            for name, src in DEMO_PROGRAMS.items():
                print(f"\n{'='*60}")
                print(f"  {name}")
                print(f"{'='*60}")
                try:
                    run_wen_code(src)
                except Exception as e:
                    print(f"  错误: {e}")

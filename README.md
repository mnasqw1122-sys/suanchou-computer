# SuanChou Computer / 算筭计算机

> **Two states can express everything.**
> **—  = ON (1)     |  = OFF (0)**
>
> Bridging ancient Chinese counting rods and modern computing. Bridging Chinese characters and binary logic. A proof of concept that *glyph-level understanding can be modeled as computation*.

***

[中文](#算筭计算机)   |   [English](#suanchou-computer)   |   [Quick Start](#quick-start)   |   [License](#license)

***

## 算筭计算机

### 思想的起点

> 既然古代中国用算筭（— 和 |）就能完成计算，而汉字又由笔画组成 —— 那么能否用算筭来架起计算机与自然语言之间的桥梁？

这个问题的答案是：**可以。** 符号计算的通道是通的。

```
古代算筭 (— / |)
    → 二进制计算 (0 / 1)
    → 汉字笔画编码 (横竖撇捺点折钩提 → 3-bit)
    → 字形 ↔ 语义 映射
    → 算筭码直接编程
```

### 四个核心洞见

**1. 算筭与二进制同构。** — 和 | 就是两种状态，与现代计算机的 0 和 1 完全一致。古代中国人用算筭完成复杂计算这件事本身，就已经证明了「两种状态足以表达一切」。

**2. 汉字可以编码为算筭信号。** 永字八法的八种基本笔画——横竖撇捺点折钩提——每种用 3-bit 编码，任意汉字的「形」就可以无歧义地转化为一串 — 和 | 信号。字形不再是一种模糊的视觉印象，而是一段精确的、可计算的数据。

**3. 「理解」可以建模为「计算」。** 当人眼看到一个汉字时，视觉系统将其笔画转化为神经信号，大脑对这些信号进行模式匹配、联想、推断——这一整套「理解」流程，完全可以用算筭计算来模拟：模式匹配 → 位运算（AND/OR/XOR），语义联想 → 索引查找，关联推断 → 相似度计算。

**4. 算筭码可以原生编程。** 如果数据本身就是 `—` 和 `|`，那就直接在这个层面上写程序。不需要先把算筭码翻译成整数、再翻译成字符串、再翻译回笔画——直接操作算筭信号。ROD\_CHAR 直接识别字符，ROD\_CMP 直接比较字形，ROD\_TAG 直接查询语义。

### 代码做了什么

这是一个完整的概念验证系统（\~2500 行 Python），包含六个层次：

| 层次  | 文件                         | 功能                     | <br />       |
| --- | -------------------------- | ---------------------- | :----------- |
| 物理层 | `counting_rod_computer.py` | — 和                    | 的定义，加减乘除、位运算 |
| 编码层 | `stroke_encoder.py`        | 8 种笔画 ↔ 3-bit 算筭信号     | <br />       |
| 字典层 | `stroke_dictionary.py`     | 130 个汉字的笔画/标签/算筭码多维度索引 | <br />       |
| 理解层 | `semantic_layer.py`        | 字形比较、语义关联、关联图谱         | <br />       |
| 指令层 | `suanchou_isa.py`          | 26 条算筭指令的完整 ISA 定义     | <br />       |
| 执行层 | `suanchou_vm.py`           | 虚算筭拟机 + 算筭汇编器 + 执行引擎   | <br />       |
| 应用层 | `suanchou_search.py`       | 算筭码搜索引擎 + 可视化流水线       | <br />       |

### 验证结果

- **算术运算**：算筭码完成 42 + 13 × 7 = 133，全流程以 — 和 | 表示
- **汉字编解码**：130 个汉字的笔画 ↔ 算筭码往返 100% 一致
- **算筭码精确反查**：任意已收录汉字的算筭码输入 → 100% 精确命中该字
- **字形相似度**：木 vs 本 = 88.9%，木 vs 森 = 50%，符合直观
- **合体字流水线**：木 × 2 = 林（聚集），木 × 3 = 森（繁茂）——算筭码层面清晰可见
- **算筭虚拟机**：支持循环、跳转、比较，执行了完整的算筭汇编程序

##

*「一阴一阳之谓道。」— 《周易·系辞》*

***

## SuanChou Computer

### Where the Idea Comes From

> If ancient China could compute using counting rods (— and |), and Chinese characters are made of strokes — can counting rods bridge the gap between computers and natural language?

The answer is: **Yes.** At the symbolic level, the channel is open.

### Four Core Insights

**1. Counting rods are isomorphic to binary.** — and | are just two states, identical to 0 and 1. The fact that ancient Chinese mathematicians completed complex calculations with counting rods is itself proof that *two states are sufficient to express anything*.

**2. Chinese characters can be encoded as counting-rod signals.** The eight basic strokes (horizontal, vertical, left-falling, right-falling, dot, bend, hook, rising) each encoded in 3 bits. Any Chinese character's *shape* can be losslessly converted into a string of — and | signals.

**3. "Understanding" can be modeled as computation.** Pattern matching → bitwise operations. Semantic association → index lookup. The entire cognitive pipeline can be simulated by counting-rod computation.

**4. Counting-rod code is a native programming paradigm.** If data already lives as — and |, write programs that operate directly on those signals. No translation through integers, strings, or encodings. ROD\_CHAR directly identifies characters. ROD\_CMP directly compares glyphs. ROD\_TAG directly queries semantics.

### What This Project Is

A complete proof-of-concept (\~2500 lines of Python) demonstrating six layers:

| Layer       | File                       | Description                                               | <br />                                             |
| ----------- | -------------------------- | --------------------------------------------------------- | :------------------------------------------------- |
| Physical    | `counting_rod_computer.py` | — and                                                     | as fundamental units; all arithmetic & bitwise ops |
| Encoding    | `stroke_encoder.py`        | 8 strokes ↔ 3-bit counting-rod signals                    | <br />                                             |
| Dictionary  | `stroke_dictionary.py`     | 130 characters with multi-dimensional indices             | <br />                                             |
| Semantic    | `semantic_layer.py`        | Glyph comparison, semantic association, relation graphs   | <br />                                             |
| ISA         | `suanchou_isa.py`          | 26-instruction SuanChou ISA definition                    | <br />                                             |
| VM          | `suanchou_vm.py`           | Virtual machine + assembler for native rod-code execution | <br />                                             |
| Application | `suanchou_search.py`       | Search engine with interactive & visual pipeline modes    | <br />                                             |

### Verifications

- **Arithmetic**: 42 + 13 × 7 = 133, computed entirely with — and |
- **Round-trip encoding**: All 130 characters encode/decode losslessly
- **Exact rod lookup**: Any stored character's rod code → 100% hit rate
- **Glyph similarity**: 木 vs 本 = 88.9%, 木 vs 森 = 50% — matches intuition
- **Compound characters**: 木 × 2 = 林 (aggregation), 木 × 3 = 森 (density) — visible as rod-code repetition
- **SuanChou VM**: Executes assembly with loops, branches, and comparisons

##

*"One yin, one yang — that is the Dao." — I Ching, Xi Ci*

***

## Quick Start

```bash
# Navigate to the project directory
cd suanchou_computer

# Interactive mode (explore characters by stroke/rod code)
py main.py --interactive

# Full pipeline demo (rod computation + VM execution + search engine)
py suanchou_search.py --all

# Interactive search engine (query by stroke, tag, radical, similarity, rod code)
py suanchou_search.py -i

# SuanChou VM execution demo (running assembly programs)
py suanchou_vm.py

# Efficiency analysis report
py efficiency_analysis.py
```

## Project Structure

```
suanchou_computer/
├── counting_rod_computer.py   # The core: arithmetic & logic on — and |
├── stroke_encoder.py          # Stroke → 3-bit → rod signals
├── stroke_dictionary.py       # 130-character stroke/semantic dictionary
├── semantic_layer.py          # Similarity, comparison, relation graphs
├── suanchou_isa.py            # 26-instruction ISA definition
├── suanchou_vm.py             # VM + assembler for native rod-code execution
├── suanchou_search.py         # Search engine + visual pipeline demo
├── extended_strokes.py        # 130-character stroke database
├── efficiency_analysis.py     # Theoretical vs. practical efficiency report
├── main.py                    # Main demo entry point
└── README.md                  # This file
```

## License

MIT — use it, build on it, share it. If this project helps your research or inspires your work, a link back is appreciated but not required.

***

*The bridge between Chinese characters and computation is not a metaphor. It is an architecture waiting to be built.*

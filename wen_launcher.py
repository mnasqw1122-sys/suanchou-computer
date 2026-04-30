# -*- coding: utf-8 -*-
"""文语言独立运行器 —— 供 PyInstaller 打包为 wen.exe"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from wen_lang import WenRuntime, WenLexer, WenParser, run_wen_code, DEMO_PROGRAMS

    if len(sys.argv) < 2:
        print("文语言 独立运行器")
        print()
        print("用法：wen.exe <文件.wen>")
        print("      wen.exe show 程序名   显示内置演示源码")
        print("      wen.exe demo         运行所有演示")
        print("      wen.exe              进入对话模式")
        print()
        print("也可以把 .wen 文件拖到 wen.exe 图标上运行。")
        input("按 Enter 退出...")
        return

    arg = sys.argv[1]

    if arg == "demo":
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
                run_wen_code(src)
    elif arg == "show":
        if len(sys.argv) > 2:
            name = sys.argv[2]
            if name in DEMO_PROGRAMS:
                print(DEMO_PROGRAMS[name])
            else:
                print(f"演示程序: {list(DEMO_PROGRAMS.keys())}")
        else:
            print(f"可用: {list(DEMO_PROGRAMS.keys())}")
    else:
        filepath = arg
        if not os.path.exists(filepath):
            print(f"文件不存在：{filepath}")
            input("按 Enter 退出...")
            return
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        print(f"\n文语言 运行：{os.path.basename(filepath)}\n")
        run_wen_code(source)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
简单测试智能文本重组修复功能
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(__file__))

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

def test_with_main():
    """使用main.py来测试修复"""
    
    print("=== 使用main.py测试智能文本重组修复 ===\n")
    
    # 使用命令行调用main.py
    import subprocess
    
    cmd = [
        sys.executable, "main.py",
        "-i", "test5.pdf",
        "-o", "test5_fixed.pdf", 
        "-li", "en",
        "-lo", "zh-cn",
        "-s", "google",
        "--thread", "1"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("注意观察输出中是否有智能文本重组的日志信息...\n")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print("=== 标准输出 ===")
        print(result.stdout)
        
        print("\n=== 标准错误输出 ===")
        print(result.stderr)
        
        print(f"\n=== 返回码: {result.returncode} ===")
        
        if result.returncode == 0:
            print("✓ 翻译成功完成")
            print("请检查生成的文件:")
            print("- test5_fixed-mono.pdf (单语版本)")
            print("- test5_fixed-dual.pdf (双语版本)")
            print("\n请打开文件查看关键句子是否完整翻译:")
            print("原文: 'you can go to Settings > About phone to view the HyperOS version'")
            print("应该被翻译为完整的中文句子")
        else:
            print("✗ 翻译失败")
            
    except subprocess.TimeoutExpired:
        print("✗ 翻译超时")
    except Exception as e:
        print(f"✗ 执行出错: {e}")

def analyze_log_for_fix():
    """分析日志以验证修复效果"""
    
    print("\n=== 分析修复效果 ===")
    print("在上面的输出中查找以下关键信息:")
    print("1. '智能文本重组' - 表示重组功能已启动")
    print("2. '发现go to段落' - 表示找到了目标段落")
    print("3. '找到合并候选段落' - 表示找到了需要合并的段落")
    print("4. '合并段落' - 表示成功合并了分割的文本")
    print("5. '在合并点插入图片占位符' - 表示正确插入了图片占位符")
    print("6. 没有 '跳过翻译' 消息针对关键句子 - 表示句子进入了翻译流程")

if __name__ == "__main__":
    test_with_main()
    analyze_log_for_fix()
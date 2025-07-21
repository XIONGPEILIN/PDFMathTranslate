#!/usr/bin/env python3
"""
使用DEBUG级别测试智能文本重组修复
"""

import logging
import sys
import os
import subprocess

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

def test_with_debug():
    """使用DEBUG级别测试"""
    
    print("=== 使用DEBUG级别测试智能文本重组 ===\n")
    
    # 设置环境变量启用DEBUG
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    cmd = [
        sys.executable, "main.py",
        "-i", "test5.pdf",
        "-o", "test5_debug.pdf", 
        "-li", "en",
        "-lo", "zh-cn",
        "-s", "google",
        "--thread", "1"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("启用DEBUG日志，查找智能文本重组过程...\n")
    
    try:
        # 执行命令，捕获所有输出
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=180,
            env=env
        )
        
        print("=== 完整输出分析 ===")
        full_output = result.stdout + result.stderr
        
        # 查找关键日志信息
        key_indicators = [
            "智能文本重组",
            "发现go to段落", 
            "找到合并候选段落",
            "合并段落",
            "在合并点插入图片占位符",
            "开始翻译:",
            "跳过翻译:",
            "your device is running",
            "you can go to"
        ]
        
        print("查找关键日志指标:")
        for indicator in key_indicators:
            if indicator in full_output:
                print(f"✓ 找到: '{indicator}'")
                # 显示相关上下文
                lines = full_output.split('\n')
                for i, line in enumerate(lines):
                    if indicator in line:
                        start = max(0, i-2)
                        end = min(len(lines), i+3)
                        print(f"  上下文 (行 {i}):")
                        for j in range(start, end):
                            prefix = "  >>> " if j == i else "      "
                            print(f"{prefix}{lines[j]}")
                        print()
                        break
            else:
                print(f"✗ 未找到: '{indicator}'")
        
        print(f"\n=== 返回码: {result.returncode} ===")
        
        if result.returncode != 0:
            print("执行失败，完整错误输出:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("✗ 执行超时")
    except Exception as e:
        print(f"✗ 执行出错: {e}")

if __name__ == "__main__":
    test_with_debug()
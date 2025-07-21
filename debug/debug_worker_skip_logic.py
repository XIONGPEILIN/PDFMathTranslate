#!/usr/bin/env python3
"""
调试worker函数的跳过逻辑，找出为什么包含图片的文本被跳过
"""

import re
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def test_worker_skip_logic():
    """测试worker函数的跳过逻辑"""
    
    # 测试文本列表
    test_texts = [
        "you can go to Settings > [图片] About phone [图片] to view the HyperOS version",
        "you can go to Settings > <IMG_PLACEHOLDER:0:100.0,200.0,150.0,250.0:Settings> About phone <IMG_PLACEHOLDER:1:200.0,200.0,250.0,250.0:phone> to view the HyperOS version",
        "you can go to Settings > <f0:100.0,200.0,150.0,250.0> About phone <f1:200.0,200.0,250.0,250.0> to view the HyperOS version",
        "you can go to Settings > 图0 About phone 图1 to view the HyperOS version",
        "Settings > [图片] About phone",
        "[图片]",
        "图0",
        "<f0:100.0,200.0,150.0,250.0>",
        "<IMG_PLACEHOLDER:0:100.0,200.0,150.0,250.0:Settings>",
        "{v0}",
        "",
        "   ",
        "Normal text without images",
        "Text with formula {v0} inside",
        "Only formula: {v0}",
    ]
    
    print("=== 测试worker函数跳过逻辑 ===\n")
    
    for i, text in enumerate(test_texts):
        print(f"测试 {i+1}: '{text}'")
        
        # 当前的跳过逻辑
        should_skip = not text.strip() or re.match(r"^\{v\d+\}$", text)
        
        print(f"  是否跳过: {should_skip}")
        print(f"  空白检查: {not text.strip()}")
        print(f"  公式检查: {re.match(r'^\\{v\\d+\\}$', text) is not None}")
        
        if should_skip:
            print(f"  结果: 跳过翻译")
        else:
            print(f"  结果: 进行翻译")
        
        print()

def test_placeholder_patterns():
    """测试占位符模式匹配"""
    
    print("=== 测试占位符模式匹配 ===\n")
    
    # 测试模式
    patterns = [
        r"^\{v\d+\}$",  # 纯公式
        r"^<f\d+:[^>]+>$",  # 纯图片占位符
        r"^<IMG_PLACEHOLDER:[^>]*>$",  # 纯增强占位符
        r"^图\d+$",  # 纯简化标记
        r"^\[图片\]$",  # 纯图片标记
    ]
    
    test_texts = [
        "you can go to Settings > [图片] About phone [图片] to view the HyperOS version",
        "you can go to Settings > 图0 About phone 图1 to view the HyperOS version",
        "[图片]",
        "图0",
        "<f0:100.0,200.0,150.0,250.0>",
        "<IMG_PLACEHOLDER:0:100.0,200.0,150.0,250.0:Settings>",
        "{v0}",
    ]
    
    for text in test_texts:
        print(f"文本: '{text}'")
        for pattern in patterns:
            match = re.match(pattern, text)
            print(f"  模式 {pattern}: {'匹配' if match else '不匹配'}")
        print()

if __name__ == "__main__":
    test_worker_skip_logic()
    test_placeholder_patterns()
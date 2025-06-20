#!/usr/bin/env python3
"""
调试实际翻译过程，找出包含图片的文本丢失的原因
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(__file__))

from pdf2zh.placeholder_processor import PlaceholderProcessor
from pdf2zh.translator import GoogleTranslator

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

def simulate_worker_function():
    """模拟worker函数的完整处理过程"""
    
    # 测试文本（模拟从test5.pdf中提取的包含图片的文本）
    test_texts = [
        "you can go to Settings > [图片] About phone [图片] to view the HyperOS version",
        "you can go to Settings > <f0:100.0,200.0,150.0,250.0> About phone <f1:200.0,200.0,250.0,250.0> to view the HyperOS version",
        "Settings",
        "About phone", 
        "HyperOS version",
        "",  # 空文本
        "   ",  # 空白文本
        "{v0}",  # 公式
    ]
    
    # 初始化占位符处理器和翻译器
    placeholder_processor = PlaceholderProcessor()
    translator = GoogleTranslator("en", "zh-cn", None, envs={})
    
    print("=== 模拟完整的worker函数处理过程 ===\n")
    
    for i, s in enumerate(test_texts):
        print(f"处理文本 {i+1}: '{s}'")
        
        # 检查跳过条件
        if not s.strip():
            print("  -> 跳过原因: 空白文本")
            print("  -> 返回原文")
            print()
            continue
            
        import re
        if re.match(r"^\{v\d+\}$", s):
            print("  -> 跳过原因: 纯公式")
            print("  -> 返回原文")
            print()
            continue
        
        print("  -> 通过跳过检查，开始翻译处理")
        
        try:
            # 重置占位符处理器
            placeholder_processor.reset()
            
            # 预处理：简化占位符
            simplified_text = placeholder_processor.simplify_placeholders(s)
            print(f"  -> 简化后: '{simplified_text}'")
            
            # 翻译简化后的文本
            if simplified_text.strip():
                translated_simplified = translator.translate(simplified_text)
                print(f"  -> 翻译结果: '{translated_simplified}'")
                
                # 后处理：恢复占位符
                restored_text = placeholder_processor.restore_placeholders(translated_simplified)
                print(f"  -> 恢复后: '{restored_text}'")
                
                # 验证文本完整性
                is_valid = placeholder_processor.validate_text_integrity(s, restored_text)
                print(f"  -> 完整性验证: {'通过' if is_valid else '失败'}")
                
                if not is_valid:
                    print(f"  -> 完整性验证失败，使用直接翻译")
                    direct_translation = translator.translate(s)
                    print(f"  -> 直接翻译结果: '{direct_translation}'")
                    final_result = direct_translation
                else:
                    final_result = restored_text
            else:
                print("  -> 简化后文本为空，跳过翻译")
                final_result = s
            
            print(f"  -> 最终结果: '{final_result}'")
            
        except Exception as e:
            print(f"  -> 翻译出错: {e}")
            print(f"  -> 返回原文: '{s}'")
        
        print()

def debug_segment_extraction():
    """调试段落提取过程"""
    print("=== 调试段落提取过程 ===\n")
    
    # 模拟可能的段落分割情况
    full_text = "you can go to Settings > [图片] About phone [图片] to view the HyperOS version"
    
    # 可能的分割方式
    possible_segments = [
        ["you can go to Settings > [图片] About phone [图片] to view the HyperOS version"],
        ["you can go to Settings > ", "[图片]", " About phone ", "[图片]", " to view the HyperOS version"],
        ["you can go to Settings > [图片] About phone [图片] to view the HyperOS version", ""],
        ["", "you can go to Settings > [图片] About phone [图片] to view the HyperOS version"],
    ]
    
    for i, segments in enumerate(possible_segments):
        print(f"分割方式 {i+1}: {segments}")
        for j, segment in enumerate(segments):
            if not segment.strip():
                print(f"  段落 {j+1}: '{segment}' -> 跳过(空白)")
            else:
                print(f"  段落 {j+1}: '{segment}' -> 翻译")
        print()

if __name__ == "__main__":
    simulate_worker_function()
    debug_segment_extraction()
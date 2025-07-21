#!/usr/bin/env python3
"""
全面调试test5.pdf的文本提取和翻译问题
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(__file__))

import fitz  # PyMuPDF
from pdf2zh.high_level import translate

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

def analyze_text_structure():
    """分析test5.pdf的文本结构，特别关注图片导致的分割问题"""
    
    print("=== 分析test5.pdf文本结构 ===\n")
    
    try:
        doc = fitz.open("test5.pdf")
        page = doc[0]
        
        # 获取详细的文本块信息
        text_blocks = page.get_text("dict")
        
        print("详细文本结构分析:")
        print(f"总块数: {len(text_blocks['blocks'])}")
        print()
        
        # 重点关注包含"Settings"和"About phone"的区域
        target_blocks = []
        
        for i, block in enumerate(text_blocks['blocks']):
            if 'lines' in block:  # 文本块
                block_text = ""
                for line in block['lines']:
                    for span in line['spans']:
                        block_text += span['text']
                
                if block_text.strip():
                    print(f"文本块 {i}: bbox={block['bbox']}")
                    print(f"  内容: '{block_text}'")
                    
                    # 检查是否包含关键词
                    if any(keyword in block_text for keyword in ['Settings', 'About phone', 'you can go to']):
                        target_blocks.append((i, block, block_text))
                        print(f"  *** 包含关键文本 ***")
                    print()
            else:  # 图像块
                print(f"图像块 {i}: bbox={block['bbox']}")
                print()
        
        # 分析目标文本块的连续性
        print("=== 关键文本块分析 ===")
        if target_blocks:
            print("找到的关键文本块:")
            for idx, (block_num, block, text) in enumerate(target_blocks):
                print(f"  {idx+1}. 块{block_num}: '{text}'")
            
            # 检查块之间是否有图像分隔
            print("\n检查块之间的分隔:")
            for i in range(len(target_blocks) - 1):
                current_block_num = target_blocks[i][0]
                next_block_num = target_blocks[i+1][0]
                
                if next_block_num - current_block_num > 1:
                    print(f"  块{current_block_num}和块{next_block_num}之间有{next_block_num - current_block_num - 1}个块")
                    
                    # 检查中间的块
                    for middle_idx in range(current_block_num + 1, next_block_num):
                        middle_block = text_blocks['blocks'][middle_idx]
                        if 'lines' not in middle_block:  # 图像块
                            print(f"    中间块{middle_idx}: 图像块 bbox={middle_block['bbox']}")
        else:
            print("未找到包含关键文本的块")
        
        doc.close()
        
    except Exception as e:
        print(f"分析失败: {e}")

def simulate_text_reconstruction():
    """模拟文本重建过程，分析分割对翻译的影响"""
    
    print("\n=== 模拟文本重建过程 ===\n")
    
    # 基于实际提取的结果，模拟可能的文本分割
    actual_segments = [
        "your device is running, you can go to ",  # 文本块5
        "Settings > ",                              # 文本块7 
        "About phone to view the HyperOS version ", # 文本块9
        "information."                              # 文本块10
    ]
    
    print("实际提取的文本段落:")
    for i, segment in enumerate(actual_segments):
        print(f"  段落{i+1}: '{segment}'")
    
    print("\n如果单独翻译每个段落:")
    # 这里我们只是模拟，实际翻译需要调用翻译服务
    simulated_translations = [
        "您的设备正在运行，您可以转到",
        "设置 >", 
        "关于手机以查看HyperOS版本",
        "信息。"
    ]
    
    for i, (original, translated) in enumerate(zip(actual_segments, simulated_translations)):
        print(f"  段落{i+1}: '{original}' -> '{translated}'")
    
    reconstructed = " ".join(simulated_translations)
    print(f"\n重建后的完整翻译: '{reconstructed}'")
    
    # 对比完整文本翻译
    complete_text = " ".join(actual_segments)
    print(f"\n完整原文: '{complete_text}'")
    print("如果作为完整文本翻译，应该得到更连贯的结果")

def check_url_handling():
    """检查URL处理问题"""
    
    print("\n=== 检查URL处理 ===\n")
    
    try:
        doc = fitz.open("test5.pdf")
        page = doc[0]
        
        all_text = page.get_text()
        
        # 查找URL相关文本
        if "mi.com" in all_text:
            print("找到URL相关文本:")
            # 找到URL的上下文
            lines = all_text.split('\n')
            for i, line in enumerate(lines):
                if "mi.com" in line:
                    print(f"  行{i}: '{line}'")
                    
                    # 检查特殊字符
                    if '�' in line:
                        print("  *** 发现特殊字符 '�' ***")
                        print(f"  完整行内容 (repr): {repr(line)}")
        else:
            print("未找到URL文本")
        
        doc.close()
        
    except Exception as e:
        print(f"检查URL失败: {e}")

def identify_root_causes():
    """识别问题的根本原因"""
    
    print("\n=== 问题根本原因分析 ===\n")
    
    causes = [
        "1. 文本分割问题：图像将连续的文本分割成多个独立块",
        "2. 独立翻译导致上下文丢失：每个文本块单独翻译，缺乏语境",
        "3. PDF编码问题：特殊字符'�'表明存在编码转换问题",
        "4. URL处理异常：www.mi.com被错误处理",
        "5. 文本重建算法不完善：无法正确合并被分割的语义单元"
    ]
    
    for cause in causes:
        print(cause)
    
    print("\n具体表现:")
    print("- 原文: 'If you are not sure which software version your device is running, you can go to Settings > About phone to view the HyperOS version information'")
    print("- 分割后: ['your device is running, you can go to ', 'Settings > ', 'About phone to view the HyperOS version ', 'information.']")
    print("- 翻译时缺少关键连接: 'If you are not sure which software version' 部分被分离")
    print("- 结果: 翻译时无法理解完整语义，导致部分内容丢失")

def test_character_encoding():
    """测试字符编码问题"""
    
    print("\n=== 字符编码问题测试 ===\n")
    
    try:
        doc = fitz.open("test5.pdf")
        page = doc[0]
        
        # 尝试不同的文本提取方法
        methods = [
            ("get_text()", page.get_text()),
            ("get_text('text')", page.get_text("text")),
            ("get_text('blocks')", str(page.get_text("blocks"))),
        ]
        
        for method_name, text in methods:
            print(f"{method_name}:")
            if '�' in text:
                print("  发现特殊字符 '�'")
                # 找出特殊字符的位置
                positions = [i for i, char in enumerate(text) if char == '�']
                for pos in positions[:5]:  # 只显示前5个
                    start = max(0, pos - 20)
                    end = min(len(text), pos + 20)
                    context = text[start:end]
                    print(f"    位置{pos}: '{context}'")
            else:
                print("  未发现特殊字符")
            print()
        
        doc.close()
        
    except Exception as e:
        print(f"编码测试失败: {e}")

if __name__ == "__main__":
    analyze_text_structure()
    simulate_text_reconstruction()
    check_url_handling()  
    test_character_encoding()
    identify_root_causes()
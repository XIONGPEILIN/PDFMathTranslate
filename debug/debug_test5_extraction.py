#!/usr/bin/env python3
"""
调试test5.pdf的实际文本提取和翻译过程
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(__file__))

import fitz  # PyMuPDF
from pdf2zh.converter import TranslateConverter
from pdf2zh.translator import GoogleTranslator

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

def extract_text_segments_from_test5():
    """从test5.pdf中提取文本段落，查看分割情况"""
    
    print("=== 从test5.pdf提取文本段落 ===\n")
    
    # 打开PDF文件
    try:
        doc = fitz.open("test5.pdf")
    except Exception as e:
        print(f"无法打开test5.pdf: {e}")
        return
    
    page = doc[0]  # 第一页
    
    # 提取文本块
    text_blocks = page.get_text("dict")
    
    print(f"页面中的文本块数量: {len(text_blocks['blocks'])}")
    print()
    
    for i, block in enumerate(text_blocks['blocks']):
        if 'lines' in block:  # 文本块
            print(f"文本块 {i}:")
            for j, line in enumerate(block['lines']):
                line_text = ""
                for span in line['spans']:
                    line_text += span['text']
                print(f"  行 {j}: '{line_text}'")
                
                # 检查是否包含关键文本
                if "Settings" in line_text and "About phone" in line_text:
                    print(f"  *** 找到目标文本！***")
                    print(f"  完整行: '{line_text}'")
                    
            print()
        else:  # 图像块
            print(f"图像块 {i}: bbox={block['bbox']}")
            print()
    
    doc.close()

def debug_converter_text_extraction():
    """调试转换器的文本提取过程"""
    
    print("=== 调试转换器文本提取 ===\n")
    
    # 这里我们需要模拟转换器的实际工作过程
    # 但由于转换器依赖复杂的PDF解析，我们先检查简单的文本提取
    
    try:
        doc = fitz.open("test5.pdf")
        page = doc[0]
        
        # 获取页面上的所有文本
        all_text = page.get_text()
        print("页面所有文本:")
        print(repr(all_text))
        print()
        
        # 查找关键文本
        target_text = "you can go to Settings"
        if target_text in all_text:
            print(f"✓ 找到目标文本: '{target_text}'")
            # 找到上下文
            start_idx = all_text.find(target_text)
            context_start = max(0, start_idx - 50)
            context_end = min(len(all_text), start_idx + 200)
            context = all_text[context_start:context_end]
            print(f"上下文: '{context}'")
        else:
            print(f"✗ 未找到目标文本: '{target_text}'")
            
        doc.close()
        
    except Exception as e:
        print(f"处理PDF时出错: {e}")

def check_text_in_lines():
    """检查文本在行中的分布"""
    
    print("=== 检查文本行分布 ===\n")
    
    try:
        doc = fitz.open("test5.pdf")
        page = doc[0]
        
        # 获取文本行
        text_dict = page.get_text("dict")
        
        all_lines = []
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        line_text += span["text"]
                    if line_text.strip():
                        all_lines.append({
                            "text": line_text,
                            "bbox": line["bbox"]
                        })
        
        print(f"总共找到 {len(all_lines)} 行文本")
        print()
        
        # 查找包含Settings的行
        settings_lines = []
        for i, line in enumerate(all_lines):
            if "Settings" in line["text"] or "About phone" in line["text"]:
                settings_lines.append((i, line))
                print(f"行 {i}: '{line['text']}'")
                print(f"  bbox: {line['bbox']}")
        
        if not settings_lines:
            print("未找到包含Settings或About phone的行")
            
            # 显示所有行以供调试
            print("\n所有文本行:")
            for i, line in enumerate(all_lines):
                print(f"行 {i}: '{line['text']}'")
        
        doc.close()
        
    except Exception as e:
        print(f"处理PDF时出错: {e}")

if __name__ == "__main__":
    extract_text_segments_from_test5()
    debug_converter_text_extraction()
    check_text_in_lines()
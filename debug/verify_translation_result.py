#!/usr/bin/env python3
"""
验证翻译结果中关键句子是否完整
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import fitz  # PyMuPDF

def verify_translation_result():
    """检查翻译结果文件"""
    
    print("=== 验证翻译结果 ===\n")
    
    # 检查生成的文件
    mono_file = "test5-mono.pdf"
    dual_file = "test5-dual.pdf"
    
    for filename in [mono_file, dual_file]:
        if os.path.exists(filename):
            print(f"✓ 找到文件: {filename}")
            
            try:
                doc = fitz.open(filename)
                page = doc[0]  # 第一页
                
                # 获取所有文本
                all_text = page.get_text()
                print(f"\n{filename} 的页面文本:")
                print("=" * 50)
                print(all_text[:1000] + "..." if len(all_text) > 1000 else all_text)
                print("=" * 50)
                
                # 查找关键中文翻译
                key_phrases = [
                    "设置",
                    "关于手机", 
                    "您可以转到",
                    "你可以去",
                    "查看",
                    "版本",
                    "HyperOS"
                ]
                
                found_phrases = []
                for phrase in key_phrases:
                    if phrase in all_text:
                        found_phrases.append(phrase)
                        print(f"✓ 找到关键词: '{phrase}'")
                
                if len(found_phrases) >= 3:
                    print(f"✓ {filename}: 翻译成功！找到了 {len(found_phrases)} 个关键词")
                else:
                    print(f"✗ {filename}: 翻译可能不完整，只找到 {len(found_phrases)} 个关键词")
                
                # 检查是否有完整的句子结构
                if "设置" in all_text and "关于手机" in all_text and ("查看" in all_text or "版本" in all_text):
                    print(f"✓ {filename}: 句子结构完整")
                else:
                    print(f"? {filename}: 句子结构需要进一步检查")
                
                doc.close()
                print()
                
            except Exception as e:
                print(f"✗ 读取 {filename} 时出错: {e}")
        else:
            print(f"✗ 文件不存在: {filename}")
    
    # 比较原文和翻译结果
    print("\n=== 对比分析 ===")
    print("原文关键句子: 'you can go to Settings > About phone to view the HyperOS version'")
    print("期望的中文翻译: '您可以转到设置 > 关于手机查看HyperOS版本'")
    print("或类似的完整中文句子")

def check_original_vs_result():
    """对比原文和翻译结果"""
    
    print("\n=== 原文vs翻译结果对比 ===")
    
    # 检查原文
    if os.path.exists("test5.pdf"):
        print("检查原文 test5.pdf:")
        try:
            doc = fitz.open("test5.pdf")
            page = doc[0]
            all_text = page.get_text()
            
            target_text = "you can go to"
            if target_text in all_text:
                start_idx = all_text.find(target_text)
                context_start = max(0, start_idx - 20)
                context_end = min(len(all_text), start_idx + 100)
                context = all_text[context_start:context_end]
                print(f"原文上下文: '{context}'")
            
            doc.close()
        except Exception as e:
            print(f"读取原文出错: {e}")

if __name__ == "__main__":
    verify_translation_result()
    check_original_vs_result()
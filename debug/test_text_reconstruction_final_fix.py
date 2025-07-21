#!/usr/bin/env python3
"""
测试修复后的文本重组功能
"""

import logging
import sys
import os
import subprocess
import fitz

# 设置详细日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

def test_fixed_reconstruction():
    """测试修复后的文本重组功能"""
    
    print("=== 测试修复后的文本重组功能 ===\n")
    
    # 检查输入文件
    if not os.path.exists("test5.pdf"):
        print("✗ 测试文件 test5.pdf 不存在")
        return False
    
    # 执行翻译
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
    
    try:
        # 执行翻译
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✓ 翻译执行成功")
            
            # 检查输出文件
            if os.path.exists("test5_fixed.pdf"):
                print("✓ 输出文件已生成")
                
                # 验证翻译结果
                return verify_translation_result("test5_fixed.pdf")
            else:
                print("✗ 输出文件未生成")
                return False
        else:
            print(f"✗ 翻译执行失败，返回码: {result.returncode}")
            print("错误输出:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ 翻译执行超时")
        return False
    except Exception as e:
        print(f"✗ 翻译执行出错: {e}")
        return False

def verify_translation_result(pdf_path):
    """验证翻译结果的完整性"""
    
    print(f"\n=== 验证翻译结果: {pdf_path} ===")
    
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        text = page.get_text()
        
        print("翻译后的文本内容:")
        print(f"总字符数: {len(text)}")
        print()
        
        # 检查关键中文内容
        key_chinese_phrases = [
            "不确定",
            "软件版本", 
            "设备正在运行",
            "可以转到",
            "设置",
            "关于手机",
            "查看",
            "版本信息"
        ]
        
        found_phrases = []
        missing_phrases = []
        
        for phrase in key_chinese_phrases:
            if phrase in text:
                found_phrases.append(phrase)
                print(f"✓ 找到关键短语: '{phrase}'")
            else:
                missing_phrases.append(phrase)
                print(f"✗ 缺失关键短语: '{phrase}'")
        
        # 显示完整的相关文本段落
        print("\n相关文本段落:")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(phrase in line for phrase in ['用户指南', 'HyperOS', '设置', '关于']):
                print(f"行{i}: {line.strip()}")
        
        # 评估修复效果
        success_rate = len(found_phrases) / len(key_chinese_phrases)
        print(f"\n=== 修复效果评估 ===")
        print(f"关键短语识别率: {success_rate:.1%} ({len(found_phrases)}/{len(key_chinese_phrases)})")
        
        if success_rate >= 0.8:
            print("✓ 修复效果良好")
            result = True
        elif success_rate >= 0.6:
            print("◐ 修复效果一般")
            result = False
        else:
            print("✗ 修复效果不佳")
            result = False
        
        # 检查是否还有遗漏的关键内容
        if "If you are not sure" in text:
            print("⚠ 检测到未翻译的英文内容，可能存在翻译不完整")
            result = False
        
        doc.close()
        return result
        
    except Exception as e:
        print(f"验证失败: {e}")
        return False

def compare_with_original():
    """与原始版本进行对比"""
    
    print("\n=== 与原始版本对比 ===")
    
    # 检查是否有原始翻译结果
    original_files = ["test5-mono.pdf", "test5-dual.pdf"]
    
    for original_file in original_files:
        if os.path.exists(original_file):
            print(f"\n对比文件: {original_file}")
            
            try:
                doc = fitz.open(original_file)
                page = doc[0]
                original_text = page.get_text()
                
                # 简单的内容长度对比
                print(f"原始文件字符数: {len(original_text)}")
                
                if os.path.exists("test5_fixed.pdf"):
                    fixed_doc = fitz.open("test5_fixed.pdf")
                    fixed_page = fixed_doc[0]
                    fixed_text = fixed_page.get_text()
                    
                    print(f"修复后字符数: {len(fixed_text)}")
                    
                    # 检查是否包含更多关键内容
                    original_has_key = any(phrase in original_text for phrase in ["不确定", "软件版本"])
                    fixed_has_key = any(phrase in fixed_text for phrase in ["不确定", "软件版本"])
                    
                    if fixed_has_key and not original_has_key:
                        print("✓ 修复版本包含更多关键内容")
                    elif not fixed_has_key and original_has_key:
                        print("✗ 修复版本丢失了原有内容")
                    else:
                        print("◐ 内容包含度相似")
                    
                    fixed_doc.close()
                
                doc.close()
                
            except Exception as e:
                print(f"对比失败: {e}")

def main():
    """主函数"""
    
    print("开始测试文本重组修复效果...")
    
    # 执行测试
    success = test_fixed_reconstruction()
    
    if success:
        print("\n🎉 测试成功！文本重组修复生效")
        compare_with_original()
    else:
        print("\n❌ 测试失败，需要进一步调试")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
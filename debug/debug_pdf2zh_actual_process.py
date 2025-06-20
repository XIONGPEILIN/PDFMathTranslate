#!/usr/bin/env python3
"""
调试pdf2zh实际处理test5.pdf的流程
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(__file__))

from pdf2zh.high_level import translate
from pdf2zh.doclayout import OnnxModel, ModelInstance
from pdf2zh.translator import GoogleTranslator

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

def debug_actual_translation():
    """调试实际的翻译过程"""
    
    print("=== 调试实际PDF翻译过程 ===\n")
    
    # 初始化模型
    try:
        ModelInstance.value = OnnxModel.load_available()
        print("模型加载成功")
    except Exception as e:
        print(f"模型加载失败: {e}")
        return
    
    # 准备参数
    args = {
        'files': ['test5.pdf'],
        'lang_in': 'en',
        'lang_out': 'zh',
        'service': 'google',
        'output': '',
        'thread': 1,  # 单线程便于调试
        'debug': True,
        'pages': None,
        'vfont': '',
        'vchar': '',
    }
    
    print("开始翻译...")
    try:
        # 调用实际的翻译函数
        translate(model=ModelInstance.value, **args)
        print("翻译完成")
    except Exception as e:
        print(f"翻译失败: {e}")
        import traceback
        traceback.print_exc()

def analyze_missing_content():
    """分析缺失内容的具体原因"""
    
    print("\n=== 分析缺失内容的具体原因 ===\n")
    
    # 完整的原始文本
    original_complete = "If you are not sure which software version your device is running, you can go to Settings > About phone to view the HyperOS version information"
    
    # 实际被分割的文本段落
    actual_segments = [
        "If you are not sure which software version ",  # 这部分在块4中
        "your device is running, you can go to ",       # 这部分在块5中
        "Settings > ",                                   # 这部分在块7中
        "About phone to view the HyperOS version ",     # 这部分在块9中
        "information."                                   # 这部分在块10中
    ]
    
    print("原始完整文本:")
    print(f"'{original_complete}'")
    print()
    
    print("实际分割后的段落:")
    for i, segment in enumerate(actual_segments):
        print(f"  段落{i+1}: '{segment}'")
    
    # 分析哪些段落可能被跳过
    print("\n分析各段落的处理情况:")
    
    for i, segment in enumerate(actual_segments):
        # 检查是否为空或过短
        if not segment.strip():
            print(f"  段落{i+1}: 可能被跳过 - 空白文本")
        elif len(segment.strip()) < 3:
            print(f"  段落{i+1}: 可能被跳过 - 文本过短")
        else:
            print(f"  段落{i+1}: 正常处理")
    
    # 分析翻译结果丢失的原因
    print("\n翻译结果丢失分析:")
    missing_part = "If you are not sure which software version"
    print(f"缺失部分: '{missing_part}'")
    print("可能原因:")
    print("  1. 该部分在块4中，但可能被其他处理逻辑跳过")
    print("  2. 文本重建时未正确合并相邻块")
    print("  3. 翻译过程中该段落被错误地归类为不需要翻译")

def check_text_block_processing():
    """检查文本块处理逻辑"""
    
    print("\n=== 检查文本块处理逻辑 ===\n")
    
    # 基于实际观察到的块分布
    blocks_info = [
        (4, "the phone generic user guide for the HyperOS version. If you are not sure which software version "),
        (5, "your device is running, you can go to "),
        (7, "Settings > "),
        (9, "About phone to view the HyperOS version "),
        (10, "information."),
    ]
    
    print("相关文本块信息:")
    for block_num, content in blocks_info:
        print(f"  块{block_num}: '{content}'")
        
        # 检查每个块的特征
        if content.endswith(" "):
            print(f"    - 以空格结尾，可能是句子的一部分")
        if content.startswith(" "):
            print(f"    - 以空格开头，可能是句子的continuation")
        if "If you are not sure" in content:
            print(f"    - 包含关键丢失文本")
        if len(content.strip()) < 20:
            print(f"    - 文本较短，长度: {len(content.strip())}")
    
    print("\n问题分析:")
    print("  1. 块4包含完整的'If you are not sure which software version'")
    print("  2. 但在翻译结果中这部分丢失了")
    print("  3. 这表明问题可能在于:")
    print("     - 块4的翻译结果被错误处理")
    print("     - 或者在文本重建时块4被忽略")
    print("     - 或者翻译服务对该块返回了不完整的结果")

def verify_translation_cache():
    """验证翻译缓存和实际处理"""
    
    print("\n=== 验证翻译缓存和处理 ===\n")
    
    # 测试关键文本段落的翻译
    test_segments = [
        "the phone generic user guide for the HyperOS version. If you are not sure which software version ",
        "your device is running, you can go to ",
        "Settings > ",
        "About phone to view the HyperOS version ",
        "information.",
    ]
    
    print("测试关键段落的翻译:")
    
    try:
        translator = GoogleTranslator("en", "zh", None, envs={})
        
        for i, segment in enumerate(test_segments):
            print(f"\n段落{i+1}: '{segment}'")
            try:
                result = translator.translate(segment)
                print(f"翻译结果: '{result}'")
                
                # 检查翻译是否完整
                if len(result.strip()) < len(segment.strip()) * 0.3:
                    print("  ⚠️ 翻译结果可能不完整")
                else:
                    print("  ✓ 翻译结果长度合理")
                    
            except Exception as e:
                print(f"翻译失败: {e}")
                
    except Exception as e:
        print(f"初始化翻译器失败: {e}")

if __name__ == "__main__":
    analyze_missing_content()
    check_text_block_processing()
    verify_translation_cache()
    # debug_actual_translation()  # 这个可能需要较长时间，先注释掉
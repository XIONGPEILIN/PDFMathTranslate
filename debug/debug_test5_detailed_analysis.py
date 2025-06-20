#!/usr/bin/env python3
"""
详细分析 test5.pdf 翻译问题的调试脚本
重点关注文本分割、占位符处理和翻译完整性
"""

import logging
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar, LTFigure

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def analyze_original_text_extraction():
    """分析原文提取过程"""
    print("\n" + "="*60)
    print("📄 原文文本提取分析")
    print("="*60)
    
    all_text_segments = []
    all_figures = []
    
    for page_layout in extract_pages("test5.pdf"):
        print(f"\n页面 {page_layout.pageid} 内容分析:")
        
        for element in page_layout:
            if isinstance(element, LTTextBox):
                for line in element:
                    if isinstance(line, LTTextLine):
                        line_text = line.get_text().strip()
                        if line_text:
                            all_text_segments.append({
                                'text': line_text,
                                'bbox': (line.x0, line.y0, line.x1, line.y1),
                                'page': page_layout.pageid
                            })
                            print(f"  文本段: '{line_text}' @ ({line.x0:.1f}, {line.y0:.1f})")
            
            elif isinstance(element, LTFigure):
                all_figures.append({
                    'bbox': (element.x0, element.y0, element.x1, element.y1),
                    'page': page_layout.pageid
                })
                print(f"  图片: @ ({element.x0:.1f}, {element.y0:.1f}, {element.x1:.1f}, {element.y1:.1f})")
    
    # 分析完整原文
    complete_text = " ".join([seg['text'] for seg in all_text_segments])
    print(f"\n🔤 完整原文:")
    print(f"'{complete_text}'")
    
    # 检查关键短语
    key_phrases = [
        "if you are not sure which software version",
        "your device is running",
        "you can go to settings", 
        "about phone",
        "view the hyperos version information"
    ]
    
    print(f"\n🔍 关键短语完整性检查:")
    for phrase in key_phrases:
        found = phrase.lower() in complete_text.lower()
        status = "✅" if found else "❌"
        print(f"{status} '{phrase}' - {'找到' if found else '缺失'}")
    
    return all_text_segments, all_figures, complete_text

def analyze_text_segmentation_issues(text_segments):
    """分析文本分割问题"""
    print("\n" + "="*60)
    print("✂️ 文本分割问题分析") 
    print("="*60)
    
    # 查找可能被图片分割的连续文本
    potential_splits = []
    
    for i, seg1 in enumerate(text_segments):
        text1 = seg1['text'].lower().strip()
        
        # 查找以连接词结尾的文本段
        if any(text1.endswith(word) for word in ['to', 'can', 'go', 'the', 'which', 'software']):
            print(f"\n🔗 发现潜在分割起点 {i}: '{seg1['text']}'")
            
            # 在附近段落中查找可能的连接
            for j, seg2 in enumerate(text_segments[i+1:i+5], i+1):
                text2 = seg2['text'].lower().strip()
                
                # 检查语义连续性
                if is_semantically_connected(text1, text2):
                    potential_splits.append({
                        'start_idx': i,
                        'end_idx': j,
                        'start_text': seg1['text'],
                        'end_text': seg2['text'],
                        'gap_y': abs(seg1['bbox'][1] - seg2['bbox'][1]),
                        'gap_x': seg2['bbox'][0] - seg1['bbox'][2]
                    })
                    print(f"  ➜ 连接到段落 {j}: '{seg2['text']}'")
                    print(f"    坐标间隔: X={seg2['bbox'][0] - seg1['bbox'][2]:.1f}, Y={abs(seg1['bbox'][1] - seg2['bbox'][1]):.1f}")
    
    return potential_splits

def is_semantically_connected(text1, text2):
    """判断两个文本段是否语义连续"""
    # 具体的连接模式
    connection_patterns = [
        (r'\bcan go to\b', r'^settings'),
        (r'\bsettings\b', r'^.*about'),
        (r'\bto\b', r'^(settings|about|view)'),
        (r'\bwhich software\b', r'^version'),
        (r'\bdevice is\b', r'^running'),
        (r'\byou can\b', r'^go'),
        (r'\bthe\b', r'^(phone|hyperos|version)'),
    ]
    
    for pattern1, pattern2 in connection_patterns:
        if re.search(pattern1, text1) and re.search(pattern2, text2):
            return True
    
    return False

def analyze_placeholder_processing():
    """分析占位符处理逻辑"""
    print("\n" + "="*60)
    print("🏷️ 占位符处理分析")
    print("="*60)
    
    # 模拟原始文本被分割的情况
    original_complete = "Thanks for choosing Xiaomi phone, please read the user guide carefully before you start This is the phone generic user guide for the HyperOS version If you are not sure which software version your device is running, you can go to Settings > About phone to view the HyperOS version information For more HyperOS features, see https://www.mi.com/global/hyperos"
    
    # 模拟分割后的文本段（基于实际运行观察到的分割模式）
    segmented_texts = [
        "Thanks for choosing Xiaomi phone, please read the user guide carefully before you start This is the phone generic user guide for the HyperOS version",
        "If you are not sure which software version",  # 这部分经常丢失
        "your device is running, you can go to",       # 这部分经常丢失
        "Settings >",                                  # 图片占位符应该在这里
        "About phone to view",                         # 图片占位符应该在这里  
        "the HyperOS version information For more HyperOS features, see https://www.mi.com/global/hyperos"
    ]
    
    print("📝 原始完整文本:")
    print(f"'{original_complete}'")
    
    print("\n✂️ 分割后的文本段:")
    for i, segment in enumerate(segmented_texts):
        print(f"  段落 {i}: '{segment}'")
    
    # 分析丢失的内容
    print("\n❌ 翻译过程中丢失的内容分析:")
    missing_parts = [
        "If you are not sure which software version",
        "your device is running, you can go to", 
        "About phone to view",
        "the HyperOS version information"
    ]
    
    for part in missing_parts:
        print(f"  🔸 '{part}' - 在智能重组过程中未正确处理")
    
    return segmented_texts

def analyze_url_corruption():
    """分析URL格式损坏问题"""
    print("\n" + "="*60)
    print("🔗 URL格式损坏分析")
    print("="*60)
    
    original_url = "https://www.mi.com/global/hyperos"
    corrupted_url = "https//www.mi.com/global/hyperos"  # 从翻译结果观察到
    
    print(f"原始URL: {original_url}")
    print(f"损坏URL: {corrupted_url}")
    print(f"问题: 缺少冒号 ':'")
    
    # 这可能是翻译服务或占位符处理过程中的问题
    print("\n🔍 可能原因:")
    print("1. 翻译服务（Google Translate）处理URL时去除了冒号")
    print("2. 占位符处理过程中正则表达式匹配问题")
    print("3. 文本重组过程中字符丢失")
    
    return original_url, corrupted_url

def analyze_title_addition():
    """分析标题添加问题"""
    print("\n" + "="*60)
    print("📰 标题添加问题分析") 
    print("="*60)
    
    print("🔍 观察到的问题:")
    print("翻译结果中添加了原文没有的标题: '关于用户指南'")
    
    print("\n💡 可能原因:")
    print("1. 翻译服务根据上下文自动添加了标题")
    print("2. 翻译提示词或模板中包含了标题格式化指令")
    print("3. 占位符处理逻辑错误地插入了标题")
    
    return "关于用户指南"

def main():
    """主分析函数"""
    print("🔧 开始 test5.pdf 翻译问题详细分析...")
    
    # 1. 分析原文提取
    text_segments, figures, complete_text = analyze_original_text_extraction()
    
    # 2. 分析文本分割问题
    potential_splits = analyze_text_segmentation_issues(text_segments)
    
    # 3. 分析占位符处理
    segmented_texts = analyze_placeholder_processing()
    
    # 4. 分析URL损坏
    original_url, corrupted_url = analyze_url_corruption()
    
    # 5. 分析标题添加
    added_title = analyze_title_addition()
    
    # 生成诊断总结
    print("\n" + "="*60)
    print("🎯 问题根因诊断总结")
    print("="*60)
    
    print("\n🔴 主要问题根因:")
    print("1. **智能文本重组逻辑缺陷** (converter.py:478-605)")
    print("   - find_and_merge_split_paragraphs() 函数未能正确识别和合并所有被图片分割的文本段")
    print("   - 语义连续性检查模式不够全面，遗漏了关键的连接模式")
    
    print("\n2. **文本完整性验证失效** (converter.py:607-646)")
    print("   - validate_text_completeness() 只是警告但未修复丢失的内容")
    print("   - 关键短语检查发现问题但没有有效的修复机制")
    
    print("\n🔧 需要修复的具体位置:")
    print("1. converter.py:458-476 - 扩展 is_sentence_continuation() 的连接模式")
    print("2. converter.py:486-525 - 改进 find_and_merge_split_paragraphs() 的搜索逻辑") 
    print("3. converter.py:632-642 - 增强 validate_text_completeness() 的修复能力")
    print("4. 翻译服务配置 - 添加URL保护和格式保持规则")
    
    print(f"\n📊 统计信息:")
    print(f"- 原文文本段数: {len(text_segments)}")
    print(f"- 检测到的图片数: {len(figures)}")
    print(f"- 潜在分割点数: {len(potential_splits)}")
    print(f"- 完整原文长度: {len(complete_text)} 字符")

if __name__ == "__main__":
    main()
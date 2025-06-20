#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试动态图片位置调整功能
"""

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf2zh.placeholder_processor import PlaceholderProcessor
from pdf2zh.converter import TranslateConverter

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_placeholder_simplification():
    """测试占位符简化功能"""
    print("\n=== 测试占位符简化功能 ===")
    
    processor = PlaceholderProcessor()
    
    # 测试用例1：包含嵌入图片的文本
    text1 = "Settings > <IMG_PLACEHOLDER:0:234.56,679.67,248.80,693.65:Settings > > About phone <IMG_PLACEHOLDER:1:300.1,680.2,320.5,695.8:About phone > to view the HyperOS version"
    simplified1 = processor.simplify_placeholders(text1)
    print(f"原文: {text1}")
    print(f"简化: {simplified1}")
    
    # 测试用例2：包含普通图片的文本
    text2 = "Click <f0:100.0,200.0,150.0,250.0> to open menu <f1:300.0,200.0,350.0,250.0> for options"
    simplified2 = processor.simplify_placeholders(text2)
    print(f"原文: {text2}")
    print(f"简化: {simplified2}")
    
    return processor, simplified1, simplified2

def test_translation_simulation():
    """模拟翻译过程"""
    print("\n=== 模拟翻译过程 ===")
    
    processor, simplified1, simplified2 = test_placeholder_simplification()
    
    # 模拟翻译结果（中文）
    translated1 = "设置 > 图0 关于手机 图1 查看HyperOS版本"
    translated2 = "点击 图0 打开菜单 图1 选择选项"
    
    print(f"翻译前: {simplified1}")
    print(f"翻译后: {translated1}")
    print(f"翻译前: {simplified2}")
    print(f"翻译后: {translated2}")
    
    return processor, translated1, translated2

def test_placeholder_restoration():
    """测试占位符恢复功能"""
    print("\n=== 测试占位符恢复功能 ===")
    
    processor, translated1, translated2 = test_translation_simulation()
    
    # 恢复占位符
    restored1 = processor.restore_placeholders(translated1)
    restored2 = processor.restore_placeholders(translated2)
    
    print(f"恢复后1: {restored1}")
    print(f"恢复后2: {restored2}")
    
    # 验证恢复是否正确
    if "IMG_PLACEHOLDER" in restored1:
        print("✅ 增强占位符恢复成功")
    else:
        print("❌ 增强占位符恢复失败")
    
    return restored1, restored2

def test_dynamic_position_logic():
    """测试动态位置计算逻辑"""
    print("\n=== 测试动态位置计算逻辑 ===")
    
    # 模拟converter中的动态位置计算函数
    def calculate_dynamic_image_position(original_bbox, current_x, current_y, current_line, text_size, line_spacing):
        """
        模拟converter中的动态位置计算
        """
        original_width = original_bbox[2] - original_bbox[0]
        original_height = original_bbox[3] - original_bbox[1]
        
        # 计算图片在翻译后文本中的新位置
        new_x = current_x + text_size * 0.2  # 小幅向右偏移
        new_y = current_y - current_line * text_size * line_spacing
        
        # 调整图片位置，确保不与文字重叠
        if original_height > text_size:
            new_y -= (original_height - text_size) / 2
        
        # 计算新的bbox
        new_bbox = (
            new_x,
            new_y - original_height,  # 图片通常以左下角为原点
            new_x + original_width,
            new_y
        )
        
        return new_bbox
    
    # 测试场景：翻译前后图片位置变化
    print("场景1：英文 'Settings > [图0] About phone' -> 中文 '设置 > [图0] 关于手机'")
    
    # 原始图片位置
    original_bbox = (234.56, 679.67, 248.80, 693.65)
    print(f"原始图片位置: {original_bbox}")
    
    # 英文文本中的位置
    english_x, english_y = 250.0, 685.0  # 模拟英文 "Settings >" 后的位置
    
    # 中文文本中的位置（假设中文更紧凑）
    chinese_x, chinese_y = 180.0, 685.0  # 模拟中文 "设置 >" 后的位置
    
    # 计算新位置
    text_size = 12.0
    line_spacing = 1.4
    current_line = 0
    
    new_bbox_english = calculate_dynamic_image_position(
        original_bbox, english_x, english_y, current_line, text_size, line_spacing
    )
    
    new_bbox_chinese = calculate_dynamic_image_position(
        original_bbox, chinese_x, chinese_y, current_line, text_size, line_spacing
    )
    
    print(f"英文环境下新位置: {new_bbox_english}")
    print(f"中文环境下新位置: {new_bbox_chinese}")
    print(f"位置偏移: x={new_bbox_chinese[0] - new_bbox_english[0]:.2f}, y={new_bbox_chinese[1] - new_bbox_english[1]:.2f}")

def test_integration():
    """完整流程测试"""
    print("\n=== 完整流程测试 ===")
    
    # 1. 占位符简化
    processor = PlaceholderProcessor()
    original_text = "Settings > <IMG_PLACEHOLDER:0:234.56,679.67,248.80,693.65:Settings > > About phone <IMG_PLACEHOLDER:1:300.1,680.2,320.5,695.8:About phone > to view version"
    simplified_text = processor.simplify_placeholders(original_text)
    
    print(f"1. 原文: {original_text}")
    print(f"2. 简化: {simplified_text}")
    
    # 2. 模拟翻译
    translated_text = "设置 > 图0 关于手机 图1 查看版本"
    print(f"3. 翻译: {translated_text}")
    
    # 3. 占位符恢复
    restored_text = processor.restore_placeholders(translated_text)
    print(f"4. 恢复: {restored_text}")
    
    # 4. 验证完整性
    integrity_ok = processor.validate_text_integrity(original_text, restored_text)
    print(f"5. 完整性验证: {'通过' if integrity_ok else '失败'}")
    
    # 5. 显示统计信息
    stats = processor.get_statistics()
    print(f"6. 处理统计: {stats}")

if __name__ == "__main__":
    print("动态图片位置调整功能测试")
    print("=" * 50)
    
    try:
        test_placeholder_simplification()
        test_translation_simulation()
        test_placeholder_restoration()
        test_dynamic_position_logic()
        test_integration()
        
        print("\n✅ 所有测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
#!/usr/bin/env python3
"""使用真实的test5.pdf数据测试修正后的图像检测逻辑"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pdf2zh.ocr import get_ocr_processor
from pdf2zh.image_processor import ImageProcessor

def test_with_real_data():
    """使用test5.pdf的真实数据进行测试"""
    print("=== 使用test5.pdf真实数据测试 ===")
    
    # 创建处理器
    ocr_processor = get_ocr_processor("eng")
    image_processor = ImageProcessor(ocr_processor)
    
    # 真实的文本块位置（从main.py输出）
    text_blocks = [
        (292.3, 803.7, 299.0, 820.1),  # 文本块1: "1"
        (36.0, 32.8, 198.5, 55.7),     # 文本块2: "Chapter 1 Get started"
        (36.0, 72.2, 170.3, 92.3),     # 文本块3: "About the user guide"
        (36.3, 103.5, 558.3, 119.8),   # 文本块4: "Thanks for choosing..."
        (36.2, 124.5, 558.3, 140.8),   # 文本块5: "the phone generic..."
        (36.2, 148.3, 558.3, 165.5),   # 文本块6: "your device is running..."
        (36.2, 172.6, 97.8, 189.0),    # 文本块7: "information."
        (36.2, 201.6, 398.2, 217.9),   # 文本块8: "For more HyperOS..."
        (36.8, 233.1, 139.6, 253.1),   # 文本块9: "Phone overview"
        (42.2, 559.1, 381.4, 574.2),   # 文本块10: "1. Front camera..."
        (42.2, 588.6, 417.6, 629.7),   # 文本块11: "4. Fingerprint..."
        (42.2, 644.0, 261.8, 659.0),   # 文本块12: "7. Flash..."
        (67.7, 680.5, 94.3, 697.7),    # 文本块13: "Note"
        (72.0, 703.1, 562.0, 717.4),   # 文本块14: "The illustration..."
        (72.0, 724.3, 121.0, 737.9),   # 文本块15: "the screen."
        (36.0, 753.3, 143.3, 773.4),   # 文本块16: "Insert a SIM card"
        (36.3, 784.6, 303.4, 800.9),   # 文本块17: "1. Withdraw the SIM..."
    ]
    
    # 真实的图像位置
    images = [
        (234.6, 148.2, 248.8, 162.2),  # 图像1 - 应该嵌入
        (311.4, 149.1, 327.8, 165.1),  # 图像2 - 应该嵌入
        (203.7, 264.4, 387.6, 544.2),  # 图像3 - 大图，不嵌入
        (54.0, 681.7, 67.6, 695.4),    # 图像4 - 应该嵌入
    ]
    
    expected_results = [True, True, False, True]  # 根据您的说明
    
    print("测试结果：")
    all_correct = True
    
    for i, (image_rect, expected) in enumerate(zip(images, expected_results), 1):
        result = image_processor.is_image_between_texts(text_blocks, image_rect, "horizontal")
        status = "✅" if result == expected else "❌"
        print(f"  图像 {i}: {image_rect}")
        print(f"    预期: {'嵌入' if expected else '不嵌入'}")
        print(f"    实际: {'嵌入' if result else '不嵌入'}")
        print(f"    结果: {status} {'正确' if result == expected else '错误'}")
        
        if result != expected:
            all_correct = False
            # 详细分析为什么不正确
            print(f"    🔍 详细分析图像 {i}:")
            analyze_specific_image(text_blocks, image_rect, i)
        print()
    
    print(f"总体结果: {'✅ 全部正确' if all_correct else '❌ 有错误'}")
    return all_correct

def analyze_specific_image(text_blocks, image_rect, image_num):
    """详细分析特定图像的位置关系"""
    x0, y0, x1, y1 = image_rect
    
    print(f"      图像位置: ({x0}, {y0}, {x1}, {y1})")
    
    # 查找与图像在同一行的文本块
    y_tolerance = 10
    same_line_blocks = []
    
    for i, text_block in enumerate(text_blocks, 1):
        tx0, ty0, tx1, ty1 = text_block
        
        # 检查Y轴重叠
        if not (y1 < ty0 - y_tolerance or y0 > ty1 + y_tolerance):
            same_line_blocks.append((i, text_block))
            
            # 检查图像是否在这个文本块内部
            if tx0 < x0 and x1 < tx1:
                print(f"      📍 图像在文本块{i}内部: 文本X({tx0}-{tx1}) 包含 图像X({x0}-{x1})")
            
            # 检查位置关系
            if x1 <= tx0:
                print(f"      📍 图像在文本块{i}左侧: 图像右边界{x1} <= 文本左边界{tx0}")
            elif x0 >= tx1:
                print(f"      📍 图像在文本块{i}右侧: 图像左边界{x0} >= 文本右边界{tx1}")
    
    print(f"      同行文本块: {[f'块{i}' for i, _ in same_line_blocks]}")
    
    # 特别分析文本块6（最可能包含图像1和2的块）
    if image_num in [1, 2]:
        text_block_6 = text_blocks[5]  # 索引5 = 文本块6
        tx0, ty0, tx1, ty1 = text_block_6
        print(f"      文本块6分析:")
        print(f"        文本块6位置: ({tx0}, {ty0}, {tx1}, {ty1})")
        print(f"        Y轴重叠: {not (y1 < ty0 - y_tolerance or y0 > ty1 + y_tolerance)}")
        print(f"        X轴包含: {tx0 < x0 and x1 < tx1}")

if __name__ == "__main__":
    test_with_real_data()
#!/usr/bin/env python3
"""
演示图像OCR功能的脚本
展示如何检测PDF中嵌入在文本行之间的图像，并使用OCR提取图像中的文字
"""

import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from pdf2zh.ocr import get_ocr_processor
from pdf2zh.image_processor import ImageProcessor
import numpy as np


def demo_image_detection():
    """演示图像嵌入检测功能"""
    print("=== 图像嵌入检测演示 ===")
    
    # 创建OCR处理器和图像处理器
    ocr_processor = get_ocr_processor("eng")
    image_processor = ImageProcessor(ocr_processor)
    
    # 模拟文本块数据（来自main.py的分析结果）
    print("\n模拟的PDF文本块：")
    text_blocks = [
        (36.3, 103.5, 558.3, 119.8),   # 文本块1: "Thanks for choosing..."
        (36.2, 124.5, 558.3, 140.8),   # 文本块2: "the phone generic..."
        (36.2, 148.3, 234.6, 165.5),   # 文本块3: "your device is running, you can go to"
        (248.8, 148.3, 327.8, 165.5),  # 文本块4: "About phone to view..."
        (36.2, 172.6, 97.8, 189.0),    # 文本块5: "information."
    ]
    
    text_contents = [
        "Thanks for choosing Xiaomi phone, please read the user guide carefully before you start. This is",
        "the phone generic user guide for the HyperOS version. If you are not sure which software version",
        "your device is running, you can go to",
        "About phone to view the HyperOS version",
        "information."
    ]
    
    for i, (block, content) in enumerate(zip(text_blocks, text_contents)):
        print(f"  文本块 {i+1}: {block} -> {content[:50]}...")
    
    # 模拟图像位置（来自main.py的分析结果）
    print("\n模拟的PDF图像：")
    images = [
        (234.6, 148.2, 248.8, 162.2),  # 图像1: 嵌入在文本块3和4之间
        (311.4, 149.1, 327.8, 165.1),  # 图像2: 在文本块4右侧
        (203.7, 264.4, 387.6, 544.2),  # 图像3: 大图，独立存在
    ]
    
    for i, image_rect in enumerate(images):
        print(f"  图像 {i+1}: {image_rect}")
        
        # 检测图像是否嵌入在文本之间
        is_embedded = image_processor.is_image_between_texts(
            text_blocks, image_rect, "horizontal"
        )
        
        if is_embedded:
            print(f"    ✅ 图像 {i+1} 嵌入在文本之间")
            
            # 查找前面的文字
            preceding_text = image_processor.find_preceding_text(
                text_blocks, text_contents, image_rect, "horizontal"
            )
            
            if preceding_text:
                print(f"    📝 前面的文字: '{preceding_text}'")
                
                # 模拟OCR提取（实际场景中会从真实图像提取）
                if i == 0:  # 第一个图像假设是一个箭头或符号
                    simulated_ocr = ">"
                else:
                    simulated_ocr = f"图像{i+1}的文字"
                
                print(f"    🔍 模拟OCR结果: '{simulated_ocr}'")
                
                # 创建图像占位符
                placeholder = f"{{img:{hash(str(image_rect)) % 10000}}}"
                print(f"    🏷️  图像占位符: {placeholder}")
                
                # 集成到文本中
                # 找到包含前面文字的完整文本
                for j, content in enumerate(text_contents):
                    if preceding_text in content:
                        integrated = image_processor.integrate_image_content(
                            content, preceding_text, simulated_ocr, placeholder
                        )
                        print(f"    ✨ 集成后文本: '{integrated}'")
                        break
            else:
                print(f"    ❌ 图像 {i+1} 前面没有找到相关文字")
        else:
            print(f"    ❌ 图像 {i+1} 未嵌入在文本之间")


def demo_text_integration():
    """演示文本集成功能"""
    print("\n\n=== 文本集成演示 ===")
    
    ocr_processor = get_ocr_processor("eng")
    image_processor = ImageProcessor(ocr_processor)
    
    # 演示不同的文本集成场景
    test_cases = [
        {
            "name": "基本集成",
            "original": "请点击 按钮继续操作。",
            "preceding": "点击",
            "ocr": "设置",
            "placeholder": "{img:1234}"
        },
        {
            "name": "段落中间集成",
            "original": "打开应用后，在主界面找到设置选项，然后进行配置。",
            "preceding": "设置选项",
            "ocr": "⚙️",
            "placeholder": "{img:5678}"
        },
        {
            "name": "没有匹配的情况",
            "original": "这是原始文本。",
            "preceding": "不存在的文字",
            "ocr": "新内容",
            "placeholder": "{img:9999}"
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"  原文: {case['original']}")
        print(f"  前导文字: {case['preceding']}")
        print(f"  OCR文字: {case['ocr']}")
        print(f"  占位符: {case['placeholder']}")
        
        result = image_processor.integrate_image_content(
            case['original'], case['preceding'], case['ocr'], case['placeholder']
        )
        print(f"  结果: {result}")


def demo_coordinate_conversion():
    """演示坐标转换"""
    print("\n\n=== 坐标转换演示 ===")
    
    # 模拟PDF页面尺寸（从main.py的分析可以看出大约是595x842）
    pdf_width, pdf_height = 595, 842
    
    # 模拟图像在PDF中的位置（PDF坐标系：原点在左下角）
    pdf_image_rect = (234.6, 148.2, 248.8, 162.2)
    
    print(f"PDF坐标系中的图像位置: {pdf_image_rect}")
    print(f"PDF页面尺寸: {pdf_width} x {pdf_height}")
    
    # 转换为图像坐标系（原点在左上角）
    x0, y0, x1, y1 = pdf_image_rect
    img_y0 = int(pdf_height - y1)
    img_y1 = int(pdf_height - y0)
    img_x0 = int(x0)
    img_x1 = int(x1)
    
    image_coords = (img_x0, img_y0, img_x1, img_y1)
    print(f"图像坐标系中的位置: {image_coords}")
    
    print("说明：")
    print("  - PDF坐标系：原点在左下角，Y轴向上为正")
    print("  - 图像坐标系：原点在左上角，Y轴向下为正")
    print("  - 转换公式：img_y = pdf_height - pdf_y")


if __name__ == "__main__":
    print("🔍 PDF图像OCR功能演示")
    print("=" * 50)
    
    try:
        demo_image_detection()
        demo_text_integration()
        demo_coordinate_conversion()
        
        print("\n\n✅ 演示完成！")
        print("\n功能总结：")
        print("1. ✅ 检测图像是否嵌入在文本行之间")
        print("2. ✅ 查找图像前面的相关文字")
        print("3. ✅ 使用OCR提取图像中的文字（需要pytesseract）")
        print("4. ✅ 为图像创建占位符")
        print("5. ✅ 将OCR文字集成到翻译流程中")
        print("6. ✅ 正确处理PDF和图像坐标系转换")
        
        print("\n使用说明：")
        print("- 如果图像嵌入在文本行之间且前面有相关文字，系统会：")
        print("  1. 使用OCR提取图像中的文字")
        print("  2. 在前面文字后添加OCR结果")
        print("  3. 添加图像占位符以便后续调整位置")
        print("- 如果图像前面没有相关文字，则不添加占位符")
        print("- 支持水平和垂直方向的图像嵌入检测")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
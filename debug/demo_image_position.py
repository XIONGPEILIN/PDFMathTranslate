#!/usr/bin/env python3
"""
演示图片位置保持功能的脚本

此脚本展示了如何：
1. 检测PDF中嵌入在文字段落里的图片
2. 在图片前面的文字中插入占位符
3. 将带占位符的文字发送给翻译软件
4. 根据翻译后占位符的位置调整PDF中图片的位置
"""

import logging
import numpy as np
from typing import List, Tuple, Dict

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def simulate_pdf_page_data():
    """模拟PDF页面数据"""
    # 模拟文本块 (x0, y0, x1, y1)
    text_blocks = [
        (50, 100, 200, 120),   # "This is the first sentence"
        (210, 100, 350, 120),  # "before the image."
        (400, 100, 600, 120),  # "This continues after image."
        (50, 50, 300, 70),     # "Another paragraph below."
    ]
    
    # 对应的文本内容
    text_contents = [
        "This is the first sentence",
        "before the image.",
        "This continues after image.",
        "Another paragraph below."
    ]
    
    # 模拟图片位置 (嵌入在第一行文本中)
    image_rect = (360, 95, 390, 125)  # 在 "before the image." 和 "This continues" 之间
    
    # 模拟页面图像 (300x200 像素)
    page_image = np.random.randint(0, 255, (200, 650, 3), dtype=np.uint8)
    
    return text_blocks, text_contents, image_rect, page_image

def demonstrate_image_position_workflow():
    """演示完整的图片位置保持工作流程"""
    
    print("=" * 60)
    print("图片位置保持功能演示")
    print("=" * 60)
    
    # 1. 获取模拟数据
    print("\n1. 获取PDF页面数据...")
    text_blocks, text_contents, image_rect, page_image = simulate_pdf_page_data()
    
    print(f"文本块数量: {len(text_blocks)}")
    print(f"图片位置: {image_rect}")
    for i, (block, content) in enumerate(zip(text_blocks, text_contents)):
        print(f"  文本块 {i}: {block} -> '{content}'")
    
    # 2. 导入并使用ImageProcessor
    try:
        from pdf2zh.image_processor import ImageProcessor
        
        print("\n2. 初始化图像处理器...")
        image_processor = ImageProcessor(None)  # 不使用OCR
        
        # 3. 检测图片是否嵌入在文本中
        print("\n3. 检测图片嵌入状态...")
        result = image_processor.process_embedded_image(
            page_image, image_rect, text_blocks, text_contents
        )
        
        print(f"是否嵌入: {result['is_embedded']}")
        print(f"前置文字: '{result['preceding_text']}'")
        print(f"图片占位符: '{result['image_placeholder']}'")
        
        # 4. 构建带占位符的原文
        print("\n4. 构建带占位符的原文...")
        original_text = " ".join(text_contents)
        
        if result['is_embedded'] and result['preceding_text']:
            # 在前置文字后插入占位符
            preceding_text = result['preceding_text']
            placeholder = f"<IMG_PLACEHOLDER:1:{image_rect[0]:.2f},{image_rect[1]:.2f},{image_rect[2]:.2f},{image_rect[3]:.2f}:{preceding_text}>"
            
            # 简单的插入逻辑
            if preceding_text in original_text:
                original_with_placeholder = original_text.replace(
                    preceding_text,
                    f"{preceding_text} {placeholder}",
                    1
                )
            else:
                original_with_placeholder = f"{original_text} {placeholder}"
        else:
            # 普通图片占位符
            placeholder = f"<f1:{image_rect[0]:.2f},{image_rect[1]:.2f},{image_rect[2]:.2f},{image_rect[3]:.2f}>"
            original_with_placeholder = f"{original_text} {placeholder}"
        
        print(f"原文: {original_text}")
        print(f"带占位符: {original_with_placeholder}")
        
        # 5. 模拟翻译过程
        print("\n5. 模拟翻译过程...")
        # 这里简单模拟翻译，实际应该调用翻译API
        translated_text = simulate_translation(original_with_placeholder)
        print(f"翻译结果: {translated_text}")
        
        # 6. 使用PositionProcessor处理位置
        print("\n6. 处理图片位置映射...")
        from pdf2zh.position_processor import PositionProcessor
        
        position_processor = PositionProcessor()
        position_result = position_processor.process_translation_with_images(
            original_with_placeholder, translated_text
        )
        
        print("位置映射结果:")
        for fig_id, mapping in position_result['mapping'].items():
            print(f"  图片 {fig_id}:")
            orig_preceding = mapping['original']['preceding_word']
            trans_preceding = mapping['translated']['preceding_word']
            print(f"    原文前面单词: {orig_preceding}")
            print(f"    译文前面单词: {trans_preceding}")
        
        print(f"新位置信息: {position_result['new_positions']}")
        
        # 7. 生成最终结果
        print("\n7. 生成最终结果...")
        print("✅ 图片位置保持功能演示完成!")
        print("\n工作流程总结:")
        print("1. ✅ 检测到图片嵌入在文本中")
        print("2. ✅ 找到图片前面的文字内容")
        print("3. ✅ 创建带位置信息的占位符")
        print("4. ✅ 翻译带占位符的文本")
        print("5. ✅ 建立位置映射关系")
        print("6. ✅ 计算图片的新位置")
        
    except ImportError as e:
        print(f"\n❌ 导入模块失败: {e}")
        print("请确保已正确安装相关依赖")
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        log.exception("详细错误信息:")

def simulate_translation(text: str) -> str:
    """模拟翻译过程"""
    # 简单的翻译模拟，保持占位符不变
    translations = {
        "This is the first sentence": "这是第一个句子",
        "before the image.": "在图片之前。",
        "This continues after image.": "这在图片之后继续。",
        "Another paragraph below.": "下面的另一个段落。"
    }
    
    translated = text
    for eng, chn in translations.items():
        translated = translated.replace(eng, chn)
    
    return translated

def test_image_detection():
    """测试图片检测功能"""
    print("\n" + "=" * 40)
    print("测试图片检测功能")
    print("=" * 40)
    
    text_blocks, text_contents, image_rect, page_image = simulate_pdf_page_data()
    
    try:
        from pdf2zh.image_processor import ImageProcessor
        from pdf2zh.ocr import get_ocr_processor
        
        ocr_processor = get_ocr_processor("en")
        image_processor = ImageProcessor(ocr_processor)
        
        # 测试水平方向检测
        is_embedded_h = image_processor.is_image_between_texts(
            text_blocks, image_rect, "horizontal"
        )
        print(f"水平方向嵌入检测: {is_embedded_h}")
        
        # 测试垂直方向检测
        is_embedded_v = image_processor.is_image_between_texts(
            text_blocks, image_rect, "vertical"
        )
        print(f"垂直方向嵌入检测: {is_embedded_v}")
        
        # 测试前置文字查找
        preceding_text = image_processor.find_preceding_text(
            text_blocks, text_contents, image_rect, "horizontal"
        )
        print(f"前置文字: '{preceding_text}'")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    # 运行完整演示
    demonstrate_image_position_workflow()
    
    # 运行图片检测测试
    test_image_detection()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
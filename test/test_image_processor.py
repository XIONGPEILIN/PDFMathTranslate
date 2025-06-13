import unittest
import numpy as np
from unittest.mock import MagicMock, patch
from pdf2zh.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        # 创建一个模拟的OCR处理器
        self.mock_ocr_processor = MagicMock()
        self.image_processor = ImageProcessor(self.mock_ocr_processor)

    def test_is_image_between_texts_horizontal(self):
        """测试水平方向的图像嵌入检测"""
        # 设置文本块：左侧文本块 (0,10,50,20) 右侧文本块 (100,10,150,20)
        text_blocks = [(0, 10, 50, 20), (100, 10, 150, 20)]
        
        # 图像在两个文本块之间 (60,12,90,18)
        image_rect = (60, 12, 90, 18)
        result = self.image_processor.is_image_between_texts(text_blocks, image_rect, "horizontal")
        self.assertTrue(result)
        
        # 图像不在两个文本块之间 (0,12,30,18) - 与左侧文本重叠
        image_rect = (0, 12, 30, 18)
        result = self.image_processor.is_image_between_texts(text_blocks, image_rect, "horizontal")
        self.assertFalse(result)

    def test_is_image_between_texts_vertical(self):
        """测试垂直方向的图像嵌入检测"""
        # 设置文本块：上方文本块 (10,0,20,50) 下方文本块 (10,100,20,150)
        text_blocks = [(10, 0, 20, 50), (10, 100, 20, 150)]
        
        # 图像在两个文本块之间 (12,60,18,90)
        image_rect = (12, 60, 18, 90)
        result = self.image_processor.is_image_between_texts(text_blocks, image_rect, "vertical")
        self.assertTrue(result)
        
        # 图像不在两个文本块之间 (12,0,18,30) - 与上方文本重叠
        image_rect = (12, 0, 18, 30)
        result = self.image_processor.is_image_between_texts(text_blocks, image_rect, "vertical")
        self.assertFalse(result)

    def test_find_preceding_text_horizontal(self):
        """测试查找图像前面的文字（水平方向）"""
        text_blocks = [(10, 100, 50, 120), (60, 100, 100, 120), (120, 100, 160, 120)]
        text_contents = ["Hello", "world", "test"]
        
        # 图像位置在 "world" 右侧
        image_rect = (110, 102, 115, 118)
        
        result = self.image_processor.find_preceding_text(
            text_blocks, text_contents, image_rect, "horizontal"
        )
        self.assertEqual(result, "world")

    def test_find_preceding_text_vertical(self):
        """测试查找图像前面的文字（垂直方向）"""
        text_blocks = [(100, 10, 120, 50), (100, 60, 120, 100), (100, 120, 120, 160)]
        text_contents = ["Line 1", "Line 2", "Line 3"]
        
        # 图像位置在 "Line 2" 下方
        image_rect = (102, 110, 118, 115)
        
        result = self.image_processor.find_preceding_text(
            text_blocks, text_contents, image_rect, "vertical"
        )
        self.assertEqual(result, "Line 2")

    def test_process_embedded_image_success(self):
        """测试成功处理嵌入图像的情况"""
        # 模拟页面图像
        page_image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # 设置文本块和内容
        text_blocks = [(10, 100, 50, 120), (120, 100, 160, 120)]
        text_contents = ["前面的文字", "后面的文字"]
        
        # 图像位置在两个文本块之间
        image_rect = (60, 102, 110, 118)
        
        # 模拟OCR返回结果
        self.mock_ocr_processor.extract_text_from_page_region.return_value = "图像中的文字"
        
        result = self.image_processor.process_embedded_image(
            page_image, image_rect, text_blocks, text_contents, "horizontal"
        )
        
        self.assertTrue(result["is_embedded"])
        self.assertEqual(result["preceding_text"], "前面的文字")
        self.assertEqual(result["ocr_text"], "图像中的文字")
        self.assertIsNotNone(result["image_placeholder"])
        self.assertTrue(result["image_placeholder"].startswith("{img:"))

    def test_process_embedded_image_not_embedded(self):
        """测试图像未嵌入的情况"""
        page_image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # 设置文本块和内容
        text_blocks = [(10, 100, 50, 120), (120, 100, 160, 120)]
        text_contents = ["前面的文字", "后面的文字"]
        
        # 图像位置不在两个文本块之间
        image_rect = (0, 102, 30, 118)
        
        result = self.image_processor.process_embedded_image(
            page_image, image_rect, text_blocks, text_contents, "horizontal"
        )
        
        self.assertFalse(result["is_embedded"])
        self.assertIsNone(result["preceding_text"])
        self.assertIsNone(result["ocr_text"])
        self.assertIsNone(result["image_placeholder"])

    def test_integrate_image_content(self):
        """测试图像内容集成功能"""
        text_content = "这是前面的文字，后面还有内容。"
        preceding_text = "前面的文字"
        ocr_text = "图像文字"
        image_placeholder = "{img:1234}"
        
        result = self.image_processor.integrate_image_content(
            text_content, preceding_text, ocr_text, image_placeholder
        )
        
        expected = "这是前面的文字 图像文字 {img:1234}，后面还有内容。"
        self.assertEqual(result, expected)

    def test_integrate_image_content_no_match(self):
        """测试找不到匹配文字时的处理"""
        text_content = "这是原始内容。"
        preceding_text = "不存在的文字"
        ocr_text = "图像文字"
        image_placeholder = "{img:1234}"
        
        result = self.image_processor.integrate_image_content(
            text_content, preceding_text, ocr_text, image_placeholder
        )
        
        # 应该追加到末尾
        expected = "这是原始内容。 图像文字 {img:1234}"
        self.assertEqual(result, expected)

    def test_empty_text_blocks(self):
        """测试空文本块的处理"""
        result = self.image_processor.is_image_between_texts([], (10, 10, 20, 20))
        self.assertFalse(result)
        
        result = self.image_processor.find_preceding_text([], [], (10, 10, 20, 20))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
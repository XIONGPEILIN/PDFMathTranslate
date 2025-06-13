import unittest
import numpy as np
from unittest.mock import patch, MagicMock
from pdf2zh.ocr import OCRProcessor, get_ocr_processor


class TestOCRProcessor(unittest.TestCase):
    def setUp(self):
        self.ocr_processor = OCRProcessor("eng")

    def test_initialization(self):
        """测试OCR处理器初始化"""
        self.assertEqual(self.ocr_processor.lang_in, "eng")
        
    def test_get_tesseract_lang(self):
        """测试语言代码转换"""
        test_cases = [
            ("en", "eng"),
            ("zh", "chi_sim"),
            ("zh-cn", "chi_sim"),
            ("zh-tw", "chi_tra"),
            ("ja", "jpn"),
            ("ko", "kor"),
            ("unknown", "eng"),  # 默认回退到英语
        ]
        
        for input_lang, expected in test_cases:
            processor = OCRProcessor(input_lang)
            result = processor._get_tesseract_lang()
            self.assertEqual(result, expected, f"Language {input_lang} should map to {expected}")
    
    def test_clean_text(self):
        """测试文本清理功能"""
        test_cases = [
            ("Hello\n\nWorld\n", "Hello World"),
            ("  Spaced   Text  \n", "Spaced   Text"),
            ("\n\n\n", ""),
            ("Normal text", "Normal text"),
            ("Line1\nLine2\n  Line3  ", "Line1 Line2 Line3"),
        ]
        
        for input_text, expected in test_cases:
            result = self.ocr_processor._clean_text(input_text)
            self.assertEqual(result, expected)
    
    @patch('pdf2zh.ocr.TESSERACT_AVAILABLE', False)
    def test_ocr_not_available(self):
        """测试OCR不可用时的处理"""
        processor = OCRProcessor("eng")
        self.assertFalse(processor.available)
        
        # 创建一个测试图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = processor.extract_text_from_page_region(test_image, (0, 0, 50, 50))
        self.assertIsNone(result)
    
    @patch('pdf2zh.ocr.TESSERACT_AVAILABLE', True)
    def test_extract_text_from_page_region_success(self):
        """测试成功从页面区域提取文字"""
        # 创建测试图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        processor = OCRProcessor("eng")
        processor.available = True
        
        # 模拟pytesseract.image_to_string方法
        with patch('pdf2zh.ocr.pytesseract.image_to_string') as mock_image_to_string:
            mock_image_to_string.return_value = "Test text from image"
            
            result = processor.extract_text_from_page_region(test_image, (10, 10, 90, 90))
            
            self.assertEqual(result, "Test text from image")
            mock_image_to_string.assert_called_once()
    
    @patch('pdf2zh.ocr.TESSERACT_AVAILABLE', True)
    def test_extract_text_from_page_region_empty(self):
        """测试从页面区域提取空文字"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        processor = OCRProcessor("eng")
        processor.available = True
        
        # 模拟pytesseract返回空字符串
        with patch('pdf2zh.ocr.pytesseract.image_to_string') as mock_image_to_string:
            mock_image_to_string.return_value = "   \n\n  "
            
            result = processor.extract_text_from_page_region(test_image, (10, 10, 90, 90))
            
            self.assertIsNone(result)
    
    @patch('pdf2zh.ocr.TESSERACT_AVAILABLE', True)
    def test_extract_text_from_page_region_error(self):
        """测试OCR处理出错的情况"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        processor = OCRProcessor("eng")
        processor.available = True
        
        # 模拟pytesseract抛出异常
        with patch('pdf2zh.ocr.pytesseract.image_to_string') as mock_image_to_string:
            mock_image_to_string.side_effect = Exception("OCR failed")
            
            result = processor.extract_text_from_page_region(test_image, (10, 10, 90, 90))
            
            self.assertIsNone(result)
    
    @patch('pdf2zh.ocr.TESSERACT_AVAILABLE', True)
    def test_bbox_bounds_checking(self):
        """测试边界框边界检查"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        processor = OCRProcessor("eng")
        processor.available = True
        
        with patch('pdf2zh.ocr.pytesseract.image_to_string') as mock_image_to_string:
            mock_image_to_string.return_value = "Valid text"
            
            # 测试超出图像边界的bbox
            result = processor.extract_text_from_page_region(test_image, (-10, -10, 200, 200))
            
            # 应该自动调整到有效范围
            mock_image_to_string.assert_called_once()
    
    def test_get_ocr_processor_singleton(self):
        """测试OCR处理器单例模式"""
        processor1 = get_ocr_processor("eng")
        processor2 = get_ocr_processor("eng")
        
        # 相同语言应该返回同一个实例
        self.assertIs(processor1, processor2)
        
        # 不同语言应该创建新实例
        processor3 = get_ocr_processor("zh")
        self.assertIsNot(processor1, processor3)


if __name__ == "__main__":
    unittest.main()
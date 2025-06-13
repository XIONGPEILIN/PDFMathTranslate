"""图像处理模块：检测嵌入在文本中的图像并提取文字"""

import logging
from typing import List, Tuple, Dict, Optional
import numpy as np

log = logging.getLogger(__name__)


class ImageProcessor:
    """处理PDF中嵌入在文本行之间的图像"""
    
    def __init__(self, ocr_processor):
        self.ocr_processor = ocr_processor
    
    def is_image_between_texts(self, text_blocks: List[Tuple], image_rect: Tuple, direction="horizontal") -> bool:
        """
        判断图像是否处于两个文本块之间或嵌入在文本块内部。
        
        Args:
            text_blocks: 文本块列表 [(x0, y0, x1, y1), ...]
            image_rect: 图像矩形 (x0, y0, x1, y1)
            direction: "horizontal" 表示横向判断，"vertical" 表示纵向判断
            
        Returns:
            bool: 图像是否嵌入在文本之间
        """
        if not text_blocks:
            return False
        
        x0, y0, x1, y1 = image_rect
        
        if direction == "horizontal":
            # 检查图像是否在文本行内嵌入
            for text_block in text_blocks:
                tx0, ty0, tx1, ty1 = text_block
                
                # 检查Y轴重叠（同一行） - 使用容差处理
                y_tolerance = 10  # 10像素容差
                if not (y1 < ty0 - y_tolerance or y0 > ty1 + y_tolerance):
                    # 检查图像是否在文本块的X范围内（嵌入在文本行中）
                    if tx0 < x0 and x1 < tx1:  # 图像完全在文本块内部
                        return True
            
            # 检查图像是否与同行文本块相邻（行首、行中、行尾）
            same_line_blocks = []
            for text_block in text_blocks:
                tx0, ty0, tx1, ty1 = text_block
                # 检查Y轴重叠（同一行）
                y_tolerance = 10
                if not (y1 < ty0 - y_tolerance or y0 > ty1 + y_tolerance):
                    same_line_blocks.append(text_block)
            
            if same_line_blocks:
                # 按X轴排序（左到右）
                same_line_blocks = sorted(same_line_blocks, key=lambda b: b[0])
                gap_tolerance = 5  # 允许5像素的间隙
                
                # 检查图像是否在行首（图像右侧紧邻文本）
                for text_block in same_line_blocks:
                    tx0, ty0, tx1, ty1 = text_block
                    if abs(x1 - tx0) <= gap_tolerance:  # 图像右边界与文本左边界相邻
                        return True
                
                # 检查图像是否在行尾（图像左侧紧邻文本）
                for text_block in same_line_blocks:
                    tx0, ty0, tx1, ty1 = text_block
                    if abs(tx1 - x0) <= gap_tolerance:  # 文本右边界与图像左边界相邻
                        return True
                
                # 检查图像是否在两个文本块之间（行中）
                for i in range(len(same_line_blocks) - 1):
                    left_block = same_line_blocks[i]
                    right_block = same_line_blocks[i + 1]
                    
                    # 图像在两个文本块之间的条件（横向）
                    if (left_block[2] <= x0 + gap_tolerance and x1 <= right_block[0] + gap_tolerance):
                        return True
        
        else:  # vertical
            # 检查图像是否在文本列内嵌入
            for text_block in text_blocks:
                tx0, ty0, tx1, ty1 = text_block
                
                # 检查X轴重叠（同一列）
                x_tolerance = 10
                if not (x1 < tx0 - x_tolerance or x0 > tx1 + x_tolerance):
                    # 检查图像是否在文本块的Y范围内（嵌入在文本列中）
                    if ty0 < y0 and y1 < ty1:  # 图像完全在文本块内部
                        return True
            
            # 按Y轴排序（上到下）
            text_blocks = sorted(text_blocks, key=lambda b: b[1])
            
            # 检查图像是否在任意两个文本块之间（纵向）
            for i in range(len(text_blocks) - 1):
                upper_block = text_blocks[i]
                lower_block = text_blocks[i + 1]
                
                # 检查X轴重叠
                x_tolerance = 10
                upper_x_overlap = not (x1 < upper_block[0] - x_tolerance or x0 > upper_block[2] + x_tolerance)
                lower_x_overlap = not (x1 < lower_block[0] - x_tolerance or x0 > lower_block[2] + x_tolerance)
                
                if upper_x_overlap and lower_x_overlap:
                    # 图像在两个文本块之间的条件（纵向）：
                    # 1. 图像顶部在上方文本块底部之下
                    # 2. 图像底部在下方文本块顶部之上
                    if (upper_block[3] <= y0 and y1 <= lower_block[1]):
                        return True
        
        return False
    
    def find_preceding_text(self, text_blocks: List[Tuple], text_contents: List[str], 
                          image_rect: Tuple, direction="horizontal") -> Optional[str]:
        """
        找到图像前面的文字内容。
        
        Args:
            text_blocks: 文本块列表 [(x0, y0, x1, y1), ...]
            text_contents: 对应的文本内容列表
            image_rect: 图像矩形 (x0, y0, x1, y1)
            direction: 搜索方向
            
        Returns:
            Optional[str]: 图像前面的文字内容，如果没有则返回None
        """
        if not text_blocks or len(text_blocks) != len(text_contents):
            return None
        
        x0, y0, x1, y1 = image_rect
        preceding_texts = []
        
        if direction == "horizontal":
            # 找到图像左侧的文本块
            for i, (tx0, ty0, tx1, ty1) in enumerate(text_blocks):
                # 检查文本块是否在图像左侧
                if tx1 <= x0 and abs(ty0 - y0) < 20:  # 20像素的容差，认为在同一行
                    preceding_texts.append((tx1, text_contents[i]))  # 记录右边界位置和文本
            
            # 按右边界位置排序，取最靠近图像的文本
            if preceding_texts:
                preceding_texts.sort(key=lambda x: x[0], reverse=True)
                return preceding_texts[0][1]
        
        else:  # vertical
            # 找到图像上方的文本块
            for i, (tx0, ty0, tx1, ty1) in enumerate(text_blocks):
                # 检查文本块是否在图像上方
                if ty1 <= y0 and abs(tx0 - x0) < 50:  # 50像素的容差，认为在同一列
                    preceding_texts.append((ty1, text_contents[i]))  # 记录下边界位置和文本
            
            # 按下边界位置排序，取最靠近图像的文本
            if preceding_texts:
                preceding_texts.sort(key=lambda x: x[0], reverse=True)
                return preceding_texts[0][1]
        
        return None
    
    def process_embedded_image(self, page_image: np.ndarray, image_rect: Tuple, 
                             text_blocks: List[Tuple], text_contents: List[str], 
                             direction="horizontal") -> Dict:
        """
        处理嵌入在文本中的图像。
        
        Args:
            page_image: 页面图像
            image_rect: 图像矩形
            text_blocks: 文本块列表
            text_contents: 文本内容列表
            direction: 检测方向
            
        Returns:
            Dict: 处理结果，包含是否嵌入、前面的文字、OCR文字等
        """
        result = {
            "is_embedded": False,
            "preceding_text": None,
            "ocr_text": None,
            "image_placeholder": None
        }
        
        # 检查图像是否嵌入在文本之间
        result["is_embedded"] = self.is_image_between_texts(text_blocks, image_rect, direction)
        
        if result["is_embedded"]:
            log.debug(f"图像 {image_rect} 嵌入在文本之间")
            
            # 找到图像前面的文字
            result["preceding_text"] = self.find_preceding_text(
                text_blocks, text_contents, image_rect, direction
            )
            
            if result["preceding_text"]:
                log.debug(f"图像前面的文字: {result['preceding_text'][:50]}...")
                
                # 使用OCR提取图像中的文字
                x0, y0, x1, y1 = image_rect
                h, w = page_image.shape[:2]
                
                # 转换坐标系（PDF坐标系原点在左下角，图像坐标系原点在左上角）
                img_y0 = int(h - y1)
                img_y1 = int(h - y0)
                img_x0 = int(x0)
                img_x1 = int(x1)
                
                result["ocr_text"] = self.ocr_processor.extract_text_from_page_region(
                    page_image, (img_x0, img_y0, img_x1, img_y1)
                )
                
                if result["ocr_text"]:
                    log.debug(f"OCR提取的文字: {result['ocr_text'][:50]}...")
                    # 创建图像占位符，格式为 {img:序号}
                    result["image_placeholder"] = f"{{img:{hash(str(image_rect)) % 10000}}}"
                else:
                    log.debug("OCR未能从图像中提取到文字")
            else:
                log.debug("图像前面没有找到相关文字")
        else:
            log.debug(f"图像 {image_rect} 未嵌入在文本之间")
        
        return result
    
    def integrate_image_content(self, text_content: str, preceding_text: str, 
                              ocr_text: str, image_placeholder: str) -> str:
        """
        将图像内容集成到文本中。
        
        Args:
            text_content: 原始文本内容
            preceding_text: 图像前面的文字
            ocr_text: OCR提取的文字
            image_placeholder: 图像占位符
            
        Returns:
            str: 集成后的文本内容
        """
        if not preceding_text or not ocr_text:
            return text_content
        
        # 在前面文字后添加OCR文字和图像占位符
        # 例如：原文 "前面的文字" -> "前面的文字 OCR文字 {img:1234}"
        
        # 找到preceding_text在text_content中的位置
        try:
            # 清理文本，移除多余的空格和换行
            clean_preceding = preceding_text.strip()
            clean_content = text_content.strip()
            
            # 寻找匹配位置
            pos = clean_content.find(clean_preceding)
            if pos != -1:
                # 在匹配位置后插入OCR文字和占位符
                insert_pos = pos + len(clean_preceding)
                integrated_text = (
                    clean_content[:insert_pos] + 
                    f" {ocr_text} {image_placeholder}" + 
                    clean_content[insert_pos:]
                )
                return integrated_text
            else:
                # 如果找不到精确匹配，追加到末尾
                return f"{clean_content} {ocr_text} {image_placeholder}"
        
        except Exception as e:
            log.warning(f"集成图像内容时出错: {e}")
            return text_content
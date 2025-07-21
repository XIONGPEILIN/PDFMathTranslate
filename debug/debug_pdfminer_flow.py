#!/usr/bin/env python3
"""
调试PDFMiner的实际处理流程
"""

import logging
import sys
import os
import io
from pathlib import Path

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pymupdf import Document, Font

from pdf2zh.converter import TranslateConverter
from pdf2zh.pdfinterp import PDFPageInterpreterEx
from pdf2zh.doclayout import OnnxModel

def debug_pdfminer_conversion():
    """调试PDFMiner的实际转换过程"""
    
    print("=== 调试PDFMiner转换过程 ===\n")
    
    try:
        # 打开PDF文件
        with open("test5.pdf", "rb") as f:
            pdf_data = f.read()
        
        # 使用PyMuPDF处理字体
        doc_zh = Document(stream=pdf_data)
        
        # 创建资源管理器
        rsrcmgr = PDFResourceManager()
        
        # 创建布局（简化版）
        layout = {0: None}  # 简化的布局
        
        # 创建转换器
        device = TranslateConverter(
            rsrcmgr,
            "",  # vfont
            "",  # vchar
            1,   # thread
            layout,
            "en",  # lang_in
            "zh-cn",  # lang_out
            "google",  # service
            "noto",  # noto_name
            None,  # noto
            {},    # envs
            None,  # prompt
            False, # ignore_cache
            {},    # page_images
            {}     # embedded_images
        )
        
        # 解析PDF
        parser = PDFParser(io.BytesIO(pdf_data))
        doc = PDFDocument(parser)
        interpreter = PDFPageInterpreterEx(rsrcmgr, device, {})
        
        # 处理第一页
        for pageno, page in enumerate(PDFPage.create_pages(doc)):
            if pageno > 0:  # 只处理第一页
                break
                
            print(f"处理页面 {pageno}")
            page.pageno = pageno
            
            # 创建简单的布局（全部允许翻译）
            import numpy as np
            layout[page.pageno] = np.ones((800, 600))  # 简化的布局矩阵
            
            # 处理页面
            interpreter.process_page(page)
            break
        
        device.close()
        
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pdfminer_conversion()
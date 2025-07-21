#!/usr/bin/env python3
"""
测试当前的翻译结果，查看调试输出
"""

import logging
import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(__file__))

from pdf2zh.high_level import translate
from pdf2zh.doclayout import OnnxModel

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

def test_current_translation():
    """测试当前的翻译结果"""
    
    print("=== 测试当前翻译结果 ===\n")
    
    try:
        # 初始化模型
        model = OnnxModel("pdf2zh/doclayout/lp_models/models/handwritten/layout/model.onnx")
        
        # 翻译 test5.pdf
        result = translate(
            files=["test5.pdf"],
            output="./",
            lang_in="en",
            lang_out="zh-cn",
            service="google",
            thread=1,
            model=model,
            envs={}
        )
        
        print(f"翻译完成: {result}")
        
    except Exception as e:
        print(f"翻译失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_translation()
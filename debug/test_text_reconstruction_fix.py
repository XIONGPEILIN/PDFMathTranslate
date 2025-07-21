#!/usr/bin/env python3
"""
测试文本重组修复功能
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(__file__))

from pdf2zh.converter import TranslateConverter
from pdf2zh.translator import GoogleTranslator

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

def test_text_reconstruction():
    """测试文本重组功能是否能正确合并被分割的文本"""
    
    print("=== 测试智能文本重组功能 ===\n")
    
    # 模拟被分割的段落数据
    print("模拟原始分割情况：")
    print("段落 0: 'your device is running, you can go to '")
    print("图像块: Settings图标")
    print("段落 1: 'Settings > '") 
    print("图像块: About phone图标")
    print("段落 2: 'About phone to view the HyperOS version '")
    print()
    
    print("期望的智能重组结果：")
    print("段落 0: 'your device is running, you can go to <f0:...> Settings > <f1:...> About phone to view the HyperOS version '")
    print()
    
    # 现在让我们通过实际翻译test5.pdf来验证
    print("=== 实际翻译test5.pdf验证 ===\n")
    
    try:
        # 导入必要的模块进行实际测试
        import fitz
        from pdf2zh.high_level import translate
        from pdf2zh.doclayout import OnnxModel
        
        # 简单配置
        print("开始翻译test5.pdf...")
        print("注意观察日志中的智能文本重组过程...")
        
        # 创建模型（如果需要）
        try:
            model = OnnxModel()
        except:
            print("警告：无法加载ONNX模型，将使用默认布局检测")
            model = None
        
        # 执行翻译
        result = translate(
            files=['test5.pdf'],
            output='.',
            lang_in='en',
            lang_out='zh-cn',
            service='google',
            thread=1,
            model=model
        )
        
        if result:
            print(f"✓ 翻译完成: {result}")
            print("请检查翻译结果中是否包含完整的关键句子")
            print("生成的文件:")
            for mono_file, dual_file in result:
                print(f"  单语版本: {mono_file}")
                print(f"  双语版本: {dual_file}")
        else:
            print("✗ 翻译失败")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

def analyze_log_output():
    """分析日志输出以验证修复效果"""
    
    print("\n=== 分析修复效果 ===")
    print("请检查上面的日志输出中：")
    print("1. 是否出现了'智能文本重组'的日志")
    print("2. 是否显示了'找到合并候选段落'")
    print("3. 是否显示了'合并段落'的成功信息")
    print("4. 翻译结果中是否包含完整的句子")

if __name__ == "__main__":
    test_text_reconstruction()
    analyze_log_output()
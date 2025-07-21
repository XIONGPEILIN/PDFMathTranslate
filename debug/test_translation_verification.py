#!/usr/bin/env python3
"""
PDF2ZH 翻译修复验证脚本
用于验证 test5.pdf 翻译问题修复是否有效
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主验证函数"""
    print("=== PDF2ZH 翻译修复验证开始 ===")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 导入必要的模块
        from pdf2zh.high_level import translate
        from pdf2zh.doclayout import OnnxModel, ModelInstance
        
        # 设置模型
        ModelInstance.value = OnnxModel.load_available()
        
        # 定义参数
        input_file = "test5.pdf"
        
        if not os.path.exists(input_file):
            print(f"错误：文件 {input_file} 不存在")
            return 1
            
        print(f"开始翻译文件：{input_file}")
        
        # 执行翻译
        args = {
            'files': [input_file],
            'lang_in': 'en',
            'lang_out': 'zh',
            'service': 'google',
            'thread': 4,
            'pages': None,
            'vfont': '',
            'vchar': '',
            'output': '',
            'compatible': False,
            'debug': True,
            'prompt': None,
            'skip_subset_fonts': False,
            'ignore_cache': True  # 强制重新翻译
        }
        
        print("翻译参数：")
        for key, value in args.items():
            print(f"  {key}: {value}")
        
        # 执行翻译
        translate(model=ModelInstance.value, **args)
        
        print("=== 翻译完成 ===")
        
        # 查找生成的翻译文件
        possible_outputs = [
            "test5-dual.pdf",
            "test5-mono.pdf", 
            "test5_translated.pdf"
        ]
        
        found_files = []
        for output_file in possible_outputs:
            if os.path.exists(output_file):
                found_files.append(output_file)
                print(f"找到翻译结果文件：{output_file}")
        
        if not found_files:
            print("警告：未找到翻译结果文件")
            # 列出当前目录的所有 PDF 文件
            pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
            print(f"当前目录的 PDF 文件：{pdf_files}")
            
        return 0
        
    except Exception as e:
        print(f"翻译过程中出错：{e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
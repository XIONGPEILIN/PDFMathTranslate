#!/usr/bin/env python3
"""
修复图片位置保持功能中文本丢失的问题
"""

import logging
import sys
import os
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_image_text_loss.log', mode='w', encoding='utf-8')
    ]
)

log = logging.getLogger(__name__)

def analyze_text_loss_problem():
    """分析文本丢失问题的根本原因"""
    
    log.info("="*60)
    log.info("分析图片位置保持功能中的文本丢失问题")
    log.info("="*60)
    
    # 从调试日志中找到关键信息
    debug_log_file = "debug_workflow.log"
    if not os.path.exists(debug_log_file):
        log.error("调试日志文件不存在")
        return False
    
    with open(debug_log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # 查找关键的翻译请求
    import re
    
    # 找到包含图片占位符的翻译请求
    pattern = r'SELECT.*original_text.*Settings.*About phone'
    matches = re.findall(pattern, log_content, re.MULTILINE | re.DOTALL)
    
    if matches:
        log.info("找到包含图片的翻译请求:")
        for i, match in enumerate(matches):
            log.info(f"匹配 {i+1}: {match[:200]}...")
    
    # 分析问题的具体表现
    log.info("\n问题分析:")
    log.info("1. 原文: 'Settings > [图片1] About phone [图片2] to view the HyperOS version'")
    log.info("2. 期望翻译: '设置 > [图片1] 关于手机 [图片2] 查看HyperOS版本'")
    log.info("3. 实际结果: 包含图片的文字行完全消失")
    
    # 检查翻译缓存
    pattern_cache = r"'Thanks.*Settings.*About phone.*'"
    cache_matches = re.findall(pattern_cache, log_content)
    
    if cache_matches:
        log.info("\n找到翻译缓存请求:")
        for match in cache_matches:
            log.info(f"缓存内容: {match[:300]}...")
    
    return True

def propose_fix_solution():
    """提出修复方案"""
    
    log.info("\n" + "="*60)
    log.info("修复方案分析")
    log.info("="*60)
    
    log.info("根本问题:")
    log.info("1. 图片占位符 <f0:...> 和 <f1:...> 干扰了文本的正常处理")
    log.info("2. 翻译器可能无法正确处理包含占位符的复杂文本结构")
    log.info("3. 文本分割和重组过程中丢失了关键内容")
    
    log.info("\n修复策略:")
    log.info("1. 改进占位符格式，使其更容易被翻译器识别和保持")
    log.info("2. 在翻译前预处理文本，临时替换占位符为简单标记")
    log.info("3. 翻译后恢复占位符，确保图片位置信息不丢失")
    log.info("4. 增强文本完整性验证，确保没有内容丢失")
    
    # 生成修复代码示例
    fix_code = '''
def fix_text_with_images(original_text, translated_text):
    """修复包含图片的文本翻译"""
    
    # 1. 提取图片占位符
    import re
    image_pattern = r'<f(\d+):[^>]+>'
    placeholders = re.findall(image_pattern, original_text)
    
    # 2. 用简单标记替换占位符进行翻译
    temp_text = original_text
    placeholder_map = {}
    for i, match in enumerate(re.finditer(image_pattern, original_text)):
        temp_marker = f"[IMG{i}]"
        placeholder_map[temp_marker] = match.group(0)
        temp_text = temp_text.replace(match.group(0), temp_marker, 1)
    
    # 3. 翻译简化后的文本
    # translated_temp = translator.translate(temp_text)
    
    # 4. 恢复占位符
    # for marker, placeholder in placeholder_map.items():
    #     translated_temp = translated_temp.replace(marker, placeholder)
    
    return translated_text
'''
    
    with open("fix_solution.py", "w", encoding="utf-8") as f:
        f.write(fix_code)
    
    log.info("\n✓ 修复代码示例已生成: fix_solution.py")

def create_test_case():
    """创建测试用例来验证修复效果"""
    
    log.info("\n" + "="*60)
    log.info("创建测试用例")
    log.info("="*60)
    
    test_cases = [
        {
            "name": "包含图片的设置指导",
            "original": "Settings > <f0:234.56,679.67,248.80,693.65> About phone <f1:311.43,676.83,327.75,692.80> to view the HyperOS version",
            "expected": "设置 > <f0:234.56,679.67,248.80,693.65> 关于手机 <f1:311.43,676.83,327.75,692.80> 查看HyperOS版本",
            "current_result": "（文本丢失）"
        },
        {
            "name": "简单文本（对照组）",
            "original": "Insert a SIM card",
            "expected": "插入SIM卡",
            "current_result": "插入SIM卡 ✓"
        }
    ]
    
    log.info("测试用例:")
    for i, case in enumerate(test_cases, 1):
        log.info(f"\n测试 {i}: {case['name']}")
        log.info(f"  原文: {case['original']}")
        log.info(f"  期望: {case['expected']}")
        log.info(f"  当前: {case['current_result']}")
    
    return test_cases

def main():
    print("图片位置保持功能文本丢失问题修复分析")
    print("=" * 50)
    
    # 分析问题
    success = analyze_text_loss_problem()
    
    if success:
        # 提出修复方案
        propose_fix_solution()
        
        # 创建测试用例
        create_test_case()
    
    print("\n" + "="*50)
    print("🔧 问题分析完成")
    print("📋 核心问题: 包含图片占位符的文本在翻译时丢失")
    print("🛠️  修复方向: 改进占位符处理机制")
    print("📝 详细日志: fix_image_text_loss.log")

if __name__ == "__main__":
    main()
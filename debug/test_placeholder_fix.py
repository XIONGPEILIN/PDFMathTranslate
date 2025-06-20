#!/usr/bin/env python3
"""
测试图片占位符修复效果
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_placeholder_fix.log', mode='w', encoding='utf-8')
    ]
)

log = logging.getLogger(__name__)

def test_placeholder_processor():
    """测试占位符处理器功能"""
    
    log.info("="*60)
    log.info("测试占位符处理器功能")
    log.info("="*60)
    
    from pdf2zh.placeholder_processor import PlaceholderProcessor
    
    processor = PlaceholderProcessor()
    
    # 测试用例1：包含复杂占位符的文本
    test_cases = [
        {
            "name": "包含图片的设置指导",
            "original": "Settings > <f0:234.56,679.67,248.80,693.65> About phone <f1:311.43,676.83,327.75,692.80> to view the HyperOS version",
            "expected_chinese": "设置 > [IMG0] 关于手机 [IMG1] 查看HyperOS版本"
        },
        {
            "name": "增强占位符格式",
            "original": "Thanks for purchasing <IMG_PLACEHOLDER:0:234.56,679.67,248.80,693.65:Settings> this device.",
            "expected_chinese": "感谢购买 [IMG0] 此设备。"
        },
        {
            "name": "混合占位符格式",
            "original": "Check <f0:100,200,150,250> settings and <IMG_PLACEHOLDER:1:300,400,350,450:phone> options",
            "expected_chinese": "检查 [IMG0] 设置和 [IMG1] 选项"
        }
    ]
    
    success_count = 0
    
    for i, case in enumerate(test_cases, 1):
        log.info(f"\n--- 测试用例 {i}: {case['name']} ---")
        
        # 重置处理器
        processor.reset()
        
        # 步骤1：简化占位符
        simplified = processor.simplify_placeholders(case["original"])
        log.info(f"原文: {case['original']}")
        log.info(f"简化后: {simplified}")
        
        # 步骤2：模拟翻译（这里手动提供翻译结果）
        # 在实际应用中，这里会调用翻译器
        mock_translation = case["expected_chinese"]
        log.info(f"模拟翻译: {mock_translation}")
        
        # 步骤3：恢复占位符
        restored = processor.restore_placeholders(mock_translation)
        log.info(f"恢复后: {restored}")
        
        # 步骤4：验证完整性
        integrity_ok = processor.validate_text_integrity(case["original"], restored)
        log.info(f"完整性验证: {'✓' if integrity_ok else '✗'}")
        
        # 步骤5：检查结果
        has_placeholders = ("<f0:" in restored or "<f1:" in restored or "IMG_PLACEHOLDER" in restored)
        log.info(f"占位符保留: {'✓' if has_placeholders else '✗'}")
        
        if integrity_ok and has_placeholders:
            success_count += 1
            log.info(f"测试用例 {i}: ✓ 成功")
        else:
            log.warning(f"测试用例 {i}: ✗ 失败")
    
    # 输出统计信息
    stats = processor.get_statistics()
    log.info(f"\n处理统计: {stats}")
    
    log.info(f"\n测试结果: {success_count}/{len(test_cases)} 个用例通过")
    return success_count == len(test_cases)

def test_full_workflow():
    """测试完整的翻译工作流程"""
    
    log.info("\n" + "="*60)
    log.info("测试完整翻译工作流程")
    log.info("="*60)
    
    input_file = "test5.pdf"
    
    if not os.path.exists(input_file):
        log.error(f"测试文件 {input_file} 不存在")
        return False
    
    try:
        from pdf2zh.high_level import translate_stream
        from pdf2zh.doclayout import DocLayoutModel
        
        log.info("加载模型...")
        model = DocLayoutModel.load_available()
        
        log.info("读取PDF文件...")
        with open(input_file, 'rb') as f:
            pdf_content = f.read()
        
        log.info("执行翻译（使用修复后的占位符处理）...")
        
        # 启用详细日志
        logging.getLogger('pdf2zh.converter').setLevel(logging.DEBUG)
        logging.getLogger('pdf2zh.placeholder_processor').setLevel(logging.DEBUG)
        
        result = translate_stream(
            stream=pdf_content,
            pages=None,
            lang_in="en",
            lang_out="zh",
            service="google",
            thread=1,
            model=model
        )
        
        if result:
            mono_content, dual_content = result
            log.info(f"翻译完成!")
            log.info(f"  单语版本: {len(mono_content)} bytes")
            log.info(f"  双语版本: {len(dual_content)} bytes")
            
            # 保存修复后的版本
            with open("test5_fixed_mono.pdf", "wb") as f:
                f.write(mono_content)
            with open("test5_fixed_dual.pdf", "wb") as f:
                f.write(dual_content)
            
            log.info("修复后的文件已保存")
            return True
        else:
            log.error("翻译失败")
            return False
            
    except Exception as e:
        log.error(f"测试失败: {e}")
        log.exception("详细错误信息:")
        return False

def verify_fix_effectiveness():
    """验证修复效果"""
    
    log.info("\n" + "="*60)
    log.info("验证修复效果")
    log.info("="*60)
    
    # 检查生成的文件
    fixed_files = ["test5_fixed_dual.pdf", "test5_fixed_mono.pdf"]
    results = []
    
    for filename in fixed_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            log.info(f"✓ 文件 {filename} 生成成功 ({size} bytes)")
            results.append(True)
        else:
            log.warning(f"✗ 文件 {filename} 未找到")
            results.append(False)
    
    # 检查日志中的关键信息
    log_file = "test_placeholder_fix.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 统计关键指标
        simplify_count = log_content.count("简化占位符")
        restore_count = log_content.count("恢复占位符")
        integrity_count = log_content.count("完整性验证")
        
        log.info(f"处理统计:")
        log.info(f"  占位符简化: {simplify_count} 次")
        log.info(f"  占位符恢复: {restore_count} 次")
        log.info(f"  完整性验证: {integrity_count} 次")
        
        if simplify_count > 0 and restore_count > 0:
            log.info("✓ 占位符处理机制正常工作")
            results.append(True)
        else:
            log.warning("✗ 占位符处理机制未正常工作")
            results.append(False)
    
    return all(results)

def main():
    print("图片占位符修复效果测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 测试1：占位符处理器功能
    if test_placeholder_processor():
        success_count += 1
        print("✓ 占位符处理器测试通过")
    else:
        print("✗ 占位符处理器测试失败")
    
    # 测试2：完整工作流程
    if test_full_workflow():
        success_count += 1
        print("✓ 完整工作流程测试通过")
    else:
        print("✗ 完整工作流程测试失败")
    
    # 测试3：修复效果验证
    if verify_fix_effectiveness():
        success_count += 1
        print("✓ 修复效果验证通过")
    else:
        print("✗ 修复效果验证失败")
    
    print("\n" + "="*50)
    print(f"测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！图片占位符修复成功！")
        print("📋 关键改进:")
        print("  - 复杂占位符简化为 [IMG0], [IMG1] 等")
        print("  - 翻译前预处理，翻译后恢复")
        print("  - 增加文本完整性验证")
        print("  - 防止包含图片的文本行丢失")
    else:
        print("⚠ 部分测试失败，需要进一步调试")
    
    print(f"📝 详细日志: test_placeholder_fix.log")
    
    return success_count == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
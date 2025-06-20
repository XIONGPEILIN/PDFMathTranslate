#!/usr/bin/env python3
"""
测试占位符处理器的完整性检查修复
"""

import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf2zh.placeholder_processor import PlaceholderProcessor

# 设置日志级别为DEBUG以查看详细信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_integrity_check():
    """测试完整性检查的各种情况"""
    processor = PlaceholderProcessor()
    
    print("=" * 60)
    print("测试占位符处理器完整性检查修复")
    print("=" * 60)
    
    # 测试用例1：包含图片占位符的文本
    print("\n1. 测试包含图片占位符的文本")
    original1 = "这是一个测试 <IMG_PLACEHOLDER:1:100.0,200.0,150.0,250.0:test> 包含图片的文本"
    processed1 = "This is a test [IMG1] containing images"
    
    print(f"原文: {original1}")
    print(f"处理后: {processed1}")
    result1 = processor.validate_text_integrity(original1, processed1)
    print(f"完整性检查结果: {'✓ 通过' if result1 else '✗ 失败'}")
    
    # 测试用例2：只有占位符的文本
    print("\n2. 测试只有占位符的文本")
    original2 = "<f0:234.56,679.67,248.80,693.65>"
    processed2 = "[IMG0]"
    
    print(f"原文: {original2}")
    print(f"处理后: {processed2}")
    result2 = processor.validate_text_integrity(original2, processed2)
    print(f"完整性检查结果: {'✓ 通过' if result2 else '✗ 失败'}")
    
    # 测试用例3：复杂的增强占位符
    print("\n3. 测试复杂的增强占位符")
    original3 = "前置文本 <IMG_PLACEHOLDER:2:300.0,400.0,350.0,450.0:前置文本内容> 后续文本"
    processed3 = "Preceding text [IMG2] following text"
    
    print(f"原文: {original3}")
    print(f"处理后: {processed3}")
    result3 = processor.validate_text_integrity(original3, processed3)
    print(f"完整性检查结果: {'✓ 通过' if result3 else '✗ 失败'}")
    
    # 测试用例4：多个占位符
    print("\n4. 测试多个占位符")
    original4 = "文本1 <f0:100,200,150,250> 文本2 <IMG_PLACEHOLDER:1:300,400,350,450:文本1> 文本3"
    processed4 = "Text1 [IMG0] Text2 [IMG1] Text3"
    
    print(f"原文: {original4}")
    print(f"处理后: {processed4}")
    result4 = processor.validate_text_integrity(original4, processed4)
    print(f"完整性检查结果: {'✓ 通过' if result4 else '✗ 失败'}")
    
    # 测试用例5：长度比例过低的情况（修复前会失败）
    print("\n5. 测试长度比例过低的情况")
    original5 = "很长的文本内容包含了大量的占位符 <IMG_PLACEHOLDER:0:100,200,150,250:很长的文本内容包含了大量的占位符> 和其他内容"
    processed5 = "[IMG0]"
    
    print(f"原文: {original5}")
    print(f"处理后: {processed5}")
    result5 = processor.validate_text_integrity(original5, processed5)
    print(f"完整性检查结果: {'✓ 通过' if result5 else '✗ 失败'}")
    
    # 测试用例6：空文本
    print("\n6. 测试空文本")
    original6 = ""
    processed6 = ""
    
    print(f"原文: '{original6}'")
    print(f"处理后: '{processed6}'")
    result6 = processor.validate_text_integrity(original6, processed6)
    print(f"完整性检查结果: {'✓ 通过' if result6 else '✗ 失败'}")
    
    # 统计结果
    all_results = [result1, result2, result3, result4, result5, result6]
    passed = sum(all_results)
    total = len(all_results)
    
    print("\n" + "=" * 60)
    print(f"测试结果总结: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有测试用例都通过了！完整性检查修复成功。")
        return True
    else:
        print("❌ 部分测试用例失败，需要进一步调试。")
        return False

def test_placeholder_processing():
    """测试占位符处理的完整流程"""
    processor = PlaceholderProcessor()
    
    print("\n" + "=" * 60)
    print("测试占位符处理完整流程")
    print("=" * 60)
    
    # 测试文本
    original_text = "这是一个包含图片的文档 <IMG_PLACEHOLDER:1:100.0,200.0,150.0,250.0:这是一个包含图片的文档> 和普通占位符 <f2:300.0,400.0,350.0,450.0> 的测试"
    
    print(f"原始文本: {original_text}")
    
    # 步骤1: 简化占位符
    simplified = processor.simplify_placeholders(original_text)
    print(f"简化后: {simplified}")
    
    # 模拟翻译过程
    mock_translation = "This is a document containing images [IMG1] and normal placeholders [IMG2] for testing"
    print(f"模拟翻译: {mock_translation}")
    
    # 步骤2: 恢复占位符
    restored = processor.restore_placeholders(mock_translation)
    print(f"恢复后: {restored}")
    
    # 步骤3: 验证完整性
    integrity_ok = processor.validate_text_integrity(original_text, restored)
    print(f"完整性检查: {'✓ 通过' if integrity_ok else '✗ 失败'}")
    
    # 获取统计信息
    stats = processor.get_statistics()
    print(f"处理统计: {stats}")
    
    return integrity_ok

if __name__ == "__main__":
    print("开始测试占位符处理器完整性检查修复...")
    
    # 运行测试
    test1_passed = test_integrity_check()
    test2_passed = test_placeholder_processing()
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！修复成功！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，请检查修复代码。")
        sys.exit(1)
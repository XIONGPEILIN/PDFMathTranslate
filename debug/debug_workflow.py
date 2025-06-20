#!/usr/bin/env python3
"""
调试图片位置保持的完整工作流程
"""

import logging
import sys
import os
import io
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置详细调试日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_workflow.log', mode='w', encoding='utf-8')
    ]
)

log = logging.getLogger(__name__)

def test_workflow_step_by_step():
    """逐步测试工作流程"""
    
    input_file = "test5.pdf"
    
    if not os.path.exists(input_file):
        log.error(f"文件 {input_file} 不存在")
        return False
    
    log.info("="*60)
    log.info("开始逐步调试图片位置保持工作流程")
    log.info("="*60)
    
    try:
        # 步骤1: 设置环境
        from pdf2zh.high_level import translate_stream
        from pdf2zh.doclayout import DocLayoutModel
        
        log.info("步骤1: 加载模型和环境")
        model = DocLayoutModel.load_available()
        log.info("✓ 模型加载成功")
        
        # 步骤2: 读取PDF文件
        with open(input_file, 'rb') as f:
            pdf_content = f.read()
        log.info(f"✓ PDF文件读取成功，大小: {len(pdf_content)} bytes")
        
        # 步骤3: 执行翻译流程（带详细日志）
        log.info("步骤3: 执行翻译流程...")
        
        # 启用详细的调试日志
        logging.getLogger('pdf2zh.converter').setLevel(logging.DEBUG)
        logging.getLogger('pdf2zh.image_processor').setLevel(logging.DEBUG)
        logging.getLogger('pdf2zh.position_processor').setLevel(logging.DEBUG)
        
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
            log.info(f"✓ 翻译完成")
            log.info(f"  单语版本大小: {len(mono_content)} bytes")
            log.info(f"  双语版本大小: {len(dual_content)} bytes")
            
            # 保存调试版本
            with open("test5_debug_mono.pdf", "wb") as f:
                f.write(mono_content)
            with open("test5_debug_dual.pdf", "wb") as f:
                f.write(dual_content)
            
            log.info("✓ 调试版本文件已保存")
            return True
        else:
            log.error("✗ 翻译失败")
            return False
            
    except Exception as e:
        log.error(f"工作流程调试失败: {e}")
        log.exception("详细错误信息:")
        return False

def analyze_debug_logs():
    """分析调试日志中的关键信息"""
    
    log.info("\n" + "="*60)
    log.info("分析调试日志")
    log.info("="*60)
    
    if not os.path.exists("debug_workflow.log"):
        log.warning("调试日志文件不存在")
        return
    
    with open("debug_workflow.log", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 统计关键信息
    key_patterns = {
        "图片检测": ["嵌入图片", "embedded", "is_image_between_texts"],
        "占位符": ["IMG_PLACEHOLDER", "placeholder", "占位符"],
        "位置处理": ["position", "位置", "bbox", "rect"],
        "翻译处理": ["translate", "翻译", "worker"],
        "错误": ["ERROR", "Exception", "failed"],
        "警告": ["WARNING", "warning"]
    }
    
    results = {}
    for category, patterns in key_patterns.items():
        count = 0
        for pattern in patterns:
            count += content.lower().count(pattern.lower())
        results[category] = count
    
    log.info("调试日志统计:")
    for category, count in results.items():
        log.info(f"  {category}: {count} 次")
    
    # 查找具体的图片处理记录
    lines = content.split('\n')
    image_lines = []
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in ["image", "图片", "figure", "embedded"]):
            image_lines.append((i+1, line.strip()))
    
    if image_lines:
        log.info(f"\n找到 {len(image_lines)} 条图片相关记录:")
        for line_num, line in image_lines[:20]:  # 显示前20条
            log.info(f"  L{line_num}: {line}")

def create_test_report():
    """创建测试报告"""
    
    log.info("\n" + "="*60)
    log.info("生成工作流程调试报告")
    log.info("="*60)
    
    report = []
    report.append("# Test5.pdf 图片位置保持工作流程调试报告")
    report.append("")
    report.append("## 问题描述")
    report.append("虽然图片嵌入检测功能正常，但翻译后的图片位置没有按预期调整。")
    report.append("具体问题：")
    report.append("- 图片1和2前面有文字，理论上应该跟随文字移动")
    report.append("- 图片3和4前面没有文字，位置应该保持不变")
    report.append("- 实际结果：所有图片位置都没有变化")
    report.append("")
    report.append("## 可能原因分析")
    report.append("1. 图片位置调整逻辑可能没有被正确调用")
    report.append("2. 双语版本可能直接复制了原始图片，跳过了位置调整")
    report.append("3. 位置调整可能发生在不同的处理阶段")
    report.append("4. 图片嵌入检测的条件可能过于严格")
    report.append("")
    report.append("## 调试结果")
    
    # 检查生成的文件
    if os.path.exists("test5_debug_dual.pdf"):
        size = os.path.getsize("test5_debug_dual.pdf")
        report.append(f"- ✓ 调试版本生成成功 ({size} bytes)")
    else:
        report.append("- ✗ 调试版本生成失败")
    
    if os.path.exists("debug_workflow.log"):
        with open("debug_workflow.log", "r", encoding="utf-8") as f:
            log_content = f.read()
        
        error_count = log_content.count("ERROR")
        warning_count = log_content.count("WARNING")
        
        report.append(f"- 错误数量: {error_count}")
        report.append(f"- 警告数量: {warning_count}")
    
    report.append("")
    report.append("## 建议")
    report.append("1. 检查 converter.py 中的图片处理逻辑")
    report.append("2. 验证占位符是否被正确创建和处理")
    report.append("3. 确认位置调整代码是否被执行")
    report.append("4. 可能需要调整图片嵌入检测的阈值")
    
    # 保存报告
    with open("workflow_debug_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    log.info("✓ 工作流程调试报告已生成: workflow_debug_report.md")

def main():
    print("Test5.pdf 工作流程调试")
    print("=" * 40)
    
    success = test_workflow_step_by_step()
    
    if success:
        analyze_debug_logs()
        create_test_report()
    
    print("\n" + "="*40)
    if success:
        print("🔧 工作流程调试完成")
        print("📋 详细报告: workflow_debug_report.md")
        print("📝 调试日志: debug_workflow.log")
    else:
        print("⚠ 工作流程调试失败")

if __name__ == "__main__":
    main()
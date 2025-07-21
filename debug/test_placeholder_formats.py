#!/usr/bin/env python3
"""测试不同占位符格式在翻译中的稳定性"""

import logging
import re
from pdf2zh.placeholder_processor import PlaceholderProcessor

# 设置日志
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class TestPlaceholderProcessor(PlaceholderProcessor):
    """测试用的占位符处理器，支持不同的简化格式"""
    
    def __init__(self, format_type="numbers"):
        super().__init__()
        self.format_type = format_type
    
    def _get_simple_marker(self, img_id: str) -> str:
        """根据格式类型生成简单标记"""
        if self.format_type == "numbers":
            return f"[{img_id}]"  # 用方括号包围避免与数字混淆
        elif self.format_type == "chinese":
            return f"图{img_id}"
        elif self.format_type == "circles":
            # 支持1-20的圆圈数字
            circle_numbers = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
            num = int(img_id)
            if num <= 20:
                return circle_numbers[num-1]
            else:
                return f"({num})"
        elif self.format_type == "img_tags":
            return f"[IMG{img_id}]"  # 保持方括号格式
        else:
            return f"[{img_id}]"
    
    def simplify_placeholders(self, text: str) -> str:
        """简化占位符为指定格式"""
        if not text or not text.strip():
            return text
            
        # 匹配增强的图片占位符格式：<IMG_PLACEHOLDER:id:bbox:preceding_text>
        enhanced_pattern = r'<IMG_PLACEHOLDER:(\d+):([^:]+):([^>]*)>'
        
        def replace_enhanced(match):
            original = match.group(0)
            img_id = match.group(1)
            
            simple_marker = self._get_simple_marker(img_id)
            
            # 存储映射关系
            self.placeholder_map[simple_marker] = original
            self.reverse_map[original] = simple_marker
            
            log.debug(f"简化增强占位符: {original} -> {simple_marker}")
            return simple_marker
        
        # 匹配普通图片占位符格式：<f0:234.56,679.67,248.80,693.65>
        simple_pattern = r'<f(\d+):([^>]+)>'
        
        def replace_simple(match):
            original = match.group(0)
            img_id = match.group(1)
            
            simple_marker = self._get_simple_marker(img_id)
            
            # 存储映射关系
            self.placeholder_map[simple_marker] = original
            self.reverse_map[original] = simple_marker
            
            log.debug(f"简化普通占位符: {original} -> {simple_marker}")
            return simple_marker
        
        # 先处理增强占位符，再处理普通占位符
        result = re.sub(enhanced_pattern, replace_enhanced, text)
        result = re.sub(simple_pattern, replace_simple, result)
        
        return result
    
    def restore_placeholders(self, text: str) -> str:
        """恢复占位符"""
        if not text or not text.strip():
            return text
            
        result = text
        restored_count = 0
        
        # 恢复所有简单标记为原始占位符
        for simple_marker, original_placeholder in self.placeholder_map.items():
            if simple_marker in result:
                result = result.replace(simple_marker, original_placeholder)
                restored_count += 1
                log.debug(f"恢复占位符: {simple_marker} -> {original_placeholder}")
        
        return result

def test_format_stability():
    """测试不同格式的稳定性"""
    
    # 测试文本（包含多种占位符）
    test_text = """
    这是一个包含图片的文档。<f0:100.0,200.0,150.0,250.0>这里有第一张图片。
    接下来是第二张图片<f1:300.0,400.0,350.0,450.0>，然后是更多内容。
    最后还有一个增强占位符<IMG_PLACEHOLDER:2:500.0,600.0,550.0,650.0:前置文本>在这里。
    """
    
    formats = {
        "numbers": "纯数字",
        "chinese": "中文标识", 
        "circles": "圆圈数字",
        "img_tags": "IMG标签"
    }
    
    results = {}
    
    for format_type, format_name in formats.items():
        print(f"\n=== 测试格式: {format_name} ({format_type}) ===")
        
        processor = TestPlaceholderProcessor(format_type)
        
        # 简化
        simplified = processor.simplify_placeholders(test_text)
        print(f"简化后: {simplified}")
        
        # 模拟翻译可能的变化（大小写、空格等）
        translated = simplified.replace("这是", "This is").replace("图片", "image")
        if format_type == "img_tags":
            # 模拟翻译器可能改变大小写
            translated = translated.replace("IMG", "img")
        
        print(f"模拟翻译后: {translated}")
        
        # 恢复
        restored = processor.restore_placeholders(translated)
        print(f"恢复后: {restored}")
        
        # 检查恢复的成功率
        original_placeholders = re.findall(r'<[^>]+>', test_text)
        restored_placeholders = re.findall(r'<[^>]+>', restored)
        
        success_rate = len(restored_placeholders) / len(original_placeholders) if original_placeholders else 0
        
        results[format_type] = {
            "name": format_name,
            "simplified": simplified,
            "translated": translated,
            "restored": restored,
            "success_rate": success_rate,
            "original_count": len(original_placeholders),
            "restored_count": len(restored_placeholders)
        }
        
        print(f"恢复成功率: {success_rate:.2%} ({len(restored_placeholders)}/{len(original_placeholders)})")
    
    # 总结
    print("\n=== 格式对比总结 ===")
    for format_type, result in results.items():
        print(f"{result['name']}: 成功率 {result['success_rate']:.2%}, "
              f"简化示例: '{list(result['simplified'].split())[1] if len(result['simplified'].split()) > 1 else 'N/A'}'")
    
    # 推荐最佳格式
    best_format = max(results.keys(), key=lambda k: results[k]['success_rate'])
    print(f"\n推荐格式: {results[best_format]['name']} (成功率: {results[best_format]['success_rate']:.2%})")
    
    return best_format, results

if __name__ == "__main__":
    best_format, results = test_format_stability()
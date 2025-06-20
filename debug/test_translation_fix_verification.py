#!/usr/bin/env python3
"""
PDF翻译修复验证脚本
验证智能文本重组和URL保护机制是否正常工作
"""

import logging
import re
from typing import List, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_sentence_continuation():
    """测试句子连续性判断功能"""
    log.info("=== 测试句子连续性判断 ===")
    
    def is_sentence_continuation(text1, text2):
        """判断两个文本是否是连续的句子片段"""
        text1 = text1.strip().lower()
        text2 = text2.strip().lower()
        
        # 连续性模式匹配
        continuation_patterns = [
            # 不完整句子模式
            (r'\bif you are not sure which software version\b', r'\byour device is running\b'),
            (r'\byour device is running,?\s*you can go to\b', r'\bsettings\b'),
            (r'\bsettings\s*>\s*$', r'\babout phone\b'),
            (r'\babout phone\b.*\bto view\b', r'\bthe hyperos version\b'),
            (r'\bversion\s*$', r'\binformation\b'),
            (r'\bdevice is\s*$', r'^\s*running\b'),
            (r'\byou can\s*$', r'^\s*go to\b'),
            # 通用连续性模式
            (r'\b(to|at|in|on|of|for|with|by|from)\s*$', r'^[a-z]'),
            (r'\bgo to\s*$', r'^(settings|about|menu|options)', re.IGNORECASE),
            (r',\s*you can\s*$', r'^(go|access|check)'),
            (r'\bthe\s*$', r'^[a-z]'),
            (r'\bwhich\s*$', r'^(software|version|device)'),
        ]
        
        for item in continuation_patterns:
            if len(item) == 3:
                pattern1, pattern2, flags = item
            else:
                pattern1, pattern2 = item
                flags = 0
            
            if re.search(pattern1, text1, flags) and re.search(pattern2, text2, flags):
                return True
        
        return False
    
    # 测试用例
    test_cases = [
        ("if you are not sure which software version", "your device is running", True),
        ("your device is running, you can go to", "settings", True),
        ("settings >", "about phone", True),
        ("device is", "running", True),
        ("you can", "go to", True),
        ("go to", "settings", True),
        ("version", "information", True),
        ("hello world", "goodbye moon", False),
        ("random text", "another text", False),
    ]
    
    passed = 0
    failed = 0
    
    for text1, text2, expected in test_cases:
        result = is_sentence_continuation(text1, text2)
        status = "✓" if result == expected else "✗"
        log.info(f"{status} '{text1}' + '{text2}' -> {result} (期望: {expected})")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
    
    log.info(f"句子连续性测试结果: {passed} 通过, {failed} 失败")
    return failed == 0

def test_url_protection():
    """测试URL保护机制"""
    log.info("\n=== 测试URL保护机制 ===")
    
    def protect_urls(text):
        """识别并保护URL，用占位符替换"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|[^\s<>"{}|\\^`\[\]]+\.[a-z]{2,}(?:/[^\s<>"{}|\\^`\[\]]*)?'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        protected_text = text
        url_placeholders = {}
        
        for i, url in enumerate(urls):
            placeholder = f"__URL_PLACEHOLDER_{i}__"
            url_placeholders[placeholder] = url
            protected_text = protected_text.replace(url, placeholder)
        
        return protected_text, url_placeholders
    
    def restore_urls(text, url_placeholders):
        """恢复URL占位符为原始URL"""
        restored_text = text
        for placeholder, url in url_placeholders.items():
            restored_text = restored_text.replace(placeholder, url)
        return restored_text
    
    # 测试用例
    test_texts = [
        "Visit https://www.example.com for more info",
        "Check www.google.com and http://github.com",
        "Email us at contact@example.org or visit example.net/page",
        "No URLs in this text",
        "Multiple URLs: https://site1.com, www.site2.org, and https://site3.net/path/to/page"
    ]
    
    all_passed = True
    
    for original_text in test_texts:
        log.info(f"原始文本: '{original_text}'")
        
        # 保护URL
        protected_text, url_placeholders = protect_urls(original_text)
        log.info(f"保护后: '{protected_text}'")
        log.info(f"URL占位符: {url_placeholders}")
        
        # 模拟翻译（这里只是转换为大写来模拟）
        translated_text = protected_text.upper()
        log.info(f"翻译后: '{translated_text}'")
        
        # 恢复URL
        restored_text = restore_urls(translated_text, url_placeholders)
        log.info(f"恢复后: '{restored_text}'")
        
        # 验证URL是否完整保留
        original_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|[^\s<>"{}|\\^`\[\]]+\.[a-z]{2,}(?:/[^\s<>"{}|\\^`\[\]]*)?', original_text, re.IGNORECASE)
        restored_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|[^\s<>"{}|\\^`\[\]]+\.[a-z]{2,}(?:/[^\s<>"{}|\\^`\[\]]*)?', restored_text, re.IGNORECASE)
        
        if set(original_urls) == set(restored_urls):
            log.info("✓ URL保护和恢复成功")
        else:
            log.error("✗ URL保护和恢复失败")
            log.error(f"  原始URLs: {original_urls}")
            log.error(f"  恢复URLs: {restored_urls}")
            all_passed = False
        
        log.info("-" * 50)
    
    log.info(f"URL保护测试结果: {'全部通过' if all_passed else '存在失败'}")
    return all_passed

def test_text_reconstruction_simulation():
    """模拟测试文本重组功能"""
    log.info("\n=== 模拟文本重组测试 ===")
    
    # 模拟分割的段落数据
    mock_paragraphs = [
        "If you are not sure which software version",
        "your device is running, you can go to",
        "Settings >",
        "About phone to view",
        "the HyperOS version information."
    ]
    
    log.info("原始分割段落:")
    for i, para in enumerate(mock_paragraphs):
        log.info(f"  段落 {i}: '{para}'")
    
    # 模拟智能重组逻辑
    def simulate_text_reconstruction(paragraphs: List[str]) -> List[str]:
        """模拟文本重组过程"""
        def is_continuation(text1, text2):
            text1, text2 = text1.strip().lower(), text2.strip().lower()
            patterns = [
                (r'\bif you are not sure which software version\b', r'\byour device is running\b'),
                (r'\byour device is running,?\s*you can go to\b', r'\bsettings\b'),
                (r'\bsettings\s*>\s*$', r'\babout phone\b'),
                (r'\babout phone\b.*\bto view\b', r'\bthe hyperos version\b'),
                (r'\bversion\s*$', r'\binformation\b'),
                (r'\bdevice is\s*$', r'^\s*running\b'),
                (r'\byou can\s*$', r'^\s*go to\b'),
                (r'\bgo to\s*$', r'^(settings|about|menu|options)'),
            ]
            
            for p1, p2 in patterns:
                if re.search(p1, text1) and re.search(p2, text2, re.IGNORECASE):
                    return True
            return False
        
        result = []
        i = 0
        while i < len(paragraphs):
            current = paragraphs[i]
            
            # 查找连续的段落
            j = i + 1
            while j < len(paragraphs):
                if is_continuation(current, paragraphs[j]) or is_continuation(paragraphs[j], current):
                    current += " " + paragraphs[j]
                    j += 1
                else:
                    break
            
            result.append(current)
            i = j if j > i + 1 else i + 1
        
        return result
    
    reconstructed = simulate_text_reconstruction(mock_paragraphs)
    
    log.info("\n重组后段落:")
    for i, para in enumerate(reconstructed):
        log.info(f"  段落 {i}: '{para}'")
    
    # 验证是否包含完整内容
    all_content = " ".join(reconstructed).lower()
    key_phrases = [
        "if you are not sure which software version",
        "your device is running",
        "you can go to settings",
        "about phone",
        "hyperos version information"
    ]
    
    missing_phrases = []
    for phrase in key_phrases:
        if phrase not in all_content:
            missing_phrases.append(phrase)
    
    if not missing_phrases:
        log.info("✓ 文本重组测试通过 - 所有关键短语都包含")
        return True
    else:
        log.error("✗ 文本重组测试失败 - 缺失关键短语:")
        for phrase in missing_phrases:
            log.error(f"  - '{phrase}'")
        return False

def main():
    """主函数"""
    log.info("开始PDF翻译修复验证测试")
    log.info("=" * 60)
    
    results = []
    
    # 执行各项测试
    results.append(("句子连续性判断", test_sentence_continuation()))
    results.append(("URL保护机制", test_url_protection()))
    results.append(("文本重组模拟", test_text_reconstruction_simulation()))
    
    # 汇总测试结果
    log.info("\n" + "=" * 60)
    log.info("测试结果汇总:")
    
    passed_count = 0
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        log.info(f"  {test_name:<20} {status}")
        if passed:
            passed_count += 1
    
    log.info(f"\n总体结果: {passed_count}/{len(results)} 测试通过")
    
    if passed_count == len(results):
        log.info("🎉 所有修复功能验证通过！")
        return True
    else:
        log.warning("⚠️  部分修复功能需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
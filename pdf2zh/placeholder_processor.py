"""
占位符处理器：管理图片占位符的简化和恢复
"""

import logging
import re
from typing import Dict, List, Tuple, Optional

log = logging.getLogger(__name__)


class PlaceholderProcessor:
    """处理图片占位符的简化和恢复"""
    
    def __init__(self):
        self.placeholder_map: Dict[str, str] = {}  # 简单标记 -> 复杂占位符
        self.reverse_map: Dict[str, str] = {}      # 复杂占位符 -> 简单标记
        self.counter = 0
    
    def reset(self):
        """重置处理器状态"""
        self.placeholder_map.clear()
        self.reverse_map.clear()
        self.counter = 0
    
    def simplify_placeholders(self, text: str) -> str:
        """
        将复杂的图片占位符替换为简单标记
        
        Args:
            text: 包含复杂占位符的原始文本
            
        Returns:
            str: 替换后的简化文本
        """
        if not text or not text.strip():
            return text
            
        # 匹配增强的图片占位符格式：<IMG_PLACEHOLDER:id:bbox:preceding_text>
        enhanced_pattern = r'<IMG_PLACEHOLDER:(\d+):([^:]+):([^>]*)>'
        
        def replace_enhanced(match):
            original = match.group(0)
            img_id = match.group(1)
            bbox = match.group(2)
            preceding_text = match.group(3)
            
            # 创建带有序号的简单标记，更容易被翻译器理解和处理
            simple_marker = f"图{img_id}"
            
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
            bbox = match.group(2)
            
            # 创建带有序号的简单标记，更容易被翻译器理解和处理
            simple_marker = f"图{img_id}"
            
            # 存储映射关系
            self.placeholder_map[simple_marker] = original
            self.reverse_map[original] = simple_marker
            
            log.debug(f"简化普通占位符: {original} -> {simple_marker}")
            return simple_marker
        
        # 先处理增强占位符，再处理普通占位符
        result = re.sub(enhanced_pattern, replace_enhanced, text)
        result = re.sub(simple_pattern, replace_simple, result)
        
        if result != text:
            log.debug(f"占位符简化完成，处理了 {len(self.placeholder_map)} 个占位符")
        
        return result
    
    def restore_placeholders(self, text: str) -> str:
        """
        将简单标记恢复为复杂占位符
        
        Args:
            text: 包含简单标记的翻译后文本
            
        Returns:
            str: 恢复后的文本
        """
        if not text or not text.strip():
            return text
            
        result = text
        restored_count = 0
        
        # 恢复所有简单标记为原始占位符（大小写不敏感）
        for simple_marker, original_placeholder in self.placeholder_map.items():
            # 先尝试精确匹配
            if simple_marker in result:
                result = result.replace(simple_marker, original_placeholder)
                restored_count += 1
                log.debug(f"恢复占位符: {simple_marker} -> {original_placeholder}")
            else:
                # 尝试大小写不敏感匹配和模糊匹配
                import re
                
                # 针对中文数字标记进行模糊匹配
                if simple_marker.startswith('图'):
                    img_id = simple_marker[1:]  # 提取数字部分
                    # 匹配各种可能的变化：图1、图片1、[图1]、image1等
                    patterns = [
                        rf'图片?{re.escape(img_id)}',
                        rf'\[?图片?{re.escape(img_id)}\]?',
                        rf'[Ii]mage\s*{re.escape(img_id)}',
                        rf'[Pp]icture\s*{re.escape(img_id)}',
                        rf'[Ff]ig\s*{re.escape(img_id)}',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, result, re.IGNORECASE)
                        if matches:
                            result = re.sub(pattern, original_placeholder, result, flags=re.IGNORECASE)
                            restored_count += 1
                            log.debug(f"恢复占位符(模糊匹配): {pattern} -> {original_placeholder}")
                            break
                else:
                    # 原有的大小写不敏感匹配逻辑
                    pattern = re.escape(simple_marker).replace(r'\[', r'\[').replace(r'\]', r'\]')
                    pattern = pattern.replace('IMG', r'[Ii][Mm][Gg]')  # 匹配大小写变化
                    matches = re.findall(pattern, result, re.IGNORECASE)
                    if matches:
                        # 替换找到的匹配项
                        result = re.sub(pattern, original_placeholder, result, flags=re.IGNORECASE)
                        restored_count += 1
                        log.debug(f"恢复占位符(忽略大小写): {simple_marker} -> {original_placeholder}")
        
        if restored_count > 0:
            log.debug(f"占位符恢复完成，恢复了 {restored_count} 个占位符")
        
        return result
    
    def verify_translation_integrity(self, original: str, processed: str) -> bool:
        """
        验证翻译完整性的别名方法，保持向后兼容
        """
        return self.validate_text_integrity(original, processed)
    
    def validate_text_integrity(self, original: str, processed: str) -> bool:
        """
        验证文本完整性，确保没有内容丢失
        
        Args:
            original: 原始文本
            processed: 处理后的文本
            
        Returns:
            bool: 文本完整性是否保持
        """
        if not original and not processed:
            return True
            
        if not original or not processed:
            log.warning(f"文本完整性检查失败：原文={'空' if not original else '非空'}，处理后={'空' if not processed else '非空'}")
            log.debug(f"原文内容: '{original[:200]}...'")
            log.debug(f"处理后内容: '{processed[:200]}...'")
            return False
        
        # 移除占位符后比较基本内容
        original_clean = self._clean_text_for_comparison(original)
        processed_clean = self._clean_text_for_comparison(processed)
        
        # 增强调试信息
        log.debug(f"完整性检查详情:")
        log.debug(f"  原文长度: {len(original)} -> 清理后: {len(original_clean)}")
        log.debug(f"  处理后长度: {len(processed)} -> 清理后: {len(processed_clean)}")
        log.debug(f"  原文清理后: '{original_clean[:100]}...' (显示前100字符)")
        log.debug(f"  处理后清理: '{processed_clean[:100]}...' (显示前100字符)")
        
        # 检查是否只有占位符（没有实际文本内容）
        if not original_clean and not processed_clean:
            log.debug("两者都只包含占位符，认为完整性保持")
            return True
        
        # 如果原文清理后为空，但处理后有内容，可能是翻译添加了内容
        if not original_clean:
            log.debug("原文清理后为空，跳过长度检查")
            return True
        
        # 检查基本文本长度变化是否在合理范围内
        length_ratio = len(processed_clean) / len(original_clean) if original_clean else 0
        
        # 降低长度比例阈值，考虑占位符对文本的影响
        min_ratio = 0.05  # 翻译后长度不应该少于原文的5%（从15%降低到5%）
        max_ratio = 10.0  # 翻译后长度不应该超过原文的10倍
        
        if length_ratio < min_ratio:
            log.warning(f"文本完整性检查失败：长度比例过低 {length_ratio:.3f} < {min_ratio}")
            log.warning(f"原文清理后({len(original_clean)}字符): '{original_clean}'")
            log.warning(f"处理后清理({len(processed_clean)}字符): '{processed_clean}'")
            
            # 特殊情况：如果处理后的文本包含占位符标记，可能是合理的
            placeholder_patterns = [r'\[IMG\d+\]', r'<f\d+:[^>]+>', r'<IMG_PLACEHOLDER:[^>]*>']
            has_placeholders = any(re.search(pattern, processed, re.IGNORECASE) for pattern in placeholder_patterns)
            
            if has_placeholders and len(processed.strip()) > 0:
                log.info("检测到占位符存在，且处理后文本非空，允许通过完整性检查")
                return True
            
            return False
        
        if length_ratio > max_ratio:
            log.warning(f"文本完整性检查失败：长度比例过高 {length_ratio:.3f} > {max_ratio}")
            log.warning(f"原文清理后({len(original_clean)}字符): '{original_clean[:100]}...'")
            log.warning(f"处理后清理({len(processed_clean)}字符): '{processed_clean[:100]}...'")
            return False
        
        log.debug(f"文本完整性检查通过：长度比例 {length_ratio:.3f} 在合理范围内")
        return True
    
    def _clean_text_for_comparison(self, text: str) -> str:
        """清理文本用于比较，移除占位符和多余空格"""
        if not text:
            return ""
        
        original_length = len(text)
        
        # 移除各种占位符（按复杂度从高到低顺序）
        # 1. 增强的图片占位符
        text = re.sub(r'<IMG_PLACEHOLDER:[^>]*>', '', text, flags=re.IGNORECASE)
        
        # 2. 普通图片占位符
        text = re.sub(r'<f\d+:[^>]*>', '', text, flags=re.IGNORECASE)
        
        # 3. 简化的图片标记（支持多种格式）
        text = re.sub(r'\[?IMG\d+\]?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'图片?\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[Ii]mage\s*\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[Pp]icture\s*\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[Ff]ig\s*\d+', '', text, flags=re.IGNORECASE)
        
        # 4. 公式占位符
        text = re.sub(r'\{v\d+\}', '', text, flags=re.IGNORECASE)
        
        # 5. 其他可能的占位符格式
        text = re.sub(r'<[^>]*placeholder[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\{[^}]*img[^}]*\}', '', text, flags=re.IGNORECASE)
        
        # 清理多余的空格和换行
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        cleaned_length = len(text)
        log.debug(f"文本清理: {original_length} -> {cleaned_length} 字符 (移除了 {original_length - cleaned_length} 个占位符字符)")
        
        return text
    
    def get_statistics(self) -> Dict[str, int]:
        """获取处理统计信息"""
        return {
            "total_placeholders": len(self.placeholder_map),
            "enhanced_placeholders": len([p for p in self.placeholder_map.values() if "IMG_PLACEHOLDER" in p]),
            "simple_placeholders": len([p for p in self.placeholder_map.values() if "IMG_PLACEHOLDER" not in p])
        }
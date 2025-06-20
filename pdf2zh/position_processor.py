"""位置处理模块：处理翻译后图片位置的恢复"""

import logging
import re
from typing import Dict, List, Tuple, Optional

log = logging.getLogger(__name__)


class PositionProcessor:
    """处理翻译后图片位置恢复的处理器"""
    
    def __init__(self):
        self.position_mappings = {}  # 存储位置映射关系
    
    def extract_image_placeholders(self, text: str) -> List[Dict]:
        """
        从文本中提取图片占位符信息。
        
        Args:
            text: 包含占位符的文本
            
        Returns:
            List[Dict]: 占位符信息列表
        """
        placeholders = []
        
        # 匹配增强的图片占位符
        enhanced_pattern = r"<IMG_PLACEHOLDER:(\d+):([^:]+):([^>]*)>"
        for match in re.finditer(enhanced_pattern, text):
            fig_id = int(match.group(1))
            bbox_str = match.group(2)
            preceding_text = match.group(3)
            
            bbox = tuple(map(float, bbox_str.split(',')))
            
            placeholders.append({
                "type": "enhanced",
                "fig_id": fig_id,
                "bbox": bbox,
                "preceding_text": preceding_text,
                "match": match,
                "start_pos": match.start(),
                "end_pos": match.end()
            })
        
        # 匹配普通图片占位符
        normal_pattern = r"<f(\d+):([^>]+)>"
        for match in re.finditer(normal_pattern, text):
            fig_id = int(match.group(1))
            bbox_str = match.group(2)
            bbox = tuple(map(float, bbox_str.split(',')))
            
            placeholders.append({
                "type": "normal",
                "fig_id": fig_id,
                "bbox": bbox,
                "match": match,
                "start_pos": match.start(),
                "end_pos": match.end()
            })
        
        # 按位置排序
        placeholders.sort(key=lambda x: x["start_pos"])
        return placeholders
    
    def find_word_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """
        找到文本中每个单词的位置。
        
        Args:
            text: 输入文本
            
        Returns:
            List[Tuple[str, int, int]]: [(单词, 开始位置, 结束位置), ...]
        """
        words = []
        # 使用正则表达式匹配单词（包括中文字符、英文单词等）
        word_pattern = r'\S+'
        
        for match in re.finditer(word_pattern, text):
            word = match.group()
            start_pos = match.start()
            end_pos = match.end()
            words.append((word, start_pos, end_pos))
        
        return words
    
    def map_placeholder_to_words(self, original_text: str, translated_text: str) -> Dict:
        """
        建立占位符与单词的映射关系。
        
        Args:
            original_text: 原始文本（包含占位符）
            translated_text: 翻译后文本（包含占位符）
            
        Returns:
            Dict: 映射关系
        """
        mapping = {}
        
        # 提取原文和译文中的占位符
        original_placeholders = self.extract_image_placeholders(original_text)
        translated_placeholders = self.extract_image_placeholders(translated_text)
        
        # 建立占位符的对应关系
        placeholder_map = {}
        for orig_ph in original_placeholders:
            for trans_ph in translated_placeholders:
                if orig_ph["fig_id"] == trans_ph["fig_id"]:
                    placeholder_map[orig_ph["fig_id"]] = {
                        "original": orig_ph,
                        "translated": trans_ph
                    }
                    break
        
        # 分析每个占位符的位置
        for fig_id, ph_info in placeholder_map.items():
            original_ph = ph_info["original"]
            translated_ph = ph_info["translated"]
            
            # 找到原文中占位符前面的单词
            orig_words = self.find_word_positions(original_text[:original_ph["start_pos"]])
            orig_preceding_word = orig_words[-1] if orig_words else None
            
            # 找到译文中占位符前面的单词
            trans_words = self.find_word_positions(translated_text[:translated_ph["start_pos"]])
            trans_preceding_word = trans_words[-1] if trans_words else None
            
            # 找到原文中占位符后面的单词
            orig_following_words = self.find_word_positions(original_text[original_ph["end_pos"]:])
            orig_following_word = orig_following_words[0] if orig_following_words else None
            
            # 找到译文中占位符后面的单词
            trans_following_words = self.find_word_positions(translated_text[translated_ph["end_pos"]:])
            trans_following_word = trans_following_words[0] if trans_following_words else None
            
            mapping[fig_id] = {
                "original": {
                    "preceding_word": orig_preceding_word,
                    "following_word": orig_following_word,
                    "placeholder": original_ph
                },
                "translated": {
                    "preceding_word": trans_preceding_word,
                    "following_word": trans_following_word,
                    "placeholder": translated_ph
                }
            }
            
            log.debug(f"图片 {fig_id} 位置映射:")
            log.debug(f"  原文前面单词: {orig_preceding_word}")
            log.debug(f"  译文前面单词: {trans_preceding_word}")
            log.debug(f"  原文后面单词: {orig_following_word}")
            log.debug(f"  译文后面单词: {trans_following_word}")
        
        return mapping
    
    def calculate_new_positions(self, mapping: Dict, original_layout: Dict, 
                              translated_layout: Dict) -> Dict:
        """
        基于映射关系计算图片的新位置。
        
        Args:
            mapping: 位置映射关系
            original_layout: 原文布局信息
            translated_layout: 译文布局信息
            
        Returns:
            Dict: 新的位置信息
        """
        new_positions = {}
        
        for fig_id, map_info in mapping.items():
            try:
                # 获取译文中前面单词的位置信息
                trans_preceding = map_info["translated"]["preceding_word"]
                trans_following = map_info["translated"]["following_word"]
                
                if trans_preceding:
                    # 基于前面单词的位置计算图片新位置
                    word_text, word_start, word_end = trans_preceding
                    
                    # 这里需要根据实际的布局信息计算具体位置
                    # 简化版本：保持原始的bbox，但可以根据需要调整
                    original_bbox = map_info["original"]["placeholder"]["bbox"]
                    
                    # 可以根据前后单词的变化来调整位置
                    # 这里先保持原位置，具体的位置计算需要更多布局信息
                    new_positions[fig_id] = {
                        "bbox": original_bbox,
                        "context": {
                            "preceding_word": word_text,
                            "word_position": (word_start, word_end)
                        }
                    }
                    
                    log.debug(f"图片 {fig_id} 新位置计算完成: {original_bbox}")
                
            except Exception as e:
                log.warning(f"计算图片 {fig_id} 新位置时出错: {e}")
                # fallback到原位置
                original_bbox = map_info["original"]["placeholder"]["bbox"]
                new_positions[fig_id] = {"bbox": original_bbox}
        
        return new_positions
    
    def process_translation_with_images(self, original_text: str, translated_text: str,
                                      original_layout: Dict = None, 
                                      translated_layout: Dict = None) -> Dict:
        """
        处理包含图片的翻译文本，计算图片的新位置。
        
        Args:
            original_text: 原始文本
            translated_text: 翻译后文本
            original_layout: 原文布局信息（可选）
            translated_layout: 译文布局信息（可选）
            
        Returns:
            Dict: 处理结果，包含位置映射和新位置信息
        """
        # 建立位置映射
        mapping = self.map_placeholder_to_words(original_text, translated_text)
        
        # 计算新位置
        new_positions = self.calculate_new_positions(
            mapping, original_layout or {}, translated_layout or {}
        )
        
        return {
            "mapping": mapping,
            "new_positions": new_positions,
            "processed_text": translated_text
        }

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

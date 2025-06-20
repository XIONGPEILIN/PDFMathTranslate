#!/usr/bin/env python3
"""
详细分析 test5.pdf 的图片位置变化
特别关注嵌入文本中的图片应该如何跟随文字移动
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)

log = logging.getLogger(__name__)

def analyze_text_and_image_layout():
    """详细分析文本和图片的布局关系"""
    
    original_pdf = "test5.pdf"
    translated_pdf = "test5-dual.pdf"
    
    if not os.path.exists(original_pdf) or not os.path.exists(translated_pdf):
        log.error("PDF文件不存在")
        return False
    
    log.info("="*70)
    log.info("详细分析 test5.pdf 的文本和图片布局关系")
    log.info("="*70)
    
    try:
        import fitz  # PyMuPDF
        
        # 打开文件
        doc_orig = fitz.open(original_pdf)
        doc_trans = fitz.open(translated_pdf)
        
        # 分析原文页面
        page_orig = doc_orig[0]  # 第一页
        # 翻译文件是双语版本，原文在第一页，译文在第二页
        page_trans_orig = doc_trans[0]  # 翻译文件中的原文页面
        page_trans_zh = doc_trans[1] if len(doc_trans) > 1 else doc_trans[0]  # 翻译文件中的中文页面
        
        log.info("分析原文档结构:")
        
        # 获取原文图片
        images_orig = page_orig.get_images()
        log.info(f"原文图片数量: {len(images_orig)}")
        
        # 获取原文文本块
        text_blocks_orig = []
        try:
            text_dict = page_orig.get_text("dict")  # type: ignore
            if text_dict and "blocks" in text_dict:
                for block in text_dict["blocks"]:
                    if "lines" in block:
                        bbox = block["bbox"]
                        text_content = ""
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text_content += span["text"]
                        if text_content.strip():
                            text_blocks_orig.append({
                                "bbox": bbox,
                                "text": text_content.strip()
                            })
        except:
            pass
        
        log.info(f"原文文本块数量: {len(text_blocks_orig)}")
        
        # 分析每个图片与文本的关系
        for i, img in enumerate(images_orig):
            log.info(f"\n--- 图片 {i+1} 分析 ---")
            
            # 获取图片位置
            try:
                img_rects = page_orig.get_image_rects(img[0])  # type: ignore
                if img_rects:
                    img_rect = img_rects[0]
                    img_bbox = (img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1)
                    log.info(f"图片位置: ({img_bbox[0]:.1f}, {img_bbox[1]:.1f}, {img_bbox[2]:.1f}, {img_bbox[3]:.1f})")
                    log.info(f"图片尺寸: {img[2]}x{img[3]}")
                    
                    # 查找图片前面的文本
                    preceding_texts = []
                    following_texts = []
                    
                    for text_block in text_blocks_orig:
                        text_bbox = text_block["bbox"]
                        text_content = text_block["text"]
                        
                        # 检查文本是否在图片前面（左侧，同一行或接近）
                        if (text_bbox[2] <= img_bbox[0] and  # 文本右边界 <= 图片左边界
                            abs(text_bbox[1] - img_bbox[1]) < 20):  # Y坐标接近（同一行）
                            distance = img_bbox[0] - text_bbox[2]
                            preceding_texts.append({
                                "text": text_content,
                                "distance": distance,
                                "bbox": text_bbox
                            })
                        
                        # 检查文本是否在图片后面（右侧）
                        elif (text_bbox[0] >= img_bbox[2] and  # 文本左边界 >= 图片右边界
                              abs(text_bbox[1] - img_bbox[1]) < 20):  # Y坐标接近（同一行）
                            distance = text_bbox[0] - img_bbox[2]
                            following_texts.append({
                                "text": text_content,
                                "distance": distance,
                                "bbox": text_bbox
                            })
                    
                    # 按距离排序，找最近的
                    preceding_texts.sort(key=lambda x: x["distance"])
                    following_texts.sort(key=lambda x: x["distance"])
                    
                    if preceding_texts:
                        nearest_preceding = preceding_texts[0]
                        log.info(f"前面最近的文字: '{nearest_preceding['text'][:30]}...'")
                        log.info(f"  距离: {nearest_preceding['distance']:.1f}像素")
                        log.info(f"  预期: 翻译后图片应该跟随文字移动")
                    else:
                        log.info("前面没有文字 - 预期: 翻译后位置不变")
                    
                    if following_texts:
                        nearest_following = following_texts[0]
                        log.info(f"后面最近的文字: '{nearest_following['text'][:30]}...'")
                        log.info(f"  距离: {nearest_following['distance']:.1f}像素")
                
            except Exception as e:
                log.warning(f"无法获取图片 {i+1} 的详细位置信息: {e}")
        
        # 现在分析翻译后的变化
        log.info("\n" + "="*50)
        log.info("分析翻译后的位置变化:")
        
        # 比较原文页面和中文页面的图片位置
        images_trans_zh = page_trans_zh.get_images()
        log.info(f"中文页面图片数量: {len(images_trans_zh)}")
        
        # 获取中文页面的文本块
        text_blocks_zh = []
        try:
            text_dict = page_trans_zh.get_text("dict")  # type: ignore
            if text_dict and "blocks" in text_dict:
                for block in text_dict["blocks"]:
                    if "lines" in block:
                        bbox = block["bbox"]
                        text_content = ""
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text_content += span["text"]
                        if text_content.strip():
                            text_blocks_zh.append({
                                "bbox": bbox,
                                "text": text_content.strip()
                            })
        except:
            pass
        
        log.info(f"中文页面文本块数量: {len(text_blocks_zh)}")
        
        # 比较图片位置变化
        for i in range(min(len(images_orig), len(images_trans_zh))):
            log.info(f"\n--- 图片 {i+1} 位置变化分析 ---")
            
            # 原文图片位置
            try:
                orig_rects = page_orig.get_image_rects(images_orig[i][0])  # type: ignore
                orig_rect = orig_rects[0] if orig_rects else None
            except:
                orig_rect = None
            
            # 中文图片位置
            try:
                zh_rects = page_trans_zh.get_image_rects(images_trans_zh[i][0])  # type: ignore
                zh_rect = zh_rects[0] if zh_rects else None
            except:
                zh_rect = None
            
            if orig_rect and zh_rect:
                orig_pos = (orig_rect.x0, orig_rect.y0, orig_rect.x1, orig_rect.y1)
                zh_pos = (zh_rect.x0, zh_rect.y0, zh_rect.x1, zh_rect.y1)
                
                x_shift = zh_pos[0] - orig_pos[0]
                y_shift = zh_pos[1] - orig_pos[1]
                total_shift = (x_shift**2 + y_shift**2)**0.5
                
                log.info(f"原文位置: ({orig_pos[0]:.1f}, {orig_pos[1]:.1f}, {orig_pos[2]:.1f}, {orig_pos[3]:.1f})")
                log.info(f"中文位置: ({zh_pos[0]:.1f}, {zh_pos[1]:.1f}, {zh_pos[2]:.1f}, {zh_pos[3]:.1f})")
                log.info(f"位置变化: X={x_shift:.1f}, Y={y_shift:.1f}, 总位移={total_shift:.1f}像素")
                
                if total_shift < 1:
                    log.info("✓ 位置几乎没有变化（独立图片）")
                elif total_shift < 10:
                    log.info("✓ 位置微调（可能是格式优化）")
                else:
                    log.info("✓ 位置明显变化（跟随文字移动）")
            else:
                log.warning("无法获取详细位置信息")
        
        doc_orig.close()
        doc_trans.close()
        
        return True
        
    except ImportError:
        log.error("PyMuPDF 未安装")
        return False
    except Exception as e:
        log.error(f"分析失败: {e}")
        return False

def check_embedded_image_processing():
    """检查嵌入图片处理的日志记录"""
    
    log.info("\n" + "="*50)
    log.info("检查图片嵌入处理的详细日志")
    
    # 搜索所有日志文件中的相关信息
    import glob
    
    log_files = glob.glob("*.log")
    
    for log_file in log_files:
        log.info(f"\n检查日志文件: {log_file}")
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 查找图片处理相关的关键词
            keywords = [
                "嵌入图片", "embedded", "IMG_PLACEHOLDER", "is_embedded",
                "preceding_text", "图片前面", "figure", "image_rect"
            ]
            
            found_entries = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                for keyword in keywords:
                    if keyword in line:
                        found_entries.append((i+1, line.strip()))
                        break
            
            if found_entries:
                log.info(f"  找到 {len(found_entries)} 条相关记录:")
                for line_num, entry in found_entries[:10]:  # 只显示前10条
                    log.info(f"    L{line_num}: {entry}")
                if len(found_entries) > 10:
                    log.info(f"    ... 还有 {len(found_entries) - 10} 条记录")
            else:
                log.info("  未找到图片嵌入处理的相关记录")
                
        except Exception as e:
            log.warning(f"  读取日志文件失败: {e}")

def main():
    print("Test5.pdf 详细位置分析")
    print("=" * 40)
    
    success = analyze_text_and_image_layout()
    
    if success:
        check_embedded_image_processing()
    
    print("\n" + "="*40)
    if success:
        print("🔍 详细分析完成")
        print("现在可以更准确地判断图片位置保持功能的效果")
    else:
        print("⚠ 分析失败，请检查依赖")

if __name__ == "__main__":
    main()
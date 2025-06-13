import fitz  # PyMuPDF
import os

def is_image_between_texts(text_blocks, image_rect, direction="horizontal"):
    """
    判断图像是否处于两个文本块之间。
    direction: "horizontal" 表示横向判断，"vertical" 表示纵向判断
    """
    if not text_blocks:
        return False
    
    if direction == "horizontal":
        # 按X轴排序（左到右）
        text_blocks = sorted(text_blocks, key=lambda b: b[0])
        
        # 检查图像是否在任意两个文本块之间（横向）
        for i in range(len(text_blocks) - 1):
            left_block = text_blocks[i]
            right_block = text_blocks[i + 1]
            
            # left_block[2] 是左侧文本块的右边界X坐标
            # right_block[0] 是右侧文本块的左边界X坐标
            # image_rect.x0 是图像的左边界X坐标
            # image_rect.x1 是图像的右边界X坐标
            
            # 图像在两个文本块之间的条件（横向）：
            # 1. 图像左边界在左侧文本块右边界之右
            # 2. 图像右边界在右侧文本块左边界之左
            if (left_block[2] <= image_rect.x0 and 
                image_rect.x1 <= right_block[0]):
                return True
    
    else:  # vertical
        # 按Y轴排序（上到下）
        text_blocks = sorted(text_blocks, key=lambda b: b[1])
        
        # 检查图像是否在任意两个文本块之间（纵向）
        for i in range(len(text_blocks) - 1):
            upper_block = text_blocks[i]
            lower_block = text_blocks[i + 1]
            
            # upper_block[3] 是上方文本块的底部Y坐标
            # lower_block[1] 是下方文本块的顶部Y坐标
            # image_rect.y0 是图像的顶部Y坐标
            # image_rect.y1 是图像的底部Y坐标
            
            # 图像在两个文本块之间的条件（纵向）：
            # 1. 图像顶部在上方文本块底部之下
            # 2. 图像底部在下方文本块顶部之上
            if (upper_block[3] <= image_rect.y0 and 
                image_rect.y1 <= lower_block[1]):
                return True
    
    return False

def save_image_from_pdf(doc, img, page_number, img_index, output_dir="extracted_images"):
    """
    从PDF中提取并保存图像到本地
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    xref = img[0]
    try:
        # 获取图像数据
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        
        # 生成文件名
        filename = f"page_{page_number}_image_{img_index}.{image_ext}"
        filepath = os.path.join(output_dir, filename)
        
        # 保存图像
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        print(f"    图像尺寸: {len(image_bytes)} bytes, 格式: {image_ext}")
        return filepath
    except Exception as e:
        print(f"    保存图像失败: {str(e)}")
        return None

def print_text_blocks(text_blocks_full):
    """
    打印文本块信息
    """
    print("  === 文本块详情 ===")
    for i, block in enumerate(text_blocks_full):
        x0, y0, x1, y1, text, block_no, block_type = block
        # 清理文本，移除换行符和多余空格
        text = list(text)
        if text:  # 只显示非空文本
            print(f"    文本块 {i+1}: ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
            print(f"      内容: {text}")

def analyze_pdf(filepath, save_images=True, check_direction="horizontal", show_text=True):
    """
    分析PDF中的图像位置
    check_direction: "horizontal" 检查横向, "vertical" 检查纵向, "both" 检查两个方向
    show_text: 是否显示文本块内容
    """
    doc = fitz.open(filepath)
    for page_number, page in enumerate(doc):
        print(f"\nPage {page_number + 1}:")
        
        # 获取完整的文本块信息（包含文本内容）
        text_blocks_full = page.get_text("blocks")
        text_blocks = [b[:4] for b in text_blocks_full]  # 只提取矩形位置
        images = page.get_images(full=True)
        
        print(f"  文本块数量: {len(text_blocks)}")
        print(f"  图像数量: {len(images)}")
        
        # 显示文本块信息
        if show_text and text_blocks_full:
            print_text_blocks(text_blocks_full)
        
        if not images:
            print("  没有图像。")
            continue

        print("  === 图像分析 ===")
        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                # 使用更安全的方法获取图像位置
                img_rects = page.get_image_rects(xref)
                
                if not img_rects:
                    print(f"  图像 {img_index + 1}: 无法获取位置信息")
                    # 即使无法获取位置，也尝试保存图像
                    if save_images:
                        saved_path = save_image_from_pdf(doc, img, page_number + 1, img_index + 1)
                        if saved_path:
                            print(f"    已保存到: {saved_path}")
                    continue

                embedded_horizontal = False
                embedded_vertical = False
                for rect in img_rects:
                    print(f"  图像 {img_index + 1} 位置: ({rect.x0:.1f}, {rect.y0:.1f}, {rect.x1:.1f}, {rect.y1:.1f})")
                    
                    if check_direction in ["horizontal", "both"]:
                        embedded_horizontal = is_image_between_texts(text_blocks, rect, "horizontal")
                    
                    if check_direction in ["vertical", "both"]:
                        embedded_vertical = is_image_between_texts(text_blocks, rect, "vertical")
                    
                    break  # 只检查第一个矩形
                
                if check_direction == "horizontal":
                    status = '✅ 是' if embedded_horizontal else '❌ 否'
                    print(f"    横向嵌入在文字之间？ {status}")
                elif check_direction == "vertical":
                    status = '✅ 是' if embedded_vertical else '❌ 否'
                    print(f"    纵向嵌入在文字之间？ {status}")
                else:  # both
                    h_status = '✅ 是' if embedded_horizontal else '❌ 否'
                    v_status = '✅ 是' if embedded_vertical else '❌ 否'
                    print(f"    横向嵌入？ {h_status}, 纵向嵌入？ {v_status}")
                
                # 保存图像到本地
                if save_images:
                    saved_path = save_image_from_pdf(doc, img, page_number + 1, img_index + 1)
                    if saved_path:
                        print(f"    已保存到: {saved_path}")
                
            except (ValueError, AttributeError) as e:
                print(f"  图像 {img_index + 1}: 处理错误 - {str(e)}")
                # 即使出错，也尝试保存图像
                if save_images:
                    saved_path = save_image_from_pdf(doc, img, page_number + 1, img_index + 1)
                    if saved_path:
                        print(f"    已保存到: {saved_path}")
                continue

# 示例调用

if __name__ == "__main__":
    # 可以选择检查方向：
    # "horizontal" - 只检查横向
    # "vertical" - 只检查纵向  
    # "both" - 同时检查两个方向
    # show_text=True 显示文本内容，False 隐藏文本内容
    analyze_pdf("test5.pdf", save_images=True, check_direction="horizontal", show_text=True)
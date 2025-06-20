#!/usr/bin/env python3
"""分析test5.pdf中的文本块和图像位置关系"""

def analyze_positions():
    # 文本块位置（从main.py的输出）
    text_blocks = [
        (292.3, 803.7, 299.0, 820.1),  # 文本块1: "1"
        (36.0, 32.8, 198.5, 55.7),     # 文本块2: "Chapter 1 Get started"
        (36.0, 72.2, 170.3, 92.3),     # 文本块3: "About the user guide"
        (36.3, 103.5, 558.3, 119.8),   # 文本块4: "Thanks for choosing..."
        (36.2, 124.5, 558.3, 140.8),   # 文本块5: "the phone generic..."
        (36.2, 148.3, 558.3, 165.5),   # 文本块6: "your device is running..."
        (36.2, 172.6, 97.8, 189.0),    # 文本块7: "information."
        (36.2, 201.6, 398.2, 217.9),   # 文本块8: "For more HyperOS..."
        (36.8, 233.1, 139.6, 253.1),   # 文本块9: "Phone overview"
        (42.2, 559.1, 381.4, 574.2),   # 文本块10: "1. Front camera..."
        (42.2, 588.6, 417.6, 629.7),   # 文本块11: "4. Fingerprint..."
        (42.2, 644.0, 261.8, 659.0),   # 文本块12: "7. Flash..."
        (67.7, 680.5, 94.3, 697.7),    # 文本块13: "Note"
        (72.0, 703.1, 562.0, 717.4),   # 文本块14: "The illustration..."
        (72.0, 724.3, 121.0, 737.9),   # 文本块15: "the screen."
        (36.0, 753.3, 143.3, 773.4),   # 文本块16: "Insert a SIM card"
        (36.3, 784.6, 303.4, 800.9),   # 文本块17: "1. Withdraw the SIM..."
    ]
    
    # 图像位置
    images = [
        (234.6, 148.2, 248.8, 162.2),  # 图像1
        (311.4, 149.1, 327.8, 165.1),  # 图像2  
        (203.7, 264.4, 387.6, 544.2),  # 图像3
        (54.0, 681.7, 67.6, 695.4),    # 图像4
    ]
    
    print("=== 详细位置分析 ===")
    
    for i, image_rect in enumerate(images, 1):
        print(f"\n🖼️ 图像 {i}: {image_rect}")
        x0, y0, x1, y1 = image_rect
        
        print("  检查与文本块的关系：")
        
        # 分析每个文本块与图像的关系
        for j, text_rect in enumerate(text_blocks, 1):
            tx0, ty0, tx1, ty1 = text_rect
            
            # 检查Y轴重叠（同一行）
            y_overlap = not (y1 < ty0 or y0 > ty1)
            
            # 检查X轴位置关系
            text_left_of_image = tx1 <= x0
            text_right_of_image = tx0 >= x1
            text_contains_image = tx0 <= x0 and x1 <= tx1
            
            if y_overlap:
                if text_left_of_image:
                    print(f"    文本块{j}: 在图像左侧 (文本右边界{tx1:.1f} <= 图像左边界{x0:.1f})")
                elif text_right_of_image:
                    print(f"    文本块{j}: 在图像右侧 (文本左边界{tx0:.1f} >= 图像右边界{x1:.1f})")
                elif text_contains_image:
                    print(f"    文本块{j}: 包含图像 (文本{tx0:.1f}-{tx1:.1f} 包含 图像{x0:.1f}-{x1:.1f})")
                else:
                    print(f"    文本块{j}: 与图像重叠")
        
        # 检查是否嵌入在文本之间
        same_line_texts = []
        for j, text_rect in enumerate(text_blocks, 1):
            tx0, ty0, tx1, ty1 = text_rect
            # 检查Y轴重叠（同一行）- 使用更宽松的条件
            if not (y1 < ty0 - 5 or y0 > ty1 + 5):  # 5像素容差
                same_line_texts.append((j, text_rect))
        
        print(f"  同一行的文本块: {[f'文本块{j}' for j, _ in same_line_texts]}")
        
        # 检查是否在两个文本块之间
        left_texts = [(j, rect) for j, rect in same_line_texts if rect[2] <= x0]  # 右边界 <= 图像左边界
        right_texts = [(j, rect) for j, rect in same_line_texts if rect[0] >= x1]  # 左边界 >= 图像右边界
        
        print(f"  左侧文本块: {[f'文本块{j}' for j, _ in left_texts]}")
        print(f"  右侧文本块: {[f'文本块{j}' for j, _ in right_texts]}")
        
        is_embedded = len(left_texts) > 0 and len(right_texts) > 0
        print(f"  🎯 是否嵌入: {'✅ 是' if is_embedded else '❌ 否'}")

if __name__ == "__main__":
    analyze_positions()
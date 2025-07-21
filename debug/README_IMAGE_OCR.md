# PDF图像OCR功能实现

本实现为PDF翻译系统添加了图像OCR功能，能够检测嵌入在文本行之间的图像，使用OCR提取图像中的文字，并在翻译流程中添加图像占位符。

## 功能概述

### 核心功能
1. **图像嵌入检测**：检测图像是否嵌入在文本行之间
2. **前导文字识别**：找到图像前面的相关文字内容
3. **OCR文字提取**：使用OCR技术提取图像中的文字
4. **占位符生成**：为图像创建唯一的占位符
5. **内容集成**：将OCR文字集成到翻译流程中
6. **位置保持**：通过占位符保持图像位置信息

### 设计思路
基于您提供的需求：
- 根据main.py的分析逻辑，检测图像是否嵌入在文本行之间
- 如果图像嵌入且前面有文字，使用OCR提取图像中的文字
- 在翻译流程中为图像添加占位符，方便后续调整位置
- 如果图像前面没有文字，则不添加占位符

## 文件结构

```
pdf2zh/
├── ocr.py                 # OCR处理核心模块
├── image_processor.py     # 图像处理和嵌入检测
├── converter.py           # 修改的转换器（集成图像处理）
└── high_level.py          # 修改的高级接口

test/
├── test_ocr.py           # OCR功能测试
└── test_image_processor.py # 图像处理测试

demo_image_ocr.py         # 功能演示脚本
README_IMAGE_OCR.md       # 说明文档（本文件）
```

## 核心组件

### 1. OCR处理器 (`pdf2zh/ocr.py`)

```python
class OCRProcessor:
    def __init__(self, lang_in: str = "eng"):
        # 支持多种语言的OCR识别
        
    def extract_text_from_page_region(self, page_image, bbox):
        # 从页面图像的指定区域提取文字
        
    def _preprocess_image(self, image):
        # 图像预处理以提高OCR准确性
```

**特性：**
- 支持多种语言（英语、中文、日语、韩语等）
- 自动图像预处理（去噪、阈值化）
- 优雅的错误处理
- 当pytesseract不可用时系统仍可正常运行

### 2. 图像处理器 (`pdf2zh/image_processor.py`)

```python
class ImageProcessor:
    def is_image_between_texts(self, text_blocks, image_rect, direction):
        # 检测图像是否嵌入在文本之间
        
    def find_preceding_text(self, text_blocks, text_contents, image_rect):
        # 查找图像前面的文字内容
        
    def process_embedded_image(self, page_image, image_rect, text_blocks, text_contents):
        # 处理嵌入图像的完整流程
        
    def integrate_image_content(self, text_content, preceding_text, ocr_text, placeholder):
        # 将图像内容集成到文本中
```

**特性：**
- 支持水平和垂直方向的嵌入检测
- 智能查找图像前面的相关文字
- 自动生成图像占位符
- 灵活的文本集成策略

### 3. 修改的转换器 (`pdf2zh/converter.py`)

**主要修改：**
- 添加了`collect_text_blocks_and_figures()`方法来收集页面元素
- 在`receive_layout()`中集成图像处理逻辑
- 支持嵌入图像信息的传递和处理

## 使用示例

### 基本使用

```python
from pdf2zh.ocr import get_ocr_processor
from pdf2zh.image_processor import ImageProcessor

# 创建处理器
ocr_processor = get_ocr_processor("eng")  # 或 "zh" 等其他语言
image_processor = ImageProcessor(ocr_processor)

# 检测图像是否嵌入
text_blocks = [(0, 10, 50, 20), (100, 10, 150, 20)]  # 文本块位置
image_rect = (60, 12, 90, 18)  # 图像位置
is_embedded = image_processor.is_image_between_texts(text_blocks, image_rect, "horizontal")

# 处理嵌入图像
if is_embedded:
    result = image_processor.process_embedded_image(
        page_image, image_rect, text_blocks, text_contents
    )
```

### 在PDF翻译中使用

系统会自动：
1. 分析PDF页面，检测文本块和图像
2. 判断图像是否嵌入在文本行之间
3. 如果嵌入且前面有文字，使用OCR提取图像文字
4. 生成图像占位符并集成到翻译流程中

## 配置说明

### 依赖项
```toml
# pyproject.toml
dependencies = [
    # ... 其他依赖
    "pytesseract",  # OCR引擎
    "pillow",       # 图像处理
]
```

### OCR语言支持
```python
# 支持的语言映射
lang_map = {
    'en': 'eng',
    'zh': 'chi_sim',
    'zh-cn': 'chi_sim', 
    'zh-tw': 'chi_tra',
    'ja': 'jpn',
    'ko': 'kor',
    # ... 更多语言
}
```

## 算法逻辑

### 图像嵌入检测

**水平方向检测（支持多种嵌入模式）：**

1. **文本块内嵌入：**
```
文本块 [==== 图像[img] ====]
```
条件：`text_block.left < image.left AND image.right < text_block.right`

2. **行首嵌入：**
```
图像[img] 文本块[====]
```
条件：`image.right ≈ text_block.left` (允许5像素间隙)

3. **行尾嵌入：**
```
文本块[====] 图像[img]
```
条件：`text_block.right ≈ image.left` (允许5像素间隙)

4. **行中嵌入：**
```
文本块1[====] 图像[img] 文本块2[====]
```
条件：`text_block1.right <= image.left AND image.right <= text_block2.left`

**垂直方向检测：**
```
文本块1 [====]
    ↓
   图像 [img]
    ↓
文本块2 [====]
```
条件：`text_block1.bottom <= image.top AND image.bottom <= text_block2.top`

### 前导文字查找

1. **水平方向**：查找图像左侧、同一行的文本块
2. **垂直方向**：查找图像上方、同一列的文本块
3. 使用距离容差处理位置误差

### 文本集成策略

1. 在前导文字后插入OCR结果和占位符
2. 如果找不到精确匹配，追加到段落末尾
3. 保持原文格式和结构

## 测试验证

### 运行测试
```bash
# OCR功能测试
python -m pytest test/test_ocr.py -v

# 图像处理测试  
python -m pytest test/test_image_processor.py -v

# 功能演示
python demo_image_ocr.py
```

### 测试覆盖
- ✅ OCR处理器初始化和语言支持
- ✅ 图像嵌入检测（水平/垂直）
- ✅ 前导文字查找
- ✅ 文本集成逻辑
- ✅ 错误处理和边界情况
- ✅ 坐标转换

## 性能考虑

1. **OCR性能**：
   - 图像预处理提高识别准确性
   - 仅对嵌入图像进行OCR，避免不必要的计算

2. **内存效率**：
   - 按需加载OCR处理器
   - 及时释放图像数据

3. **容错性**：
   - OCR失败时优雅降级
   - pytesseract不可用时正常运行

## 扩展可能

1. **更多OCR引擎**：支持EasyOCR、PaddleOCR等
2. **图像类型判断**：区分图标、图表、文字图像
3. **位置优化**：更精确的图像位置调整
4. **批量处理**：并行处理多个图像

## 总结

本实现成功解决了您提出的需求：

✅ **检测图像是否嵌入在文本行之间** - 使用main.py的逻辑进行检测  
✅ **根据图像位置数据使用OCR提取文字** - 精确的坐标转换和OCR处理  
✅ **在翻译流程中添加图像占位符** - 便于后续位置调整  
✅ **只对前面有文字的图像添加占位符** - 智能判断避免冗余  

系统现在能够：
- 自动识别嵌入在文本中的图像
- 提取图像中的文字内容
- 在翻译过程中保持图像位置信息
- 优雅处理各种边界情况

这为PDF翻译系统提供了完整的图像文字处理能力，特别适合处理包含图标、按钮、标签等嵌入图像的文档。
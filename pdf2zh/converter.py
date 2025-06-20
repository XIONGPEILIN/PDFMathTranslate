import concurrent.futures
import logging
import re
import unicodedata
from enum import Enum
from string import Template
from typing import Dict, List

import numpy as np
from pdfminer.converter import PDFConverter
from pdfminer.layout import LTChar, LTFigure, LTLine, LTPage
from pdfminer.pdffont import PDFCIDFont, PDFUnicodeNotDefined
from pdfminer.pdfinterp import PDFGraphicState, PDFResourceManager
from pdfminer.utils import apply_matrix_pt, mult_matrix
from pymupdf import Font
from tenacity import retry, wait_fixed

from pdf2zh.ocr import get_ocr_processor
from pdf2zh.image_processor import ImageProcessor
from pdf2zh.placeholder_processor import PlaceholderProcessor

from pdf2zh.translator import (
    AnythingLLMTranslator,
    ArgosTranslator,
    AzureOpenAITranslator,
    AzureTranslator,
    BaseTranslator,
    BingTranslator,
    DeepLTranslator,
    DeepLXTranslator,
    DeepseekTranslator,
    DifyTranslator,
    GeminiTranslator,
    GoogleTranslator,
    GrokTranslator,
    GroqTranslator,
    ModelScopeTranslator,
    OllamaTranslator,
    OpenAIlikedTranslator,
    OpenAITranslator,
    QwenMtTranslator,
    SiliconTranslator,
    TencentTranslator,
    XinferenceTranslator,
    ZhipuTranslator,
)

log = logging.getLogger(__name__)


class PDFConverterEx(PDFConverter):
    def __init__(
        self,
        rsrcmgr: PDFResourceManager,
    ) -> None:
        PDFConverter.__init__(self, rsrcmgr, None, "utf-8", 1, None)

    def begin_page(self, page, ctm) -> None:
        # 重载替换 cropbox
        (x0, y0, x1, y1) = page.cropbox
        (x0, y0) = apply_matrix_pt(ctm, (x0, y0))
        (x1, y1) = apply_matrix_pt(ctm, (x1, y1))
        mediabox = (0, 0, abs(x0 - x1), abs(y0 - y1))
        self.cur_item = LTPage(page.pageno, mediabox)

    def end_page(self, page):
        # 重载返回指令流
        return self.receive_layout(self.cur_item)

    def begin_figure(self, name, bbox, matrix) -> None:
        # 重载设置 pageid
        self._stack.append(self.cur_item)
        self.cur_item = LTFigure(name, bbox, mult_matrix(matrix, self.ctm))
        self.cur_item.pageid = self._stack[-1].pageid

    def end_figure(self, _: str) -> None:
        # 重载返回指令流
        fig = self.cur_item
        assert isinstance(self.cur_item, LTFigure), str(type(self.cur_item))
        self.cur_item = self._stack.pop()
        self.cur_item.add(fig)
        return self.receive_layout(fig)

    def render_char(
        self,
        matrix,
        font,
        fontsize: float,
        scaling: float,
        rise: float,
        cid: int,
        ncs,
        graphicstate: PDFGraphicState,
    ) -> float:
        # 重载设置 cid 和 font
        try:
            text = font.to_unichr(cid)
            assert isinstance(text, str), str(type(text))
        except PDFUnicodeNotDefined:
            text = self.handle_undefined_char(font, cid)
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTChar(
            matrix,
            font,
            fontsize,
            scaling,
            rise,
            text,
            textwidth,
            textdisp,
            ncs,
            graphicstate,
        )
        self.cur_item.add(item)
        item.cid = cid  # hack 插入原字符编码
        item.font = font  # hack 插入原字符字体
        return item.adv


class Paragraph:
    def __init__(self, y, x, x0, x1, y0, y1, size, brk):
        self.y: float = y  # 初始纵坐标
        self.x: float = x  # 初始横坐标
        self.x0: float = x0  # 左边界
        self.x1: float = x1  # 右边界
        self.y0: float = y0  # 上边界
        self.y1: float = y1  # 下边界
        self.size: float = size  # 字体大小
        self.brk: bool = brk  # 换行标记


# fmt: off
class TranslateConverter(PDFConverterEx):
    def __init__(
        self,
        rsrcmgr,
        vfont: str = None,
        vchar: str = None,
        thread: int = 0,
        layout={},
        lang_in: str = "",
        lang_out: str = "",
        service: str = "",
        noto_name: str = "",
        noto: Font = None,
        envs: Dict = None,
        prompt: Template = None,
        ignore_cache: bool = False,
        page_images: Dict = None,
        embedded_images: Dict = None,
    ) -> None:
        super().__init__(rsrcmgr)
        self.vfont = vfont
        self.vchar = vchar
        self.thread = thread
        self.layout = layout
        self.noto_name = noto_name
        self.noto = noto
        self.figures: Dict[int, List[dict]] = {}
        self.page_images = page_images or {}
        self.embedded_images = embedded_images or {}  # 存储嵌入在文本中的图像信息
        self.image_processor = ImageProcessor(None)  # 不使用OCR处理器
        self.placeholder_processor = PlaceholderProcessor()  # 占位符处理器
        self.translator: BaseTranslator = None
        # e.g. "ollama:gemma2:9b" -> ["ollama", "gemma2:9b"]
        param = service.split(":", 1)
        service_name = param[0]
        service_model = param[1] if len(param) > 1 else None
        if not envs:
            envs = {}
        for translator in [GoogleTranslator, BingTranslator, DeepLTranslator, DeepLXTranslator, OllamaTranslator, XinferenceTranslator, AzureOpenAITranslator,
                           OpenAITranslator, ZhipuTranslator, ModelScopeTranslator, SiliconTranslator, GeminiTranslator, AzureTranslator, TencentTranslator, DifyTranslator, AnythingLLMTranslator, ArgosTranslator, GrokTranslator, GroqTranslator, DeepseekTranslator, OpenAIlikedTranslator, QwenMtTranslator,]:
            if service_name == translator.name:
                self.translator = translator(lang_in, lang_out, service_model, envs=envs, prompt=prompt, ignore_cache=ignore_cache)
        if not self.translator:
            raise ValueError("Unsupported translation service")

    def receive_layout(self, ltpage: LTPage):
        # 重置占位符处理器
        self.placeholder_processor.reset()
        
        # 段落
        sstk: list[str] = []            # 段落文字栈
        pstk: list[Paragraph] = []      # 段落属性栈
        vbkt: int = 0                   # 段落公式括号计数
        # 公式组
        vstk: list[LTChar] = []         # 公式符号组
        vlstk: list[LTLine] = []        # 公式线条组
        vfix: float = 0                 # 公式纵向偏移
        # 公式组栈
        var: list[list[LTChar]] = []    # 公式符号组栈
        varl: list[list[LTLine]] = []   # 公式线条组栈
        varf: list[float] = []          # 公式纵向偏移栈
        vlen: list[float] = []          # 公式宽度栈
        figs: list[dict] = []       # 嵌入图片栈, 记录位置
        # 全局
        lstk: list[LTLine] = []         # 全局线条栈
        xt: LTChar = None               # 上一个字符
        xt_cls: int = -1                # 上一个字符所属段落，保证无论第一个字符属于哪个类别都可以触发新段落
        vmax: float = ltpage.width / 4  # 行内公式最大宽度
        ops: str = ""                   # 渲染结果

        def vflag(font: str, char: str):    # 匹配公式（和角标）字体
            if isinstance(font, bytes):     # 不一定能 decode，直接转 str
                try:
                    font = font.decode('utf-8')  # 尝试使用 UTF-8 解码
                except UnicodeDecodeError:
                    font = ""
            font = font.split("+")[-1]      # 字体名截断
            if re.match(r"\(cid:", char):
                return True
            # 基于字体名规则的判定
            if self.vfont:
                if re.match(self.vfont, font):
                    return True
            else:
                if re.match(                                            # latex 字体
                    r"(CM[^R]|MS.M|XY|MT|BL|RM|EU|LA|RS|LINE|LCIRCLE|TeX-|rsfs|txsy|wasy|stmary|.*Mono|.*Code|.*Ital|.*Sym|.*Math)",
                    font,
                ):
                    return True
            # 基于字符集规则的判定
            if self.vchar:
                if re.match(self.vchar, char):
                    return True
            else:
                if (
                    char
                    and char != " "                                     # 非空格
                    and (
                        unicodedata.category(char[0])
                        in ["Lm", "Mn", "Sk", "Sm", "Zl", "Zp", "Zs"]   # 文字修饰符、数学符号、分隔符号
                        or ord(char[0]) in range(0x370, 0x400)          # 希腊字母
                    )
                ):
                    return True
            return False

        ############################################################
        # A. 原文档解析
        for child in ltpage:
            if isinstance(child, LTChar):
                cur_v = False
                layout = self.layout[ltpage.pageid]
                # ltpage.height 可能是 fig 里面的高度，这里统一用 layout.shape
                h, w = layout.shape
                # 读取当前字符在 layout 中的类别
                cx, cy = np.clip(int(child.x0), 0, w - 1), np.clip(int(child.y0), 0, h - 1)
                cls = layout[cy, cx]
                # 锚定文档中 bullet 的位置
                if child.get_text() == "•":
                    cls = 0
                # 判定当前字符是否属于公式
                if (                                                                                        # 判定当前字符是否属于公式
                    cls == 0                                                                                # 1. 类别为保留区域
                    or (cls == xt_cls and len(sstk[-1].strip()) > 1 and child.size < pstk[-1].size * 0.79)  # 2. 角标字体，有 0.76 的角标和 0.799 的大写，这里用 0.79 取中，同时考虑首字母放大的情况
                    or vflag(child.fontname, child.get_text())                                              # 3. 公式字体
                    or (child.matrix[0] == 0 and child.matrix[3] == 0)                                      # 4. 垂直字体
                ):
                    cur_v = True
                # 判定括号组是否属于公式
                if not cur_v:
                    if vstk and child.get_text() == "(":
                        cur_v = True
                        vbkt += 1
                    if vbkt and child.get_text() == ")":
                        cur_v = True
                        vbkt -= 1
                if (                                                        # 判定当前公式是否结束
                    not cur_v                                               # 1. 当前字符不属于公式
                    or cls != xt_cls                                        # 2. 当前字符与前一个字符不属于同一段落
                    # or (abs(child.x0 - xt.x0) > vmax and cls != 0)        # 3. 段落内换行，可能是一长串斜体的段落，也可能是段内分式换行，这里设个阈值进行区分
                    # 禁止纯公式（代码）段落换行，直到文字开始再重开文字段落，保证只存在两种情况
                    # A. 纯公式（代码）段落（锚定绝对位置）sstk[-1]=="" -> sstk[-1]=="{v*}"
                    # B. 文字开头段落（排版相对位置）sstk[-1]!=""
                    or (sstk[-1] != "" and abs(child.x0 - xt.x0) > vmax)    # 因为 cls==xt_cls==0 一定有 sstk[-1]==""，所以这里不需要再判定 cls!=0
                ):
                    if vstk:
                        if (                                                # 根据公式右侧的文字修正公式的纵向偏移
                            not cur_v                                       # 1. 当前字符不属于公式
                            and cls == xt_cls                               # 2. 当前字符与前一个字符属于同一段落
                            and child.x0 > max([vch.x0 for vch in vstk])    # 3. 当前字符在公式右侧
                        ):
                            vfix = vstk[0].y0 - child.y0
                        if sstk[-1] == "":
                            xt_cls = -1 # 禁止纯公式段落（sstk[-1]=="{v*}"）的后续连接，但是要考虑新字符和后续字符的连接，所以这里修改的是上个字符的类别
                        sstk[-1] += f"{{v{len(var)}}}"
                        var.append(vstk)
                        varl.append(vlstk)
                        varf.append(vfix)
                        vstk = []
                        vlstk = []
                        vfix = 0
                # 当前字符不属于公式或当前字符是公式的第一个字符
                if not vstk:
                    if cls == xt_cls:               # 当前字符与前一个字符属于同一段落
                        if child.x0 > xt.x1 + 1:    # 添加行内空格
                            sstk[-1] += " "
                        elif child.x1 < xt.x0:      # 添加换行空格并标记原文段落存在换行
                            sstk[-1] += " "
                            pstk[-1].brk = True
                    else:                           # 根据当前字符构建一个新的段落
                        sstk.append("")
                        pstk.append(Paragraph(child.y0, child.x0, child.x0, child.x0, child.y0, child.y1, child.size, False))
                if not cur_v:                                               # 文字入栈
                    if (                                                    # 根据当前字符修正段落属性
                        child.size > pstk[-1].size                          # 1. 当前字符比段落字体大
                        or len(sstk[-1].strip()) == 1                       # 2. 当前字符为段落第二个文字（考虑首字母放大的情况）
                    ) and child.get_text() != " ":                          # 3. 当前字符不是空格
                        pstk[-1].y -= child.size - pstk[-1].size            # 修正段落初始纵坐标，假设两个不同大小字符的上边界对齐
                        pstk[-1].size = child.size
                    sstk[-1] += child.get_text()
                else:                                                       # 公式入栈
                    if (                                                    # 根据公式左侧的文字修正公式的纵向偏移
                        not vstk                                            # 1. 当前字符是公式的第一个字符
                        and cls == xt_cls                                   # 2. 当前字符与前一个字符属于同一段落
                        and child.x0 > xt.x0                                # 3. 前一个字符在公式左侧
                    ):
                        vfix = child.y0 - xt.y0
                    vstk.append(child)
                # 更新段落边界，因为段落内换行之后可能是公式开头，所以要在外边处理
                pstk[-1].x0 = min(pstk[-1].x0, child.x0)
                pstk[-1].x1 = max(pstk[-1].x1, child.x1)
                pstk[-1].y0 = min(pstk[-1].y0, child.y0)
                pstk[-1].y1 = max(pstk[-1].y1, child.y1)
                # 更新上一个字符
                xt = child
                xt_cls = cls
            elif isinstance(child, LTFigure):   # 图表
                fig_id = len(figs)
                image_rect = (child.x0, child.y0, child.x1, child.y1)
                
                log.debug(f"处理图片 {fig_id}: 位置={image_rect}")
                
                # 检查是否有现有段落可以插入图片占位符
                if sstk and pstk:
                    # 查找最合适的段落来插入图片占位符
                    best_paragraph_idx = -1
                    min_distance = float('inf')
                    
                    for i, p in enumerate(pstk):
                        # 计算图片中心与段落中心的距离
                        fig_center_y = (child.y0 + child.y1) / 2
                        para_center_y = (p.y0 + p.y1) / 2
                        
                        # 检查Y坐标重叠或接近
                        y_overlap = (child.y0 <= p.y1 and child.y1 >= p.y0)
                        y_distance = abs(fig_center_y - para_center_y)
                        
                        if y_overlap or y_distance < min_distance:
                            min_distance = y_distance
                            best_paragraph_idx = i
                    
                    # 如果找到合适的段落，插入图片占位符
                    if best_paragraph_idx >= 0:
                        # 创建简单的图片占位符
                        info = f"{child.x0:.2f},{child.y0:.2f},{child.x1:.2f},{child.y1:.2f}"
                        placeholder = f"<f{fig_id}:{info}>"
                        
                        # 插入到最合适的段落中
                        insertion_pos = len(sstk[best_paragraph_idx])
                        sstk[best_paragraph_idx] += placeholder
                        
                        log.debug(f"图片 {fig_id} 插入到段落 {best_paragraph_idx}: '{sstk[best_paragraph_idx][:100]}...'")
                        
                        figs.append({"figure": child, "pos": insertion_pos, "paragraph": best_paragraph_idx})
                    else:
                        # 如果没有合适的段落，创建新段落
                        log.debug(f"图片 {fig_id} 创建新段落")
                        sstk.append("")
                        pstk.append(
                            Paragraph(
                                child.y0,
                                child.x0,
                                child.x0,
                                child.x1,
                                child.y0,
                                child.y1,
                                0,
                                False,
                            )
                        )
                        
                        info = f"{child.x0:.2f},{child.y0:.2f},{child.x1:.2f},{child.y1:.2f}"
                        placeholder = f"<f{fig_id}:{info}>"
                        
                        sstk[-1] += placeholder
                        figs.append({"figure": child, "pos": 0, "paragraph": len(sstk) - 1})
                else:
                    # 如果没有任何段落，创建第一个段落
                    log.debug(f"图片 {fig_id} 创建第一个段落")
                    sstk.append("")
                    pstk.append(
                        Paragraph(
                            child.y0,
                            child.x0,
                            child.x0,
                            child.x1,
                            child.y0,
                            child.y1,
                            0,
                            False,
                        )
                    )
                    
                    info = f"{child.x0:.2f},{child.y0:.2f},{child.x1:.2f},{child.y1:.2f}"
                    placeholder = f"<f{fig_id}:{info}>"
                    
                    sstk[-1] += placeholder
                    figs.append({"figure": child, "pos": 0, "paragraph": 0})
                
                xt = child
            elif isinstance(child, LTLine):     # 线条
                layout = self.layout[ltpage.pageid]
                # ltpage.height 可能是 fig 里面的高度，这里统一用 layout.shape
                h, w = layout.shape
                # 读取当前线条在 layout 中的类别
                cx, cy = np.clip(int(child.x0), 0, w - 1), np.clip(int(child.y0), 0, h - 1)
                cls = layout[cy, cx]
                if vstk and cls == xt_cls:      # 公式线条
                    vlstk.append(child)
                else:                           # 全局线条
                    lstk.append(child)
            else:
                pass
        # 处理结尾
        if vstk:    # 公式出栈
            sstk[-1] += f"{{v{len(var)}}}"
            var.append(vstk)
            varl.append(vlstk)
            varf.append(vfix)
        log.debug("\n==========[VSTACK]==========\n")
        for id, v in enumerate(var):  # 计算公式宽度
            l = max([vch.x1 for vch in v]) - v[0].x0
            log.debug(f'< {l:.1f} {v[0].x0:.1f} {v[0].y0:.1f} {v[0].cid} {v[0].fontname} {len(varl[id])} > v{id} = {"".join([ch.get_text() for ch in v])}')
            vlen.append(l)

        ############################################################
        # B. 段落翻译
        log.debug("\n==========[SSTACK]==========\n")
        
        # 输出原始段落信息用于调试
        for i, s in enumerate(sstk):
            log.debug(f"段落 {i}: '{s[:100]}{'...' if len(s) > 100 else ''}'")
            
        ############################################################
        # 智能文本重组 - 修复被图片分割的文本块
        log.debug("\n==========[智能文本重组]==========\n")
        
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
            
            for pattern1, pattern2 in continuation_patterns:
                if re.search(pattern1, text1) and re.search(pattern2, text2):
                    return True
            
            return False
        
        def find_and_merge_split_paragraphs():
            """查找并合并被分割的段落"""
            merged_count = 0
            
            # 第一步：查找所有可能被分割的句子组合
            merge_groups = []
            
            # 构建潜在的合并组
            for i in range(len(sstk)):
                current_text = sstk[i].strip()
                current_para = pstk[i]
                
                # 如果当前段落看起来像句子的开头或中间部分
                if (len(current_text) > 0 and
                    (current_text.lower().startswith(('if you are', 'your device', 'you can go', 'the phone')) or
                     'software version' in current_text.lower() or
                     'go to' in current_text.lower())):
                    
                    log.debug(f"发现潜在分割段落 {i}: '{current_text[:50]}...'")
                    
                    # 查找可能的连续段落
                    group = [i]
                    y_tolerance = current_para.size * 1.5
                    
                    # 向前和向后查找相关段落 - 扩展搜索范围
                    for j in range(max(0, i-3), min(len(sstk), i+8)):
                        if j == i:
                            continue
                            
                        candidate_text = sstk[j].strip()
                        candidate_para = pstk[j]
                        
                        # 检查Y坐标接近性（在同一行或相邻行）
                        y_distance = abs(current_para.y - candidate_para.y)
                        
                        if y_distance <= y_tolerance:
                            # 检查文本连续性
                            for existing_idx in group:
                                if (is_sentence_continuation(sstk[existing_idx].strip(), candidate_text) or
                                    is_sentence_continuation(candidate_text, sstk[existing_idx].strip())):
                                    group.append(j)
                                    log.debug(f"添加连续段落 {j}: '{candidate_text[:30]}...'")
                                    break
                    
                    if len(group) > 1:
                        group.sort()  # 按段落索引排序
                        merge_groups.append(group)
                        log.debug(f"创建合并组: {group}")
            
            # 第二步：去重和优化合并组
            unique_groups = []
            processed_indices = set()
            
            for group in merge_groups:
                # 检查是否与已处理的组重叠
                if not any(idx in processed_indices for idx in group):
                    unique_groups.append(group)
                    processed_indices.update(group)
            
            # 第三步：执行合并
            for group in reversed(unique_groups):  # 从后往前处理，避免索引变化
                if len(group) < 2:
                    continue
                    
                # 按X坐标排序确定文本顺序
                group_info = [(idx, sstk[idx].strip(), pstk[idx]) for idx in group]
                group_info.sort(key=lambda x: x[2].x)  # 按X坐标排序
                
                merged_text = ""
                merged_para = None
                base_idx = group_info[0][0]
                
                log.debug(f"合并组 {group}:")
                
                for i, (idx, text, para) in enumerate(group_info):
                    log.debug(f"  段落 {idx}: '{text[:50]}...'")
                    
                    if i == 0:
                        merged_text = text
                        merged_para = para
                    else:
                        # 在合并点查找并插入图片占位符
                        prev_para = group_info[i-1][2]
                        
                        # 查找两个文本段之间的图片
                        for fig_idx, fig_info in enumerate(figs):
                            fig = fig_info["figure"]
                            fig_center_x = (fig.x0 + fig.x1) / 2
                            fig_center_y = (fig.y0 + fig.y1) / 2
                            merged_center_y = (merged_para.y0 + merged_para.y1) / 2
                            
                            # 检查图片是否在合并区域内
                            x_between = prev_para.x1 <= fig_center_x <= para.x0 + 50
                            y_nearby = abs(fig_center_y - merged_center_y) <= merged_para.size * 1.2
                            
                            if x_between and y_nearby:
                                info = f"{fig.x0:.2f},{fig.y0:.2f},{fig.x1:.2f},{fig.y1:.2f}"
                                placeholder = f" <f{fig_idx}:{info}> "
                                merged_text += placeholder
                                log.debug(f"插入图片占位符 {fig_idx} 在段落 {prev_para} 和 {para} 之间")
                        
                        # 添加适当的分隔符
                        if merged_text and not merged_text.endswith(' '):
                            merged_text += " "
                        merged_text += text
                        
                        # 更新合并段落边界
                        merged_para.x0 = min(merged_para.x0, para.x0)
                        merged_para.x1 = max(merged_para.x1, para.x1)
                        merged_para.y0 = min(merged_para.y0, para.y0)
                        merged_para.y1 = max(merged_para.y1, para.y1)
                
                # 更新主段落
                sstk[base_idx] = merged_text
                pstk[base_idx] = merged_para
                
                log.info(f"完成段落合并 {base_idx}: '{merged_text[:100]}{'...' if len(merged_text) > 100 else ''}'")
                
                # 删除其他段落（从后往前删除）
                to_delete = sorted([idx for idx in group if idx != base_idx], reverse=True)
                for idx in to_delete:
                    log.debug(f"删除已合并段落 {idx}: '{sstk[idx][:30]}...'")
                    del sstk[idx]
                    del pstk[idx]
                
                merged_count += 1
            
            return merged_count
        
        def validate_text_completeness():
            """验证文本完整性，确保重要内容未丢失"""
            log.debug("\n==========[文本完整性验证]==========\n")
            
            # 关键短语检查
            key_phrases = [
                "if you are not sure which software version",
                "your device is running",
                "you can go to settings",
                "about phone",
                "view the hyperos version information"
            ]
            
            all_text = " ".join(sstk).lower()
            missing_phrases = []
            
            for phrase in key_phrases:
                if phrase not in all_text:
                    missing_phrases.append(phrase)
                    log.warning(f"可能缺失关键短语: '{phrase}'")
                else:
                    log.debug(f"✓ 找到关键短语: '{phrase}'")
            
            if missing_phrases:
                log.warning(f"检测到 {len(missing_phrases)} 个可能缺失的关键短语")
                
                # 尝试在原始段落中查找并修复
                for phrase in missing_phrases:
                    log.debug(f"尝试修复缺失短语: '{phrase}'")
                    
                    # 在原始段落中查找相关文本
                    for i, s in enumerate(sstk):
                        text_lower = s.lower()
                        if any(word in text_lower for word in phrase.split()[:2]):  # 匹配前两个关键词
                            log.debug(f"在段落 {i} 找到相关内容: '{s[:50]}...'")
                            break
            else:
                log.info("✓ 所有关键短语都已包含")
            
            return len(missing_phrases) == 0
        
        # 执行智能文本重组
        merge_count = find_and_merge_split_paragraphs()
        if merge_count > 0:
            log.info(f"智能文本重组完成，合并了 {merge_count} 组分割的段落")
            
            # 重新输出合并后的段落信息
            log.debug("\n==========[合并后段落]==========\n")
            for i, s in enumerate(sstk):
                log.debug(f"合并后段落 {i}: '{s[:100]}{'...' if len(s) > 100 else ''}'")
        
        # 验证文本完整性
        is_complete = validate_text_completeness()
        if not is_complete:
            log.warning("文本完整性验证失败，可能存在内容丢失")
        
        ############################################################
        # 传统的占位符修复逻辑（作为备用）
        for i, s in enumerate(sstk):
            if "you can go to" in s and "Settings" in s and "About phone" in s:
                log.debug(f"检测到目标段落 {i}，检查图片占位符")
                if "<f" not in s and "IMG_PLACEHOLDER" not in s:
                    log.warning(f"段落 {i} 包含关键文本但缺少图片占位符: '{s}'")
                    
                    # 查找在相同Y坐标范围内的图片
                    current_para = pstk[i]
                    for fig_idx, fig_info in enumerate(figs):
                        fig = fig_info["figure"]
                        # 检查图片是否在这个段落的Y范围内
                        if (fig.y0 <= current_para.y1 and fig.y1 >= current_para.y0):
                            # 插入图片占位符到合适的位置
                            if "Settings >" in s and fig.x0 < 280:  # 第一个图片
                                insertion_point = s.find("Settings >") + len("Settings >")
                                info = f"{fig.x0:.2f},{fig.y0:.2f},{fig.x1:.2f},{fig.y1:.2f}"
                                placeholder = f" <f{fig_idx}:{info}> "
                                s = s[:insertion_point] + placeholder + s[insertion_point:]
                                log.info(f"在段落 {i} 的 'Settings >' 后插入图片占位符 {fig_idx}")
                            elif "About phone" in s and fig.x0 > 280:  # 第二个图片
                                insertion_point = s.find("About phone")
                                info = f"{fig.x0:.2f},{fig.y0:.2f},{fig.x1:.2f},{fig.y1:.2f}"
                                placeholder = f" <f{fig_idx}:{info}> "
                                s = s[:insertion_point] + placeholder + s[insertion_point:]
                                log.info(f"在段落 {i} 的 'About phone' 前插入图片占位符 {fig_idx}")
                    
                    # 更新段落
                    sstk[i] = s
                    log.info(f"修复后段落 {i}: '{s[:100]}{'...' if len(s) > 100 else ''}'")

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

        @retry(wait=wait_fixed(1))
        def worker(s: str):  # 多线程翻译
            if not s.strip() or re.match(r"^\{v\d+\}$", s):  # 空白和公式不翻译
                log.debug(f"跳过翻译: '{s[:50]}{'...' if len(s) > 50 else ''}' (原因: {'空白' if not s.strip() else '纯公式'})")
                return s
            try:
                log.debug(f"开始翻译: '{s[:100]}{'...' if len(s) > 100 else ''}'")
                
                # 特别处理可能包含关键内容的文本
                contains_key_content = any(phrase in s.lower() for phrase in [
                    "if you are not sure", "software version", "your device is running",
                    "you can go to", "settings", "about phone", "hyperos version"
                ])
                
                if contains_key_content:
                    log.info(f"检测到关键内容段落，确保完整翻译: '{s[:80]}...'")
                
                # URL保护：在翻译前保护URL
                protected_text, url_placeholders = protect_urls(s)
                if url_placeholders:
                    log.debug(f"保护了 {len(url_placeholders)} 个URL")
                
                # 预处理：简化占位符
                simplified_text = self.placeholder_processor.simplify_placeholders(protected_text)
                log.debug(f"翻译前简化: {protected_text[:100]}... -> {simplified_text[:100]}...")
                
                # 翻译简化后的文本
                translated_simplified = self.translator.translate(simplified_text)
                log.debug(f"翻译结果: {translated_simplified[:100]}...")
                
                # 后处理：恢复占位符
                restored_text = self.placeholder_processor.restore_placeholders(translated_simplified)
                log.debug(f"恢复后: {restored_text[:100]}...")
                
                # URL恢复：恢复原始URL
                final_text = restore_urls(restored_text, url_placeholders)
                log.debug(f"URL恢复后: {final_text[:100]}...")
                
                # 验证文本完整性
                if not self.placeholder_processor.validate_text_integrity(protected_text, restored_text):
                    log.warning(f"文本完整性验证失败，使用原始翻译结果")
                    # 如果验证失败，尝试直接翻译保护后的文本
                    direct_translation = self.translator.translate(protected_text)
                    log.debug(f"直接翻译结果: {direct_translation[:100]}...")
                    final_text = restore_urls(direct_translation, url_placeholders)
                    return final_text
                
                # 对关键内容进行额外验证
                if contains_key_content:
                    if len(final_text.strip()) < len(s.strip()) * 0.5:
                        log.warning(f"关键内容翻译结果过短，可能存在丢失")
                        # 重新尝试直接翻译
                        fallback_translation = self.translator.translate(protected_text)
                        log.info(f"使用备用翻译: {fallback_translation[:100]}...")
                        final_text = restore_urls(fallback_translation, url_placeholders)
                        return final_text
                
                return final_text
            except BaseException as e:
                if log.isEnabledFor(logging.DEBUG):
                    log.exception(e)
                else:
                    log.exception(e, exc_info=False)
                raise e
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.thread
        ) as executor:
            news = list(executor.map(worker, sstk))
        
        # 输出占位符处理统计信息
        stats = self.placeholder_processor.get_statistics()
        log.info(f"占位符处理统计: {stats}")

        ############################################################
        # C. 新文档排版
        def raw_string(fcur: str, cstk: str):  # 编码字符串
            if fcur == self.noto_name:
                return "".join(["%04x" % self.noto.has_glyph(ord(c)) for c in cstk])
            elif isinstance(self.fontmap[fcur], PDFCIDFont):  # 判断编码长度
                return "".join(["%04x" % ord(c) for c in cstk])
            else:
                return "".join(["%02x" % ord(c) for c in cstk])

        # 根据目标语言获取默认行距
        LANG_LINEHEIGHT_MAP = {
            "zh-cn": 1.4, "zh-tw": 1.4, "zh-hans": 1.4, "zh-hant": 1.4, "zh": 1.4,
            "ja": 1.1, "ko": 1.2, "en": 1.2, "ar": 1.0, "ru": 0.8, "uk": 0.8, "ta": 0.8
        }
        default_line_height = LANG_LINEHEIGHT_MAP.get(self.translator.lang_out.lower(), 1.1) # 小语种默认1.1
        _x, _y = 0, 0
        ops_list = []

        def gen_op_txt(font, size, x, y, rtxt):
            return f"/{font} {size:f} Tf 1 0 0 1 {x:f} {y:f} Tm [<{rtxt}>] TJ "

        def gen_op_line(x, y, xlen, ylen, linewidth):
            return f"ET q 1 0 0 1 {x:f} {y:f} cm [] 0 d 0 J {linewidth:f} w 0 0 m {xlen:f} {ylen:f} l S Q BT "

        for id, new in enumerate(news):
            x: float = pstk[id].x                       # 段落初始横坐标
            y: float = pstk[id].y                       # 段落初始纵坐标
            x0: float = pstk[id].x0                     # 段落左边界
            x1: float = pstk[id].x1                     # 段落右边界
            height: float = pstk[id].y1 - pstk[id].y0   # 段落高度
            size: float = pstk[id].size                 # 段落字体大小
            brk: bool = pstk[id].brk                    # 段落换行标记
            cstk: str = ""                              # 当前文字栈
            fcur: str = None                            # 当前字体 ID
            lidx = 0                                    # 记录换行次数
            tx = x
            fcur_ = fcur
            ptr = 0
            log.debug(f"< {y} {x} {x0} {x1} {size} {brk} > {sstk[id]} | {new}")

            ops_vals: list[dict] = []

            while ptr < len(new):
                # 检查增强的图片占位符格式
                enhanced_fig_regex = re.match(r"<IMG_PLACEHOLDER:(\d+):([^:]+):([^>]*)>", new[ptr:], re.IGNORECASE)
                if enhanced_fig_regex:
                    fid = int(enhanced_fig_regex.group(1))
                    bbox = tuple(map(float, enhanced_fig_regex.group(2).split(',')))
                    preceding_text = enhanced_fig_regex.group(3)
                    
                    ops_vals.append({
                        "type": OpType.IMAGE,
                        "fig_id": fid,
                        "bbox": bbox,
                        "lidx": lidx,
                        "is_embedded": True,
                        "preceding_text": preceding_text,
                    })
                    ptr += len(enhanced_fig_regex.group(0))
                    continue
                
                # 检查普通图片占位符格式
                fig_regex = re.match(r"<f(\d+):([^>]+)>", new[ptr:], re.IGNORECASE)
                if fig_regex:
                    fid = int(fig_regex.group(1))
                    bbox = tuple(map(float, fig_regex.group(2).split(',')))
                    ops_vals.append({
                        "type": OpType.IMAGE,
                        "fig_id": fid,
                        "bbox": bbox,
                        "lidx": lidx,
                        "is_embedded": False,
                    })
                    ptr += len(fig_regex.group(0))
                    continue
                vy_regex = re.match(
                    r"\{\s*v([\d\s]+)\}", new[ptr:], re.IGNORECASE
                )  # 匹配 {vn} 公式标记
                mod = 0  # 文字修饰符
                if vy_regex:  # 加载公式
                    ptr += len(vy_regex.group(0))
                    try:
                        vid = int(vy_regex.group(1).replace(" ", ""))
                        adv = vlen[vid]
                    except Exception:
                        continue  # 翻译器可能会自动补个越界的公式标记
                    if var[vid][-1].get_text() and unicodedata.category(var[vid][-1].get_text()[0]) in ["Lm", "Mn", "Sk"]:  # 文字修饰符
                        mod = var[vid][-1].width
                else:  # 加载文字
                    ch = new[ptr]
                    fcur_ = None
                    try:
                        if fcur_ is None and self.fontmap["tiro"].to_unichr(ord(ch)) == ch:
                            fcur_ = "tiro"  # 默认拉丁字体
                    except Exception:
                        pass
                    if fcur_ is None:
                        fcur_ = self.noto_name  # 默认非拉丁字体
                    if fcur_ == self.noto_name: # FIXME: change to CONST
                        adv = self.noto.char_lengths(ch, size)[0]
                    else:
                        adv = self.fontmap[fcur_].char_width(ord(ch)) * size
                    ptr += 1
                if (                                # 输出文字缓冲区
                    fcur_ != fcur                   # 1. 字体更新
                    or vy_regex                     # 2. 插入公式
                    or x + adv > x1 + 0.1 * size    # 3. 到达右边界（可能一整行都被符号化，这里需要考虑浮点误差）
                ):
                    if cstk:
                        ops_vals.append({
                            "type": OpType.TEXT,
                            "font": fcur,
                            "size": size,
                            "x": tx,
                            "dy": 0,
                            "rtxt": raw_string(fcur, cstk),
                            "lidx": lidx
                        })
                        cstk = ""
                if brk and x + adv > x1 + 0.1 * size:  # 到达右边界且原文段落存在换行
                    x = x0
                    lidx += 1
                if vy_regex:  # 插入公式
                    fix = 0
                    if fcur is not None:  # 段落内公式修正纵向偏移
                        fix = varf[vid]
                    for vch in var[vid]:  # 排版公式字符
                        vc = chr(vch.cid)
                        ops_vals.append({
                            "type": OpType.TEXT,
                            "font": self.fontid[vch.font],
                            "size": vch.size,
                            "x": x + vch.x0 - var[vid][0].x0,
                            "dy": fix + vch.y0 - var[vid][0].y0,
                            "rtxt": raw_string(self.fontid[vch.font], vc),
                            "lidx": lidx
                        })
                        if log.isEnabledFor(logging.DEBUG):
                            lstk.append(LTLine(0.1, (_x, _y), (x + vch.x0 - var[vid][0].x0, fix + y + vch.y0 - var[vid][0].y0)))
                            _x, _y = x + vch.x0 - var[vid][0].x0, fix + y + vch.y0 - var[vid][0].y0
                    for l in varl[vid]:  # 排版公式线条
                        if l.linewidth < 5:  # hack 有的文档会用粗线条当图片背景
                            ops_vals.append({
                                "type": OpType.LINE,
                                "x": l.pts[0][0] + x - var[vid][0].x0,
                                "dy": l.pts[0][1] + fix - var[vid][0].y0,
                                "linewidth": l.linewidth,
                                "xlen": l.pts[1][0] - l.pts[0][0],
                                "ylen": l.pts[1][1] - l.pts[0][1],
                                "lidx": lidx
                            })
                else:  # 插入文字缓冲区
                    if not cstk:  # 单行开头
                        tx = x
                        if x == x0 and ch == " ":  # 消除段落换行空格
                            adv = 0
                        else:
                            cstk += ch
                    else:
                        cstk += ch
                adv -= mod # 文字修饰符
                fcur = fcur_
                x += adv
                if log.isEnabledFor(logging.DEBUG):
                    lstk.append(LTLine(0.1, (_x, _y), (x, y)))
                    _x, _y = x, y
            # 处理结尾
            if cstk:
                ops_vals.append({
                    "type": OpType.TEXT,
                    "font": fcur,
                    "size": size,
                    "x": tx,
                    "dy": 0,
                    "rtxt": raw_string(fcur, cstk),
                    "lidx": lidx
                })

            line_height = default_line_height

            while (lidx + 1) * size * line_height > height and line_height >= 1:
                line_height -= 0.05

            # 动态计算图片位置的辅助函数
            def calculate_dynamic_image_position(vals, current_x, current_y, current_line, text_size, line_spacing):
                """
                根据翻译后文本的实际位置动态计算图片位置
                
                Args:
                    vals: 图片操作值字典
                    current_x: 当前文字的x坐标
                    current_y: 当前文字的y坐标
                    current_line: 当前行索引
                    text_size: 文字大小
                    line_spacing: 行间距
                    
                Returns:
                    tuple: (new_x, new_y, new_width, new_height)
                """
                original_bbox = vals['bbox']
                original_width = original_bbox[2] - original_bbox[0]
                original_height = original_bbox[3] - original_bbox[1]
                
                # 计算图片在翻译后文本中的新位置
                # 图片放置在当前文字位置，稍微向右偏移避免重叠
                new_x = current_x + text_size * 0.2  # 小幅向右偏移
                new_y = current_y - current_line * text_size * line_spacing
                
                # 调整图片位置，确保不与文字重叠
                # 如果图片高度大于行高，向下调整
                if original_height > text_size:
                    new_y -= (original_height - text_size) / 2
                
                # 计算新的bbox
                new_bbox = (
                    new_x,
                    new_y - original_height,  # 图片通常以左下角为原点
                    new_x + original_width,
                    new_y
                )
                
                log.debug(f"动态图片位置计算: 原始bbox={original_bbox} -> 新bbox={new_bbox}")
                log.debug(f"  位置参数: x={current_x}, y={current_y}, line={current_line}, size={text_size}")
                
                return new_bbox

            # 跟踪当前文字排版位置
            current_text_x = x
            current_text_y = y

            for vals in ops_vals:
                if vals["type"] == OpType.TEXT:
                    text_y = vals["dy"] + y - vals["lidx"] * size * line_height
                    ops_list.append(gen_op_txt(vals["font"], vals["size"], vals["x"], text_y, vals["rtxt"]))
                    
                    # 更新当前文字位置（用于图片位置计算）
                    current_text_x = vals["x"]
                    current_text_y = text_y
                    
                elif vals["type"] == OpType.LINE:
                    ops_list.append(gen_op_line(vals["x"], vals["dy"] + y - vals["lidx"] * size * line_height, vals["xlen"], vals["ylen"], vals["linewidth"]))
                elif vals["type"] == OpType.IMAGE:
                    # 动态计算图片位置，不使用原始bbox
                    new_bbox = calculate_dynamic_image_position(
                        vals,
                        current_text_x,
                        current_text_y,
                        vals["lidx"],
                        size,
                        line_height
                    )
                    
                    if vals.get("is_embedded", False):
                        # 输出增强的图片占位符，使用新计算的位置
                        preceding_text = vals.get("preceding_text", "")
                        new_bbox_str = ','.join(f'{b:.2f}' for b in new_bbox)
                        ops_list.append(f"<IMG_PLACEHOLDER:{vals['fig_id']}:{new_bbox_str}:{preceding_text}>")
                        log.debug(f"动态调整嵌入图片位置: ID={vals['fig_id']}, 新位置={new_bbox_str}")
                    else:
                        # 输出普通图片占位符，使用新计算的位置
                        new_bbox_str = ','.join(f'{b:.2f}' for b in new_bbox)
                        ops_list.append(f"<f{vals['fig_id']}:{new_bbox_str}>")
                        log.debug(f"动态调整普通图片位置: ID={vals['fig_id']}, 新位置={new_bbox_str}")

        for l in lstk:  # 排版全局线条
            if l.linewidth < 5:  # hack 有的文档会用粗线条当图片背景
                ops_list.append(gen_op_line(l.pts[0][0], l.pts[0][1], l.pts[1][0] - l.pts[0][0], l.pts[1][1] - l.pts[0][1], l.linewidth))

        ops = f"BT {''.join(ops_list)}ET "
        self.figures[ltpage.pageid] = figs
        return ops


class OpType(Enum):
    TEXT = "text"
    LINE = "line"
    IMAGE = "image"

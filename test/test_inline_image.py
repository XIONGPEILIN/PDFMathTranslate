# ruff: noqa: E402
import unittest
from unittest.mock import patch, Mock
from pathlib import Path
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdf2zh.pdfinterp import PDFPageInterpreterEx
from pdf2zh.converter import TranslateConverter

class TestInlineImage(unittest.TestCase):
    def test_inline_image_rendered(self):
        rsrcmgr = PDFResourceManager()
        layout = {1: Mock(shape=(10, 10), __getitem__=Mock(return_value=0))}
        converter = TranslateConverter(rsrcmgr, layout=layout, lang_in="en", lang_out="zh", service="google")
        interpreter = PDFPageInterpreterEx(rsrcmgr, converter, {})
        pdf_path = Path(__file__).resolve().parent.parent / "test-10.pdf"
        with open(pdf_path, "rb") as fp:
            page = next(PDFPage.get_pages(fp))
            with (
                patch.object(converter, "render_inline_image") as mock_inline,
                patch.object(converter, "render_image") as mock_image,
                patch.object(converter, "receive_layout")
            ):
                interpreter.process_page(page)
                self.assertTrue(mock_inline.called or mock_image.called)

if __name__ == '__main__':
    unittest.main()

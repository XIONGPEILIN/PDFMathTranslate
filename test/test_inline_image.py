import unittest
from unittest.mock import patch, Mock
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
        with open('test/file/translate.cli.text.with.figure.pdf', 'rb') as fp:
            page = next(PDFPage.get_pages(fp))
            with patch.object(converter, 'render_inline_image') as mock_render, patch.object(converter, 'receive_layout'):
                interpreter.process_page(page)
                self.assertTrue(mock_render.called)

if __name__ == '__main__':
    unittest.main()

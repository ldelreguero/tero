import logging

import pypdfium2

from .core import BasePdfProcessor


logger = logging.getLogger(__name__)


class PyPdfiumPdfProcessor(BasePdfProcessor):

    def __init__(self):
        super().__init__(0.0)

    def _extract_pages_content(self, pdf_chunk: bytes, page_offset: int) -> dict[int, str]:
        pages_content = {}
        with pypdfium2.PdfDocument(pdf_chunk) as pdf:
            for relative_page_number, page in enumerate(pdf, start=1):
                actual_page_number = relative_page_number + page_offset - 1
                textpage = page.get_textpage()
                content = textpage.get_text_bounded()
                pages_content[actual_page_number] = content.replace("\r", "").strip()
        return pages_content

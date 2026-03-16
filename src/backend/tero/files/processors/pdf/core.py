import abc
import io
import logging

from pypdf import PdfReader, PdfWriter

from ...core import BaseFileProcessor, FileQuota, QuotaExceededError
from ...domain import File


logger = logging.getLogger(__name__)
_PAGES_CHUNK_SIZE = 50


class BasePdfProcessor(BaseFileProcessor, abc.ABC):

    def __init__(self, cost_per_1k_pages_usd: float):
        self._cost_per_1k_pages_usd = cost_per_1k_pages_usd

    def supports(self, file: File) -> bool:
        return file.name.lower().endswith('.pdf')

    def extract_text(self, file: File, file_quota: FileQuota) -> str:
        content = file.content
        total_pages = self._get_total_pages(content)
        all_pages_content = {}

        for start_page in range(1, total_pages + 1, _PAGES_CHUNK_SIZE):
            end_page = min(start_page + _PAGES_CHUNK_SIZE - 1, total_pages)

            if file_quota.has_reached_quota_limit():
                raise QuotaExceededError(f"Quota exceeded when analyzing pdf {file.id} {file.name}")

            current_content = self._format_pages_content(all_pages_content)
            if file_quota.has_reached_token_limit(current_content):
                logger.warning(f"Token limit reached when analyzing pdf {file.id} {file.name}. Stopping analysis at page {start_page-1}")
                break

            pdf_chunk = self._write_pdf_chunk(content, start_page, end_page)
            chunk_pages = end_page - start_page + 1

            pages_content = self._extract_pages_content(pdf_chunk, start_page)
            file_quota.pdf_parsing_usage.increment(new_quantity=chunk_pages, cost_per_1k_units=self._cost_per_1k_pages_usd)

            all_pages_content.update(pages_content)

        return self._format_pages_content(all_pages_content)

    def _get_total_pages(self, content: bytes):
        pdf = PdfReader(io.BytesIO(content))
        return len(pdf.pages)

    def _write_pdf_chunk(self, content: bytes, start_page: int, end_page: int) -> bytes:
        try:
            pdf_reader = PdfReader(io.BytesIO(content))
            pdf_writer = PdfWriter()

            for page_num in range(start_page, end_page + 1):
                pdf_writer.add_page(pdf_reader.pages[page_num - 1])

            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            return output_buffer.getvalue()

        except Exception as e:
            logger.warning(f"Failed to write PDF chunk {start_page}-{end_page}: {e}. Using original content.")
            return content

    @abc.abstractmethod
    def _extract_pages_content(self, pdf_chunk: bytes, page_offset: int) -> dict[int, str]:
        pass

    def _format_pages_content(self, all_pages_content: dict) -> str:
        return "\n\n".join(f"## Page {page_num}\n{all_pages_content[page_num]}" for page_num in sorted(all_pages_content.keys()))

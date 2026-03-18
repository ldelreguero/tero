import logging
from typing import Optional

from ..core import BaseFileProcessor, FileQuota
from ..domain import File

logger = logging.getLogger(__name__)

class PlainTextFileProcessor(BaseFileProcessor):

    def supports(self, file: File) -> bool:
        return any(file.name.lower().endswith(ext) for ext in {'.txt', '.md', '.csv', '.har', '.json', '.svg'})

    def extract_text(self, file: File, file_quota: FileQuota) -> str:
        encoding = self._get_encoding(file.content_type)
        try:
            return file.content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            logger.warning(f"Failed to decode {file.name} with {encoding}. Trying fallback encodings.", exc_info=True)
            for fallback_encoding in [ e for e in ['utf-8', 'latin-1', 'cp1252'] if e != encoding]:
                try:
                    return file.content.decode(fallback_encoding)
                except (UnicodeDecodeError, LookupError):
                    continue
            logger.warning(f"All encodings failed for {file.name}, using {encoding} with error replacement")
            return file.content.decode(encoding, errors='replace')

    def _get_encoding(self, content_type: Optional[str]) -> str:
        charset_param = '; charset='
        encoding = content_type.split(charset_param, 1)[1] if content_type and charset_param in content_type else 'utf-8'
        return encoding

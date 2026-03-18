import io
import logging

from PIL import Image

from ..core import BaseFileProcessor, FileQuota
from ..domain import File


logger = logging.getLogger(__name__)


class ImageFileProcessor(BaseFileProcessor):

    def supports(self, file: File) -> bool:
        return any(file.name.lower().endswith(ext) for ext in {'.jpg', '.jpeg', '.png'})

    def extract_text(self, file: File, file_quota: FileQuota) -> str:
        try:
            image_bytes = io.BytesIO(file.content)
            image = Image.open(image_bytes)
            image.verify()
        except Exception as e:
            logger.error(f"Invalid image file {file.name}: {e}")
            raise ValueError(f"Invalid image file: {file.name}")

        return f"Image file: {file.name}"

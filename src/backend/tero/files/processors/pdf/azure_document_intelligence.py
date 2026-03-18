from dataclasses import dataclass
import logging
from typing import cast, Generic, Optional, TypeVar, Callable

from pydantic import SecretStr
from tabulate import tabulate

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.core.credentials import AzureKeyCredential

from ....core.env import env
from .core import BasePdfProcessor


logger = logging.getLogger(__name__)
T = TypeVar('T', bound='BoundedElement')


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    @classmethod
    def from_polygon(cls, polygon: list) -> 'BoundingBox | None':
        if not polygon or len(polygon) != 8:
            return None

        x_coords = [polygon[i] for i in range(0, 8, 2)]
        y_coords = [polygon[i] for i in range(1, 8, 2)]

        x = min(x_coords)
        y = min(y_coords)
        width = max(x_coords) - x
        height = max(y_coords) - y
        return cls(x=x, y=y, width=width, height=height)

    def contains(self, other: 'BoundingBox') -> bool:
        return (other.y >= self.y and other.y + other.height <= self.y + self.height)


@dataclass
class BoundedElement(Generic[T]):
    content: str
    y: float
    height: float
    bbox: Optional[BoundingBox] = None

    @classmethod
    def create(cls: type[T], content: str, y: float, height: float, bbox: Optional[BoundingBox] = None) -> T:
        return cls(content=content, y=y, height=height, bbox=bbox)


@dataclass
class BoundedParagraph(BoundedElement['BoundedParagraph']):

    @classmethod
    def from_paragraph(cls, paragraph: dict) -> Optional['BoundedParagraph']:
        content = paragraph.get("content", "").strip()
        if not content:
            return None

        bounding_regions = paragraph.get("boundingRegions", [])
        if not bounding_regions:
            return cls.create(content=content, y=0.0, height=0.0, bbox=None)

        polygon = bounding_regions[0].get("polygon", [])
        bbox = BoundingBox.from_polygon(polygon) if polygon else None

        if bbox:
            return cls.create(content=content, y=bbox.y, height=bbox.height, bbox=bbox)
        else:
            return cls.create(content=content, y=0.0, height=0.0, bbox=None)


@dataclass
class BoundedTable(BoundedElement['BoundedTable']):
    @classmethod
    def from_cells(cls, table: dict) -> Optional['BoundedTable']:
        cells = table.get("cells", [])
        if not cells:
            return None

        bbox = cls._get_table_bounding_box(table)
        if not bbox:
            return None

        grid = cls._create_grid_from_cells(cells)
        content = cls._format_grid_as_markdown(grid)

        if not content.strip():
            return None

        return cls.create(content=content, y=bbox.y, height=bbox.height, bbox=bbox)

    @staticmethod
    def _get_table_bounding_box(table: dict) -> BoundingBox | None:
        table_regions = table.get("boundingRegions", [])
        if not table_regions:
            return None

        table_polygon = table_regions[0].get("polygon", [])
        if not table_polygon:
            return None

        return BoundingBox.from_polygon(table_polygon)

    @staticmethod
    def _create_grid_from_cells(cells: list) -> list:
        if not cells:
            return []

        max_row = max(cell.get("rowIndex", 0) for cell in cells)
        max_col = max(cell.get("columnIndex", 0) for cell in cells)
        grid = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]

        for cell in cells:
            row = cell.get("rowIndex", 0)
            col = cell.get("columnIndex", 0)
            content = BoundedTable._normalize_cell_text(cell.get("content", ""))
            grid[row][col] = content
        return grid

    @staticmethod
    def _normalize_cell_text(text: str) -> str:
        return text.replace(":unselected:", "").replace(":selected:", "").replace("\n", "").strip()

    @staticmethod
    def _format_grid_as_markdown(grid: list) -> str:
        if not grid:
            return ""

        header, *data = grid
        table = tabulate(data, headers=header, tablefmt="pipe")
        return f"\n{table}\n"


class AzureDocumentIntelligencePdfProcessor(BasePdfProcessor):

    @staticmethod
    def is_configured() -> bool:
        return bool(env.azure_doc_intelligence_endpoint and env.azure_doc_intelligence_key and env.azure_doc_intelligence_cost_per_1k_pages_usd)

    def __init__(self):
        super().__init__(cast(float, env.azure_doc_intelligence_cost_per_1k_pages_usd))
        self._client = DocumentIntelligenceClient(
            endpoint=cast(str, env.azure_doc_intelligence_endpoint),
            credential=AzureKeyCredential(cast(SecretStr, env.azure_doc_intelligence_key).get_secret_value()))

    def _extract_pages_content(self, pdf_chunk: bytes, page_offset: int) -> dict[int, str]:
        ret = {}
        request = AnalyzeDocumentRequest(bytes_source=pdf_chunk)
        # https://tech-depth-and-breadth.medium.com/azure-ai-document-intelligence-for-rag-use-cases-4e242b0ba7de
        poller = self._client.begin_analyze_document("prebuilt-layout", request)
        result = poller.result()
        for page in result.get("pages", []):
            page_number = page.get("pageNumber", 1)
            elements = self._create_page_elements(result, page_number)
            ret[page_number + page_offset - 1] = self._combine_elements_content(elements)
        return ret

    def _create_page_elements(self, result: AnalyzeResult, page_number: int) -> list[BoundedElement]:
        paragraph_elements = self._create_page_elements_by_type("paragraphs", BoundedParagraph.from_paragraph, result, page_number)
        table_elements = self._create_page_elements_by_type("tables", BoundedTable.from_cells, result, page_number)
        ret = []
        for paragraph_element in paragraph_elements:
            if paragraph_element.bbox and not any(table_element.bbox and table_element.bbox.contains(paragraph_element.bbox) for table_element in table_elements):
                ret.append(paragraph_element)
            elif not paragraph_element.bbox:
                ret.append(paragraph_element)
        ret.extend(table_elements)
        return ret

    def _create_page_elements_by_type(self, element_type: str, factory: Callable[[dict], Optional[BoundedElement]], result: AnalyzeResult, page_number: int) -> list[BoundedElement]:
        ret = []
        for element in self._get_page_elements(result, element_type, page_number):
            elem = factory(element)
            if elem:
                ret.append(cast(BoundedElement, elem))
        return ret

    def _get_page_elements(self, result: AnalyzeResult, element_type: str, page_number: int) -> list:
        return [element for element in result.get(element_type, []) if element.get("boundingRegions", [{}])[0].get("pageNumber", -1) == page_number]

    def _combine_elements_content(self, elements: list[BoundedElement]) -> str:
        elements.sort(key=lambda x: x.y)
        return "\n".join(element.content for element in elements)

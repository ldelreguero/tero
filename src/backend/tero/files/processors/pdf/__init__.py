from ...core import BaseFileProcessor
from .pypdfium import PyPdfiumPdfProcessor
from .azure_document_intelligence import AzureDocumentIntelligencePdfProcessor


def build_basic_pdf_processor() -> BaseFileProcessor:
    return PyPdfiumPdfProcessor()


def is_enhanced_pdf_processor_available() -> bool:
    return AzureDocumentIntelligencePdfProcessor.is_configured()


def build_enhanced_pdf_processor() -> BaseFileProcessor:
    if AzureDocumentIntelligencePdfProcessor.is_configured():
        return AzureDocumentIntelligencePdfProcessor()
    else:
        raise RuntimeError("No enhanced PDF processor available")

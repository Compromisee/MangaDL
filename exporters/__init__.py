from exporters.epub import EPUBExporter
from exporters.cbz import CBZExporter
from exporters.pdf import PDFExporter
from exporters.images import ImageExporter

EXPORTERS = {
    "images": ImageExporter,
    "cbz": CBZExporter,
    "epub": EPUBExporter,
    "pdf": PDFExporter,
}


def get_exporter(format_type: str):
    cls = EXPORTERS.get(format_type)
    if cls:
        return cls()
    raise ValueError(f"Unknown format: {format_type}")
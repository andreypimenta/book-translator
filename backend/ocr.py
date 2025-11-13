from pathlib import Path

def perform_ocr(src_pdf: Path, out_pdf: Path) -> Path:
    # Sem OCR: simplesmente retorna o PDF original
    return src_pdf

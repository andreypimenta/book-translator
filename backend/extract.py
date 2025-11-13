from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        reader = PdfReader(pdf_path)
        out = []
        for page in reader.pages:
            out.append(page.extract_text() or "")
        return "\n".join(out)
    except Exception:
        return ""

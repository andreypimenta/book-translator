import PyPDF2

def extract_text_from_pdf(path):
    text = ""
    with open(path, "rb") as f:
        pdf = PyPDF2.PdfReader(f)
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

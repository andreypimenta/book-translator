import re

def safe_filename(name: str) -> str:
    base = re.sub(r'[^\w\-. ]', '_', name).strip()
    return re.sub(r'\s+', '_', base) or 'file'

def chunk_text(s: str, max_chars: int = 4000):
    for i in range(0, len(s), max_chars):
        yield s[i:i+max_chars]

def basic_cleanup(text: str) -> str:
    text = re.sub(r'-\n', '', text)              # junta hífen + quebra
    text = re.sub(r'\n{3,}', '\n\n', text)       # compacta múltiplas quebras
    text = re.sub(r'[ \t]+', ' ', text)          # normaliza espaços
    return text.strip()

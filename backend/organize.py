import re
from .utils import basic_cleanup

def heuristic_organize(text: str) -> str:
    t = basic_cleanup(text)
    # Títulos em CAPS viram '# TÍTULO'
    t = re.sub(r'\n([A-Z][A-Z0-9 ,.\-:]{6,})\n', r'\n# \1\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t

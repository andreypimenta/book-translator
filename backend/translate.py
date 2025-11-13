import os, time, requests
from .utils import chunk_text

LT_URL = os.getenv("LT_URL", "https://libretranslate.com/translate")
LT_API_KEY = os.getenv("LT_API_KEY", "")

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "book-translator/1.0"
}

def _call_lt_json(text: str, source: str, target: str) -> str:
    # payload JSON (algumas instâncias exigem JSON em vez de form)
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }
    if LT_API_KEY:
        payload["api_key"] = LT_API_KEY
    r = requests.post(LT_URL, json=payload, headers=HEADERS, timeout=180)
    # tratar códigos de erro de forma descritiva
    if r.status_code >= 400:
        raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text[:240]}", response=r)
    js = r.json()
    if isinstance(js, dict) and "translatedText" in js:
        return js["translatedText"]
    # Alguns servidores retornam lista
    if isinstance(js, list) and js and isinstance(js[0], dict) and "translatedText" in js[0]:
        return js[0]["translatedText"]
    return str(js)

def _translate_with_fallback(text: str, source: str, target: str, depth: int = 0) -> str:
    """
    Tenta traduzir; se receber 400 (payload inválido), divide o texto e traduz recursivamente.
    Evita loops infinitos com profundidade limitada.
    """
    try:
        return _call_lt_json(text, source, target)
    except requests.HTTPError as e:
        # 400 geralmente é "payload" problemático (muito grande / caracteres especiais)
        if e.response is not None and e.response.status_code == 400 and len(text) > 200 and depth < 6:
            mid = len(text) // 2
            left = _translate_with_fallback(text[:mid], source, target, depth + 1)
            right = _translate_with_fallback(text[mid:], source, target, depth + 1)
            return left + right
        # 429/5xx → retry com backoff
        status = e.response.status_code if e.response is not None else None
        if status in (429, 500, 502, 503, 504):
            delay = min(2 ** (depth + 1), 16)
            time.sleep(delay)
            return _translate_with_fallback(text, source, target, depth + 1)
        # outros erros → repassa
        raise
    except Exception:
        # fallback genérico: tenta quebrar se for muito grande
        if len(text) > 200 and depth < 6:
            mid = len(text) // 2
            left = _translate_with_fallback(text[:mid], source, target, depth + 1)
            right = _translate_with_fallback(text[mid:], source, target, depth + 1)
            return left + right
        raise

def libre_translate(text: str, source="en", target="pt") -> str:
    # chunks pequenos para reduzir chance de 400/413/timeout
    out = []
    for ch in chunk_text(text, 1000):
        ch = ch.strip()
        if not ch:
            continue
        translated = _translate_with_fallback(ch, source, target, depth=0)
        out.append(translated)
        # pequeno delay para não saturar a instância pública
        time.sleep(0.2)
    return "\n".join(out)

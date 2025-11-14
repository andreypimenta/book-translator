import time, requests
from .utils import chunk_text

LT_URL = "https://libretranslate.de/translate"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def _call_lt(text, source, target):
    payload = {"q": text, "source": source, "target": target, "format": "text"}
    r = requests.post(LT_URL, json=payload, headers=HEADERS, timeout=60)
    if r.status_code >= 400:
        raise Exception(f"Error {r.status_code}: {r.text[:200]}")
    return r.json().get("translatedText", "")

def libre_translate(text, source="en", target="pt"):
    out = []
    for chunk in chunk_text(text, 900):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            translated = _call_lt(chunk, source, target)
        except:
            mid = len(chunk) // 2
            translated = libre_translate(chunk[:mid]) + libre_translate(chunk[mid:])
        out.append(translated)
        time.sleep(0.3)
    return "\n".join(out)

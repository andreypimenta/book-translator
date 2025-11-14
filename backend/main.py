from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import tempfile, shutil, requests

from .extract import extract_text_from_pdf
from .translate import libre_translate
from .organize import organize_text

app = FastAPI(title="Book Translator", version="0.2.0")

# ========================
# CORS
# ========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois pode restringir p/ domínio do front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# HELPERS
# ========================
def _process_pdf_file(path: str, lang_source: str, lang_target: str, organize: bool):
    original_text = extract_text_from_pdf(path)
    if not original_text.strip():
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto do PDF")

    translated = libre_translate(original_text, source=lang_source, target=lang_target)

    if organize:
        translated = organize_text(translated)

    return {"original_text": original_text, "translated_text": translated}

# ========================
# ROTAS
# ========================

@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- ROTA ANTIGA (COMPATÍVEL) ----------
@app.post("/upload")
async def upload_legacy(
    file: UploadFile = File(...),
    lang_source: str = Form("en"),
    lang_target: str = Form("pt"),
    organize: bool = Form(True),
):
    """
    Rota original /upload (mantida por compatibilidade).
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    return _process_pdf_file(temp_path, lang_source, lang_target, organize)

# ---------- NOVO: /upload_file ----------
@app.post("/upload_file")
async def upload_file(
    file: UploadFile = File(...),
    lang_source: str = Form("en"),
    lang_target: str = Form("pt"),
    organize: bool = Form(True),
):
    """
    Rota usada pelo frontend React:

    formData.append('file', file);
    formData.append('lang_source', 'en');
    formData.append('lang_target', 'pt');
    formData.append('organize', 'true');
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    return _process_pdf_file(temp_path, lang_source, lang_target, organize)

# ---------- NOVO: /upload_url ----------
@app.post("/upload_url")
async def upload_url(
    data: dict = Body(...)
):
    """
    Espera JSON:
    {
      "url": "https://...",
      "lang_source": "en",
      "lang_target": "pt",
      "organize": true
    }
    """
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Campo 'url' é obrigatório")

    lang_source = data.get("lang_source", "en")
    lang_target = data.get("lang_target", "pt")
    organize = bool(data.get("organize", True))

    resp = requests.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="URL inválida ou inacessível")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(resp.content)
        temp_path = tmp.name

    return _process_pdf_file(temp_path, lang_source, lang_target, organize)

# ---------- WEBHOOK WHATSAPP (STUB) ----------
@app.post("/webhook/whatsapp/connection-update")
async def whatsapp_webhook_stub(payload: dict = Body(None)):
    # Mantido só pra não quebrar nada que eventualmente use essa rota
    return {"ok": True}

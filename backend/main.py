from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import tempfile, shutil, requests
from sqlalchemy.orm import Session

from .extract import extract_text_from_pdf
from .translate import libre_translate
from .organize import organize_text
from .db import Base, engine, SessionLocal
from .models import Translation
from .schemas import TranslationOut, URLRequest

Base.metadata.create_all(bind=engine)

app = FastAPI()

# ========== CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # em produção, pode restringir p/ domínio do front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== DB DEPENDENCY ==========
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== ENDPOINTS ==========

@app.post("/upload_file", response_model=TranslationOut)
async def upload_file(
    file: UploadFile = File(...),
    lang_source: str = Form("en"),
    lang_target: str = Form("pt"),
    organize: bool = Form(True),
    db: Session = Depends(get_db),
):
    """
    Recebe um PDF via multipart/form-data:
      - file
      - lang_source (ex: 'en')
      - lang_target (ex: 'pt')
      - organize (true/false)
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    original_text = extract_text_from_pdf(temp_path)
    if not original_text.strip():
        raise HTTPException(400, "Não foi possível extrair texto do PDF")

    translated = libre_translate(original_text, source=lang_source, target=lang_target)

    if organize:
        translated = organize_text(translated)

    entry = Translation(original_text=original_text, translated_text=translated)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.post("/upload_url", response_model=TranslationOut)
async def upload_url(
    payload: URLRequest,
    db: Session = Depends(get_db),
):
    """
    Espera JSON no formato:
    {
      "url": "...",
      "lang_source": "en",
      "lang_target": "pt",
      "organize": true
    }
    """
    r = requests.get(payload.url)
    if r.status_code != 200:
        raise HTTPException(400, "URL inválida ou inacessível")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(r.content)
        temp_path = tmp.name

    original_text = extract_text_from_pdf(temp_path)
    if not original_text.strip():
        raise HTTPException(400, "Não foi possível extrair texto do PDF")

    translated = libre_translate(original_text, source=payload.lang_source, target=payload.lang_target)

    if payload.organize:
        translated = organize_text(translated)

    entry = Translation(original_text=original_text, translated_text=translated)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get("/translations", response_model=list[TranslationOut])
def list_translations(db: Session = Depends(get_db)):
    return db.query(Translation).all()


@app.get("/translations/{id}", response_model=TranslationOut)
def get_translation(id: int, db: Session = Depends(get_db)):
    entry = db.query(Translation).filter(Translation.id == id).first()
    if not entry:
        raise HTTPException(404, "Not found")
    return entry

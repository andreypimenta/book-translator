from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile, shutil
from backend.extract import extract_text_from_pdf
from backend.translate import libre_translate
from backend.organize import organize_text

app = FastAPI()

# ================================
#            CORS
# ================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # pode trocar depois pela URL do seu app Lovable/Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
#            ENDPOINT
# ================================
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    organize: bool = Form(False),
    lang_source: str = Form("en"),
    lang_target: str = Form("pt")
):
    # criar temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    # extrair texto
    text_org = extract_text_from_pdf(temp_path)

    # traduzir
    translated = libre_translate(text_org, source=lang_source, target=lang_target)

    # organizar
    if organize:
        translated = organize_text(translated)

    return {"output_text": translated}

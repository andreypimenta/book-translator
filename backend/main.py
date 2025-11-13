import os, tempfile, traceback
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from .ocr import perform_ocr
from .extract import extract_text_from_pdf
from .organize import heuristic_organize
from .translate import libre_translate
from .utils import safe_filename

app = FastAPI(title="Book Translator 0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

def _cleanup(path: str):
    try:
        os.remove(path)
    except Exception:
        pass

@app.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    organize: bool = Form(True),
    lang_source: str = Form("en"),
    lang_target: str = Form("pt"),
    translate: bool = Form(True)   # permite pular tradução
):
    try:
        if not file.filename.lower().endswith(".pdf"):
            return JSONResponse({"error": "Envie um PDF"}, status_code=400)

        # Use um diretório temporário apenas para processamento intermediário
        with tempfile.TemporaryDirectory() as tmp_proc:
            src_pdf = Path(tmp_proc) / safe_filename(file.filename)
            with open(src_pdf, "wb") as f:
                f.write(await file.read())

            # (OCR desativado por enquanto; perform_ocr apenas devolve src_pdf)
            ocr_pdf = Path(tmp_proc) / f"{src_pdf.stem}_ocr.pdf"
            pdf_for_text = perform_ocr(src_pdf, ocr_pdf)

            raw_text = extract_text_from_pdf(str(pdf_for_text))
            if not raw_text.strip():
                return JSONResponse(
                    {"error":"Extração vazia. O PDF pode ser apenas imagem/escaneado ou protegido."},
                    status_code=422
                )

            text_org = heuristic_organize(raw_text) if organize else raw_text

        # Agora, crie o ARQUIVO FINAL fora do TemporaryDirectory, com delete=False
        suffix = f"_translated_{lang_target}.txt" if translate else "_extracted.txt"
        ntf = tempfile.NamedTemporaryFile(prefix="book_", suffix=suffix, delete=False)
        out_path = ntf.name
        ntf.close()

        if translate:
            content = libre_translate(text_org, source=lang_source, target=lang_target)
        else:
            content = text_org

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        # agenda limpeza após enviar o arquivo
        background_tasks.add_task(_cleanup, out_path)
        filename = Path(safe_filename(file.filename)).stem + suffix
        return FileResponse(out_path, media_type="text/plain", filename=filename)

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)

# silencia 404s externos
@app.post("/webhook/whatsapp/connection-update")
async def whatsapp_webhook_stub():
    return {"status":"ok"}

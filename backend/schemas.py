from pydantic import BaseModel

class TranslationOut(BaseModel):
    id: int
    original_text: str
    translated_text: str

    class Config:
        orm_mode = True

class URLRequest(BaseModel):
    url: str
    lang_source: str = "en"
    lang_target: str = "pt"
    organize: bool = True

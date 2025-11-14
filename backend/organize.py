def organize_text(text: str) -> str:
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return text

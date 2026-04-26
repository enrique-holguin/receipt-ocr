from src.models.receipt import DocumentType

DOCUMENT_KEYWORDS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.YAPE: ("yape",),
}


def classify(text: str) -> DocumentType:
    """Return the DocumentType that matches keywords found in text.

    Args:
        text: Raw OCR text from a receipt image.

    Returns:
        The first matching DocumentType, or DocumentType.UNKNOWN if none match.
    """
    lower = text.lower()
    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return doc_type
    return DocumentType.UNKNOWN

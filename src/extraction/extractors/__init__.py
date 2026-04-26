from collections.abc import Callable
from typing import Any

from src.extraction.extractors.yape import extract_yape
from src.models.receipt import DocumentType

# Single source of truth for supported document types.
# To add a new type: import its extractor above and add an entry here.
EXTRACTORS: dict[DocumentType, Callable[[str], dict[str, Any]]] = {
    DocumentType.YAPE: extract_yape,
}

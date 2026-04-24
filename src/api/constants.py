from types import MappingProxyType

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)

# Maps MIME type → file extension (no leading dot).
ALLOWED_EXTENSIONS: MappingProxyType[str, str] = MappingProxyType(
    {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
)

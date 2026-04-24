# Principios arquitectónicos

## Filosofía Unix aplicada

- **Una responsabilidad por módulo.** Si el nombre del archivo necesita un "y" o "and", se divide.
- **Componer funciones pequeñas.** Preferir `a(b(c(x)))` o pipelines explícitos sobre objetos con muchos métodos que se llaman entre sí.
- **Funciones puras donde se pueda.** Preprocesamiento, parsing, clasificación y normalización son puras: input → output, sin I/O escondido.
- **Side effects aislados.** Disco, red y DB solo en `repositories/` y `services/`. Nunca en `extractors/`, `ocr/`, `schemas/`.
- **Mecanismo separado de política.** El motor OCR no sabe qué es una boleta. El clasificador no sabe leer texto. El extractor no sabe guardar. Cada capa ignora qué pasa antes y después.
- **Interfaces explícitas.** Usar `typing.Protocol` para definir contratos entre capas (ej. `OCREngine`, `DocumentClassifier`, `ReceiptExtractor`). Esto permite intercambiar implementaciones sin tocar el resto.
- **Fallar temprano y ruidosamente.** Validaciones al borde (Pydantic en la API, checks explícitos al entrar a cada función pública). Excepciones específicas, nunca `except Exception: pass`.
- **Datos sobre comportamiento.** Preferir pasar estructuras de datos inmutables (`dataclasses frozen`, Pydantic models) entre capas, en lugar de objetos con métodos que mutan estado.

## Clean code concreto

- **Nombres.** Variables y funciones describen intención, no implementación. `extract_amount` no `parse_s`. Sin abreviaturas oscuras.
- **Funciones cortas.** Apuntar a <20 líneas. Si crece, extraer sub-funciones con nombre.
- **Sin comentarios que expliquen el "qué".** El código se explica solo con buenos nombres. Los comentarios solo para el "por qué" cuando no es obvio.
- **Type hints en todo.** Sin excepciones. `mypy --strict` debe pasar.
- **Docstrings estilo Google** en funciones públicas de módulos.
- **Sin magic numbers/strings.** Constantes nombradas en un módulo `constants.py` por capa.
- **Early returns sobre anidación profunda.** Máximo 2 niveles de anidación.
- **Inmutabilidad por defecto.** `frozen=True` en dataclasses, `tuple` sobre `list` cuando no muta, `Mapping` sobre `dict` en firmas.

## Flujo de datos del proyecto

```
UploadedImage (bytes)
  → PreprocessedImage (ndarray)           [ocr/preprocessor.py — puro]
  → OCRResult (blocks + confidence)        [ocr/engine.py — puro, wrapper sobre PaddleOCR]
  → DocumentType (enum)                    [extractors/classifier.py — puro]
  → ExtractedReceipt (dataclass)           [extractors/{tipo}.py — puro]
  → NormalizedReceipt (Pydantic)           [services/normalizer.py — puro]
  → PersistedReceipt (DB row)              [repositories/ — side effects aquí]
```

Cada flecha es una función con firma explícita. Ninguna función salta pasos.

## Protocolos principales

Definir en `src/core/protocols.py`:

- `OCREngine`: `process(image: bytes) -> OCRResult`
- `DocumentClassifier`: `classify(ocr_result: OCRResult) -> DocumentType`
- `ReceiptExtractor`: `extract(ocr_result: OCRResult) -> ExtractedReceipt`

Las implementaciones concretas viven en sus módulos; las capas superiores dependen del protocolo, no de la implementación.

## Reglas de testing

- Tests unitarios para cada función pura, sin mocks.
- Tests de integración para las capas con side effects, usando DB de test real (no mocks de SQLAlchemy).
- Fixtures de imágenes reales anonimizadas en `tests/fixtures/images/`.
- Coverage mínimo aceptable: 80% global, 95% en `extractors/` y `ocr/`.

## Prohibido

- Clases con más de 5 métodos públicos.
- Funciones con más de 4 parámetros posicionales (usar dataclass de input si hacen falta más).
- Herencia de más de 1 nivel. Preferir composición y Protocols.
- Imports circulares (si aparecen, es señal de mala separación de capas).
- `print()` en código productivo. Solo `logging`.
- Dependencias entre módulos de la misma capa (ej. `extractors/yape.py` no importa de `extractors/plin.py`).

# Local Extraction

`llm_wiki.ingest` is a framework service. `llm-wiki ingest` does not call it yet.

```text
source -> detect -> extract -> quality gate -> derived/extraction -> manifest
```

The service reads local files only. It does not call a cloud API, an LLM, or an OCR engine. Images and PDFs without a meaningful text layer are marked `ocr_needed`. An `OcrProvider` argument is accepted and ignored until a later stage.

## Outputs

Given an output directory, a run writes only under that directory:

```text
derived/extraction/
├── text/         clean and review extracts
├── rejected/     short reason files for rejected inputs
└── manifests/extraction.json
```

Source files are not modified. Nothing is written to `wiki/`. Re-running the same inputs replaces the same output paths. If two names sanitize to one path, the later file gets a `-2`, `-3`, ... suffix. Paths in the manifest are relative to the output directory. Absolute paths, usernames, and extracted body text are not stored in the manifest.

`derived/` is rebuildable and not canonical.

## Statuses

| Status | Meaning |
|---|---|
| `clean` | Readable extract with enough Unicode letters or digits to keep. |
| `review` | Readable, but short. |
| `reject` | Binary signatures, empty text, or too many control/replacement characters. |
| `ocr_needed` | Image, or a PDF/DOCX/PPTX with no meaningful text layer. |
| `skip` | Extension this stage does not extract. |
| `error` | The local extractor raised. |

The quality gate counts Unicode alphanumeric characters. It does not require English or Latin text. Thresholds live in `src/llm_wiki/ingest/quality.py`.

Text-like files are also sniffed for JPEG, PNG, ZIP, `[Content_Types].xml`, and `ppt/slides` bytes. A `.md` file that contains those bytes is `reject`, not clean Markdown.

## Readers

- Markdown and text: UTF-8, with replacement characters if decoding fails, then the quality gate.
- PDF: `pypdf`.
- DOCX: `python-docx`.
- PPTX: slide text from the package XML, kept behind `## Slide N` headings. No extra dependency.

## Entry point

```python
from llm_wiki.ingest import extract_sources

extract_sources(source_path, output_dir)
```

`source_path` may be a file or a directory. Directory walks are recursive.

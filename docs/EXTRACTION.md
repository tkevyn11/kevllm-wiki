# Local Extraction

`llm_wiki.ingest` is a framework service. `llm-wiki ingest` uses it only when you pass `--extract`. Without that flag, ingest keeps the frozen baseline: every file becomes a note, and `work/ingest-manifest.jsonl` still records an absolute input path.

```text
source -> detect -> extract -> quality gate -> derived/extraction -> manifest
```

The service reads local files only. It does not call a cloud API or an LLM. Images and PDFs without a meaningful text layer are marked `ocr_needed` unless the caller passes an `OcrProvider`. `llm-wiki ingest --extract` does not pass one. `llm-wiki ingest --extract --ocr` passes the local PaddleOCR provider.

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

## Ingest integration

```bash
llm-wiki ingest path/to/sample-paper.md --extract
llm-wiki ingest path/to/folder --extract
```

| Status | Wiki note | What you see |
|---|---|---|
| `clean` | Created from the extracted text | `Clean: created note <id>` |
| `review` | Not created | `Review: ... requires review` |
| `ocr_needed` | Not created | `OCR needed: ...` OCR was not requested, or this file type has no OCR path |
| `skip` | Not created | `Skipped: ...` |
| `reject` | Not created | `Rejected: ...` and exit 3 |
| `error` | Not created | `Error: ...` and exit 3 |

A mixed directory still processes every file. Exit code `3` means at least one `reject` or `error`. `review`, `ocr_needed`, and `skip` do not by themselves fail the command.

Provenance copies keep their relative path under `raw/`. Note ids still come from the filename stem, with `-2` when that id already exists.

`--extract` writes `derived/extraction/manifests/ingest.jsonl`. Each line is an `extract` event with `schema_version: 1`, a workspace-relative `raw_relative` path, a source-relative path, a sha256, a note id when a note was created, and the extraction status. It does not contain absolute paths. The legacy `ingest` event in `work/ingest-manifest.jsonl` is unchanged and is not written by `--extract`.

`derived/` can be deleted and produced again. `wiki/` remains the canonical store. This path does not upload source files.

## Optional local OCR

```bash
pip install -e .
pip install -e ".[ocr]"
python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

`pip install -e .` is the base tool. `pip install -e ".[ocr]"` installs `paddleocr` and `pymupdf` from this project's optional `ocr` extra. PaddleOCR 3.x still needs a local PaddlePaddle 3.x engine, and that engine is not part of the extra. The command above is the CPU example from the PaddlePaddle install guide. A GPU machine should use the wheel that matches its driver, from that same guide.

```bash
llm-wiki ingest path/to/figure.png --extract --ocr
llm-wiki ingest path/to/scan.pdf --extract --ocr
```

OCR stays off unless both flags are present. `--ocr` alone exits 2. If the packages are missing, the command exits 2 and prints the install lines. It does not pretend the file was skipped.

The flow is: copy into `raw/`, detect the file, OCR images and textless PDFs locally, normalize the text, then run the same Unicode quality gate. `clean` becomes a note. `review` stays in `derived/extraction/text/` until `llm-wiki review approve`. Short or noisy OCR text is not auto-promoted. Ingest has no `--auto-approve-review` flag.

Scanned PDFs are rendered in memory or a temporary file with PyMuPDF and recognized page by page. The extract keeps `## Page N` headings. Poppler is not required. Text-based DOCX and PPTX extraction still works. Image-only DOCX and PPTX stay `ocr_needed`; OCR for those Office files is not included.

The first run can download model weights, so setup may use the network. After those weights are cached, OCR can run offline. The document or image is not sent to an OCR API. Manifests may name the provider (`paddleocr`) and the page count. They do not store cache directories, usernames, or absolute paths.

## Review and promotion

```text
source
  ↓
ingest --extract [--ocr]
  ↓
clean ───────────────→ wiki/
review ──→ review list/show ──→ approve ──→ wiki/
                         └────→ reject
ocr_needed / skip / reject / error
  └──────────────────────────→ no canonical note
```

`wiki/` is canonical. `derived/` stays rebuildable and is not canonical. A `review` extract becomes a note only after `llm-wiki review approve`. `llm-wiki review reject` records the refusal and leaves `wiki/` unchanged. Both decisions are appended to `derived/extraction/manifests/review.jsonl` using the review id, the source-relative path, and the source sha256. No cloud service is involved.

Approval checks that the `raw/` copy still matches the recorded sha256, reads the extracted text, and runs the quality gate again. Readable short text can be approved. Empty or noisy text cannot. The new note keeps the usual required frontmatter and sets `extraction_status: reviewed`. Approving or rejecting the same item again does not create a second note.

## Entry point

```python
from llm_wiki.ingest import extract_sources

extract_sources(source_path, output_dir)
```

`source_path` may be a file or a directory. Directory walks are recursive.

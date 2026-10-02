"""Release-candidate metadata. No network and no OCR models."""

from __future__ import annotations

import tomllib
from pathlib import Path

import llm_wiki


ROOT = Path(__file__).resolve().parents[1]


def test_version_is_0_2_0() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == "0.2.0"
    assert project["project"]["license"] == "MIT"
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("MIT License")
    assert "Copyright (c) 2026 tkevyn11" in license_text
    assert "**License:** MIT" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert llm_wiki.__version__ == "0.2.0"
    assert project["project"]["scripts"]["llm-wiki"] == "llm_wiki.cli:app"
    assert "paddleocr" not in project["project"]["dependencies"]
    assert "paddleocr>=3.0" in project["project"]["optional-dependencies"]["ocr"]
    assert "pymupdf>=1.24.0" in project["project"]["optional-dependencies"]["ocr"]
    assert all("paddlepaddle" not in item for item in project["project"]["optional-dependencies"]["ocr"])


def test_release_notes_name_version_and_deferrals() -> None:
    notes = (ROOT / "docs" / "RELEASE_NOTES_v0.2.0.md").read_text(encoding="utf-8")
    assert "0.2.0" in notes
    assert "review" in notes
    assert "derived/graphify/" in notes
    assert "image-only DOCX" in notes
    assert 'pip install "llm-wiki[ocr]"' in notes

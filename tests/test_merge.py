from pathlib import Path

import fitz
import pytest

from pdftools.operations.registry import get
from pdftools.shared.errors import ValidationError

merge = get("merge")


def _make_pdf(path: Path, pages: int) -> Path:
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Página {i + 1}", fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def test_merge_two_pdfs(tmp_path: Path) -> None:
    a = _make_pdf(tmp_path / "a.pdf", 2)
    b = _make_pdf(tmp_path / "b.pdf", 3)
    out = tmp_path / "merged.pdf"
    result = merge.run(input_pdfs=[a, b], output=out)
    assert out.exists()
    assert len(result.rows) == 2
    doc = fitz.open(str(out))
    assert doc.page_count == 5
    doc.close()


def test_merge_three_pdfs(tmp_path: Path) -> None:
    a = _make_pdf(tmp_path / "a.pdf", 1)
    b = _make_pdf(tmp_path / "b.pdf", 1)
    c = _make_pdf(tmp_path / "c.pdf", 1)
    out = tmp_path / "merged.pdf"
    merge.run(input_pdfs=[a, b, c], output=out)
    doc = fitz.open(str(out))
    assert doc.page_count == 3
    doc.close()


def test_merge_requires_two_files(tmp_path: Path) -> None:
    a = _make_pdf(tmp_path / "a.pdf", 1)
    with pytest.raises(ValidationError):
        merge.run(input_pdfs=[a], output=tmp_path / "out.pdf")

from pathlib import Path

import fitz
import pytest

from pdftools.operations.registry import get
from pdftools.shared.errors import PdfToolsError

html2pdf = get("html2pdf")


def _weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _weasyprint_available(),
    reason="WeasyPrint requer bibliotecas nativas (GTK) ausentes neste ambiente",
)
def test_html_file_to_pdf(sample_html: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    html2pdf.run(source=str(sample_html), output=out)
    assert out.exists()
    assert out.stat().st_size > 0
    doc = fitz.open(str(out))
    assert doc.page_count >= 1
    doc.close()


def test_missing_html_file_raises(tmp_path: Path) -> None:
    with pytest.raises(PdfToolsError):
        html2pdf.run(source=str(tmp_path / "nonexistent.html"), output=tmp_path / "out.pdf")

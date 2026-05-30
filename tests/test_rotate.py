from pathlib import Path

import fitz
import pytest

from pdftools.operations.registry import get
from pdftools.shared.errors import ValidationError

rotate = get("rotate")


def test_rotate_all_pages(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "rotated.pdf"
    rotate.run(input_pdf=sample_pdf, degrees=90, output=out)
    assert out.exists()
    doc = fitz.open(str(out))
    for page in doc:
        assert page.rotation == 90
    doc.close()


def test_rotate_specific_pages(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "rotated.pdf"
    rotate.run(input_pdf=sample_pdf, degrees=180, pages="1,3", output=out)
    doc = fitz.open(str(out))
    assert doc[0].rotation == 180
    assert doc[1].rotation == 0
    assert doc[2].rotation == 180
    doc.close()


def test_rotate_invalid_angle(sample_pdf: Path, tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        rotate.run(input_pdf=sample_pdf, degrees=45, output=tmp_path / "out.pdf")


def test_rotate_default_output(sample_pdf: Path) -> None:
    rotate.run(input_pdf=sample_pdf, degrees=90)
    expected = sample_pdf.parent / f"{sample_pdf.stem}_rotated.pdf"
    assert expected.exists()

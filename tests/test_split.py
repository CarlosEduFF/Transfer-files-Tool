from pathlib import Path

import fitz
import pytest

from pdftools.operations.registry import get
from pdftools.shared.errors import ValidationError

split = get("split")
split_parts = get("split-parts")


def test_split_range(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "split.pdf"
    result = split.run(input_pdf=sample_pdf, pages="1-3", output=out)
    assert out.exists()
    assert result.outputs == [out]
    doc = fitz.open(str(out))
    assert doc.page_count == 3
    doc.close()


def test_split_individual_pages(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "split.pdf"
    split.run(input_pdf=sample_pdf, pages="1,3,5", output=out)
    doc = fitz.open(str(out))
    assert doc.page_count == 3
    doc.close()


def test_split_mixed_range(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "split.pdf"
    split.run(input_pdf=sample_pdf, pages="1-2,5", output=out)
    doc = fitz.open(str(out))
    assert doc.page_count == 3
    doc.close()


def test_split_invalid_range(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "split.pdf"
    with pytest.raises(ValidationError):
        split.run(input_pdf=sample_pdf, pages="1-99", output=out)


def test_split_default_output(sample_pdf: Path) -> None:
    result = split.run(input_pdf=sample_pdf, pages="1-2")
    expected = sample_pdf.parent / f"{sample_pdf.stem}_split.pdf"
    assert expected.exists()
    assert result.outputs == [expected]
    doc = fitz.open(str(expected))
    assert doc.page_count == 2
    doc.close()


def test_split_into_parts_from_string(sample_pdf: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "partes"
    result = split_parts.run(input_pdf=sample_pdf, ranges="1-2;3-5", output_dir=out_dir)
    assert len(result.outputs) == 2
    counts = [fitz.open(str(p)).page_count for p in result.outputs]
    assert counts == [2, 3]


def test_split_into_parts_from_tuples(sample_pdf: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "partes"
    result = split_parts.run(
        input_pdf=sample_pdf, ranges=[(1, 1), (2, 4), (5, 5)], output_dir=out_dir
    )
    assert len(result.outputs) == 3


def test_split_into_parts_invalid(sample_pdf: Path, tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        split_parts.run(input_pdf=sample_pdf, ranges="1-99", output_dir=tmp_path)

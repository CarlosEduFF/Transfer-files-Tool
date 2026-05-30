from pathlib import Path

from pdftools.operations.registry import get
from pdftools.presentation.console import console

extract_text = get("extract-text")


def test_extract_text_fitz_returns_text(sample_pdf: Path) -> None:
    result = extract_text.run(input_pdf=sample_pdf, backend="fitz")
    assert not result.saved
    assert "Página" in result.text


def test_extract_text_render_to_console(sample_pdf: Path, capsys) -> None:
    result = extract_text.run(input_pdf=sample_pdf, backend="fitz")
    extract_text.render(result, console)
    captured = capsys.readouterr()
    assert "Página" in captured.out


def test_extract_text_fitz_to_file(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "text.txt"
    result = extract_text.run(input_pdf=sample_pdf, backend="fitz", output=out)
    assert result.saved
    assert out.exists()
    assert len(out.read_text(encoding="utf-8")) > 0


def test_extract_text_page_range(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "text.txt"
    extract_text.run(input_pdf=sample_pdf, pages="1-2", backend="fitz", output=out)
    content = out.read_text(encoding="utf-8")
    assert "Página 1" in content
    assert "Página 3" not in content


def test_extract_text_pdfplumber(sample_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "text.txt"
    extract_text.run(input_pdf=sample_pdf, backend="pdfplumber", output=out)
    assert out.exists()
    assert out.stat().st_size > 0

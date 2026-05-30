from pathlib import Path

import fitz

from pdftools.operations.registry import get

compress = get("compress")


def _make_large_pdf(path: Path) -> Path:
    doc = fitz.open()
    for i in range(10):
        page = doc.new_page()
        for j in range(20):
            page.insert_text((72, 72 + j * 20), f"Linha {j} da página {i + 1} com bastante texto de exemplo para gerar conteúdo.", fontsize=10)
    doc.save(str(path))
    doc.close()
    return path


def test_compress_produces_valid_pdf(tmp_path: Path) -> None:
    src = _make_large_pdf(tmp_path / "large.pdf")
    out = tmp_path / "compressed.pdf"
    compress.run(input_pdf=src, output=out)
    assert out.exists()
    doc = fitz.open(str(out))
    assert doc.page_count == 10
    doc.close()


def test_compress_default_output(tmp_path: Path) -> None:
    src = _make_large_pdf(tmp_path / "large.pdf")
    compress.run(input_pdf=src)
    expected = tmp_path / "large_compressed.pdf"
    assert expected.exists()

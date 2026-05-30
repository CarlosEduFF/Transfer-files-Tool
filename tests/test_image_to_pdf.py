from pathlib import Path

import fitz
import pytest
from PIL import Image

from pdftools.operations.registry import get
from pdftools.shared.errors import PdfToolsError

img2pdf = get("img2pdf")


def _make_image(path: Path, color: tuple = (255, 0, 0)) -> Path:
    img = Image.new("RGB", (100, 100), color=color)
    img.save(str(path))
    return path


def test_single_image_to_pdf(tmp_path: Path) -> None:
    img = _make_image(tmp_path / "img.png")
    out = tmp_path / "out.pdf"
    img2pdf.run(images=[img], output=out)
    assert out.exists()
    doc = fitz.open(str(out))
    assert doc.page_count == 1
    doc.close()


def test_multiple_images_to_pdf(tmp_path: Path) -> None:
    imgs = [_make_image(tmp_path / f"img{i}.png", (i * 40, 100, 200)) for i in range(3)]
    out = tmp_path / "out.pdf"
    img2pdf.run(images=imgs, output=out)
    doc = fitz.open(str(out))
    assert doc.page_count == 3
    doc.close()


def test_unsupported_format_raises(tmp_path: Path) -> None:
    fake = tmp_path / "file.xyz"
    fake.write_bytes(b"fake")
    with pytest.raises(PdfToolsError):
        img2pdf.run(images=[fake], output=tmp_path / "out.pdf")


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(PdfToolsError):
        img2pdf.run(images=[tmp_path / "nonexistent.png"], output=tmp_path / "out.pdf")

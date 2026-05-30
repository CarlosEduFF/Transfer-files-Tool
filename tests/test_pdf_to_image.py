from pathlib import Path

from pdftools.operations.registry import get

pdf2img = get("pdf2img")


def test_pdf_to_png(sample_pdf: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "images"
    pdf2img.run(input_pdf=sample_pdf, fmt="png", dpi=72, output_dir=out_dir)
    images = list(out_dir.glob("*.png"))
    assert len(images) == 5


def test_pdf_to_jpg(sample_pdf: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "images"
    pdf2img.run(input_pdf=sample_pdf, fmt="jpg", dpi=72, output_dir=out_dir)
    images = list(out_dir.glob("*.jpg"))
    assert len(images) == 5


def test_pdf_to_image_page_range(sample_pdf: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "images"
    pdf2img.run(input_pdf=sample_pdf, fmt="png", dpi=72, pages="1-3", output_dir=out_dir)
    images = list(out_dir.glob("*.png"))
    assert len(images) == 3


def test_pdf_to_image_creates_dir(sample_pdf: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "nested" / "dir"
    assert not out_dir.exists()
    pdf2img.run(input_pdf=sample_pdf, fmt="png", dpi=72, pages="1", output_dir=out_dir)
    assert out_dir.exists()
    assert len(list(out_dir.glob("*.png"))) == 1

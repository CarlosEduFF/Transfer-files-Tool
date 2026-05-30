from pathlib import Path

import fitz
import pytest
from PIL import Image


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    for i in range(5):
        page = doc.new_page()
        page.insert_text((72, 72), f"Página {i + 1} de exemplo", fontsize=16)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    img_path = tmp_path / "sample.png"
    img = Image.new("RGB", (200, 200), color=(100, 150, 200))
    img.save(str(img_path))
    return img_path


@pytest.fixture
def sample_html(tmp_path: Path) -> Path:
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        "<html><body><h1>Teste PDF Tools</h1><p>Conteúdo de exemplo.</p></body></html>",
        encoding="utf-8",
    )
    return html_path

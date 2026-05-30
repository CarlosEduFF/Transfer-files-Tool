import json
from pathlib import Path

from pdftools.operations.registry import get
from pdftools.presentation.console import console

metadata = get("metadata")


def test_metadata_data(sample_pdf: Path) -> None:
    result = metadata.run(input_pdf=sample_pdf, fmt="table")
    assert result.data["páginas"] == 5
    assert result.data["arquivo"] == sample_pdf.name


def test_metadata_table_render(sample_pdf: Path, capsys) -> None:
    result = metadata.run(input_pdf=sample_pdf, fmt="table")
    metadata.render(result, console)
    captured = capsys.readouterr()
    assert "páginas" in captured.out.lower()


def test_metadata_json_render(sample_pdf: Path, capsys) -> None:
    result = metadata.run(input_pdf=sample_pdf, fmt="json")
    metadata.render(result, console)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["páginas"] == 5


def test_metadata_contains_filename(sample_pdf: Path, capsys) -> None:
    result = metadata.run(input_pdf=sample_pdf, fmt="table")
    metadata.render(result, console)
    captured = capsys.readouterr()
    assert sample_pdf.name in captured.out

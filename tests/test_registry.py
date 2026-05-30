from pdftools.operations.base import Operation, Param
from pdftools.operations.registry import all as all_operations
from pdftools.operations.registry import get

EXPECTED = {
    "split", "split-parts", "merge", "compress", "rotate",
    "pdf2img", "img2pdf", "html2pdf", "extract-text", "metadata",
}


def test_all_expected_operations_registered() -> None:
    names = {op.name for op in all_operations()}
    assert EXPECTED <= names


def test_names_are_unique() -> None:
    names = [op.name for op in all_operations()]
    assert len(names) == len(set(names))


def test_get_returns_operation() -> None:
    op = get("split")
    assert isinstance(op, Operation)
    assert op.name == "split"


def test_get_unknown_raises() -> None:
    import pytest

    with pytest.raises(KeyError):
        get("does-not-exist")


def test_every_operation_has_metadata_and_params() -> None:
    for op in all_operations():
        assert op.name
        assert op.help
        assert op.menu_label
        assert isinstance(op.params, list)
        for p in op.params:
            assert isinstance(p, Param)
            assert p.name
            assert p.help

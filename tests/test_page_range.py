import pytest

from pdftools.shared.errors import ValidationError
from pdftools.shared.page_range import parse_page_range


def test_simple_range() -> None:
    assert parse_page_range("1-3", 10) == [0, 1, 2]


def test_individual_pages() -> None:
    assert parse_page_range("1,3,5", 10) == [0, 2, 4]


def test_mixed() -> None:
    assert parse_page_range("1-2,5", 10) == [0, 1, 4]


def test_dedup_preserves_order() -> None:
    assert parse_page_range("3,1-3", 10) == [2, 0, 1]


def test_out_of_bounds() -> None:
    with pytest.raises(ValidationError):
        parse_page_range("1-99", 10)


def test_zero_invalid() -> None:
    with pytest.raises(ValidationError):
        parse_page_range("0", 10)


def test_non_numeric() -> None:
    with pytest.raises(ValidationError):
        parse_page_range("a-b", 10)


def test_reversed_range_invalid() -> None:
    with pytest.raises(ValidationError):
        parse_page_range("5-2", 10)

import pytest

from app.errors import ValidationError
from app.validators import validate_barcode, validate_new_item, validate_price, validate_stock, validate_update


@pytest.mark.parametrize("bad", ["5", -1, True, None, float("nan")])
def test_invalid_prices(bad):
    with pytest.raises(ValidationError):
        validate_price(bad)


@pytest.mark.parametrize("bad", [1.5, "3", -2, True, None])
def test_invalid_stock(bad):
    with pytest.raises(ValidationError):
        validate_stock(bad)


@pytest.mark.parametrize("bad", ["abc", "123", "1234567890123456", 12345678])
def test_invalid_barcodes(bad):
    with pytest.raises(ValidationError):
        validate_barcode(bad)


def test_price_is_rounded():
    assert validate_price(2.499) == 2.5


def test_new_item_defaults():
    data = validate_new_item({"product_name": "  Tea  "})
    assert data["product"]["product_name"] == "Tea"
    assert data["price"] == 0 and data["stock"] == 0 and data["barcode"] == ""


def test_new_item_requires_name():
    with pytest.raises(ValidationError):
        validate_new_item({"price": 2})


def test_update_rejects_empty_and_unknown():
    with pytest.raises(ValidationError):
        validate_update({})
    with pytest.raises(ValidationError):
        validate_update({"colour": "red"})

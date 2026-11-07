"""Tests for the OpenFoodFacts client with requests.get mocked."""
from unittest.mock import MagicMock, patch

import pytest
import requests

from app import openfoodfacts as off
from app.errors import ExternalAPIError, ProductNotFoundError, ValidationError


def fake_response(status_code=200, json_data=None, bad_json=False):
    response = MagicMock(status_code=status_code)
    if bad_json:
        response.json.side_effect = ValueError("bad json")
    else:
        response.json.return_value = json_data
    return response


PRODUCT_PAYLOAD = {
    "status": 1,
    "product": {"product_name": "Organic Almond Milk", "brands": "Silk",
                "ingredients_text": "Filtered water, almonds", "nutriscore_grade": None},
}


@patch("app.openfoodfacts.requests.get")
def test_get_by_barcode_success(mock_get):
    mock_get.return_value = fake_response(200, PRODUCT_PAYLOAD)
    result = off.get_product_by_barcode("025293002029")
    assert result["status"] == 1 and result["barcode"] == "025293002029"
    assert result["product"]["product_name"] == "Organic Almond Milk"
    assert result["product"]["nutriscore_grade"] == ""  # None normalised
    assert "025293002029" in mock_get.call_args.args[0]
    assert mock_get.call_args.kwargs["timeout"] == off.TIMEOUT


@patch("app.openfoodfacts.requests.get")
def test_get_by_barcode_not_found(mock_get):
    mock_get.return_value = fake_response(200, {"status": 0, "status_verbose": "product not found"})
    with pytest.raises(ProductNotFoundError):
        off.get_product_by_barcode("00000000")


@patch("app.openfoodfacts.requests.get")
def test_invalid_barcode_never_calls_api(mock_get):
    with pytest.raises(ValidationError):
        off.get_product_by_barcode("abc")
    mock_get.assert_not_called()


@patch("app.openfoodfacts.requests.get", side_effect=requests.exceptions.Timeout)
def test_timeout_maps_to_504(_mock):
    with pytest.raises(ExternalAPIError) as exc:
        off.get_product_by_barcode("12345678")
    assert exc.value.status_code == 504


@patch("app.openfoodfacts.requests.get", side_effect=requests.exceptions.ConnectionError)
def test_connection_error_maps_to_502(_mock):
    with pytest.raises(ExternalAPIError) as exc:
        off.get_product_by_barcode("12345678")
    assert exc.value.status_code == 502


@patch("app.openfoodfacts.requests.get")
def test_http_error_status_maps_to_502(mock_get):
    mock_get.return_value = fake_response(500, {})
    with pytest.raises(ExternalAPIError) as exc:
        off.get_product_by_barcode("12345678")
    assert exc.value.status_code == 502


@patch("app.openfoodfacts.requests.get")
def test_invalid_json_maps_to_502(mock_get):
    mock_get.return_value = fake_response(200, bad_json=True)
    with pytest.raises(ExternalAPIError):
        off.get_product_by_barcode("12345678")


@patch("app.openfoodfacts.requests.get")
def test_search_success_filters_nameless_products(mock_get):
    mock_get.return_value = fake_response(200, {"products": [
        {"code": "111", "product_name": "Almond Milk", "brands": "Silk"},
        {"code": "222", "product_name": ""},
        {"code": "333", "product_name": "Almond Drink"},
    ]})
    results = off.search_products_by_name("almond", limit=5)
    assert [r["barcode"] for r in results] == ["111", "333"]
    assert mock_get.call_args.kwargs["params"]["search_terms"] == "almond"


@patch("app.openfoodfacts.requests.get")
def test_search_no_results(mock_get):
    mock_get.return_value = fake_response(200, {"products": []})
    with pytest.raises(ProductNotFoundError):
        off.search_products_by_name("zzzzzz")


@patch("app.openfoodfacts.requests.get")
def test_search_blank_name(mock_get):
    with pytest.raises(ValidationError):
        off.search_products_by_name("   ")
    mock_get.assert_not_called()


@patch("app.openfoodfacts.requests.get", side_effect=requests.exceptions.Timeout)
def test_search_timeout(_mock):
    with pytest.raises(ExternalAPIError):
        off.search_products_by_name("milk")

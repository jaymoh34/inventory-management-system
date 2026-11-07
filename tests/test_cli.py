"""Tests for CLI commands. HTTP calls to the Flask API are mocked."""
from unittest.mock import MagicMock, patch

import pytest
import requests

import cli

ITEM = {
    "id": 1, "barcode": "025293002029", "status": 1, "source": "mock",
    "product": {"product_name": "Organic Almond Milk", "brands": "Silk",
                "ingredients_text": "Filtered water, almonds", "categories": "Beverages",
                "quantity": "1 L", "nutriscore_grade": "b"},
    "price": 3.99, "stock": 25,
}
EXTERNAL = {"status": 1, "barcode": "12345678",
            "product": {"product_name": "Found Product", "brands": "Acme",
                        "ingredients_text": "Stuff", "categories": "Misc", "nutriscore_grade": "a"}}


def fake_response(status=200, data=None):
    response = MagicMock(status_code=status)
    response.json.return_value = data
    return response


@pytest.fixture(autouse=True)
def default_url(monkeypatch):
    monkeypatch.delenv("INVENTORY_API_URL", raising=False)


@patch("cli.requests.request")
def test_list(mock_req, capsys):
    mock_req.return_value = fake_response(200, {"count": 1, "items": [ITEM]})
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "Organic Almond Milk" in out and "1 item(s)" in out
    assert mock_req.call_args.args == ("GET", "http://127.0.0.1:5000/inventory")


@patch("cli.requests.request")
def test_list_with_search(mock_req):
    mock_req.return_value = fake_response(200, {"count": 0, "items": []})
    cli.main(["list", "--search", "tea"])
    assert mock_req.call_args.kwargs["params"] == {"search": "tea"}


@patch("cli.requests.request")
def test_view(mock_req, capsys):
    mock_req.return_value = fake_response(200, ITEM)
    assert cli.main(["view", "1"]) == 0
    out = capsys.readouterr().out
    assert "Silk" in out and "3.99" in out and "Filtered water" in out
    assert mock_req.call_args.args == ("GET", "http://127.0.0.1:5000/inventory/1")


@patch("cli.requests.request")
def test_view_not_found_shows_error(mock_req, capsys):
    mock_req.return_value = fake_response(404, {"error": "Item 9 not found"})
    assert cli.main(["view", "9"]) == 1
    assert "Item 9 not found" in capsys.readouterr().err


@patch("cli.requests.request")
def test_add_sends_only_given_fields(mock_req, capsys):
    mock_req.return_value = fake_response(201, ITEM)
    assert cli.main(["add", "--name", "Green Tea", "--price", "4.5", "--stock", "20"]) == 0
    assert mock_req.call_args.args[0] == "POST"
    assert mock_req.call_args.kwargs["json"] == {"product_name": "Green Tea", "price": 4.5, "stock": 20}
    assert "Added item 1" in capsys.readouterr().out


@patch("cli.requests.request")
def test_add_shows_server_validation_error(mock_req, capsys):
    mock_req.return_value = fake_response(400, {"error": "price must be zero or greater"})
    assert cli.main(["add", "--name", "X", "--price", "-1"]) == 1
    assert "price must be zero or greater" in capsys.readouterr().err


def test_add_requires_name():
    with pytest.raises(SystemExit):
        cli.main(["add", "--price", "2"])


def test_non_numeric_price_rejected_by_parser():
    with pytest.raises(SystemExit):
        cli.main(["update", "1", "--price", "abc"])


@patch("cli.requests.request")
def test_update_price_and_stock(mock_req, capsys):
    mock_req.return_value = fake_response(200, {**ITEM, "price": 5.0, "stock": 7})
    assert cli.main(["update", "1", "--price", "5", "--stock", "7"]) == 0
    assert mock_req.call_args.args == ("PATCH", "http://127.0.0.1:5000/inventory/1")
    assert mock_req.call_args.kwargs["json"] == {"price": 5.0, "stock": 7}
    assert "Updated item 1" in capsys.readouterr().out


@patch("cli.requests.request")
def test_update_with_nothing_to_change(mock_req, capsys):
    assert cli.main(["update", "1"]) == 1
    mock_req.assert_not_called()
    assert "Nothing to update" in capsys.readouterr().err


@patch("cli.requests.request")
def test_delete_with_yes_flag(mock_req, capsys):
    mock_req.return_value = fake_response(200, {"message": "Item 1 deleted", "item": ITEM})
    assert cli.main(["delete", "1", "--yes"]) == 0
    assert mock_req.call_args.args[0] == "DELETE"
    assert "Item 1 deleted" in capsys.readouterr().out


@patch("cli.requests.request")
def test_delete_cancelled_makes_no_request(mock_req, capsys):
    with patch("builtins.input", return_value="n"):
        assert cli.main(["delete", "1"]) == 0
    mock_req.assert_not_called()
    assert "Cancelled" in capsys.readouterr().out


@patch("cli.requests.request")
def test_delete_confirmed(mock_req):
    mock_req.return_value = fake_response(200, {"message": "Item 1 deleted", "item": ITEM})
    with patch("builtins.input", return_value="y"):
        assert cli.main(["delete", "1"]) == 0
    mock_req.assert_called_once()


@patch("cli.requests.request")
def test_find_by_barcode(mock_req, capsys):
    mock_req.return_value = fake_response(200, EXTERNAL)
    assert cli.main(["find", "--barcode", "12345678"]) == 0
    assert mock_req.call_args.args[1].endswith("/external/barcode/12345678")
    assert "Found Product" in capsys.readouterr().out


@patch("cli.requests.request")
def test_find_by_name(mock_req, capsys):
    mock_req.return_value = fake_response(200, {"count": 1, "results": [EXTERNAL]})
    assert cli.main(["find", "--name", "found", "--limit", "3"]) == 0
    assert mock_req.call_args.kwargs["params"] == {"name": "found", "limit": 3}
    assert "Result 1" in capsys.readouterr().out


def test_find_requires_barcode_or_name():
    with pytest.raises(SystemExit):
        cli.main(["find"])
    with pytest.raises(SystemExit):
        cli.main(["find", "--barcode", "1", "--name", "x"])


@patch("cli.requests.request")
def test_find_reports_external_api_failure(mock_req, capsys):
    mock_req.return_value = fake_response(502, {"error": "Could not reach OpenFoodFacts."})
    assert cli.main(["find", "--barcode", "12345678"]) == 1
    assert "Could not reach OpenFoodFacts" in capsys.readouterr().err


@patch("cli.requests.request")
def test_import_by_barcode(mock_req, capsys):
    mock_req.return_value = fake_response(201, ITEM)
    assert cli.main(["import", "--barcode", "12345678", "--price", "2.5", "--stock", "10"]) == 0
    assert mock_req.call_args.args == ("POST", "http://127.0.0.1:5000/inventory/import")
    assert mock_req.call_args.kwargs["json"] == {"price": 2.5, "stock": 10, "barcode": "12345678"}
    assert "Imported from OpenFoodFacts" in capsys.readouterr().out


@patch("cli.requests.request")
def test_import_by_name(mock_req):
    mock_req.return_value = fake_response(201, ITEM)
    cli.main(["import", "--name", "almond milk"])
    assert mock_req.call_args.kwargs["json"] == {"price": 0, "stock": 0, "name": "almond milk"}


@patch("cli.requests.request")
def test_enrich_and_low_stock(mock_req, capsys):
    mock_req.return_value = fake_response(200, ITEM)
    assert cli.main(["enrich", "1"]) == 0
    assert mock_req.call_args.args[0] == "PATCH"
    mock_req.return_value = fake_response(200, {"threshold": 10, "count": 1, "items": [ITEM]})
    assert cli.main(["low-stock"]) == 0
    assert "at or below 10" in capsys.readouterr().out


@patch("cli.requests.request", side_effect=requests.exceptions.ConnectionError)
def test_api_down_gives_friendly_message(_mock, capsys):
    assert cli.main(["list"]) == 1
    assert "Cannot connect" in capsys.readouterr().err


@patch("cli.requests.request", side_effect=requests.exceptions.Timeout)
def test_api_timeout_message(_mock, capsys):
    assert cli.main(["list"]) == 1
    assert "too long" in capsys.readouterr().err


@patch("cli.requests.request")
def test_non_json_response(mock_req, capsys):
    response = MagicMock(status_code=500)
    response.json.side_effect = ValueError
    mock_req.return_value = response
    assert cli.main(["list"]) == 1
    assert "Unexpected response" in capsys.readouterr().err


@patch("cli.requests.request")
def test_custom_api_url_from_env(mock_req, monkeypatch):
    monkeypatch.setenv("INVENTORY_API_URL", "http://example.test:9000/")
    mock_req.return_value = fake_response(200, {"count": 0, "items": []})
    cli.main(["list"])
    assert mock_req.call_args.args[1] == "http://example.test:9000/inventory"

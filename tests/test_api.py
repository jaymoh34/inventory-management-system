"""Tests for the Flask endpoints. OpenFoodFacts calls are always mocked."""
from unittest.mock import patch

from app.errors import ExternalAPIError, ProductNotFoundError

OFF_RESULT = {
    "status": 1,
    "barcode": "3017620422003",
    "product": {
        "product_name": "Imported Spread", "brands": "TestBrand",
        "ingredients_text": "Sugar, hazelnuts", "categories": "Spreads",
        "quantity": "200 g", "nutriscore_grade": "d", "image_url": "http://img/x.jpg",
    },
}


def make_result(barcode="11112222"):
    return {**OFF_RESULT, "barcode": barcode}


# ------------------------------------------------------------------ GET
def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_list_items(client):
    data = client.get("/inventory").get_json()
    assert data["count"] == 8 and len(data["items"]) == 8


def test_list_items_with_search(client):
    data = client.get("/inventory?search=nutella").get_json()
    assert [i["id"] for i in data["items"]] == [2]


def test_search_no_match_returns_empty_list(client):
    assert client.get("/inventory?search=zzzz").get_json()["count"] == 0


def test_low_stock_default_threshold(client):
    data = client.get("/inventory/low-stock").get_json()
    assert {i["id"] for i in data["items"]} == {5, 7}


def test_low_stock_invalid_threshold(client):
    assert client.get("/inventory/low-stock?threshold=abc").status_code == 400
    assert client.get("/inventory/low-stock?threshold=-1").status_code == 400


def test_get_single_item(client):
    response = client.get("/inventory/1")
    assert response.status_code == 200
    assert response.get_json()["product"]["product_name"] == "Organic Almond Milk"


def test_get_missing_item_404(client):
    response = client.get("/inventory/999")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_get_non_integer_id_returns_json_404(client):
    response = client.get("/inventory/abc")
    assert response.status_code == 404
    assert response.is_json


# ----------------------------------------------------------------- POST
def test_create_item(client):
    payload = {"product_name": "Green Tea", "brands": "Lipton", "price": 4.5, "stock": 20,
               "barcode": "87654321"}
    response = client.post("/inventory", json=payload)
    assert response.status_code == 201
    created = response.get_json()
    assert created["id"] == 9 and created["price"] == 4.5 and created["source"] == "manual"
    assert client.get("/inventory/9").status_code == 200
    assert client.get("/inventory").get_json()["count"] == 9


def test_create_item_minimal(client):
    response = client.post("/inventory", json={"product_name": "Plain"})
    assert response.status_code == 201
    assert response.get_json()["stock"] == 0


def test_create_requires_product_name(client):
    assert client.post("/inventory", json={"price": 1}).status_code == 400
    assert client.post("/inventory", json={"product_name": "   "}).status_code == 400


def test_create_rejects_bad_numbers(client):
    for bad in ({"price": -1}, {"price": "5"}, {"stock": 1.5}, {"stock": -3}, {"stock": True}):
        response = client.post("/inventory", json={"product_name": "X", **bad})
        assert response.status_code == 400, bad


def test_create_rejects_bad_barcode(client):
    assert client.post("/inventory", json={"product_name": "X", "barcode": "12ab"}).status_code == 400


def test_create_rejects_unknown_field(client):
    assert client.post("/inventory", json={"product_name": "X", "colour": "red"}).status_code == 400


def test_create_rejects_invalid_json(client):
    response = client.post("/inventory", data="not json", content_type="application/json")
    assert response.status_code == 400
    assert client.post("/inventory", json=[1, 2]).status_code == 400
    assert client.post("/inventory").status_code == 400


def test_create_duplicate_barcode_conflict(client):
    response = client.post("/inventory", json={"product_name": "Dup", "barcode": "3017620422003"})
    assert response.status_code == 409


# ---------------------------------------------------------------- PATCH
def test_patch_price_and_stock(client):
    response = client.patch("/inventory/1", json={"price": 4.25, "stock": 10})
    assert response.status_code == 200
    body = response.get_json()
    assert body["price"] == 4.25 and body["stock"] == 10
    assert client.get("/inventory/1").get_json()["stock"] == 10


def test_patch_product_name(client):
    body = client.patch("/inventory/1", json={"product_name": "Oat Milk"}).get_json()
    assert body["product"]["product_name"] == "Oat Milk"
    assert body["product"]["brands"] == "Silk"  # untouched


def test_patch_stock_zero_allowed(client):
    assert client.patch("/inventory/1", json={"stock": 0}).status_code == 200


def test_patch_missing_item(client):
    assert client.patch("/inventory/999", json={"price": 1}).status_code == 404


def test_patch_invalid_values(client):
    assert client.patch("/inventory/1", json={}).status_code == 400
    assert client.patch("/inventory/1", json={"stock": -1}).status_code == 400
    assert client.patch("/inventory/1", json={"price": "free"}).status_code == 400
    assert client.patch("/inventory/1", json={"colour": "red"}).status_code == 400
    assert client.patch("/inventory/1", json={"product_name": ""}).status_code == 400
    assert client.patch("/inventory/1", data="oops", content_type="application/json").status_code == 400


def test_patch_barcode_conflict(client):
    assert client.patch("/inventory/1", json={"barcode": "3017620422003"}).status_code == 409


def test_patch_same_barcode_on_same_item_is_ok(client):
    assert client.patch("/inventory/2", json={"barcode": "3017620422003"}).status_code == 200


# --------------------------------------------------------------- DELETE
def test_delete_item(client):
    response = client.delete("/inventory/1")
    assert response.status_code == 200
    assert response.get_json()["item"]["id"] == 1
    assert client.get("/inventory/1").status_code == 404
    assert client.get("/inventory").get_json()["count"] == 7


def test_delete_missing_item(client):
    assert client.delete("/inventory/999").status_code == 404


def test_delete_twice(client):
    client.delete("/inventory/3")
    assert client.delete("/inventory/3").status_code == 404


def test_method_not_allowed_returns_json(client):
    response = client.put("/inventory")
    assert response.status_code == 405 and response.is_json


# ------------------------------------------------------ external routes
@patch("app.openfoodfacts.get_product_by_barcode")
def test_external_barcode(mock_get, client):
    mock_get.return_value = OFF_RESULT
    response = client.get("/external/barcode/3017620422003")
    assert response.status_code == 200
    assert response.get_json()["product"]["product_name"] == "Imported Spread"
    mock_get.assert_called_once_with("3017620422003")


@patch("app.openfoodfacts.get_product_by_barcode", side_effect=ProductNotFoundError("nope"))
def test_external_barcode_not_found(_mock, client):
    assert client.get("/external/barcode/00000000").status_code == 404


@patch("app.openfoodfacts.get_product_by_barcode", side_effect=ExternalAPIError("down", 502))
def test_external_barcode_api_failure(_mock, client):
    response = client.get("/external/barcode/12345678")
    assert response.status_code == 502 and response.get_json()["error"] == "down"


@patch("app.openfoodfacts.search_products_by_name")
def test_external_search(mock_search, client):
    mock_search.return_value = [OFF_RESULT, make_result()]
    data = client.get("/external/search?name=nutella&limit=2").get_json()
    assert data["count"] == 2
    mock_search.assert_called_once_with("nutella", limit=2)


def test_external_search_validation(client):
    assert client.get("/external/search").status_code == 400
    assert client.get("/external/search?name=%20").status_code == 400
    assert client.get("/external/search?name=x&limit=abc").status_code == 400
    assert client.get("/external/search?name=x&limit=99").status_code == 400


@patch("app.openfoodfacts.search_products_by_name", side_effect=ExternalAPIError("timeout", 504))
def test_external_search_timeout(_mock, client):
    assert client.get("/external/search?name=milk").status_code == 504


# ---------------------------------------------------------------- import
@patch("app.openfoodfacts.get_product_by_barcode")
def test_import_by_barcode(mock_get, client):
    mock_get.return_value = make_result("11112222")
    response = client.post("/inventory/import", json={"barcode": "11112222", "price": 2.5, "stock": 12})
    assert response.status_code == 201
    item = response.get_json()
    assert item["id"] == 9 and item["source"] == "openfoodfacts"
    assert item["price"] == 2.5 and item["stock"] == 12
    assert item["product"]["product_name"] == "Imported Spread"
    assert client.get("/inventory").get_json()["count"] == 9


@patch("app.openfoodfacts.search_products_by_name")
def test_import_by_name(mock_search, client):
    mock_search.return_value = [make_result("22223333")]
    response = client.post("/inventory/import", json={"name": "spread"})
    assert response.status_code == 201
    assert response.get_json()["barcode"] == "22223333"
    mock_search.assert_called_once_with("spread", limit=1)


def test_import_requires_exactly_one_identifier(client):
    assert client.post("/inventory/import", json={}).status_code == 400
    assert client.post("/inventory/import", json={"barcode": "12345678", "name": "x"}).status_code == 400


def test_import_validates_price_and_stock_before_calling_api(client):
    with patch("app.openfoodfacts.get_product_by_barcode") as mock_get:
        assert client.post("/inventory/import", json={"barcode": "12345678", "price": -5}).status_code == 400
        assert client.post("/inventory/import", json={"barcode": "12345678", "stock": 1.2}).status_code == 400
        mock_get.assert_not_called()


@patch("app.openfoodfacts.get_product_by_barcode")
def test_import_duplicate_barcode(mock_get, client):
    mock_get.return_value = make_result("3017620422003")
    assert client.post("/inventory/import", json={"barcode": "3017620422003"}).status_code == 409


@patch("app.openfoodfacts.get_product_by_barcode", side_effect=ExternalAPIError("down", 502))
def test_import_api_failure_leaves_inventory_unchanged(_mock, client):
    assert client.post("/inventory/import", json={"barcode": "12345678"}).status_code == 502
    assert client.get("/inventory").get_json()["count"] == 8


@patch("app.openfoodfacts.get_product_by_barcode", side_effect=ProductNotFoundError("none"))
def test_import_product_not_found(_mock, client):
    assert client.post("/inventory/import", json={"barcode": "12345678"}).status_code == 404


# ---------------------------------------------------------------- enrich
@patch("app.openfoodfacts.get_product_by_barcode")
def test_enrich_fills_only_empty_fields(mock_get, client):
    created = client.post("/inventory", json={"product_name": "My Spread", "barcode": "99998888"}).get_json()
    mock_get.return_value = make_result("99998888")
    response = client.patch(f"/inventory/{created['id']}/enrich")
    assert response.status_code == 200
    product = response.get_json()["product"]
    assert product["product_name"] == "My Spread"          # kept
    assert product["ingredients_text"] == "Sugar, hazelnuts"  # filled
    assert product["brands"] == "TestBrand"                # filled


def test_enrich_requires_barcode(client):
    created = client.post("/inventory", json={"product_name": "No Code"}).get_json()
    assert client.patch(f"/inventory/{created['id']}/enrich").status_code == 400


def test_enrich_missing_item(client):
    assert client.patch("/inventory/999/enrich").status_code == 404


@patch("app.openfoodfacts.get_product_by_barcode", side_effect=ExternalAPIError("down", 502))
def test_enrich_api_failure(_mock, client):
    assert client.patch("/inventory/1/enrich").status_code == 502

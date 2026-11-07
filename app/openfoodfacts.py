"""Client for the OpenFoodFacts API (https://world.openfoodfacts.org).

Functions return data shaped like the real API: {"status": 1, "product": {...}}
and raise ExternalAPIError subclasses when something goes wrong.
"""
import requests

from app.errors import ExternalAPIError, ProductNotFoundError, ValidationError

BASE_URL = "https://world.openfoodfacts.org"
TIMEOUT = 10  # seconds
HEADERS = {"User-Agent": "InventoryManagementSystem/1.0 (student project)"}
PRODUCT_FIELDS = (
    "product_name", "brands", "ingredients_text", "categories",
    "quantity", "nutriscore_grade", "image_url",
)
_FIELDS_PARAM = ",".join(("code",) + PRODUCT_FIELDS)


def _get_json(url, params):
    """GET a URL and return parsed JSON, translating failures into ExternalAPIError."""
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        raise ExternalAPIError("OpenFoodFacts timed out. Please try again.", 504)
    except requests.exceptions.RequestException:
        raise ExternalAPIError("Could not reach OpenFoodFacts. Check your connection.", 502)

    if response.status_code != 200:
        raise ExternalAPIError(f"OpenFoodFacts returned HTTP {response.status_code}", 502)
    try:
        return response.json()
    except ValueError:
        raise ExternalAPIError("OpenFoodFacts returned an invalid response", 502)


def _normalise(raw):
    """Keep only the fields we store, defaulting missing values to ''."""
    return {field: str(raw.get(field) or "").strip() for field in PRODUCT_FIELDS}


def get_product_by_barcode(barcode):
    """Fetch one product by barcode. Returns {"status", "barcode", "product"}."""
    barcode = str(barcode).strip()
    if not barcode.isdigit() or not 8 <= len(barcode) <= 14:
        raise ValidationError("barcode must be 8-14 digits")

    data = _get_json(f"{BASE_URL}/api/v2/product/{barcode}.json", {"fields": _FIELDS_PARAM})
    raw = data.get("product") if isinstance(data, dict) else None
    if not isinstance(data, dict) or data.get("status") != 1 or not raw:
        raise ProductNotFoundError(f"No product found on OpenFoodFacts for barcode {barcode}")
    return {"status": 1, "barcode": barcode, "product": _normalise(raw)}


def search_products_by_name(name, limit=5):
    """Search products by name. Returns a list of {"status", "barcode", "product"}."""
    name = (name or "").strip()
    if not name:
        raise ValidationError("name is required")

    params = {
        "search_terms": name, "search_simple": 1, "action": "process",
        "json": 1, "page_size": limit, "fields": _FIELDS_PARAM,
    }
    data = _get_json(f"{BASE_URL}/cgi/search.pl", params)
    raw_products = data.get("products", []) if isinstance(data, dict) else []

    results = [
        {"status": 1, "barcode": str(p.get("code") or ""), "product": _normalise(p)}
        for p in raw_products
        if isinstance(p, dict) and p.get("product_name")
    ]
    if not results:
        raise ProductNotFoundError(f"No products found on OpenFoodFacts matching '{name}'")
    return results[:limit]
